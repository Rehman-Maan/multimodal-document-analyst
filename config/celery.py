"""Celery application configuration."""
import os

from celery import Celery


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

app = Celery("multimodal_document_analyst")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
