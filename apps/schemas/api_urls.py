from django.urls import path

from apps.schemas.api_views import (
    DocumentTypeListCreateAPIView,
    ExtractionSchemaListCreateAPIView,
    ExtractionSchemaRetrieveUpdateAPIView,
)


urlpatterns = [
    path("document-types/", DocumentTypeListCreateAPIView.as_view(), name="api-document-type-list"),
    path("schemas/", ExtractionSchemaListCreateAPIView.as_view(), name="api-schema-list"),
    path("schemas/<int:pk>/", ExtractionSchemaRetrieveUpdateAPIView.as_view(), name="api-schema-detail"),
]
