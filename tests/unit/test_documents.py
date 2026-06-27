import pytest
import fitz
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image

from apps.documents.models import DocumentPage, UploadedDocument
from apps.documents.tasks import process_document
from apps.workspaces.models import Workspace, WorkspaceMembership
from services.file_validation.validators import validate_uploaded_document


pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def isolated_media_root(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path / "media"


def make_workspace(username="owner", workspace_name="Ops"):
    user = get_user_model().objects.create_user(username=username, password="pass")
    workspace = Workspace.objects.create(name=workspace_name, created_by=user)
    WorkspaceMembership.objects.create(
        workspace=workspace,
        user=user,
        role=WorkspaceMembership.Role.OWNER,
    )
    return user, workspace


def pdf_bytes(text="Invoice total 42"):
    pdf = fitz.open()
    page = pdf.new_page()
    page.insert_text((72, 72), text)
    content = pdf.tobytes()
    pdf.close()
    return content


def image_bytes():
    from io import BytesIO

    image = Image.new("RGB", (200, 100), color=(240, 250, 245))
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def upload_file(name="invoice.pdf", content_type="application/pdf", content=None):
    if content is None:
        content = pdf_bytes()
    return SimpleUploadedFile(name, content, content_type=content_type)


def test_file_validation_accepts_pdf():
    validated = validate_uploaded_document(upload_file())

    assert validated.file_type == "PDF"
    assert validated.extension == ".pdf"


def test_file_validation_rejects_unknown_extension():
    with pytest.raises(ValidationError):
        validate_uploaded_document(upload_file(name="payload.exe", content_type="application/x-msdownload"))


def test_document_upload_view_creates_uploaded_document(client):
    user, workspace = make_workspace()
    client.force_login(user)

    response = client.post(
        reverse("document-upload", kwargs={"workspace_slug": workspace.slug}),
        {
            "title": "Supplier invoice",
            "document_type": "invoice",
            "file": upload_file(),
        },
    )

    document = UploadedDocument.objects.get(title="Supplier invoice")
    assert response.status_code == 302
    assert document.workspace == workspace
    assert document.uploaded_by == user
    assert document.file_type == "PDF"
    assert document.status == UploadedDocument.Status.PROCESSED
    assert document.page_count == 1


def test_document_library_is_workspace_scoped(client):
    user, workspace = make_workspace("owner", "Visible")
    other_user, other_workspace = make_workspace("other", "Hidden")
    UploadedDocument.objects.create(
        workspace=workspace,
        title="Visible doc",
        file=upload_file(),
        file_type="PDF",
        uploaded_by=user,
        file_size=10,
    )
    UploadedDocument.objects.create(
        workspace=other_workspace,
        title="Hidden doc",
        file=upload_file(name="hidden.pdf"),
        file_type="PDF",
        uploaded_by=other_user,
        file_size=10,
    )
    client.force_login(user)

    response = client.get(reverse("document-list", kwargs={"workspace_slug": workspace.slug}))

    assert response.status_code == 200
    assert "Visible doc" in response.content.decode()
    assert "Hidden doc" not in response.content.decode()


def test_document_detail_denies_cross_workspace_access(client):
    user, _workspace = make_workspace("owner", "Visible")
    other_user, other_workspace = make_workspace("other", "Hidden")
    hidden_document = UploadedDocument.objects.create(
        workspace=other_workspace,
        title="Hidden doc",
        file=upload_file(name="hidden.pdf"),
        file_type="PDF",
        uploaded_by=other_user,
        file_size=10,
    )
    client.force_login(user)

    response = client.get(
        reverse(
            "document-detail",
            kwargs={"workspace_slug": other_workspace.slug, "pk": hidden_document.pk},
        )
    )

    assert response.status_code == 403


def test_document_api_upload_requires_workspace_membership(client):
    user, workspace = make_workspace("owner", "Visible")
    other_user, other_workspace = make_workspace("other", "Hidden")
    client.force_login(user)

    response = client.post(
        reverse("api-document-list"),
        {
            "workspace_slug": other_workspace.slug,
            "title": "Blocked",
            "document_type": "invoice",
            "file": upload_file(),
        },
    )

    assert response.status_code == 400
    assert not UploadedDocument.objects.filter(title="Blocked").exists()

    response = client.post(
        reverse("api-document-list"),
        {
            "workspace_slug": workspace.slug,
            "title": "Allowed",
            "document_type": "invoice",
            "file": upload_file(name="allowed.pdf"),
        },
    )

    assert response.status_code == 201
    assert UploadedDocument.objects.filter(title="Allowed", uploaded_by=user).exists()
    assert other_user.workspace_memberships.exists()


def test_pdf_processing_creates_page_text_and_preview():
    user, workspace = make_workspace()
    document = UploadedDocument.objects.create(
        workspace=workspace,
        title="Process me",
        file=upload_file(content=pdf_bytes("Extract this line")),
        file_type="PDF",
        uploaded_by=user,
        file_size=10,
    )

    page_count = process_document(document.pk)
    document.refresh_from_db()

    assert page_count == 1
    assert document.status == UploadedDocument.Status.PROCESSED
    assert document.page_count == 1
    page = DocumentPage.objects.get(document=document, page_number=1)
    assert "Extract this line" in page.text_content
    assert page.image.name.endswith(".png")
    assert page.width > 0
    assert page.height > 0


def test_image_processing_creates_single_normalized_page():
    user, workspace = make_workspace()
    document = UploadedDocument.objects.create(
        workspace=workspace,
        title="Image doc",
        file=upload_file(name="scan.png", content_type="image/png", content=image_bytes()),
        file_type="PNG",
        uploaded_by=user,
        file_size=10,
    )

    process_document(document.pk)
    document.refresh_from_db()

    assert document.status == UploadedDocument.Status.PROCESSED
    assert document.page_count == 1
    page = DocumentPage.objects.get(document=document, page_number=1)
    assert page.text_content == ""
    assert page.image.name.endswith(".png")
    assert page.width == 200
    assert page.height == 100


def test_processing_failure_marks_document_failed():
    user, workspace = make_workspace()
    document = UploadedDocument.objects.create(
        workspace=workspace,
        title="Broken",
        file=upload_file(content=b"not a pdf"),
        file_type="PDF",
        uploaded_by=user,
        file_size=10,
    )

    with pytest.raises(Exception):
        process_document(document.pk)
    document.refresh_from_db()

    assert document.status == UploadedDocument.Status.FAILED
    assert document.error_message
