from decimal import Decimal, InvalidOperation


SUPPORTED_TYPES = {"string", "decimal", "date", "integer", "boolean"}


class SchemaValidationError(ValueError):
    pass


def validate_schema_definition(schema_json: dict) -> None:
    fields = schema_json.get("fields")
    if not isinstance(fields, list) or not fields:
        raise SchemaValidationError("Schema must include a non-empty fields list.")
    names = set()
    for field in fields:
        if not isinstance(field, dict):
            raise SchemaValidationError("Each field must be an object.")
        name = field.get("name")
        field_type = field.get("type")
        if not name or not isinstance(name, str):
            raise SchemaValidationError("Each field needs a string name.")
        if name in names:
            raise SchemaValidationError(f"Duplicate field name: {name}.")
        names.add(name)
        if field_type not in SUPPORTED_TYPES:
            raise SchemaValidationError(f"Unsupported field type for {name}: {field_type}.")
        if "required" in field and not isinstance(field["required"], bool):
            raise SchemaValidationError(f"Field {name} required must be a boolean.")


def validate_extracted_payload(schema_json: dict, extracted_fields: list[dict]) -> list[str]:
    errors = []
    expected = {field["name"]: field for field in schema_json.get("fields", [])}
    extracted = {field.get("field_name"): field for field in extracted_fields}
    for name, definition in expected.items():
        item = extracted.get(name)
        value = None if item is None else item.get("normalized_value")
        if definition.get("required") and value in {None, ""}:
            errors.append(f"{name} is required.")
        if value not in {None, ""}:
            errors.extend(_validate_type(name, definition["type"], value))
    return errors


def _validate_type(name: str, field_type: str, value) -> list[str]:
    if field_type == "decimal":
        try:
            Decimal(str(value))
        except (InvalidOperation, ValueError):
            return [f"{name} must be a decimal."]
    if field_type == "integer":
        try:
            int(value)
        except (TypeError, ValueError):
            return [f"{name} must be an integer."]
    if field_type == "boolean" and not isinstance(value, bool):
        return [f"{name} must be a boolean."]
    return []
