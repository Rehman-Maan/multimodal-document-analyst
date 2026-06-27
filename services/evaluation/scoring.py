from dataclasses import dataclass
from types import SimpleNamespace

from services.llm_gateway.local_extractor import extract_fields_locally


@dataclass(frozen=True)
class EvaluationResult:
    metrics: dict
    item_results: list[dict]


def score_dataset(items: list[dict]) -> EvaluationResult:
    item_results = []
    for item in items:
        predicted = _predicted_fields(item)
        item_results.append(score_item(item, predicted))
    return EvaluationResult(metrics=_aggregate(item_results), item_results=item_results)


def score_item(item: dict, predicted_fields: dict[str, str]) -> dict:
    expected_fields = item.get("expected_fields", {})
    critical_fields = set(item.get("critical_fields", []))
    expected_type = item.get("document_type", "")
    predicted_type = item.get("predicted_document_type", expected_type)
    field_results = []
    exact_matches = 0
    missing_fields = 0
    critical_matches = 0

    for name, expected_value in expected_fields.items():
        predicted_value = str(predicted_fields.get(name, "")).strip()
        expected_normalized = str(expected_value).strip()
        is_missing = predicted_value == ""
        is_match = predicted_value == expected_normalized
        if is_match:
            exact_matches += 1
        if is_missing:
            missing_fields += 1
        if name in critical_fields and is_match:
            critical_matches += 1
        field_results.append(
            {
                "field_name": name,
                "expected": expected_normalized,
                "predicted": predicted_value,
                "exact_match": is_match,
                "missing": is_missing,
                "critical": name in critical_fields,
            }
        )

    predicted_non_empty = {name for name, value in predicted_fields.items() if str(value).strip()}
    expected_names = set(expected_fields)
    true_positive_names = {
        result["field_name"] for result in field_results if result["exact_match"]
    }
    precision = _safe_divide(len(true_positive_names), len(predicted_non_empty))
    recall = _safe_divide(len(true_positive_names), len(expected_names))
    f1 = _safe_divide(2 * precision * recall, precision + recall)

    return {
        "id": item.get("id", ""),
        "document_type": expected_type,
        "predicted_document_type": predicted_type,
        "classification_match": predicted_type == expected_type,
        "field_results": field_results,
        "field_exact_match_rate": _safe_divide(exact_matches, len(expected_fields)),
        "field_precision": precision,
        "field_recall": recall,
        "field_f1": f1,
        "critical_exact_match_rate": _safe_divide(critical_matches, len(critical_fields)),
        "missing_field_rate": _safe_divide(missing_fields, len(expected_fields)),
        "invalid_output": not isinstance(predicted_fields, dict),
    }


def _predicted_fields(item: dict) -> dict[str, str]:
    if "predicted_fields" in item:
        return {name: str(value) for name, value in item["predicted_fields"].items()}
    text = item.get("text", "")
    schema = item.get("schema") or _schema_from_expected(item.get("expected_fields", {}))
    page = SimpleNamespace(page_number=1, text_content=text)
    extracted = extract_fields_locally(schema, [page])
    return {field["field_name"]: str(field.get("normalized_value") or "") for field in extracted}


def _schema_from_expected(expected_fields: dict) -> dict:
    fields = []
    for name in expected_fields:
        field_type = "string"
        if name.endswith("_date") or "date" in name:
            field_type = "date"
        elif "amount" in name or "total" in name:
            field_type = "decimal"
        fields.append({"name": name, "type": field_type, "required": True})
    return {"fields": fields}


def _aggregate(item_results: list[dict]) -> dict:
    total = len(item_results)
    return {
        "total_items": total,
        "classification_accuracy": _average(item_results, "classification_match"),
        "field_exact_match": _average(item_results, "field_exact_match_rate"),
        "field_precision": _average(item_results, "field_precision"),
        "field_recall": _average(item_results, "field_recall"),
        "field_f1": _average(item_results, "field_f1"),
        "critical_field_exact_match": _average(item_results, "critical_exact_match_rate"),
        "missing_field_rate": _average(item_results, "missing_field_rate"),
        "invalid_output_rate": _average(item_results, "invalid_output"),
    }


def _average(items: list[dict], key: str) -> float:
    if not items:
        return 0.0
    return round(sum(float(item[key]) for item in items) / len(items), 4)


def _safe_divide(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return round(numerator / denominator, 4)
