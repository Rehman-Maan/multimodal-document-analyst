# Milestone 10: Testing, CI, and Deployment

## Status

Complete and locally verified.

## What Was Added

- GitHub Actions CI at `.github/workflows/ci.yml`.
- Dependabot config at `.github/dependabot.yml`.
- Production-style Compose file at `docker-compose.prod.yml`.
- Production environment template at `.env.production.example`.
- Playwright browser smoke test at `tests/e2e/test_playwright_smoke.py`.
- Playwright development dependency and pytest `e2e` marker.
- Testing docs at `docs/testing.md`.
- Deployment docs at `docs/deployment.md`.
- Release checklist at `docs/release-checklist.md`.
- Recording-ready demo script at `docs/demo_script.md`.
- LinkedIn caption and storyboard under `docs/video/`.

## Presentation Angle

The portfolio story should be:

> I built a Django document AI workflow that processes PDFs and images, extracts structured fields into validated schemas, flags uncertain results for human review, and lets users ask cited questions about each document.

## Final Verification Checklist

```powershell
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe manage.py check --settings=config.settings.test
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run --settings=config.settings.test
.\.venv\Scripts\python.exe -m pytest --ds=config.settings.test
docker compose -f docker-compose.prod.yml config --quiet
docker build --progress=plain -f infra/docker/Dockerfile -t multimodal-document-analyst:milestone10 .
```

## Verified Locally

- `.\.venv\Scripts\python.exe -m ruff check .` passed.
- `.\.venv\Scripts\python.exe manage.py check --settings=config.settings.test` passed.
- `.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run --settings=config.settings.test` passed with no changes detected.
- `.\.venv\Scripts\python.exe -m pytest --ds=config.settings.test` passed with `57 passed`.
- `.\.venv\Scripts\python.exe -m pytest tests\e2e --ds=config.settings.test` passed with `1 passed`.
- `docker compose -f docker-compose.prod.yml config --quiet` passed.
- `docker build --progress=plain -f infra/docker/Dockerfile -t multimodal-document-analyst:milestone10 .` passed.
