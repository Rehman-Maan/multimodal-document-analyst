from django.conf import settings
from django.db import connections
from django.db.utils import OperationalError
from django.http import JsonResponse


def health_check(request):
    checks = {
        "database": _database_status(),
        "redis": _redis_status(),
    }
    status_code = 200 if all(value == "ok" for value in checks.values()) else 503
    return JsonResponse({"status": "ok" if status_code == 200 else "degraded", "checks": checks}, status=status_code)


def _database_status() -> str:
    try:
        connections["default"].cursor()
    except OperationalError:
        return "unavailable"
    return "ok"


def _redis_status() -> str:
    try:
        from redis import Redis

        client = Redis.from_url(settings.REDIS_URL, socket_connect_timeout=1, socket_timeout=1)
        return "ok" if client.ping() else "unavailable"
    except Exception:
        return "unavailable"
