from celery import shared_task

from apps.documents.models import UploadedDocument
from apps.extraction.services import run_structured_extraction
from apps.schemas.models import ExtractionSchema


@shared_task
def extract_document_fields(document_id: int, schema_id: int) -> int:
    document = UploadedDocument.objects.get(pk=document_id)
    schema = ExtractionSchema.objects.get(pk=schema_id)
    run = run_structured_extraction(document, schema)
    return run.pk
