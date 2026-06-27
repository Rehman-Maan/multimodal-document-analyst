import json

from django import forms

from apps.schemas.models import DocumentType, ExtractionSchema
from services.schema_validation.validators import SchemaValidationError, validate_schema_definition


class DocumentTypeForm(forms.ModelForm):
    class Meta:
        model = DocumentType
        fields = ["name", "slug", "description", "active"]


class ExtractionSchemaForm(forms.ModelForm):
    schema_text = forms.CharField(widget=forms.Textarea(attrs={"rows": 14}), label="Schema JSON")

    class Meta:
        model = ExtractionSchema
        fields = ["document_type", "name", "version", "active"]

    def __init__(self, *args, workspace=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.workspace = workspace
        self.fields["document_type"].queryset = DocumentType.objects.filter(workspace=workspace)
        if self.instance and self.instance.pk:
            self.fields["schema_text"].initial = json.dumps(self.instance.schema_json, indent=2)

    def clean_schema_text(self):
        raw = self.cleaned_data["schema_text"]
        try:
            schema_json = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise forms.ValidationError(f"Invalid JSON: {exc.msg}") from exc
        try:
            validate_schema_definition(schema_json)
        except SchemaValidationError as exc:
            raise forms.ValidationError(str(exc)) from exc
        return schema_json

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.workspace = self.workspace
        instance.schema_json = self.cleaned_data["schema_text"]
        if commit:
            instance.save()
        return instance
