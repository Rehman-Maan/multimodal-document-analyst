import json

from django.db import models


class VectorField(models.Field):
    description = "pgvector-compatible vector field with text fallback for tests"

    def __init__(self, dimensions=64, *args, **kwargs):
        self.dimensions = dimensions
        super().__init__(*args, **kwargs)

    def db_type(self, connection):
        if connection.vendor == "postgresql":
            return f"vector({self.dimensions})"
        return "text"

    def from_db_value(self, value, expression, connection):
        return self.to_python(value)

    def to_python(self, value):
        if value in (None, ""):
            return []
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            cleaned = value.strip()
            if cleaned.startswith("[") and cleaned.endswith("]"):
                return [float(item) for item in cleaned.strip("[]").split(",") if item.strip()]
            return json.loads(cleaned)
        return value

    def get_prep_value(self, value):
        if value in (None, ""):
            return "[]"
        if isinstance(value, str):
            return value
        return "[" + ",".join(str(float(item)) for item in value) + "]"

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs["dimensions"] = self.dimensions
        return name, path, args, kwargs
