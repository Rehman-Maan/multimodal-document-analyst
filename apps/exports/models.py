from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.db import models


def export_upload_path(instance, filename: str) -> str:
    extension = Path(filename).suffix.lower()
    return f"workspaces/{instance.workspace_id}/exports/{uuid4()}{extension}"


class ExportRecord(models.Model):
    class Format(models.TextChoices):
        JSON = "json", "JSON"
        CSV = "csv", "CSV"

    workspace = models.ForeignKey(
        "workspaces.Workspace",
        on_delete=models.CASCADE,
        related_name="export_records",
    )
    document = models.ForeignKey(
        "documents.UploadedDocument",
        on_delete=models.CASCADE,
        related_name="export_records",
    )
    extraction_run = models.ForeignKey(
        "extraction.ExtractionRun",
        on_delete=models.SET_NULL,
        related_name="export_records",
        null=True,
        blank=True,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="export_records",
    )
    format = models.CharField(max_length=20, choices=Format.choices)
    file = models.FileField(upload_to=export_upload_path)
    field_count = models.PositiveIntegerField(default=0)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["workspace", "-created_at"]),
            models.Index(fields=["document", "-created_at"]),
            models.Index(fields=["format", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.document} {self.format} export {self.pk}"
