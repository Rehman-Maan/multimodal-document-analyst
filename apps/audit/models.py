from django.conf import settings
from django.db import models


class AuditEvent(models.Model):
    class ActorType(models.TextChoices):
        USER = "user", "User"
        SYSTEM = "system", "System"

    workspace = models.ForeignKey(
        "workspaces.Workspace",
        on_delete=models.CASCADE,
        related_name="audit_events",
    )
    document = models.ForeignKey(
        "documents.UploadedDocument",
        on_delete=models.CASCADE,
        related_name="audit_events",
        null=True,
        blank=True,
    )
    actor_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_events",
    )
    actor_type = models.CharField(max_length=20, choices=ActorType.choices, default=ActorType.USER)
    event_type = models.CharField(max_length=120)
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["workspace", "-created_at"]),
            models.Index(fields=["document", "-created_at"]),
        ]

    def __str__(self) -> str:
        return self.event_type
