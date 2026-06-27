from django.utils import timezone

from apps.extraction.models import ExtractedField, ExtractionRun
from services.llm_gateway.local_extractor import extract_fields_locally
from services.llm_gateway.prompts import build_structured_extraction_prompt
from services.schema_validation.validators import validate_extracted_payload


def run_structured_extraction(document, schema) -> ExtractionRun:
    document_text = "\n\n".join(
        f"Page {page.page_number}:\n{page.text_content}" for page in document.pages.all()
    )
    prompt = build_structured_extraction_prompt(document_text, schema.schema_json)
    run = ExtractionRun.objects.create(document=document, schema=schema, prompt_snapshot=prompt)
    extracted_payload = extract_fields_locally(schema.schema_json, document.pages.all())
    validation_errors = validate_extracted_payload(schema.schema_json, extracted_payload)
    run.raw_output = {"fields": extracted_payload}
    run.validation_errors = validation_errors
    run.status = ExtractionRun.Status.NEEDS_REVIEW if validation_errors else ExtractionRun.Status.COMPLETED
    run.completed_at = timezone.now()
    run.save(update_fields=["raw_output", "validation_errors", "status", "completed_at"])

    for item in extracted_payload:
        ExtractedField.objects.create(
            run=run,
            document=document,
            field_name=item["field_name"],
            raw_value=item.get("raw_value") or "",
            normalized_value=item.get("normalized_value") or "",
            confidence=item.get("confidence") or 0,
            source_page=item.get("source_page"),
            source_text=item.get("source_text") or "",
            validation_errors=[
                error for error in validation_errors if error.startswith(f"{item['field_name']} ")
            ],
        )
    from apps.review.services import route_review_tasks

    route_review_tasks(run)
    return run
