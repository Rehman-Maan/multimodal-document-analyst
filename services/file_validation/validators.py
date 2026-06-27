from dataclasses import dataclass
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError


ALLOWED_EXTENSIONS = {
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".tif": "image/tiff",
    ".tiff": "image/tiff",
}

EXTENSION_LABELS = {
    ".pdf": "PDF",
    ".png": "PNG",
    ".jpg": "JPG",
    ".jpeg": "JPG",
    ".tif": "TIFF",
    ".tiff": "TIFF",
}


@dataclass(frozen=True)
class ValidatedUpload:
    extension: str
    file_type: str
    size_bytes: int


def validate_uploaded_document(uploaded_file) -> ValidatedUpload:
    extension = Path(uploaded_file.name).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(sorted(EXTENSION_LABELS.values()))
        raise ValidationError(f"Unsupported file type. Upload one of: {allowed}.")

    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    if uploaded_file.size > max_bytes:
        raise ValidationError(f"File is too large. Maximum upload size is {settings.MAX_UPLOAD_MB} MB.")

    content_type = getattr(uploaded_file, "content_type", "") or ""
    expected_type = ALLOWED_EXTENSIONS[extension]
    if content_type and content_type != expected_type:
        if not (expected_type == "image/jpeg" and content_type in {"image/jpg", "image/pjpeg"}):
            raise ValidationError(f"File content type {content_type} does not match {expected_type}.")

    return ValidatedUpload(
        extension=extension,
        file_type=EXTENSION_LABELS[extension],
        size_bytes=uploaded_file.size,
    )
