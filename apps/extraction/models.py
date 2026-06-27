from django.db import models


class ExtractionRun(models.Model):
    class Status(models.TextChoices):
        RUNNING = "running", "Running"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"
        NEEDS_REVIEW = "needs_review", "Needs review"

    document = models.ForeignKey(
        "documents.UploadedDocument",
        on_delete=models.CASCADE,
        related_name="extraction_runs",
    )
    schema = models.ForeignKey(
        "schemas.ExtractionSchema",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="extraction_runs",
    )
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.RUNNING)
    prompt_snapshot = models.TextField(blank=True)
    raw_output = models.JSONField(default=dict, blank=True)
    validation_errors = models.JSONField(default=list, blank=True)
    model_name = models.CharField(max_length=120, default="local-baseline")
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.document} extraction {self.pk}"


class ExtractedField(models.Model):
    run = models.ForeignKey(ExtractionRun, on_delete=models.CASCADE, related_name="fields")
    document = models.ForeignKey(
        "documents.UploadedDocument",
        on_delete=models.CASCADE,
        related_name="extracted_fields",
    )
    field_name = models.CharField(max_length=120)
    raw_value = models.TextField(blank=True)
    normalized_value = models.TextField(blank=True)
    confidence = models.FloatField(default=0)
    source_page = models.PositiveIntegerField(null=True, blank=True)
    source_text = models.TextField(blank=True)
    validation_errors = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["field_name"]
        indexes = [models.Index(fields=["document", "field_name"])]

    def __str__(self) -> str:
        return f"{self.field_name}: {self.normalized_value}"
