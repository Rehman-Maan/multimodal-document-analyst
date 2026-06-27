from django.conf import settings
from django.db import models


class EvaluationRun(models.Model):
    workspace = models.ForeignKey(
        "workspaces.Workspace",
        on_delete=models.CASCADE,
        related_name="evaluation_runs",
    )
    dataset_name = models.CharField(max_length=180)
    total_items = models.PositiveIntegerField(default=0)
    metrics = models.JSONField(default=dict, blank=True)
    item_results = models.JSONField(default=list, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="evaluation_runs",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["workspace", "-created_at"]),
            models.Index(fields=["dataset_name", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.dataset_name} evaluation {self.pk}"
