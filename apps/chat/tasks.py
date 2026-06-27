from config.celery import app
from apps.documents.models import UploadedDocument
from services.retrieval.indexing import index_document


@app.task(name="chat.index_document")
def index_document_task(document_id: int) -> int:
    document = UploadedDocument.objects.get(pk=document_id)
    return index_document(document)
