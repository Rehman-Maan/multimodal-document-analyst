from rest_framework import serializers

from apps.exports.models import ExportRecord


class ExportRecordSerializer(serializers.ModelSerializer):
    document_title = serializers.CharField(source="document.title", read_only=True)
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = ExportRecord
        fields = [
            "id",
            "document",
            "document_title",
            "extraction_run",
            "format",
            "field_count",
            "metadata",
            "download_url",
            "created_at",
        ]

    def get_download_url(self, obj):
        request = self.context.get("request")
        if not obj.file or request is None:
            return ""
        return request.build_absolute_uri(obj.file.url)
