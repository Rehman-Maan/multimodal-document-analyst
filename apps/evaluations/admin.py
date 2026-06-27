from django.contrib import admin

from apps.evaluations.models import EvaluationRun


@admin.register(EvaluationRun)
class EvaluationRunAdmin(admin.ModelAdmin):
    list_display = ["dataset_name", "workspace", "total_items", "created_by", "created_at"]
    list_filter = ["dataset_name", "created_at"]
    search_fields = ["dataset_name", "workspace__name", "created_by__username"]
    autocomplete_fields = ["workspace", "created_by"]
