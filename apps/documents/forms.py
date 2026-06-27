from pathlib import Path

from django import forms

from apps.documents.models import UploadedDocument
from services.file_validation.validators import validate_uploaded_document


DOCUMENT_TYPE_CHOICES = [
    ("", "Unspecified"),
    ("receipt", "Receipt"),
    ("invoice", "Invoice"),
    ("form", "Form"),
    ("scan", "Scan"),
    ("other", "Other"),
]


class UploadedDocumentForm(forms.ModelForm):
    title = forms.CharField(required=False)

    class Meta:
        model = UploadedDocument
        fields = ["title", "document_type", "file"]
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "June supplier invoice"}),
            "document_type": forms.Select(choices=DOCUMENT_TYPE_CHOICES),
            "file": forms.ClearableFileInput(attrs={"accept": ".pdf,.png,.jpg,.jpeg,.tif,.tiff"}),
        }

    def clean_file(self):
        uploaded_file = self.cleaned_data["file"]
        self.validated_upload = validate_uploaded_document(uploaded_file)
        return uploaded_file

    def clean_title(self):
        title = self.cleaned_data.get("title", "").strip()
        uploaded_file = self.files.get("file")
        if title:
            return title
        if uploaded_file:
            return Path(uploaded_file.name).stem.replace("_", " ").replace("-", " ").strip()
        return title
