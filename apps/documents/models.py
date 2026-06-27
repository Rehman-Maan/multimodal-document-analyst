from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.db import models
from django.urls import reverse


def document_upload_path(instance, filename: str) -> str:
    extension = Path(filename).suffix.lower()
    return f"workspaces/{instance.workspace_id}/documents/{uuid4()}{extension}"


def page_image_upload_path(instance, filename: str) -> str:
    extension = Path(filename).suffix.lower()
    return f"workspaces/{instance.document.workspace_id}/pages/{instance.document_id}-{instance.page_number}{extension}"


class UploadedDocument(models.Model):
    class Status(models.TextChoices):
        UPLOADED = "uploaded", "Uploaded"
        VALIDATING = "validating", "Validating"
        PROCESSING = "processing", "Processing"
        PROCESSED = "processed", "Processed"
        NEEDS_REVIEW = "needs_review", "Needs review"
        APPROVED = "approved", "Approved"
        FAILED = "failed", "Failed"
        ARCHIVED = "archived", "Archived"

    workspace = models.ForeignKey(
        "workspaces.Workspace",
        on_delete=models.CASCADE,
        related_name="documents",
    )
    title = models.CharField(max_length=220)
    file = models.FileField(upload_to=document_upload_path)
    file_type = models.CharField(max_length=20)
    document_type = models.CharField(max_length=80, blank=True)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.UPLOADED)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="uploaded_documents",
    )
    page_count = models.PositiveIntegerField(default=0)
    file_size = models.PositiveBigIntegerField(default=0)
    error_message = models.TextField(blank=True)
    processing_started_at = models.DateTimeField(null=True, blank=True)
    processing_completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["workspace", "status"]),
            models.Index(fields=["workspace", "-created_at"]),
        ]

    def __str__(self) -> str:
        return self.title

    def get_absolute_url(self) -> str:
        return reverse(
            "document-detail",
            kwargs={"workspace_slug": self.workspace.slug, "pk": self.pk},
        )


class DocumentPage(models.Model):
    document = models.ForeignKey(
        UploadedDocument,
        on_delete=models.CASCADE,
        related_name="pages",
    )
    page_number = models.PositiveIntegerField()
    text_content = models.TextField(blank=True)
    image = models.ImageField(upload_to=page_image_upload_path, blank=True)
    width = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["document", "page_number"],
                name="unique_document_page_number",
            )
        ]
        ordering = ["page_number"]

    def __str__(self) -> str:
        return f"{self.document} page {self.page_number}"
