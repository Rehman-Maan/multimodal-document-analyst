# Testing

## Local Checks

Run the same core checks used by CI:

```powershell
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe manage.py check --settings=config.settings.test
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run --settings=config.settings.test
.\.venv\Scripts\python.exe -m pytest --ds=config.settings.test
```

The test settings disable OpenAI usage by default, use eager Celery tasks, and keep tests deterministic.

## Browser Smoke Test

The Playwright smoke test lives in `tests/e2e/test_playwright_smoke.py`.

Install Chromium locally when you want to run it directly:

```powershell
.\.venv\Scripts\python.exe -m playwright install chromium
.\.venv\Scripts\python.exe -m pytest tests\e2e --ds=config.settings.test
```

The smoke test signs in, opens a workspace dashboard, uploads a synthetic image document, waits for processing, and confirms the document detail page renders.

## CI

`.github/workflows/ci.yml` runs:

- Ruff lint
- Django system check
- pending-migration check
- full pytest suite, including Playwright smoke coverage
- Docker image build
- Trivy image scan uploaded as SARIF

Dependabot is configured for Python dependencies, GitHub Actions, and Docker base images.
