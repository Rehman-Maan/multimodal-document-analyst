import re


AMOUNT_RE = re.compile(r"(?:total|amount|balance|due)[^\d]{0,20}(\d+(?:[.,]\d{2})?)", re.I)
DATE_RE = re.compile(r"\b(\d{4}-\d{2}-\d{2}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b")
INVOICE_RE = re.compile(r"(?:invoice|inv)[^\w]{0,12}([A-Z0-9-]{3,})", re.I)
EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
PHONE_RE = re.compile(r"(?:\+?\d[\d\s().-]{7,}\d)")


def extract_fields_locally(schema_json: dict, pages) -> list[dict]:
    page_items = list(pages)
    full_text = "\n".join(page.text_content for page in page_items)
    results = []
    for definition in schema_json.get("fields", []):
        name = definition["name"]
        field_type = definition["type"]
        raw_value, source_page, source_text, confidence = _extract_one(
            name, field_type, full_text, page_items
        )
        results.append(
            {
                "field_name": name,
                "raw_value": raw_value,
                "normalized_value": _normalize(raw_value, field_type),
                "confidence": confidence,
                "source_page": source_page,
                "source_text": source_text,
            }
        )
    return results


def _extract_one(name, field_type, full_text, pages):
    normalized_name = name.lower()
    if "email" in normalized_name:
        match = EMAIL_RE.search(full_text)
        if match:
            return _result(match.group(0), match.group(0), pages, confidence=0.95)
    if "phone" in normalized_name or "mobile" in normalized_name:
        match = PHONE_RE.search(full_text)
        if match:
            return _result(match.group(0).strip(), match.group(0).strip(), pages, confidence=0.88)
    if normalized_name in {"candidate_name", "full_name"} or (
        "name" in normalized_name and "vendor" not in normalized_name
    ):
        first_line = _first_content_line(full_text)
        if first_line:
            return _result(first_line[:120], first_line[:180], pages, confidence=0.82)
    if "summary" in normalized_name:
        return _section_result(
            full_text,
            pages,
            "Professional Summary",
            ["Technical Skills", "Professional Experience", "Education"],
        )
    if "skill" in normalized_name:
        return _section_result(
            full_text,
            pages,
            "Technical Skills",
            ["Professional Experience", "Projects", "Education"],
        )
    if "experience" in normalized_name:
        return _section_result(
            full_text,
            pages,
            "Professional Experience",
            ["Projects", "Education", "Achievements"],
        )
    if "education" in normalized_name:
        return _section_result(
            full_text,
            pages,
            "Education",
            ["Achievements", "Certifications", "Languages"],
        )
    if "certification" in normalized_name:
        return _section_result(full_text, pages, "Certifications", ["Languages"])
    if "language" in normalized_name:
        return _section_result(full_text, pages, "Languages", [])
    if field_type == "decimal":
        match = AMOUNT_RE.search(full_text)
        if match:
            return _result(match.group(1), match.group(0), pages)
    if field_type == "date" or name.endswith("_date"):
        match = DATE_RE.search(full_text)
        if match:
            return _result(match.group(1), match.group(0), pages)
    if "invoice" in name:
        match = INVOICE_RE.search(full_text)
        if match:
            return _result(match.group(1), match.group(0), pages)
    if "vendor" in name:
        line = next((line.strip() for line in full_text.splitlines() if line.strip()), "")
        if line:
            return _result(line[:120], line[:180], pages, confidence=0.45)
    return "", None, "", 0


def _first_content_line(full_text):
    for line in full_text.splitlines():
        stripped = line.strip(" |")
        if stripped:
            return stripped
    return ""


def _section_result(full_text, pages, heading, stop_headings):
    section = _section_text(full_text, heading, stop_headings)
    if not section:
        return "", None, "", 0
    value = section[:900]
    source_text = value[:180]
    return _result(value, source_text, pages, confidence=0.72)


def _section_text(full_text, heading, stop_headings):
    lines = full_text.splitlines()
    start_index = None
    for index, line in enumerate(lines):
        if line.strip().lower() == heading.lower():
            start_index = index + 1
            break
    if start_index is None:
        return ""
    stop_lookup = {item.lower() for item in stop_headings}
    section_lines = []
    for line in lines[start_index:]:
        stripped = line.strip()
        if stripped.lower() in stop_lookup:
            break
        if stripped:
            section_lines.append(stripped)
    return "\n".join(section_lines).strip()


def _result(value, source_text, pages, confidence=0.65):
    source_page = None
    for page in pages:
        if source_text in page.text_content or value in page.text_content:
            source_page = page.page_number
            break
    return value, source_page, source_text, confidence


def _normalize(value, field_type):
    if not value:
        return ""
    if field_type == "decimal":
        return value.replace(",", "")
    return value
