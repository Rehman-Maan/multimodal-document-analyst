# Release Checklist

Use this before pushing the public repo, recording a walkthrough, or posting the project.

## Local Verification

```powershell
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe manage.py check --settings=config.settings.test
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run --settings=config.settings.test
.\.venv\Scripts\python.exe -m pytest --ds=config.settings.test
docker compose -f docker-compose.prod.yml config --quiet
docker build --progress=plain -f infra/docker/Dockerfile -t multimodal-document-analyst:release .
```

## Secrets

- Confirm `.env` is not committed.
- Rotate any OpenAI key that appeared in screenshots, logs, or pasted text.
- Use `.env.production.example` as the host template.
- Use a fresh production `DJANGO_SECRET_KEY`.
- Avoid real personal documents in the public demo.

## Demo Data

- Run `python manage.py seed_demo_users`.
- Confirm `demo_owner / TestPass123!` can open the dashboard.
- Upload one invoice, one receipt, and one form from `sample_uploads/`.
- Run structured extraction against the matching schema.
- Correct or approve any review tasks.
- Ask a cited chat question.
- Export JSON and CSV.
- Run the sample evaluation report.

## Public Presentation

- README screenshots or demo video are current.
- GitHub repo description is set.
- The LinkedIn caption in `docs/video/linkedin_post_caption.md` has the final repo URL.
- The walkthrough script in `docs/demo_script.md` matches the current UI labels.
