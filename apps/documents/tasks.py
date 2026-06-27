from celery import shared_task
from django.utils import timezone

from apps.documents.models import UploadedDocument
from services.document_parsing.processors import DocumentProcessingError, process_uploaded_document


@shared_task(bind=True, autoretry_for=(), retry_backoff=False)
def process_document(self, document_id: int) -> int:
    document = UploadedDocument.objects.get(pk=document_id)
    document.status = UploadedDocument.Status.PROCESSING
    document.error_message = ""
    document.processing_started_at = timezone.now()
    document.processing_completed_at = None
    document.save(
        update_fields=[
            "status",
            "error_message",
            "processing_started_at",
            "processing_completed_at",
            "updated_at",
        ]
    )

    try:
        result = process_uploaded_document(document)
    except DocumentProcessingError as exc:
        _mark_failed(document, str(exc))
        raise
    except Exception as exc:
        _mark_failed(document, "Unexpected processing error.")
        raise DocumentProcessingError("Unexpected processing error.") from exc

    document.status = UploadedDocument.Status.PROCESSED
    document.page_count = result.page_count
    document.processing_completed_at = timezone.now()
    document.error_message = ""
    document.save(
        update_fields=[
            "status",
            "page_count",
            "processing_completed_at",
            "error_message",
            "updated_at",
        ]
    )
    return result.page_count


def _mark_failed(document: UploadedDocument, message: str) -> None:
    document.status = UploadedDocument.Status.FAILED
    document.error_message = message
    document.processing_completed_at = timezone.now()
    document.save(update_fields=["status", "error_message", "processing_completed_at", "updated_at"])
