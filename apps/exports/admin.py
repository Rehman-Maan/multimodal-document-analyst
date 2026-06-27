from django.contrib import admin

from apps.exports.models import ExportRecord


@admin.register(ExportRecord)
class ExportRecordAdmin(admin.ModelAdmin):
    list_display = ["document", "format", "field_count", "created_by", "created_at"]
    list_filter = ["format", "created_at"]
    search_fields = ["document__title", "created_by__username"]
    autocomplete_fields = ["workspace", "document", "extraction_run", "created_by"]
