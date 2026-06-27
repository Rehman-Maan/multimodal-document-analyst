# Multimodal Document Analyst

Multimodal Document Analyst is a Django document AI system that extracts structured data from PDFs and images, validates fields, routes uncertain results to human review, and supports cited chat over uploaded documents.

## Problem

Teams still process invoices, receipts, forms, scans, and compliance documents manually. This project is being built as a production-style workflow for turning messy documents into validated structured data with a human review loop.

## Demo

Recording script and storyboard are ready:

- [Demo script](docs/demo_script.md)
- [LinkedIn caption](docs/video/linkedin_post_caption.md)
- [Storyboard](docs/video/storyboard.md)

## Screenshots

### Workspace Dashboard

The workspace command center shows document volume, review status, approval progress, and the end-to-end document workflow.

![Workspace dashboard](docs/assets/dashboard.png)

### Document Library

The library gives analysts a workspace-scoped view of uploaded files, processing state, document type, owner, and workflow entry points.

![Document library](docs/assets/document-library.png)

### Document Detail

The document detail screen combines the original file, extracted page text, schema-based structured fields, review state, exports, and processing timeline.

![Document detail](docs/assets/document-detail.png)

### Cited Document Chat

The chat view answers questions against indexed document text and attaches focused citations to the evidence used.

![Cited document chat](docs/assets/document-chat.png)

### Evaluation Report

Evaluation reports score extraction quality against synthetic gold datasets so the AI workflow is measurable, not only demoable.

![Evaluation report](docs/assets/evaluation-report.png)

## Key Features

- Django backend with Django REST Framework
- PostgreSQL data store, using a pgvector-ready image for later retrieval work
- Redis-backed Celery worker and beat services
- Local media storage for uploaded and generated document files
- Split local and production settings
- Health endpoint at `/health/`
- Login/logout using Django auth
- Workspace and membership models with owner/admin/reviewer/analyst/viewer roles
- Workspace dashboard shell for the next document workflow milestones
- Workspace-scoped document upload and library
- Upload validation for PDF, PNG, JPG, and TIFF files
- Document detail shell with status and original-file access
- Celery document processing task
- PDF text extraction and rendered page previews with PyMuPDF
- Image orientation normalization and preview page creation with Pillow
- Workspace document types and extraction schemas
- Schema JSON editor with receipt and invoice defaults
- Structured extraction runs and field records with validation errors
- Confidence-based human review queue
- Field correction, document approval, and audit events
- Document chunking, embeddings, retrieval, and cited chat
- JSON and CSV exports with export history
- Gold-dataset evaluation scoring and report pages
- Browser smoke coverage with Playwright
- GitHub Actions CI with linting, tests, migration checks, Docker build, and Trivy scan

## Architecture

Browser requests go to Django and DRF. Django stores application data in PostgreSQL, media files under `media/`, and dispatches background work to Celery through Redis. Retrieval chunks use pgvector-compatible embeddings for document-specific cited chat. Exports are generated into local media and tracked with audit events. Evaluation reports score extraction quality against synthetic gold datasets. GitHub Actions verifies linting, migrations, tests, browser smoke coverage, Docker image build, and Trivy scanning.

## Tech Stack

- Django
- Django REST Framework
- PostgreSQL / pgvector-ready container
- Redis
- Celery
- OpenAI API for embeddings and cited answers when configured
- Docker Compose
- pytest and pytest-django
- Playwright
- GitHub Actions
- Trivy

## Local Setup

Create an environment file:

```powershell
Copy-Item .env.example .env
```

Run with Docker Compose:

```powershell
docker compose up --build
```

Apply database migrations:

```powershell
docker compose exec web python manage.py migrate
```

Create an admin user:

```powershell
docker compose exec web python manage.py createsuperuser
```

Or seed local demo accounts:

```powershell
docker compose exec web python manage.py seed_demo_users
```

Default local credentials from the seed command:

```text
admin / AdminPass123!
demo_owner / TestPass123!
demo_admin / TestPass123!
demo_reviewer / TestPass123!
demo_analyst / TestPass123!
demo_viewer / TestPass123!
```

Check the app:

```powershell
Invoke-RestMethod http://localhost:18000/health/
```

Open the app in a browser:

```text
http://localhost:18000/
```

After signing in, create a workspace or sign up from the login page. Then open the workspace dashboard and use **Upload document** to add a PDF or image. Uploaded files are stored under `media/workspaces/...` in local development. Uploading a document enqueues Celery processing; the document detail page shows rendered pages, extracted PDF text snippets, processing timestamps, extraction controls, extracted fields, review tasks, chat, export buttons, and errors.

For non-Docker development, create a virtual environment and install the project:

```powershell
py -m venv .venv
.\\.venv\\Scripts\\python -m pip install --upgrade pip
.\\.venv\\Scripts\\python -m pip install -e ".[dev]"
```

Use local host service URLs in `.env`:

```text
DATABASE_URL=postgres://postgres:postgres@localhost:15432/multimodal_document_analyst
REDIS_URL=redis://localhost:16379/0
MEDIA_ROOT=media
OPENAI_API_KEY=
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_CHAT_MODEL=gpt-4.1-mini
```

## Document Processing Pipeline

The current pipeline stores validated original files, processes PDFs into text and rendered page previews, normalizes images into single-page previews, and tracks processing status. It can run local baseline structured extraction against workspace schemas and store field-level confidence, source page, source text, and validation errors. Low-confidence or invalid fields are routed to human review. Processed page text can be indexed into chunks for document-specific chat with citations.

## Extraction Schemas

Each workspace can manage document types and extraction schemas. New workspaces get default receipt and invoice schemas, and the schema library includes a JSON editor for required fields and supported types: `string`, `decimal`, `date`, `integer`, and `boolean`.

## Review Workflow

Extraction creates review tasks for fields below the confidence threshold or fields with validation errors. Reviewers can open the workspace review queue, correct field values, approve or reject tasks, and approve a document after all open tasks are resolved. Review actions write audit events for traceability.

## Document Chat

Document chat indexes processed page text into chunks, creates embeddings, retrieves the most relevant chunks for each question, and stores assistant answers with page-level citations. If OpenAI credentials and the `openai` package are available, the app uses configured OpenAI embedding and chat models. Otherwise it falls back to deterministic local embeddings and extractive cited answers for development and tests.

## Exports

Approved or reviewed structured data can be exported from the document detail page as JSON or CSV. Exports use the latest extraction run and current normalized field values, so reviewer corrections are included. Each generated file is saved under local media, listed in workspace export history, and logged as an audit event.

## Evaluation Results

Evaluation datasets live in `eval/datasets/`. Run a score from the command line:

```powershell
docker compose exec web python manage.py run_extraction_eval eval/datasets/invoices_gold.yml
```

Save a report to a workspace:

```powershell
docker compose exec web python manage.py run_extraction_eval eval/datasets/invoices_gold.yml --workspace-slug demo-workspace --username demo_owner --save
```

Workspace owners and admins can also open **Evaluations** from the dashboard and run the sample evaluation report. Metrics include classification accuracy, field exact match, precision, recall, F1, critical-field exact match, missing-field rate, and invalid-output rate.

## Testing

Run the local verification suite:

```powershell
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe manage.py check --settings=config.settings.test
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run --settings=config.settings.test
.\.venv\Scripts\python.exe -m pytest --ds=config.settings.test
```

Run the Playwright smoke test:

```powershell
.\.venv\Scripts\python.exe -m playwright install chromium
.\.venv\Scripts\python.exe -m pytest tests\e2e --ds=config.settings.test
```

See [Testing](docs/testing.md) for details.

## CI/CD

The GitHub Actions workflow in `.github/workflows/ci.yml` runs:

- Ruff lint
- Django system check
- pending migration check
- pytest, including Playwright smoke coverage
- Docker image build
- Trivy image scan

Dependabot is configured for Python dependencies, GitHub Actions, and Docker base images.

## Security and Privacy

The setup keeps secrets in environment variables and excludes `.env` and uploaded media from version control. Production settings enable secure cookies and SSL redirect hooks.

## Deployment

Docker Compose runs the local development stack. A production-style stack is available in `docker-compose.prod.yml`:

```powershell
Copy-Item .env.production.example .env
docker compose -f docker-compose.prod.yml up --build -d
docker compose -f docker-compose.prod.yml exec web python manage.py migrate
docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
docker compose -f docker-compose.prod.yml exec web python manage.py seed_demo_users
```

See [Deployment](docs/deployment.md) and [Release Checklist](docs/release-checklist.md).

## Limitations

The project currently uses synthetic evaluation datasets and local fallbacks when OpenAI is unavailable. Larger gold datasets, richer OCR fallback, side-by-side document comparison, batch upload, and production object storage are good next enhancements.

## Roadmap

1. Auth and workspaces
2. Document upload and library
3. Processing pipeline
4. Schemas and structured extraction
5. Human review queue
6. Cited document chat
7. Export and audit trails
8. Evaluation and deployment hardening
9. Demo recording and portfolio screenshots
