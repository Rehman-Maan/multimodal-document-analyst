import json


def build_structured_extraction_prompt(document_text: str, schema_json: dict) -> str:
    return (
        "You are a careful document extraction system.\n\n"
        "Extract fields from the provided document using the target schema.\n\n"
        "Rules:\n"
        "- Return valid JSON only.\n"
        "- Do not invent missing fields.\n"
        "- Use null when a value is not visible or not supported.\n"
        "- Include a confidence score for each field from 0 to 1.\n"
        "- Include the source page number and supporting text when possible.\n"
        "- Preserve original values in raw_value.\n"
        "- Normalize dates, amounts, and IDs into normalized_value.\n\n"
        "Target schema:\n"
        f"{json.dumps(schema_json, indent=2)}\n\n"
        "Document text:\n"
        f"{document_text}\n"
    )
