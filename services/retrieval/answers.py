import re
from calendar import monthrange
from dataclasses import dataclass
from datetime import date

from django.conf import settings
from django.utils import timezone

from apps.chat.models import ChatMessage, ChatSession
from services.llm_gateway.openai_client import get_openai_client
from services.retrieval.search import search_document


MAX_LOCAL_EVIDENCE = 2
MAX_DISPLAY_CITATIONS = 1

STOP_WORDS = {
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
    "can",
    "know",
    "knows",
    "about",
    "him",
    "his",
    "her",
    "their",
    "current",
    "latest",
    "rao",
    "abdul",
    "rehman",
}

TERM_EXPANSIONS = {
    "qualification": {"education", "degree", "bachelor", "university", "cgpa"},
    "qualifications": {"education", "degree", "bachelor", "university", "cgpa"},
    "highest": {"education", "degree", "bachelor"},
    "degree": {"education", "bachelor", "university"},
    "employed": {"present", "experience", "employer", "job", "role", "consultant"},
    "employment": {"present", "experience", "employer", "job", "role", "consultant"},
    "works": {"present", "experience", "employer", "job", "role", "consultant"},
    "working": {"present", "experience", "employer", "job", "role", "consultant"},
    "work": {"present", "experience", "employer", "job", "role", "consultant"},
    "employer": {"experience", "company", "organization", "present", "consultant"},
    "job": {"experience", "role", "title", "position", "present"},
    "title": {"role", "position", "consultant", "experience"},
    "role": {"job", "title", "position", "experience"},
    "skills": {"technical", "tools", "technologies"},
    "skill": {"technical", "tools", "technologies"},
    "certificate": {"certifications", "certification", "course"},
    "certificates": {"certifications", "certification", "course"},
    "certified": {"certifications", "certification", "course"},
}

MONTHS = {
    "jan": 1,
    "january": 1,
    "feb": 2,
    "february": 2,
    "mar": 3,
    "march": 3,
    "apr": 4,
    "april": 4,
    "may": 5,
    "jun": 6,
    "june": 6,
    "jul": 7,
    "july": 7,
    "aug": 8,
    "august": 8,
    "sep": 9,
    "sept": 9,
    "september": 9,
    "oct": 10,
    "october": 10,
    "nov": 11,
    "november": 11,
    "dec": 12,
    "december": 12,
}

DATE_RANGE_RE = re.compile(
    r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
    r"Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?|tember)?|Oct(?:ober)?|"
    r"Nov(?:ember)?|Dec(?:ember)?)\s+\d{4}\s*[-–—]\s*"
    r"(?P<end>Present|(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|"
    r"Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?|tember)?|Oct(?:ober)?|"
    r"Nov(?:ember)?|Dec(?:ember)?)\s+\d{4})",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Evidence:
    text: str
    page_number: int | None
    score: float
    source: str
    chunk_id: int | None = None


def answer_document_question(session: ChatSession, question: str) -> ChatMessage:
    user_message = ChatMessage.objects.create(
        session=session,
        role=ChatMessage.Role.USER,
        content=question,
    )
    results = search_document(session.document, question)
    answer, citations = _answer_with_openai(session, question, results)
    if answer is None:
        answer, citations = _answer_locally(session, question, results)
    session.updated_at = user_message.created_at
    session.save(update_fields=["updated_at"])
    return ChatMessage.objects.create(
        session=session,
        role=ChatMessage.Role.ASSISTANT,
        content=answer,
        citations=citations,
    )


def _answer_locally(
    session: ChatSession, question: str, results: list[dict]
) -> tuple[str, list[dict]]:
    evidence = _rank_evidence(session, question, results)
    if not evidence:
        if _is_yes_no_question(question):
            return (
                "I do not see evidence for that in the document.",
                [],
            )
        return (
            "I could not find enough evidence in the document to answer that directly.",
            [],
        )

    selected = _select_evidence_for_answer(evidence)
    answer = _compose_answer(question, selected)
    citations = [_citation_for_evidence(item) for item in selected]
    return answer, citations


def _rank_evidence(session: ChatSession, question: str, results: list[dict]) -> list[Evidence]:
    terms = _expanded_terms(question)
    candidates = _field_evidence(session, terms) + _chunk_evidence(results, terms)
    useful = [candidate for candidate in candidates if candidate.score > 0]
    useful.sort(key=lambda item: (-item.score, len(item.text)))
    return _dedupe_evidence(useful)


def _field_evidence(session: ChatSession, terms: set[str]) -> list[Evidence]:
    run = session.document.extraction_runs.prefetch_related("fields").first()
    if not run:
        return []

    evidence = []
    for field in run.fields.all():
        label = field.field_name.replace("_", " ")
        value = field.normalized_value or field.raw_value
        if not value:
            continue
        source_text = f"{label}: {value}"
        base_score = _score_text(source_text, terms)
        if base_score <= 0:
            continue
        text = _field_fragment(label, value, terms)
        score = base_score + 0.75
        evidence.append(
            Evidence(
                text=_clean_sentence(text),
                page_number=field.source_page,
                score=score,
                source=f"field:{field.field_name}",
            )
        )
    return evidence


def _chunk_evidence(results: list[dict], terms: set[str]) -> list[Evidence]:
    evidence = []
    for result in results:
        chunk = result["chunk"]
        for fragment in _split_evidence(chunk.text):
            score = _score_text(fragment, terms)
            if score <= 0:
                continue
            evidence.append(
                Evidence(
                    text=_clean_sentence(fragment),
                    page_number=chunk.page_number,
                    score=score + min(result["score"], 1) * 0.2,
                    source="chunk",
                    chunk_id=chunk.pk,
                )
            )
    return evidence


def _compose_answer(question: str, evidence: list[Evidence]) -> str:
    field_answer = _compose_field_answer(question, evidence)
    if field_answer:
        return field_answer
    if _is_yes_no_question(question):
        return f"Yes. {evidence[0].text}"
    if len(evidence) == 1:
        return evidence[0].text
    return " ".join(item.text for item in evidence)


def _compose_field_answer(question: str, evidence: list[Evidence]) -> str:
    if not evidence or not evidence[0].source.startswith("field:"):
        return ""
    field_name = evidence[0].source.removeprefix("field:")
    value = _value_without_label(evidence[0].text)
    if not value:
        return ""
    question_terms = _expanded_terms(question)
    if field_name == "email":
        return f"The email address is {value}"
    if field_name == "phone_number":
        return f"The phone number is {value}"
    if field_name == "languages":
        return f"He knows {value}"
    if field_name == "education":
        return f"His education includes {value}"
    if field_name == "technical_skills":
        return f"His technical skills include {value}"
    if field_name == "professional_experience":
        if question_terms & {"employer", "job", "title", "role", "position", "present"}:
            return f"His current role is {value}"
        return f"His relevant experience includes {value}"
    if field_name == "candidate_name":
        return f"The candidate is {value}"
    if field_name == "certifications":
        return f"His certifications include {value}"
    return value


def _value_without_label(text: str) -> str:
    if ":" in text:
        text = text.split(":", 1)[1].strip()
    return _clean_answer_value(text)


def _clean_answer_value(text: str) -> str:
    text = text.replace("•", ";")
    text = re.sub(r"\s*;\s*", "; ", text)
    text = " ".join(text.split()).strip(" ;")
    if text and text[-1] not in ".?!":
        text = f"{text}."
    return text


def _select_evidence_for_answer(evidence: list[Evidence]) -> list[Evidence]:
    if len(evidence) <= 1:
        return evidence
    selected = [evidence[0]]
    if evidence[0].source.startswith("field:"):
        for item in evidence[1:MAX_LOCAL_EVIDENCE]:
            if item.source.startswith("field:") and item.score >= evidence[0].score * 0.72:
                selected.append(item)
        return selected
    for item in evidence[1:MAX_LOCAL_EVIDENCE]:
        if item.score >= evidence[0].score * 0.72 and not _substantially_overlaps(item.text, selected):
            selected.append(item)
    return selected


def _expanded_terms(question: str) -> set[str]:
    terms = _terms(question)
    expanded = set(terms)
    for term in terms:
        expanded.update(TERM_EXPANSIONS.get(term, set()))
    return expanded


def _terms(text: str) -> set[str]:
    words = {
        word.strip(".,?!:;()[]{}\"'").lower()
        for word in text.split()
        if len(word.strip(".,?!:;()[]{}\"'")) >= 3
    }
    return words - STOP_WORDS


def _score_text(text: str, terms: set[str]) -> float:
    if not terms:
        return 0
    text_lower = text.lower()
    exact_matches = sum(1 for term in terms if re.search(rf"\b{re.escape(term)}\b", text_lower))
    partial_matches = sum(1 for term in terms if term in text_lower) - exact_matches
    return exact_matches + partial_matches * 0.35


def _best_fragment(text: str, terms: set[str]) -> str:
    fragments = _split_evidence(text)
    if not fragments:
        return text
    fragments.sort(key=lambda fragment: (-_score_text(fragment, terms), len(fragment)))
    return fragments[0]


def _field_fragment(label: str, value: str, terms: set[str]) -> str:
    display_label = _display_label(label)
    label_score = _score_text(label, terms)
    if label_score > 0:
        return f"{display_label}: {_compact_value(value)}"
    value_fragment = _best_fragment(value, terms)
    if _score_text(value_fragment, terms) > 0:
        return f"{display_label}: {value_fragment}"
    return value_fragment


def _display_label(label: str) -> str:
    return " ".join(word.capitalize() for word in label.split())


def _compact_value(value: str) -> str:
    value = " ".join(value.split())
    if len(value) <= 220:
        return value
    return f"{value[:217].rstrip()}..."


def _split_evidence(text: str) -> list[str]:
    normalized = text.replace("\n", " ")
    parts = re.split(r"\.\s+|;\s+|\s+\u2022\s+|\s+\u00e2\u20ac\u00a2\s+", normalized)
    return [part.strip(" -") for part in parts if part.strip(" -")]


def _clean_sentence(sentence: str) -> str:
    sentence = _trim_to_section_heading(sentence)
    sentence = " ".join(sentence.split())
    if len(sentence) > 240:
        sentence = f"{sentence[:237].rstrip()}..."
    if sentence and sentence[-1] not in ".?!":
        sentence = f"{sentence}."
    return sentence


def _trim_to_section_heading(sentence: str) -> str:
    headings = [
        "Professional Summary",
        "Technical Skills",
        "Professional Experience",
        "Education",
        "Achievements",
        "Certifications",
        "Languages",
    ]
    sentence_lower = sentence.lower()
    positions = [
        sentence_lower.find(heading.lower())
        for heading in headings
        if sentence_lower.find(heading.lower()) > 0
    ]
    if not positions:
        return sentence
    return sentence[min(positions) :]


def _dedupe_evidence(items: list[Evidence]) -> list[Evidence]:
    seen = set()
    deduped = []
    for item in items:
        key = re.sub(r"\W+", " ", item.text.lower())[:120]
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def _substantially_overlaps(text: str, selected: list[Evidence]) -> bool:
    text_terms = _terms(text)
    if not text_terms:
        return False
    for item in selected:
        selected_terms = _terms(item.text)
        if not selected_terms:
            continue
        overlap = len(text_terms & selected_terms) / max(len(text_terms), 1)
        if overlap >= 0.55:
            return True
    return False


def _is_yes_no_question(question: str) -> bool:
    first_word = question.strip().split(maxsplit=1)[0].lower() if question.strip() else ""
    return first_word in {"is", "are", "was", "were", "do", "does", "did", "can", "has", "have"}


def _answer_with_openai(
    session: ChatSession, question: str, results: list[dict]
) -> tuple[str | None, list[dict]]:
    if not getattr(settings, "OPENAI_API_KEY", "") or not results:
        return None, []
    try:
        client = get_openai_client()
    except ImportError:
        return None, []
    context_items = _openai_context_items(session, question, results)
    if not context_items:
        context_items = _openai_fallback_context_items(session, results)
    if not context_items:
        return None, []
    current_date_value = timezone.localdate()
    context_items = _annotate_temporal_context(context_items, current_date_value)
    context = "\n\n".join(item["context"] for item in context_items)
    current_date = current_date_value.isoformat()
    try:
        response = client.responses.create(
            model=settings.OPENAI_CHAT_MODEL,
            input=(
                "Answer the user's question using only the provided document context. "
                "Be concise. Mention citation numbers in square brackets only for the "
                "specific sources you actually used. Do not cite unrelated sources. "
                "If the context does not support a yes/no claim, say that directly and "
                "mention what the context does support. "
                f"Current date: {current_date}. Interpret date ranges relative to the "
                "current date. If an education or job date range ended before the current "
                "date, describe it as completed or past, not pursuing/current/ongoing. "
                "Use ongoing wording only when the document says Present or the end date "
                "is after the current date. Trust explicit status notes in the context "
                "over generic wording.\n\n"
                f"Context:\n{context}\n\nQuestion: {question}"
            ),
        )
    except Exception:
        return None, []
    citations = _citations_used_by_answer(response.output_text, context_items)
    return _strip_inline_citation_markers(response.output_text), citations


def _annotate_temporal_context(
    context_items: list[dict], current_date: date
) -> list[dict]:
    for item in context_items:
        note = _temporal_status_note(item["context_text"], current_date)
        if note:
            item["context_text"] = f"{item['context_text']} {note}"
    for index, item in enumerate(context_items, start=1):
        item["context"] = f"[{index}] {item['context_text']}"
        item["label"] = str(index)
    return context_items


def _temporal_status_note(text: str, current_date: date) -> str:
    notes = []
    for match in DATE_RANGE_RE.finditer(text):
        end_text = match.group("end")
        if end_text.lower() == "present":
            notes.append(
                f"Status as of {current_date.isoformat()}: ongoing because the range ends in Present."
            )
            continue
        end_date = _parse_month_year_end(end_text)
        if not end_date:
            continue
        if end_date < current_date:
            notes.append(
                f"Status as of {current_date.isoformat()}: completed/past because the range ended in {end_text}."
            )
        else:
            notes.append(
                f"Status as of {current_date.isoformat()}: ongoing because the range ends in {end_text}."
            )
    return " ".join(dict.fromkeys(notes))


def _parse_month_year_end(value: str) -> date | None:
    parts = value.split()
    if len(parts) != 2:
        return None
    month = MONTHS.get(parts[0].lower().strip("."))
    if not month:
        return None
    try:
        year = int(parts[1])
    except ValueError:
        return None
    return date(year, month, monthrange(year, month)[1])


def _openai_context_items(session: ChatSession, question: str, results: list[dict]) -> list[dict]:
    terms = _expanded_terms(question)
    items = []
    run = session.document.extraction_runs.prefetch_related("fields").first()
    if run:
        for field in run.fields.all():
            label = field.field_name.replace("_", " ")
            value = field.normalized_value or field.raw_value
            if not value:
                continue
            text = _field_fragment(label, value, terms)
            score = _score_text(f"{label} {value}", terms)
            if score <= 0:
                continue
            items.append(
                {
                    "score": score + 0.75,
                    "context_text": text,
                    "context": "",
                    "citation": {
                        "chunk_id": None,
                        "page_number": field.source_page,
                        "score": round(score + 0.75, 4),
                        "excerpt": _clean_sentence(text),
                        "source": f"openai:{field.field_name}",
                    },
                }
            )
    for result in results:
        chunk = result["chunk"]
        score = _score_text(chunk.text, terms)
        if score <= 0:
            continue
        items.append(
            {
                "score": score + min(result["score"], 1) * 0.2,
                "context_text": chunk.text,
                "context": "",
                "citation": _citation_for_result(result, question),
            }
        )
    items.sort(key=lambda item: item["score"], reverse=True)
    selected = items[:4]
    for index, item in enumerate(selected, start=1):
        item["context"] = f"[{index}] {item['context_text']}"
        item["label"] = str(index)
    return selected


def _openai_fallback_context_items(session: ChatSession, results: list[dict]) -> list[dict]:
    items = []
    run = session.document.extraction_runs.prefetch_related("fields").first()
    priority = {
        "candidate_name": 8,
        "professional_summary": 7,
        "professional_experience": 6,
        "education": 5,
        "technical_skills": 4,
        "certifications": 3,
    }
    if run:
        for field in run.fields.all():
            if field.field_name not in priority:
                continue
            value = field.normalized_value or field.raw_value
            if not value:
                continue
            label = field.field_name.replace("_", " ")
            text = _field_fragment(label, value, {label.split()[0]})
            items.append(
                {
                    "score": priority[field.field_name],
                    "context_text": text,
                    "context": "",
                    "citation": {
                        "chunk_id": None,
                        "page_number": field.source_page,
                        "score": priority[field.field_name],
                        "excerpt": _clean_sentence(text),
                        "source": f"openai:{field.field_name}",
                    },
                }
            )
    for result in results[:2]:
        chunk = result["chunk"]
        items.append(
            {
                "score": result["score"],
                "context_text": chunk.text,
                "context": "",
                "citation": _citation_for_result(result, ""),
            }
        )
    items.sort(key=lambda item: item["score"], reverse=True)
    selected = items[:4]
    for index, item in enumerate(selected, start=1):
        item["context"] = f"[{index}] {item['context_text']}"
        item["label"] = str(index)
    return selected


def _citations_used_by_answer(answer: str, context_items: list[dict]) -> list[dict]:
    used_labels = set(re.findall(r"\[(\d+)\]", answer))
    if not used_labels and context_items:
        used_labels = {context_items[0]["label"]}
    citations = []
    for item in context_items:
        if item["label"] in used_labels:
            citations.append(item["citation"])
    structured_candidates = [
        item["citation"]
        for item in context_items
        if str(item["citation"].get("source", "")).startswith("openai:")
    ]
    citations.extend(structured_candidates)
    citations = _dedupe_citations(citations)
    citations.sort(
        key=lambda citation: (
            not str(citation.get("source", "")).startswith("openai:"),
            -float(citation.get("score", 0)),
        )
    )
    return citations[:MAX_DISPLAY_CITATIONS]


def _dedupe_citations(citations: list[dict]) -> list[dict]:
    seen = set()
    unique = []
    for citation in citations:
        key = (citation.get("source"), citation.get("page_number"), citation.get("excerpt"))
        if key in seen:
            continue
        seen.add(key)
        unique.append(citation)
    return unique


def _strip_inline_citation_markers(answer: str) -> str:
    answer = re.sub(r"(?:\s*\[\d+\])+", "", answer)
    return " ".join(answer.split())


def _citation_for_evidence(evidence: Evidence) -> dict:
    return {
        "chunk_id": evidence.chunk_id,
        "page_number": evidence.page_number,
        "score": round(evidence.score, 4),
        "excerpt": evidence.text,
        "source": evidence.source,
    }


def _citation_for_result(result: dict, question: str = "") -> dict:
    chunk = result["chunk"]
    return {
        "chunk_id": chunk.pk,
        "page_number": chunk.page_number,
        "score": round(result["score"], 4),
        "excerpt": _citation_excerpt(chunk.text, question),
        "source": "openai",
    }


def _citation_excerpt(text: str, question: str) -> str:
    normalized = " ".join(text.split())
    if not normalized:
        return ""
    terms = _expanded_terms(question)
    best_position = _best_term_position(normalized.lower(), terms)
    if best_position is None:
        return normalized[:220]
    start = max(best_position - 35, 0)
    end = min(start + 220, len(normalized))
    excerpt = normalized[start:end].strip()
    if start > 0:
        excerpt = f"...{excerpt}"
    if end < len(normalized):
        excerpt = f"{excerpt}..."
    return excerpt


def _best_term_position(text_lower: str, terms: set[str]) -> int | None:
    positions = [text_lower.find(term) for term in terms if term and text_lower.find(term) >= 0]
    if not positions:
        return None
    return min(positions)
