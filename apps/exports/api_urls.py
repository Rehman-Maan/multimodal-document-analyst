from django.urls import path

from apps.exports.api_views import DocumentExportCreateAPIView, ExportRecordListAPIView


urlpatterns = [
    path("exports/", ExportRecordListAPIView.as_view(), name="api-export-list"),
    path(
        "documents/<int:pk>/exports/<str:export_format>/",
        DocumentExportCreateAPIView.as_view(),
        name="api-document-export-create",
    ),
]
