from django.contrib import admin

from apps.review.models import ReviewTask


@admin.register(ReviewTask)
class ReviewTaskAdmin(admin.ModelAdmin):
    list_display = ["document", "field", "status", "priority", "assigned_to", "created_at", "completed_at"]
    list_filter = ["status", "priority", "created_at"]
    search_fields = ["document__title", "field__field_name", "reason"]
    autocomplete_fields = ["document", "extraction_run", "field", "assigned_to"]
