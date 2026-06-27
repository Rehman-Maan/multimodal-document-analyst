# LinkedIn Post Caption

I built Multimodal Document Analyst, a Django document AI workflow for PDFs, receipts, invoices, forms, and scans.

The goal was not just "chat with a PDF." The goal was a realistic document operations pipeline:

- Upload and validate PDFs/images
- Process files in Celery
- Extract page text and previews
- Run schema-based structured extraction
- Validate fields and confidence scores
- Route uncertain values to human review
- Ask cited questions over each document
- Export reviewed data as JSON or CSV
- Score extraction quality with evaluation reports
- Ship with tests, Playwright E2E, GitHub Actions, Docker builds, and Trivy scanning

Tech stack:
Django, DRF, Celery, Redis, PostgreSQL/pgvector-ready Docker, OpenAI-ready extraction and chat services, pytest, Playwright, GitHub Actions, Docker, and Trivy.

GitHub:
https://github.com/Rehman-Maan/multimodal-document-analyst
