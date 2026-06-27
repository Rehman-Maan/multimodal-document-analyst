# Multimodal Document Analyst: Complete Build Plan

## 1. Project Goal

Build a production-style Django application that lets users upload PDFs, receipts, invoices, forms, scans, and images, then ask questions, extract structured fields, compare documents, and send uncertain results to a human review queue.

The project should demonstrate that you can build an AI document workflow, not just "chat with a PDF." It should include file upload, document parsing, OCR or vision-based extraction, structured JSON output, validation, confidence scoring, review queues, audit logs, evaluation, and deployment.

## 2. Why This Project Matters

Many businesses still process messy documents manually: invoices, receipts, contracts, onboarding forms, insurance forms, shipping documents, and compliance files. A document analyst that can read, extract, explain, and route uncertain cases is a high-value AI application.

This project demonstrates:

- multimodal AI workflows
- document parsing and OCR
- structured extraction
- schema validation
- chat over uploaded files
- human review and correction loops
- audit-friendly document processing
- Django file handling
- background processing with Celery
- evaluation for extraction accuracy

The strongest portfolio angle is: "I built a document AI system that turns messy PDFs and images into validated structured data, while keeping humans in the loop for uncertain cases."

## 3. Target Users

### Operations Specialist

Uses the system to:

- upload receipts, invoices, and forms
- review extracted fields
- correct errors
- approve documents
- export clean data

### Analyst

Uses the system to:

- ask questions about documents
- compare document versions
- inspect evidence snippets
- download structured outputs

### Admin

Uses the system to:

- define extraction schemas
- monitor processing failures
- manage review queues
- inspect audit logs
- run evaluation reports

## 4. Core Demo Flow

The finished demo should show:

1. User signs in.
2. User creates or selects a workspace.
3. User uploads a receipt, invoice, or form image.
4. Celery starts a background processing job.
5. The system classifies the document type.
6. The system extracts text and visual content.
7. The AI extracts structured fields into JSON.
8. The system validates extracted fields against a schema.
9. Low-confidence fields are highlighted.
10. User opens the review screen and corrects a field.
11. User asks a natural-language question about the document.
12. The answer cites source text, page, or image region where possible.
13. User exports approved structured data as JSON or CSV.

## 5. Recommended Stack

### Backend

- Django
- Django REST Framework
- Celery
- Redis
- PostgreSQL
- pgvector
- object/file storage

### AI and Document Layer

Recommended hosted MVP:

- OpenAI Responses API with text and image input
- OpenAI embeddings
- PyMuPDF or pdfplumber for PDF text extraction
- Pillow for image processing
- pytesseract or EasyOCR as optional OCR baseline
- Pydantic for extraction schemas

Optional advanced stack:

- LayoutLM-style or Donut-style open-source document models
- Hugging Face Transformers
- FastAPI sidecar for heavier inference
- Qdrant for larger vector search

### Frontend

Recommended:

- Django templates plus HTMX
- Alpine.js for field editing and review interactions
- PDF/image preview panel

Alternative:

- React/Vite if you want rich document annotation UX

### Evaluation

- pytest
- pytest-django
- Playwright
- custom extraction gold set
- field-level precision/recall/F1
- exact match on critical fields

### DevOps

- Docker Compose
- GitHub Actions
- Trivy
- Dependabot

## 6. High-Level Architecture

```text
Browser
  |
  | upload, review, chat
  v
Django + DRF
  |
  +--> PostgreSQL
  |      |
  |      +--> documents, pages, extracted fields, reviews
  |      +--> pgvector chunks for document chat
  |
  +--> Object storage or local media
  |      |
  |      +--> original files
  |      +--> page images
  |      +--> generated previews
  |
  +--> Redis
  |      |
  |      +--> Celery broker
  |
  +--> Celery workers
         |
         +--> file validation
         +--> PDF/image preprocessing
         +--> OCR and text extraction
         +--> document classification
         +--> structured extraction
         +--> validation
         +--> embeddings
         +--> evaluation
```

## 7. Suggested Repository Structure

```text
multimodal-document-analyst/
  apps/
    accounts/
    workspaces/
    documents/
    schemas/
    extraction/
    review/
    chat/
    exports/
    evaluations/
    audit/
  config/
    settings/
      base.py
      local.py
      production.py
    urls.py
    asgi.py
    celery.py
  services/
    file_validation/
    document_parsing/
    ocr/
    vision_extraction/
    schema_validation/
    retrieval/
    llm_gateway/
    export_builder/
  workers/
    process_document.py
    extract_fields.py
    create_embeddings.py
    run_eval.py
  eval/
    datasets/
    receipts_gold.yml
    invoices_gold.yml
    forms_gold.yml
    reports/
  tests/
    unit/
    integration/
    e2e/
  templates/
  static/
  media/
  docs/
    architecture.md
    extraction_schemas.md
    evaluation.md
    security.md
  infra/
    docker/
    github_actions/
  docker-compose.yml
  pyproject.toml
  README.md
  LICENSE
```

## 8. Main Django Apps

### accounts

Purpose:

- login/logout
- user profile
- password reset

### workspaces

Purpose:

- organization workspace
- membership
- role-based access

Roles:

- owner
- admin
- reviewer
- analyst
- viewer

### documents

Purpose:

- uploads
- file metadata
- page records
- processing statuses
- document preview references

### schemas

Purpose:

- extraction schema definitions
- document type definitions
- field rules
- validation constraints

Example document types:

- receipt
- invoice
- purchase_order
- insurance_form
- onboarding_form
- contract
- generic_pdf

### extraction

Purpose:

- extracted field values
- confidence scores
- source references
- model output records
- validation errors

### review

Purpose:

- review queue
- human corrections
- approval workflow
- reviewer notes

### chat

Purpose:

- question answering over uploaded documents
- retrieved text chunks
- citations
- chat sessions

### exports

Purpose:

- JSON export
- CSV export
- reviewed-data export
- export history

### evaluations

Purpose:

- gold datasets
- extraction scoring
- document classification scoring
- chat QA scoring

### audit

Purpose:

- upload events
- extraction events
- review corrections
- export events
- model call metadata

## 9. Core Data Models

### Workspace

Fields:

- id
- name
- slug
- created_by
- created_at
- updated_at

### WorkspaceMembership

Fields:

- id
- workspace
- user
- role
- created_at

### DocumentType

Fields:

- id
- workspace
- name
- slug
- description
- active
- created_at
- updated_at

Examples:

- receipt
- invoice
- form
- contract

### ExtractionSchema

Fields:

- id
- workspace
- document_type
- name
- version
- schema_json
- active
- created_by
- created_at
- updated_at

Example `schema_json`:

```json
{
  "fields": [
    {
      "name": "vendor_name",
      "type": "string",
      "required": true
    },
    {
      "name": "total_amount",
      "type": "decimal",
      "required": true
    },
    {
      "name": "transaction_date",
      "type": "date",
      "required": true
    }
  ]
}
```

### UploadedDocument

Fields:

- id
- workspace
- title
- file
- file_type
- document_type
- status
- uploaded_by
- page_count
- error_message
- created_at
- updated_at

Statuses:

- uploaded
- validating
- processing
- needs_review
- approved
- failed
- archived

### DocumentPage

Fields:

- id
- document
- page_number
- text_content
- image
- width
- height
- created_at

### DocumentChunk

Fields:

- id
- workspace
- document
- page
- chunk_index
- content
- source_metadata
- embedding
- created_at

Use pgvector for `embedding`.

### ExtractionRun

Fields:

- id
- document
- schema
- model_name
- status
- raw_model_output
- normalized_output
- average_confidence
- created_at
- completed_at

Statuses:

- queued
- running
- completed
- needs_review
- failed

### ExtractedField

Fields:

- id
- extraction_run
- field_name
- field_type
- raw_value
- normalized_value
- confidence_score
- source_page
- source_text
- source_bbox
- validation_status
- validation_message
- reviewed_value
- reviewed_by
- reviewed_at
- created_at

Validation statuses:

- valid
- warning
- invalid
- missing

### ReviewTask

Fields:

- id
- document
- extraction_run
- assigned_to
- status
- priority
- reason
- created_at
- completed_at

Statuses:

- open
- in_progress
- approved
- rejected
- cancelled

### ChatSession

Fields:

- id
- workspace
- document
- user
- title
- created_at
- updated_at

### ChatMessage

Fields:

- id
- session
- role
- content
- model_name
- created_at

### Citation

Fields:

- id
- assistant_message
- document
- page
- chunk
- quote
- source_bbox
- score
- created_at

### ExportJob

Fields:

- id
- workspace
- document
- export_type
- status
- file
- created_by
- created_at
- completed_at

Export types:

- json
- csv
- reviewed_json
- reviewed_csv

### AuditEvent

Fields:

- id
- workspace
- document
- actor_user
- actor_type
- event_type
- payload
- created_at

## 10. Document Processing Pipeline

### Step 1: Upload

User uploads:

- PDF
- PNG
- JPG
- TIFF
- DOCX if desired later

The system creates `UploadedDocument` with status `uploaded`.

### Step 2: Validation

Validate:

- file extension
- MIME type
- file size
- page count
- image dimensions
- malware scan if available

For MVP:

- limit files to 20 MB
- allow PDF, PNG, JPG
- reject encrypted PDFs

### Step 3: Preprocessing

For PDFs:

- extract text with PyMuPDF or pdfplumber
- render pages to images for preview and vision input
- store one `DocumentPage` per page

For images:

- normalize orientation
- resize if too large
- store one page record
- optionally run OCR baseline

### Step 4: Document Classification

Classify the document type:

- receipt
- invoice
- form
- contract
- generic

For MVP:

- let the user select document type manually
- use AI classification as a suggestion

### Step 5: Structured Extraction

Use the selected `ExtractionSchema`.

Send the model:

- document image or page images
- extracted text
- target schema
- extraction instructions

Return strict JSON.

### Step 6: Validation

Validate extracted JSON against schema.

Check:

- required fields
- date format
- number format
- currency format
- total consistency
- allowed enum values

### Step 7: Confidence and Review Routing

Route to review if:

- required field is missing
- confidence is below threshold
- validation failed
- model output is invalid JSON
- document type is unknown

Recommended MVP threshold:

- below 0.75 confidence triggers review

### Step 8: Embeddings for Document Chat

Split extracted text into chunks.

Store embeddings for:

- OCR text
- PDF text
- extracted field summaries

### Step 9: Chat Over Document

When a user asks a question:

1. embed question
2. retrieve relevant chunks from this document
3. pass retrieved context and selected fields to LLM
4. answer with citations to page or extracted field

## 11. Prompt Contracts

### Document Classification Prompt

```text
You are a document classifier.

Classify the document into exactly one type:
receipt, invoice, purchase_order, insurance_form, onboarding_form, contract, generic_pdf, unknown

Use the visible text and layout clues only.

Return valid JSON:
{
  "document_type": "...",
  "confidence": 0.0,
  "reason": "..."
}

Document text:
{document_text}
```

### Structured Extraction Prompt

```text
You are a careful document extraction system.

Extract fields from the provided document using the target schema.

Rules:
- Return valid JSON only.
- Do not invent missing fields.
- Use null when a value is not visible or not supported.
- Include a confidence score for each field from 0 to 1.
- Include the source page number and supporting text when possible.
- Preserve original values in raw_value.
- Normalize dates, amounts, and IDs into normalized_value.

Target schema:
{schema}

Document text:
{document_text}
```

Expected output:

```json
{
  "fields": [
    {
      "name": "vendor_name",
      "raw_value": "Example Store",
      "normalized_value": "Example Store",
      "confidence": 0.94,
      "source_page": 1,
      "source_text": "Example Store"
    }
  ]
}
```

### Document Chat Prompt

```text
You are a document analyst.

Answer the user's question using only the provided document context and extracted fields.

Rules:
- If the answer is not supported, say: "I don't know based on this document."
- Cite the page, field, or source excerpt used.
- Do not infer values that are not present.
- If a value seems uncertain, mention the uncertainty.

Extracted fields:
{fields}

Document context:
{context}

Question:
{question}
```

## 12. UI Screens

### Login

Simple sign-in page.

### Workspace Dashboard

Shows:

- documents uploaded
- documents needing review
- approved documents
- failed processing jobs
- recent exports
- extraction accuracy from latest eval

### Document Upload

Features:

- drag-and-drop upload
- document type selector
- schema selector
- file validation feedback
- processing status

### Document Library

Shows:

- document title
- type
- status
- uploaded by
- uploaded date
- review status
- export status

### Document Detail

Main layout:

- left: document preview
- center: extracted fields
- right: document chat or processing timeline

Document preview should show:

- PDF page image
- page selector
- zoom controls
- highlighted source text or region if available

### Extraction Review

Shows:

- field name
- extracted value
- confidence
- validation status
- source text
- editable corrected value

Actions:

- approve field
- correct field
- mark missing
- approve document
- send back for reprocessing

### Document Chat

Features:

- ask questions about one document
- answer with page citations
- "I don't know" behavior
- citation click jumps to preview page

### Schema Builder

MVP can be simple JSON editor.

Version 2 can include:

- field builder UI
- required toggle
- type dropdown
- enum values
- validation rules

### Export History

Shows:

- export type
- created by
- status
- download link

### Evaluation Dashboard

Shows:

- extraction exact match
- field-level precision
- field-level recall
- field-level F1
- document classification accuracy
- failed examples

## 13. API Endpoints

Recommended DRF endpoints:

```text
POST   /api/workspaces/
GET    /api/workspaces/

POST   /api/document-types/
GET    /api/document-types/

POST   /api/schemas/
GET    /api/schemas/
GET    /api/schemas/{id}/
PATCH  /api/schemas/{id}/

POST   /api/documents/
GET    /api/documents/
GET    /api/documents/{id}/
POST   /api/documents/{id}/process/
POST   /api/documents/{id}/retry/
POST   /api/documents/{id}/classify/

GET    /api/documents/{id}/pages/
GET    /api/documents/{id}/fields/
PATCH  /api/fields/{id}/review/

POST   /api/documents/{id}/chat/sessions/
GET    /api/chat/sessions/{id}/messages/
POST   /api/chat/sessions/{id}/messages/

GET    /api/review/tasks/
GET    /api/review/tasks/{id}/
POST   /api/review/tasks/{id}/approve/
POST   /api/review/tasks/{id}/reject/

POST   /api/documents/{id}/exports/
GET    /api/exports/
GET    /api/exports/{id}/download/

POST   /api/evaluations/run/
GET    /api/evaluations/
GET    /api/evaluations/{id}/
```

## 14. Development Milestones

### Milestone 1: Project Setup

Estimated time: 1 to 2 days

Deliverables:

- Django project
- PostgreSQL
- Redis
- Celery
- Docker Compose
- media file handling
- health endpoint
- initial README

### Milestone 2: Auth and Workspaces

Estimated time: 2 days

Deliverables:

- login/logout
- workspace model
- memberships
- role helpers
- dashboard shell

### Milestone 3: Document Upload and Library

Estimated time: 2 to 3 days

Deliverables:

- upload screen
- file validation
- document model
- document library
- document detail shell
- status tracking

### Milestone 4: PDF and Image Processing

Estimated time: 4 to 5 days

Deliverables:

- Celery processing task
- PDF text extraction
- PDF page rendering
- image normalization
- page records
- error handling

### Milestone 5: Schemas and Structured Extraction

Estimated time: 4 to 6 days

Deliverables:

- document type model
- extraction schema model
- schema JSON editor
- structured extraction prompt
- extraction run model
- extracted field records
- validation service

### Milestone 6: Review Queue

Estimated time: 3 to 4 days

Deliverables:

- confidence thresholds
- review task model
- review screen
- field correction
- approve document flow
- audit events

### Milestone 7: Document Chat

Estimated time: 4 to 5 days

Deliverables:

- chunking service
- embeddings
- pgvector search
- chat sessions
- cited answers
- document-specific retrieval

### Milestone 8: Exports

Estimated time: 2 to 3 days

Deliverables:

- JSON export
- CSV export
- reviewed-value export
- export history
- download links

### Milestone 9: Evaluation

Estimated time: 4 to 5 days

Deliverables:

- gold extraction dataset
- extraction scoring command
- document classification scoring
- chat QA sample eval
- evaluation report page

### Milestone 10: Testing, CI, and Deployment

Estimated time: 3 to 5 days

Deliverables:

- unit tests
- integration tests
- Playwright E2E
- GitHub Actions
- Docker image build
- Trivy scan
- demo video or GIF

## 15. Testing Plan

### Unit Tests

Test:

- file validation
- schema validation
- extraction JSON parsing
- confidence threshold logic
- review routing
- export formatting
- workspace permission checks

### Integration Tests

Test:

- upload creates document
- processing creates page records
- extraction creates fields
- invalid fields create review tasks
- reviewed values override extracted values in export
- document chat retrieves only current document chunks

### E2E Tests

Use Playwright to test:

- login
- upload receipt
- wait for processing
- review extracted fields
- correct one field
- approve document
- ask document question
- export JSON

## 16. Evaluation Plan

Create datasets:

```text
eval/datasets/receipts_gold.yml
eval/datasets/invoices_gold.yml
eval/datasets/forms_gold.yml
```

Example item:

```yaml
- id: receipt_001
  file: samples/receipt_001.png
  document_type: receipt
  expected_fields:
    vendor_name: "Example Market"
    transaction_date: "2026-01-12"
    total_amount: "42.18"
    currency: "USD"
  critical_fields:
    - vendor_name
    - transaction_date
    - total_amount
```

Track:

- document classification accuracy
- field exact match
- field precision
- field recall
- field F1
- critical-field exact match
- missing-field rate
- invalid-JSON rate
- review routing accuracy
- average processing time

Minimum portfolio target:

- 50 to 100 sample documents
- at least 3 document types
- at least 10 messy scans
- at least 10 intentionally difficult documents
- at least 10 documents requiring human review

## 17. Security, Privacy, and Ethics

### File Safety

Validate all uploads.

Restrict:

- file size
- extension
- MIME type
- page count

Never execute uploaded files.

### Workspace Isolation

Every document, page, extraction, review, chat, and export must belong to a workspace.

Never allow cross-workspace access.

### Sensitive Documents

Documents may contain:

- names
- addresses
- payment details
- signatures
- account numbers
- medical or legal information

For portfolio demos, use synthetic or public sample documents only.

### Model Call Privacy

Before sending content to an external model:

- avoid real personal data
- redact unnecessary sensitive fields where possible
- log model metadata, not full secrets

### Human Review

Do not present extracted values as final when confidence is low.

Make uncertainty visible.

### Auditability

Log:

- uploads
- extraction runs
- model name and prompt version
- validation failures
- human corrections
- approvals
- exports

## 18. CI/CD and Deployment

### GitHub Actions Pipeline

Recommended pipeline:

```text
1. checkout
2. install dependencies
3. run formatting check
4. run linting
5. run unit tests
6. run integration tests
7. run extraction eval smoke test
8. run Playwright E2E smoke test
9. build Docker image
10. run Trivy scan
11. deploy on main branch
```

### Docker Compose Services

```text
web
worker
beat
postgres
redis
```

Optional:

```text
minio
flower
prometheus
grafana
```

### Environment Variables

```text
DJANGO_SECRET_KEY=
DATABASE_URL=
REDIS_URL=
OPENAI_API_KEY=
DJANGO_ALLOWED_HOSTS=
DJANGO_DEBUG=
MEDIA_ROOT=
MAX_UPLOAD_MB=
```

## 19. README Story

The README should lead with:

```text
Multimodal Document Analyst is a Django document AI system that extracts structured data from PDFs and images, validates fields, routes uncertain results to human review, and supports cited chat over uploaded documents.
```

README sections:

1. Problem
2. Demo GIF
3. Key features
4. Architecture
5. Tech stack
6. Local setup
7. Document processing pipeline
8. Extraction schemas
9. Review workflow
10. Evaluation results
11. Security and privacy
12. Screenshots
13. Deployment
14. Limitations
15. Roadmap

## 20. Portfolio Case Study Angle

Use this narrative:

```text
I built a Django-based document AI workflow that processes PDFs and images, extracts structured fields into validated schemas, flags uncertain results for human review, and lets users ask cited questions about each document.
```

Highlight:

- multimodal processing
- OCR and PDF parsing
- structured JSON extraction
- schema validation
- review queue
- cited document chat
- evaluation metrics
- secure file handling

## 21. LinkedIn Post Draft

```text
I started building Multimodal Document Analyst: a Django app for extracting and reviewing structured data from PDFs, receipts, invoices, and form images.

The goal is not just "upload a PDF and chat." The goal is a real document workflow:

- file upload and validation
- PDF/image preprocessing
- structured field extraction
- schema validation
- confidence scoring
- human review for uncertain fields
- cited chat over documents
- JSON/CSV exports
- evaluation for field-level accuracy

Document AI gets interesting when the model output has to survive validation, review, and audit trails.
```

## 22. MVP Scope

Build these first:

- login
- one workspace per user
- document upload
- PDF and image support
- manual document type selection
- receipt and invoice schemas
- structured extraction
- field validation
- review queue
- JSON export
- basic document chat
- Docker Compose
- basic tests

Do not build these in MVP:

- real enterprise storage integration
- advanced annotation canvas
- custom open-source model training
- complex contract analysis
- multi-language OCR
- Kubernetes
- billing
- mobile app

## 23. Version 2 Enhancements

After MVP:

- document auto-classification
- visual bounding-box highlighting
- schema builder UI
- batch upload
- side-by-side document comparison
- DOCX support
- MinIO or S3 storage
- advanced OCR fallback
- open-source document model sidecar
- reviewer productivity dashboard
- nightly extraction evals
- webhook export integration

## 24. First 10-Day Build Schedule

### Day 1

- create Django project
- configure PostgreSQL, Redis, Celery
- add Docker Compose
- create accounts and workspaces

### Day 2

- create document models
- build upload page
- build document library
- add file validation

### Day 3

- implement PDF text extraction
- implement PDF page rendering
- implement image normalization
- create page records

### Day 4

- create document type and schema models
- add receipt and invoice schemas
- build basic schema admin/editor

### Day 5

- implement structured extraction prompt
- save extraction runs
- save extracted fields
- parse and validate JSON output

### Day 6

- implement review routing
- build review queue
- build field correction UI
- add approve document flow

### Day 7

- implement chunking and embeddings
- add pgvector search
- build document chat backend

### Day 8

- build document detail UI
- connect preview, extracted fields, and chat
- add citation display

### Day 9

- implement JSON and CSV exports
- create evaluation dataset
- write extraction scoring command
- add core tests

### Day 10

- polish UI
- write README
- add GitHub Actions
- record demo GIF

## 25. Definition of Done

The project is portfolio-ready when:

- users can upload PDFs and images
- files are validated safely
- background processing creates page records
- structured extraction returns schema-based fields
- validation catches missing or malformed fields
- low-confidence fields enter review
- reviewers can correct and approve fields
- approved data can be exported
- users can chat with a document
- chat answers cite document evidence
- evaluation can score extraction quality
- tests pass
- Docker Compose runs the full app
- README explains the pipeline, review workflow, and metrics
- demo shows upload, extraction, review, chat, and export

