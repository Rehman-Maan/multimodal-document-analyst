import csv
import json
from io import StringIO


def build_export_payload(document, run=None) -> dict:
    run = run or document.extraction_runs.first()
    fields = []
    if run:
        queryset = run.fields.all().order_by("field_name")
        fields = [
            {
                "field_name": field.field_name,
                "value": field.normalized_value,
                "raw_value": field.raw_value,
                "confidence": field.confidence,
                "source_page": field.source_page,
                "source_text": field.source_text,
                "validation_errors": field.validation_errors,
            }
            for field in queryset
        ]
    return {
        "document": {
            "id": document.pk,
            "title": document.title,
            "status": document.status,
            "document_type": document.document_type,
            "uploaded_at": document.created_at.isoformat(),
        },
        "extraction_run": {
            "id": run.pk if run else None,
            "status": run.status if run else None,
            "schema_id": run.schema_id if run else None,
            "model_name": run.model_name if run else None,
            "completed_at": run.completed_at.isoformat() if run and run.completed_at else None,
        },
        "fields": fields,
        "field_values": {field["field_name"]: field["value"] for field in fields},
    }


def build_json_export(document, run=None) -> bytes:
    payload = build_export_payload(document, run)
    return json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")


def build_csv_export(document, run=None) -> bytes:
    payload = build_export_payload(document, run)
    output = StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=[
            "document_id",
            "document_title",
            "extraction_run_id",
            "field_name",
            "value",
            "raw_value",
            "confidence",
            "source_page",
            "source_text",
            "validation_errors",
        ],
    )
    writer.writeheader()
    for field in payload["fields"]:
        writer.writerow(
            {
                "document_id": payload["document"]["id"],
                "document_title": payload["document"]["title"],
                "extraction_run_id": payload["extraction_run"]["id"],
                "field_name": field["field_name"],
                "value": field["value"],
                "raw_value": field["raw_value"],
                "confidence": field["confidence"],
                "source_page": field["source_page"] or "",
                "source_text": field["source_text"],
                "validation_errors": "; ".join(field["validation_errors"]),
            }
        )
    return output.getvalue().encode("utf-8")
