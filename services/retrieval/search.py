from apps.chat.models import DocumentChunk
from services.retrieval.embeddings import cosine_similarity, embed_text


def search_document(document, query: str, limit: int = 4) -> list[dict]:
    query_embedding, _model = embed_text(query)
    query_terms = _expand_terms(_terms(query))
    scored = []
    for chunk in DocumentChunk.objects.filter(document=document).order_by("chunk_index"):
        semantic_score = cosine_similarity(query_embedding, chunk.embedding)
        keyword_score = _keyword_score(query_terms, chunk.text)
        score = semantic_score + keyword_score
        scored.append({"chunk": chunk, "score": score})
    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored[:limit]


def _terms(text: str) -> set[str]:
    words = {
        word.strip(".,?!:;()[]{}\"'").lower()
        for word in text.split()
        if len(word.strip(".,?!:;()[]{}\"'")) >= 3
    }
    stop_words = {
        "the",
        "and",
        "for",
        "has",
        "have",
        "does",
        "did",
        "what",
        "who",
        "why",
        "how",
        "him",
        "his",
        "rao",
        "abdul",
        "rehman",
    }
    return words - stop_words


def _expand_terms(terms: set[str]) -> set[str]:
    expanded = set(terms)
    synonyms = {
        "qualification": {"education", "degree", "bachelor", "university", "cgpa"},
        "qualifications": {"education", "degree", "bachelor", "university", "cgpa"},
        "latest": {"education", "degree", "bachelor"},
        "highest": {"education", "degree", "bachelor"},
        "degree": {"education", "bachelor", "university"},
        "current": {"present", "experience", "employer", "consultant"},
        "employed": {"present", "experience", "employer", "job", "role", "consultant"},
        "employment": {"present", "experience", "employer", "job", "role", "consultant"},
        "works": {"present", "experience", "employer", "job", "role", "consultant"},
        "working": {"present", "experience", "employer", "job", "role", "consultant"},
        "work": {"present", "experience", "employer", "job", "role", "consultant"},
        "employer": {"experience", "odolution", "company", "present"},
        "job": {"experience", "consultant", "title", "present"},
        "title": {"experience", "consultant", "odoo"},
        "role": {"experience", "consultant", "title"},
        "certificate": {"certifications", "certification", "course"},
        "certificates": {"certifications", "certification", "course"},
        "certified": {"certifications", "certification", "course"},
    }
    for term in terms:
        expanded.update(synonyms.get(term, set()))
    return expanded


def _keyword_score(query_terms: set[str], text: str) -> float:
    if not query_terms:
        return 0
    text_lower = text.lower()
    matches = sum(1 for term in query_terms if term in text_lower)
    return min(matches * 0.18, 0.72)
