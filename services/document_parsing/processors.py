from dataclasses import dataclass
from pathlib import Path

import fitz
from django.core.files.base import ContentFile
from PIL import Image, ImageOps

from apps.documents.models import DocumentPage, UploadedDocument


MAX_IMAGE_DIMENSION = 1800
PDF_RENDER_ZOOM = 2


@dataclass(frozen=True)
class ProcessingResult:
    page_count: int


class DocumentProcessingError(Exception):
    pass


def process_uploaded_document(document: UploadedDocument) -> ProcessingResult:
    if document.file_type == "PDF":
        return _process_pdf(document)
    if document.file_type in {"PNG", "JPG", "TIFF"}:
        return _process_image(document)
    raise DocumentProcessingError(f"Unsupported file type for processing: {document.file_type}")


def _process_pdf(document: UploadedDocument) -> ProcessingResult:
    file_path = document.file.path
    try:
        pdf = fitz.open(file_path)
    except Exception as exc:
        raise DocumentProcessingError("Unable to open PDF for processing.") from exc

    with pdf:
        if pdf.is_encrypted:
            raise DocumentProcessingError("Encrypted PDFs are not supported.")
        if pdf.page_count == 0:
            raise DocumentProcessingError("PDF has no pages.")

        document.pages.all().delete()
        matrix = fitz.Matrix(PDF_RENDER_ZOOM, PDF_RENDER_ZOOM)
        for index, page in enumerate(pdf, start=1):
            text_content = page.get_text("text").strip()
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            page_record = DocumentPage(
                document=document,
                page_number=index,
                text_content=text_content,
                width=pixmap.width,
                height=pixmap.height,
            )
            page_record.image.save(
                f"page-{index}.png",
                ContentFile(pixmap.tobytes("png")),
                save=False,
            )
            page_record.save()

        return ProcessingResult(page_count=pdf.page_count)


def _process_image(document: UploadedDocument) -> ProcessingResult:
    try:
        image = Image.open(document.file.path)
    except Exception as exc:
        raise DocumentProcessingError("Unable to open image for processing.") from exc

    document.pages.all().delete()
    with image:
        normalized = ImageOps.exif_transpose(image)
        normalized.thumbnail((MAX_IMAGE_DIMENSION, MAX_IMAGE_DIMENSION))
        if normalized.mode not in {"RGB", "L"}:
            normalized = normalized.convert("RGB")

        content = _image_to_png_content(normalized)
        page_record = DocumentPage(
            document=document,
            page_number=1,
            width=normalized.width,
            height=normalized.height,
        )
        page_record.image.save(f"{Path(document.file.name).stem}-normalized.png", content, save=False)
        page_record.save()

    return ProcessingResult(page_count=1)


def _image_to_png_content(image: Image.Image) -> ContentFile:
    from io import BytesIO

    buffer = BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    return ContentFile(buffer.getvalue())
