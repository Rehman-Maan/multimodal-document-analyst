from django.urls import path

from apps.extraction.api_views import DocumentExtractAPIView, DocumentFieldsAPIView


urlpatterns = [
    path("documents/<int:pk>/extract/", DocumentExtractAPIView.as_view(), name="api-document-extract"),
    path("documents/<int:pk>/fields/", DocumentFieldsAPIView.as_view(), name="api-document-fields"),
]
