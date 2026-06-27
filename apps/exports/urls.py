from django.urls import path

from apps.exports.views import ExportHistoryView, create_document_export, download_export


urlpatterns = [
    path("", ExportHistoryView.as_view(), name="export-history"),
    path(
        "documents/<int:pk>/<str:export_format>/",
        create_document_export,
        name="document-export-create",
    ),
    path("<int:pk>/download/", download_export, name="export-download"),
]
