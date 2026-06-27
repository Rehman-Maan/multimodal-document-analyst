from django.urls import path

from apps.schemas.views import (
    DocumentTypeCreateView,
    SchemaCreateView,
    SchemaDetailView,
    SchemaListView,
    seed_default_schemas,
)


urlpatterns = [
    path("", SchemaListView.as_view(), name="schema-list"),
    path("new/", SchemaCreateView.as_view(), name="schema-create"),
    path("seed-defaults/", seed_default_schemas, name="schema-seed-defaults"),
    path("document-types/new/", DocumentTypeCreateView.as_view(), name="document-type-create"),
    path("<int:pk>/", SchemaDetailView.as_view(), name="schema-detail"),
]
