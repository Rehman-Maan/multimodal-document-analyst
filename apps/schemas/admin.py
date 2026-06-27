from django.contrib import admin

from apps.schemas.models import DocumentType, ExtractionSchema


@admin.register(DocumentType)
class DocumentTypeAdmin(admin.ModelAdmin):
    list_display = ["name", "workspace", "slug", "active", "created_at"]
    list_filter = ["active", "created_at"]
    search_fields = ["name", "slug", "workspace__name"]
    autocomplete_fields = ["workspace"]


@admin.register(ExtractionSchema)
class ExtractionSchemaAdmin(admin.ModelAdmin):
    list_display = ["name", "document_type", "workspace", "version", "active", "created_at"]
    list_filter = ["active", "document_type", "created_at"]
    search_fields = ["name", "document_type__name", "workspace__name"]
    autocomplete_fields = ["workspace", "document_type", "created_by"]
