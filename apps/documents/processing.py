from django.contrib import messages

from apps.documents.tasks import process_document


def enqueue_document_processing(document, request=None) -> None:
    process_document.delay(document.pk)
    if request is not None:
        messages.success(request, "Document processing has started.")
