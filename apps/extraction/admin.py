from django.contrib import admin

from apps.extraction.models import ExtractedField, ExtractionRun


class ExtractedFieldInline(admin.TabularInline):
    model = ExtractedField
    extra = 0


@admin.register(ExtractionRun)
class ExtractionRunAdmin(admin.ModelAdmin):
    list_display = ["document", "schema", "status", "model_name", "created_at", "completed_at"]
    list_filter = ["status", "model_name", "created_at"]
    search_fields = ["document__title", "schema__name"]
    autocomplete_fields = ["document", "schema"]
    inlines = [ExtractedFieldInline]


@admin.register(ExtractedField)
class ExtractedFieldAdmin(admin.ModelAdmin):
    list_display = ["field_name", "document", "normalized_value", "confidence", "source_page"]
    search_fields = ["field_name", "normalized_value", "document__title"]
    autocomplete_fields = ["run", "document"]
