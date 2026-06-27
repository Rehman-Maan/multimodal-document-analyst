from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


DEFAULT_RECEIPT_SCHEMA = {
    "fields": [
        {"name": "vendor_name", "type": "string", "required": True},
        {"name": "total_amount", "type": "decimal", "required": True},
        {"name": "transaction_date", "type": "date", "required": False},
    ]
}

DEFAULT_INVOICE_SCHEMA = {
    "fields": [
        {"name": "invoice_number", "type": "string", "required": True},
        {"name": "vendor_name", "type": "string", "required": True},
        {"name": "invoice_date", "type": "date", "required": False},
        {"name": "total_amount", "type": "decimal", "required": True},
    ]
}

DEFAULT_RESUME_SCHEMA = {
    "fields": [
        {"name": "candidate_name", "type": "string", "required": True},
        {"name": "email", "type": "string", "required": True},
        {"name": "phone_number", "type": "string", "required": False},
        {"name": "professional_summary", "type": "string", "required": False},
        {"name": "technical_skills", "type": "string", "required": False},
        {"name": "professional_experience", "type": "string", "required": False},
        {"name": "education", "type": "string", "required": False},
        {"name": "certifications", "type": "string", "required": False},
        {"name": "languages", "type": "string", "required": False},
    ]
}


class DocumentType(models.Model):
    workspace = models.ForeignKey(
        "workspaces.Workspace",
        on_delete=models.CASCADE,
        related_name="document_types",
    )
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, blank=True)
    description = models.TextField(blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["workspace", "slug"],
                name="unique_document_type_slug_per_workspace",
            )
        ]
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = slugify(self.name) or "document-type"
        super().save(*args, **kwargs)


class ExtractionSchema(models.Model):
    workspace = models.ForeignKey(
        "workspaces.Workspace",
        on_delete=models.CASCADE,
        related_name="extraction_schemas",
    )
    document_type = models.ForeignKey(
        DocumentType,
        on_delete=models.CASCADE,
        related_name="schemas",
    )
    name = models.CharField(max_length=160)
    version = models.PositiveIntegerField(default=1)
    schema_json = models.JSONField()
    active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_extraction_schemas",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["workspace", "document_type", "name", "version"],
                name="unique_schema_version_per_type",
            )
        ]
        ordering = ["document_type__name", "name", "-version"]

    def __str__(self) -> str:
        return f"{self.name} v{self.version}"

    def get_absolute_url(self) -> str:
        return reverse(
            "schema-detail",
            kwargs={"workspace_slug": self.workspace.slug, "pk": self.pk},
        )


def ensure_default_document_types_and_schemas(workspace, user) -> None:
    defaults = [
        ("Receipt", "receipt", DEFAULT_RECEIPT_SCHEMA),
        ("Invoice", "invoice", DEFAULT_INVOICE_SCHEMA),
        ("Other", "other", DEFAULT_RESUME_SCHEMA),
    ]
    for name, slug, schema_json in defaults:
        document_type, _ = DocumentType.objects.get_or_create(
            workspace=workspace,
            slug=slug,
            defaults={"name": name, "description": f"Default {name.lower()} document type."},
        )
        schema_name = "Resume Profile" if slug == "other" else f"Default {name}"
        ExtractionSchema.objects.get_or_create(
            workspace=workspace,
            document_type=document_type,
            name=schema_name,
            version=1,
            defaults={"schema_json": schema_json, "created_by": user},
        )
