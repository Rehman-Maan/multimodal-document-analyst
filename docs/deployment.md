# Deployment

## Local Production-Style Compose

Use the production Compose file to test the same service shape expected in deployment:

```powershell
Copy-Item .env.production.example .env
docker compose -f docker-compose.prod.yml up --build -d
docker compose -f docker-compose.prod.yml exec web python manage.py migrate
docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
docker compose -f docker-compose.prod.yml exec web python manage.py seed_demo_users
```

Open:

```text
http://localhost:8000/
```

## Required Environment

```text
DJANGO_SECRET_KEY
DJANGO_DEBUG
DJANGO_ALLOWED_HOSTS
DJANGO_CSRF_TRUSTED_ORIGINS
DATABASE_URL
REDIS_URL
MEDIA_ROOT
MAX_UPLOAD_MB
OPENAI_API_KEY
OPENAI_EMBEDDING_MODEL
OPENAI_CHAT_MODEL
```

OpenAI is optional for demos because the app has local deterministic fallbacks, but configured OpenAI credentials enable stronger embeddings and cited answers.

## Deployment Checklist

1. Set `DJANGO_DEBUG=False`.
2. Use a fresh production `DJANGO_SECRET_KEY`.
3. Set `DJANGO_ALLOWED_HOSTS` and `DJANGO_CSRF_TRUSTED_ORIGINS`.
4. Run migrations.
5. Run `collectstatic`.
6. Confirm `/health/` returns database and Redis `ok`.
7. Seed or create demo users.
8. Upload a small PDF or image.
9. Confirm processing, extraction, review, chat, export, and evaluation pages work.

## CI/CD

GitHub Actions validates linting, migrations, tests, Docker image build, and Trivy scanning. Treat a green CI run as the minimum requirement before recording or sharing the public demo.
