from django.core.files.base import ContentFile
from django.utils.text import slugify

from apps.audit.models import AuditEvent
from apps.exports.models import ExportRecord
from services.export_builder.builders import build_csv_export, build_json_export, build_export_payload


def create_export_record(document, export_format: str, user) -> ExportRecord:
    run = document.extraction_runs.first()
    if export_format == ExportRecord.Format.JSON:
        content = build_json_export(document, run)
        extension = "json"
    elif export_format == ExportRecord.Format.CSV:
        content = build_csv_export(document, run)
        extension = "csv"
    else:
        raise ValueError(f"Unsupported export format: {export_format}")

    payload = build_export_payload(document, run)
    filename = f"{slugify(document.title) or 'document'}-{document.pk}.{extension}"
    record = ExportRecord.objects.create(
        workspace=document.workspace,
        document=document,
        extraction_run=run,
        created_by=user,
        format=export_format,
        field_count=len(payload["fields"]),
        metadata={
            "document_status": document.status,
            "run_status": run.status if run else None,
            "reviewed_values_included": True,
        },
    )
    record.file.save(filename, ContentFile(content), save=True)
    AuditEvent.objects.create(
        workspace=document.workspace,
        document=document,
        actor_user=user,
        event_type="document_exported",
        payload={
            "export_id": record.pk,
            "format": record.format,
            "field_count": record.field_count,
            "extraction_run_id": run.pk if run else None,
        },
    )
    return record
