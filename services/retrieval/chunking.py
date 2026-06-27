from dataclasses import dataclass


@dataclass(frozen=True)
class TextChunk:
    page_number: int | None
    chunk_index: int
    text: str


def chunk_document_pages(pages, max_words: int = 180, overlap_words: int = 30) -> list[TextChunk]:
    chunks = []
    chunk_index = 0
    step = max(max_words - overlap_words, 1)
    for page in pages:
        words = page.text_content.split()
        if not words:
            continue
        for start in range(0, len(words), step):
            text = " ".join(words[start : start + max_words]).strip()
            if not text:
                continue
            chunks.append(
                TextChunk(page_number=page.page_number, chunk_index=chunk_index, text=text)
            )
            chunk_index += 1
            if start + max_words >= len(words):
                break
    return chunks
