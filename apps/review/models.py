from django.conf import settings
from django.db import models


class ReviewTask(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        IN_PROGRESS = "in_progress", "In progress"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    class Priority(models.TextChoices):
        LOW = "low", "Low"
        NORMAL = "normal", "Normal"
        HIGH = "high", "High"

    document = models.ForeignKey(
        "documents.UploadedDocument",
        on_delete=models.CASCADE,
        related_name="review_tasks",
    )
    extraction_run = models.ForeignKey(
        "extraction.ExtractionRun",
        on_delete=models.CASCADE,
        related_name="review_tasks",
    )
    field = models.ForeignKey(
        "extraction.ExtractedField",
        on_delete=models.CASCADE,
        related_name="review_tasks",
        null=True,
        blank=True,
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_review_tasks",
    )
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.OPEN)
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.NORMAL)
    reason = models.TextField()
    corrected_value = models.TextField(blank=True)
    reviewer_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["status", "-created_at"]
        indexes = [
            models.Index(fields=["document", "status"]),
            models.Index(fields=["assigned_to", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.document} review task {self.pk}"
