# Manual Test Guide

Use this guide to test the full Multimodal Document Analyst workflow.

## Start

```powershell
docker compose up -d
docker compose exec web python manage.py migrate
docker compose exec web python manage.py seed_demo_users
```

Open:

```text
http://localhost:18000/
```

Demo login:

```text
demo_owner / TestPass123!
```

## Sample Uploads

Use files from `sample_uploads/`:

- `invoice_acme_INV-1001.pdf`
- `invoice_northwind_NW-204.pdf`
- `receipt_example_market.png`
- `form_jordan_lee.png`

## Full Flow

1. Sign in as `demo_owner`.
2. Open `Demo Workspace`.
3. Upload `sample_uploads/invoice_acme_INV-1001.pdf`.
4. Open the uploaded document detail page.
5. Wait for processing to finish, or click `Process`.
6. In `Structured extraction`, select `Invoice - Default Invoice v1`.
7. Click `Extract fields`.
8. Confirm extracted fields include:
   - `invoice_number`: `INV-1001`
   - `vendor_name`: `Acme Supplies`
   - `invoice_date`: `2026-06-27`
   - `total_amount`: `42.50`
9. Open `Review queue`.
10. Approve any low-confidence vendor task.
11. Return to the document and click `Approve document`.
12. Click `Chat`.
13. Click `Reindex`.
14. Ask: `What is the invoice total?`
15. Confirm the answer includes a citation.
16. Return to the document.
17. Click `Export JSON`.
18. Download and inspect the JSON export.
19. Click `Export CSV`.
20. Download and inspect the CSV export.
21. Open `Exports` from the dashboard and confirm export history.
22. Open `Evaluations`.
23. Click `Run sample eval`.
24. Confirm metrics show field F1, precision, recall, and critical exact match.

## Terminal Checks

```powershell
Invoke-RestMethod http://localhost:18000/health/
docker compose exec web python manage.py check
docker compose exec web python manage.py run_extraction_eval eval/datasets/invoices_gold.yml
python -m pytest tests\unit --ds=config.settings.test
python -m ruff check . --exclude .venv
```

Expected result:

- health endpoint reports database and Redis OK
- Django check reports no issues
- evaluation command prints metrics JSON
- pytest passes
- Ruff passes
