# Demo Script

## Setup

Start the stack and seed demo accounts:

```powershell
docker compose up --build -d
docker compose exec web python manage.py migrate
docker compose exec web python manage.py seed_demo_users
```

Demo login:

```text
demo_owner / TestPass123!
```

## 90-Second Demo Flow

1. Open `http://localhost:18000/` and sign in as `demo_owner`.
2. Show the Demo Workspace dashboard and the four workflow steps.
3. Open Upload document and upload `sample_uploads/invoice_acme_INV-1001.pdf` as an invoice.
4. Open the document detail page and show page previews, extracted text, and status.
5. Run structured extraction with the invoice schema.
6. Open the extracted fields and review queue.
7. Approve or correct a field, then approve the document.
8. Open document chat and ask: `What is the invoice total and due date?`
9. Show the focused citation attached to the answer.
10. Export JSON and CSV.
11. Open Evaluations and show the sample extraction scoring report.
12. Close by mentioning that CI runs linting, migration checks, pytest, Playwright, Docker build, and Trivy scanning.

## One-Minute Voiceover

"This is Multimodal Document Analyst, a Django document AI workflow for turning PDFs and scanned images into validated structured data. The goal is not just chat with a PDF. The app handles upload validation, background document processing, schema-based extraction, confidence scoring, human review, cited document chat, JSON and CSV exports, and evaluation reports.

In the demo, a user uploads an invoice, the worker extracts page text and previews, the extraction layer maps fields into a workspace schema, uncertain values can be corrected in a review queue, and the approved data can be exported. Users can also ask natural-language questions about a document, and the answer includes document evidence.

The stack is Django, Django REST Framework, Celery, Redis, PostgreSQL with pgvector-ready infrastructure, Docker Compose, OpenAI-ready services with local fallbacks, pytest, Playwright, GitHub Actions, and Trivy."

## Screenshot Checklist

- Login screen
- Workspace dashboard
- Upload document
- Document detail with preview and fields
- Review queue
- Document chat with citation
- Export card/history
- Evaluation report

## Captured Screenshots

Use these repo assets in the README, GitHub project page, LinkedIn carousel, or walkthrough:

- `docs/assets/login.png` - secure sign-in entry point.
- `docs/assets/dashboard.png` - workspace metrics and document workflow.
- `docs/assets/document-library.png` - uploaded document library.
- `docs/assets/document-detail.png` - preview, extraction, review, and exports.
- `docs/assets/document-chat.png` - grounded answer with citation.
- `docs/assets/evaluation-report.png` - extraction quality report.
