from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from config.health import health_check


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.workspaces.urls")),
    path("accounts/", include("apps.accounts.urls")),
    path("workspaces/<slug:workspace_slug>/schemas/", include("apps.schemas.urls")),
    path("workspaces/<slug:workspace_slug>/documents/", include("apps.documents.urls")),
    path("workspaces/<slug:workspace_slug>/review/", include("apps.review.urls")),
    path("workspaces/<slug:workspace_slug>/exports/", include("apps.exports.urls")),
    path("workspaces/<slug:workspace_slug>/evaluations/", include("apps.evaluations.urls")),
    path("workspaces/<slug:workspace_slug>/", include("apps.chat.urls")),
    path("api/", include("apps.workspaces.api_urls")),
    path("api/", include("apps.documents.api_urls")),
    path("api/", include("apps.schemas.api_urls")),
    path("api/", include("apps.extraction.api_urls")),
    path("api/", include("apps.review.api_urls")),
    path("api/", include("apps.chat.api_urls")),
    path("api/", include("apps.exports.api_urls")),
    path("api/", include("apps.evaluations.api_urls")),
    path("health/", health_check, name="health-check"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
