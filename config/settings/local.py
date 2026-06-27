from .base import *  # noqa: F401,F403


DEBUG = env("DJANGO_DEBUG", default=True)  # noqa: F405
ALLOWED_HOSTS = env("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1", "0.0.0.0"])  # noqa: F405

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
