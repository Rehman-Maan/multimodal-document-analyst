import hashlib
import math

from django.conf import settings

from services.llm_gateway.openai_client import get_openai_client


EMBEDDING_DIMENSIONS = 64
LOCAL_EMBEDDING_MODEL = "local-hash-embedding"


def embed_text(text: str) -> tuple[list[float], str]:
    if getattr(settings, "OPENAI_API_KEY", ""):
        remote = _embed_with_openai(text)
        if remote is not None:
            return _resize_vector(remote, EMBEDDING_DIMENSIONS), settings.OPENAI_EMBEDDING_MODEL
    return embed_text_locally(text), LOCAL_EMBEDDING_MODEL


def embed_text_locally(text: str, dimensions: int = EMBEDDING_DIMENSIONS) -> list[float]:
    vector = [0.0] * dimensions
    for token in text.lower().split():
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:2], "big") % dimensions
        sign = 1.0 if digest[2] % 2 == 0 else -1.0
        vector[index] += sign
    return _normalize(vector)


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right:
        return 0.0
    return sum(a * b for a, b in zip(left, right))


def _embed_with_openai(text: str) -> list[float] | None:
    try:
        client = get_openai_client()
    except ImportError:
        return None
    try:
        response = client.embeddings.create(model=settings.OPENAI_EMBEDDING_MODEL, input=text)
    except Exception:
        return None
    return response.data[0].embedding


def _resize_vector(vector: list[float], dimensions: int) -> list[float]:
    if len(vector) == dimensions:
        return _normalize(vector)
    resized = [0.0] * dimensions
    for index, value in enumerate(vector):
        resized[index % dimensions] += value
    return _normalize(resized)


def _normalize(vector: list[float]) -> list[float]:
    magnitude = math.sqrt(sum(value * value for value in vector))
    if magnitude == 0:
        return vector
    return [round(value / magnitude, 8) for value in vector]
