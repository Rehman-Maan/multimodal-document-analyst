from rest_framework import serializers

from apps.review.models import ReviewTask


class ReviewTaskSerializer(serializers.ModelSerializer):
    document_title = serializers.CharField(source="document.title", read_only=True)
    field_name = serializers.CharField(source="field.field_name", read_only=True)
    current_value = serializers.CharField(source="field.normalized_value", read_only=True)

    class Meta:
        model = ReviewTask
        fields = [
            "id",
            "document",
            "document_title",
            "extraction_run",
            "field",
            "field_name",
            "current_value",
            "assigned_to",
            "status",
            "priority",
            "reason",
            "corrected_value",
            "reviewer_note",
            "created_at",
            "completed_at",
        ]
        read_only_fields = [
            "id",
            "document",
            "document_title",
            "extraction_run",
            "field",
            "field_name",
            "current_value",
            "assigned_to",
            "status",
            "priority",
            "reason",
            "created_at",
            "completed_at",
        ]
