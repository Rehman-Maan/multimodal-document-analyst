from django.urls import path

from apps.documents.views import (
    DocumentDetailView,
    DocumentListView,
    DocumentUploadView,
    extract_document_view,
    process_document_view,
)


urlpatterns = [
    path("", DocumentListView.as_view(), name="document-list"),
    path("upload/", DocumentUploadView.as_view(), name="document-upload"),
    path("<int:pk>/", DocumentDetailView.as_view(), name="document-detail"),
    path("<int:pk>/process/", process_document_view, name="document-process"),
    path("<int:pk>/extract/", extract_document_view, name="document-extract"),
]
