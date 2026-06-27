from django.urls import path

from apps.documents.api_views import (
    UploadedDocumentListCreateAPIView,
    UploadedDocumentProcessAPIView,
    UploadedDocumentRetrieveAPIView,
)


urlpatterns = [
    path("documents/", UploadedDocumentListCreateAPIView.as_view(), name="api-document-list"),
    path("documents/<int:pk>/", UploadedDocumentRetrieveAPIView.as_view(), name="api-document-detail"),
    path("documents/<int:pk>/process/", UploadedDocumentProcessAPIView.as_view(), name="api-document-process"),
    path("documents/<int:pk>/retry/", UploadedDocumentProcessAPIView.as_view(), name="api-document-retry"),
]
