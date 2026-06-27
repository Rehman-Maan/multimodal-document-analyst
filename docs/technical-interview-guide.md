# Technical Interview Guide

This guide explains Multimodal Document Analyst from an engineering and interview-preparation angle. Use it to understand the architecture, defend design decisions, and answer technical questions clearly.

## One-Minute Project Explanation

Multimodal Document Analyst is a Django-based document AI workflow. Users upload PDFs or images into a workspace, the app validates and processes those files in the background, extracts page text and previews, maps document content into structured schema fields, routes uncertain fields to human review, supports cited chat over each document, exports reviewed values as JSON/CSV, and scores extraction quality with evaluation reports.

The strongest interview framing is:

> I built a production-style document AI system, not just a PDF chatbot. It combines upload validation, asynchronous processing, schema-based extraction, confidence scoring, human review, cited document Q&A, exports, audit events, evaluation metrics, Docker, tests, Playwright E2E, and GitHub Actions CI.

## System Architecture

```text
Browser
  |
  | HTML forms, Django templates, DRF APIs
  v
Django Web App
  |
  +--> PostgreSQL
  |      - users, workspaces, documents, pages
  |      - extraction schemas, runs, fields
  |      - review tasks, chat sessions, exports, evaluations, audit events
  |
  +--> Local Media Storage
  |      - original uploaded files
  |      - rendered page images
  |      - generated JSON/CSV exports
  |
  +--> Redis
  |      - Celery broker/result backend
  |
  +--> Celery Worker
  |      - document processing
  |      - page extraction/rendering
  |      - chat indexing jobs
  |
  +--> AI/Retrieval Services
         - local deterministic fallback extraction
         - optional OpenAI embeddings and answers
         - chunking, retrieval, cited answers
```

## Core Tech Stack

- **Django**: main application, templates, auth, ORM, admin, routing.
- **Django REST Framework**: API endpoints for workspaces, documents, schemas, review, chat, exports, and evaluations.
- **PostgreSQL / pgvector-ready image**: production-style relational storage with vector-search-ready infrastructure.
- **Redis + Celery**: asynchronous document processing and indexing.
- **PyMuPDF**: PDF text extraction and page rendering.
- **Pillow**: image normalization and preview generation.
- **OpenAI API optional path**: embeddings and cited chat answers when `OPENAI_API_KEY` is configured.
- **Local fallbacks**: deterministic extraction, embeddings, and answer logic so tests and demos work without external API calls.
- **Docker Compose**: local multi-service development.
- **pytest + pytest-django**: unit/integration-style test coverage.
- **Playwright**: browser smoke test for login, dashboard, upload, and processing.
- **GitHub Actions + Trivy + Dependabot**: CI, image build, security scanning, dependency monitoring.

## Django App Responsibilities

### `apps.accounts`

Handles signup, login, logout, and demo-user seeding.

Key files:

- `apps/accounts/views.py`
- `apps/accounts/forms.py`
- `apps/accounts/management/commands/seed_demo_users.py`

Interview explanation:

> I used Django auth for standard session-based login and added a seed command for repeatable demo users across roles.

### `apps.workspaces`

Models multi-tenant workspace ownership and role-based membership.

Important models:

- `Workspace`
- `WorkspaceMembership`

Roles:

- owner
- admin
- reviewer
- analyst
- viewer

Important methods:

- `workspace.user_can_view(user)`
- `workspace.user_can_manage(user)`
- `workspace.membership_for(user)`
- `membership.can_review_documents`

Interview explanation:

> Workspace scoping is the core isolation boundary. Almost every query filters by workspace to prevent cross-workspace document access.

### `apps.documents`

Owns upload, metadata, document status, page records, and document detail views.

Important models:

- `UploadedDocument`
- `DocumentPage`

Document statuses:

- uploaded
- validating
- processing
- processed
- needs_review
- approved
- failed
- archived

Key files:

- `apps/documents/models.py`
- `apps/documents/forms.py`
- `apps/documents/views.py`
- `apps/documents/tasks.py`
- `services/document_parsing/processors.py`

Interview explanation:

> Upload and processing are separated. The web request stores metadata and queues a Celery task; the worker extracts text, renders previews, and updates processing state.

### `apps.schemas`

Defines document types and extraction schemas.

Important models:

- `DocumentType`
- `ExtractionSchema`

Schemas are JSON definitions such as:

```json
{
  "fields": [
    {"name": "vendor_name", "type": "string", "required": true},
    {"name": "total_amount", "type": "decimal", "required": true}
  ]
}
```

Interview explanation:

> Schemas make extraction configurable. Instead of hard-coding invoice or receipt fields, a workspace can define fields and validation rules in JSON.

### `apps.extraction`

Stores extraction attempts and field-level outputs.

Important models:

- `ExtractionRun`
- `ExtractedField`

Important fields:

- `field_name`
- `raw_value`
- `normalized_value`
- `confidence`
- `source_page`
- `source_text`
- `validation_errors`

Key files:

- `apps/extraction/services.py`
- `services/llm_gateway/local_extractor.py`
- `services/schema_validation/validators.py`

Interview explanation:

> Extraction is stored as an auditable run. Each field has normalized value, confidence, and source evidence so review and exports can rely on structured records rather than raw model text.

### `apps.review`

Implements human review for low-confidence or invalid fields.

Important model:

- `ReviewTask`

Key services:

- `route_review_tasks`
- `correct_field`
- `reject_task`
- `approve_document_if_ready`

Interview explanation:

> The review queue is the human-in-the-loop layer. Any field below confidence threshold or with validation errors creates a task. Reviewers can correct it, approve it, or reject it. This prevents uncertain AI output from silently becoming final data.

### `apps.chat`

Implements document-specific chat with retrieval and citations.

Important models:

- `DocumentChunk`
- `ChatSession`
- `ChatMessage`

Key services:

- `services/retrieval/chunking.py`
- `services/retrieval/indexing.py`
- `services/retrieval/search.py`
- `services/retrieval/answers.py`

Interview explanation:

> Chat is scoped to one document. Page text is chunked and embedded, the question retrieves relevant chunks, and the answer includes citations. If OpenAI fails or is not configured, deterministic local retrieval still works for tests and demos.

### `apps.exports`

Builds downloadable JSON and CSV outputs from reviewed field values.

Key files:

- `apps/exports/services.py`
- `services/export_builder/builders.py`

Interview explanation:

> Exports use reviewed or normalized field values from the latest extraction run. That means human corrections are included in downstream JSON/CSV files.

### `apps.evaluations`

Stores and displays extraction-quality reports.

Key files:

- `services/evaluation/scoring.py`
- `services/evaluation/reports.py`
- `apps/evaluations/management/commands/run_extraction_eval.py`

Tracked metrics:

- classification accuracy
- field exact match
- precision
- recall
- F1
- critical-field exact match
- missing-field rate
- invalid-output rate

Interview explanation:

> I added evaluation because AI features need measurable quality. The app can score extraction outputs against synthetic gold datasets and save reports to a workspace.

### `apps.audit`

Stores important workflow events.

Examples:

- review correction
- review approval
- document approval
- export creation

Interview explanation:

> Audit events make the workflow traceable, which matters for operational document systems where users need to know who changed what and when.

## End-to-End Flow

### 1. User Signs In

Django auth handles sessions. The seeded demo user `demo_owner` belongs to `Demo Workspace`.

### 2. User Uploads a File

The upload form accepts:

- PDF
- PNG
- JPG/JPEG
- TIFF

Validation happens in `services/file_validation/validators.py`.

Checks include:

- extension
- content type
- file size

The document starts as `uploaded`.

### 3. Celery Processes the Document

`apps/documents/processing.py` calls:

```python
process_document.delay(document.pk)
```

The Celery task lives in:

```text
apps/documents/tasks.py
```

The worker:

1. marks the document as `processing`
2. calls `process_uploaded_document`
3. creates `DocumentPage` records
4. sets status to `processed`
5. records page count and completion time

PDF processing uses PyMuPDF to:

- extract text
- render page images

Image processing uses Pillow to:

- normalize orientation
- create a page preview

### 4. Structured Extraction Runs

The user chooses a schema and clicks **Extract fields**.

The extraction service:

1. reads document page text
2. builds fields based on schema JSON
3. extracts raw and normalized values
4. assigns confidence
5. validates against schema
6. stores an `ExtractionRun`
7. stores `ExtractedField` rows
8. routes uncertain fields to review

Current extraction path includes a deterministic local extractor. This keeps demos and tests stable even without OpenAI.

### 5. Review Queue Handles Uncertainty

`route_review_tasks` creates tasks when:

- confidence is below threshold
- validation errors exist
- required values are missing

Reviewers can:

- correct a field
- approve a field
- reject a task
- approve the whole document once open tasks are closed

### 6. Document Chat Uses Retrieval

For chat:

1. page text is chunked
2. each chunk gets an embedding
3. user question is embedded
4. search finds relevant chunks
5. answer service combines extracted fields and chunks
6. answer is stored as `ChatMessage`
7. citation metadata is stored as JSON on the assistant message

The answer service prefers:

- OpenAI answer if API is configured and available
- local extractive answer if not

Important design detail:

> The chat prompt includes the current date and temporal status notes so date ranges like `Nov 2021 - Jun 2025` are interpreted as completed when current date is after June 2025, while `Present` is treated as ongoing.

### 7. Exports Use Reviewed Values

JSON/CSV exports are built from:

- latest extraction run
- normalized values
- reviewed values when available

This makes export a post-review deliverable rather than raw model output.

### 8. Evaluation Measures Quality

Gold datasets live in:

```text
eval/datasets/
```

Run:

```powershell
python manage.py run_extraction_eval eval/datasets/invoices_gold.yml
```

The scoring layer compares predicted fields to expected fields and reports metrics.

## Important Design Decisions

### Why Django Templates Instead of React?

The app is workflow-heavy but not yet interaction-heavy enough to require a separate frontend. Django templates let the project move fast while still showing a professional product UI.

Interview answer:

> I chose Django templates because the core challenge was backend workflow, document processing, review logic, retrieval, and evaluation. A separate frontend would add complexity without improving the core demonstration. If the project grew into advanced annotation or bounding-box editing, React would make more sense.

### Why Celery?

Document processing can be slow. PDF rendering, OCR, extraction, embeddings, and evaluation should not block HTTP requests.

Interview answer:

> Celery gives the app a production-style async boundary. The request creates the document and queues work; the worker handles processing and updates status.

### Why Store Extracted Fields Separately?

Storing fields as rows makes review, validation, correction, export, and audit easier than keeping one JSON blob only.

Interview answer:

> I still store raw output at run level, but field rows are better for review queues, confidence thresholds, source references, exports, and per-field evaluation.

### Why Add Local Fallbacks?

External model APIs can fail, cost money, or be unavailable in CI.

Interview answer:

> The app is OpenAI-ready, but tests and demos should not depend on API availability. Local fallbacks make CI deterministic and keep the product usable offline.

### Why Include Evaluation?

AI demos can look good manually but fail silently. Evaluation makes quality measurable.

Interview answer:

> I wanted to show that I can test AI behavior beyond screenshots. The evaluation harness tracks field precision, recall, F1, exact match, missing values, and critical-field accuracy.

### Why Human Review?

Document AI often affects business records, invoices, or compliance data. Low-confidence output should not become final without review.

Interview answer:

> The human review loop is the safety layer. It turns model output into reviewed operational data.

## Data Model Summary

```text
User
  |
WorkspaceMembership
  |
Workspace
  |
  +--> UploadedDocument
  |      |
  |      +--> DocumentPage
  |      +--> ExtractionRun
  |      |      |
  |      |      +--> ExtractedField
  |      |
  |      +--> ReviewTask
  |      +--> ChatSession
  |      |      |
  |      |      +--> ChatMessage
  |      |
  |      +--> DocumentChunk
  |      +--> ExportRecord
  |
  +--> DocumentType
  +--> ExtractionSchema
  +--> EvaluationRun
  +--> AuditEvent
```

## Security and Privacy Talking Points

- `.env` is ignored and secrets come from environment variables.
- Uploaded media is ignored from version control.
- Workspaces scope access to documents.
- Upload validation restricts file types and size.
- Production settings enable secure cookies and SSL redirect hooks.
- For portfolio demos, use synthetic sample documents instead of real sensitive files.
- AI calls should avoid unnecessary sensitive data in production.

## Testing and CI

Local checks:

```powershell
python -m ruff check .
python manage.py check --settings=config.settings.test
python manage.py makemigrations --check --dry-run --settings=config.settings.test
python -m pytest --ds=config.settings.test
python -m pytest tests/e2e --ds=config.settings.test
```

GitHub Actions runs:

- Ruff lint
- Django system check
- migration drift check
- pytest
- Playwright browser smoke test
- Docker image build
- Trivy image scan

Interview explanation:

> The CI pipeline tests both backend behavior and a browser-level happy path, then builds and scans the Docker image. That gives confidence the app works as a deployable product, not just locally.

## Demo Walkthrough

Use this flow in interviews:

1. Sign in as `demo_owner`.
2. Open Demo Workspace.
3. Show dashboard metrics and workflow steps.
4. Open document library.
5. Open `Acme Invoice INV-1001`.
6. Show processed page text and rendered page link.
7. Show extracted fields with confidence and source text.
8. Show review task / approval workflow.
9. Open chat and ask invoice question.
10. Show cited answer.
11. Export JSON/CSV.
12. Open evaluation report.
13. Mention CI pipeline and tests.

## Interview Q&A

### What problem does this project solve?

It helps teams turn messy business documents into validated structured data. The system handles upload, processing, extraction, review, chat, exports, and evaluation.

### How is it different from a normal PDF chatbot?

A normal PDF chatbot usually only answers questions. This app has a full document operations workflow: schema extraction, validation, confidence scoring, review queue, audited corrections, exports, and quality evaluation.

### How do citations work?

The app stores page text as chunks. When a user asks a question, retrieval ranks chunks and extracted fields. The answer service returns an answer plus citation metadata, including page number and excerpt.

### How do you prevent hallucination?

The answer service instructs the model to use only provided document context. It also falls back to extractive local answers and shows citations. If evidence is missing, it says there is not enough evidence.

### What happens if OpenAI is down?

The app falls back to local embeddings, local field extraction, and local cited answers. This keeps tests and demos working without external dependencies.

### Why use PostgreSQL and not only files?

Documents need relational metadata: workspaces, members, review tasks, extracted fields, chat sessions, exports, and audit events. PostgreSQL is a strong fit for workflow state.

### Why use Redis?

Redis is the Celery broker/result backend. It coordinates background jobs between Django and workers.

### How would you scale this?

- Move media to S3/MinIO.
- Add multiple Celery workers.
- Use managed PostgreSQL.
- Use pgvector or Qdrant for larger vector search.
- Add object-level permissions and rate limits.
- Add OCR workers for scanned documents.
- Add observability with logs, metrics, and tracing.

### What are the current limitations?

- Evaluation datasets are small and synthetic.
- OCR is not a full production OCR pipeline yet.
- Page previews are basic; no bounding-box annotation UI.
- Local extraction is heuristic.
- Production storage is local media in the demo.
- More document types and messy scans are needed for a stronger benchmark.

### What would you improve next?

- S3/MinIO object storage.
- OCR fallback using Tesseract/EasyOCR or a hosted vision model.
- Bounding-box citations and preview highlighting.
- Batch uploads.
- Better schema builder UI.
- Larger gold datasets.
- Deployment to a public host.
- Observability dashboard.

## Resume Bullet Options

Use or adapt these:

- Built a Django document AI workflow for PDF/image upload, background processing, schema-based extraction, human review, cited chat, JSON/CSV exports, and evaluation.
- Implemented workspace-scoped document processing with Celery, Redis, PostgreSQL, file validation, rendered page previews, and reviewable extracted fields.
- Designed cited document Q&A using chunking, embeddings, retrieval, OpenAI-ready answer generation, and deterministic local fallbacks for CI stability.
- Added extraction quality evaluation with field-level precision, recall, F1, exact match, critical-field accuracy, and missing-field metrics.
- Shipped portfolio-grade DevOps with Docker Compose, pytest, Playwright E2E smoke tests, GitHub Actions, Dependabot, and Trivy scanning.

## Short Technical Pitch

> This is a Django document AI system designed around trust and operations. A user uploads a PDF or image, Celery processes it into page records, a schema-based extractor creates fields with confidence and source evidence, low-confidence fields enter human review, approved data can be exported, and users can ask cited questions over the document. I added evaluation and CI so the AI behavior is measurable and the app is deployable.

