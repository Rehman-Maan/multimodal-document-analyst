from rest_framework import serializers

from apps.extraction.models import ExtractedField, ExtractionRun


class ExtractedFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExtractedField
        fields = [
            "id",
            "field_name",
            "raw_value",
            "normalized_value",
            "confidence",
            "source_page",
            "source_text",
            "validation_errors",
        ]


class ExtractionRunSerializer(serializers.ModelSerializer):
    fields = ExtractedFieldSerializer(many=True, read_only=True)

    class Meta:
        model = ExtractionRun
        fields = [
            "id",
            "document",
            "schema",
            "status",
            "model_name",
            "validation_errors",
            "raw_output",
            "fields",
            "created_at",
            "completed_at",
        ]
