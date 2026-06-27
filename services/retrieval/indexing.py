from apps.chat.models import DocumentChunk
from services.retrieval.chunking import chunk_document_pages
from services.retrieval.embeddings import embed_text


def index_document(document) -> int:
    chunks = chunk_document_pages(document.pages.all())
    DocumentChunk.objects.filter(document=document).delete()
    created = []
    for chunk in chunks:
        embedding, model = embed_text(chunk.text)
        created.append(
            DocumentChunk(
                workspace=document.workspace,
                document=document,
                page_number=chunk.page_number,
                chunk_index=chunk.chunk_index,
                text=chunk.text,
                embedding=embedding,
                embedding_model=model,
            )
        )
    DocumentChunk.objects.bulk_create(created)
    return len(created)
