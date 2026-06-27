import pytest
import fitz
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.urls import reverse

from apps.documents.models import UploadedDocument
from apps.documents.tasks import process_document
from apps.extraction.models import ExtractedField, ExtractionRun
from apps.extraction.services import run_structured_extraction
from apps.review.models import ReviewTask
from apps.schemas.models import ExtractionSchema, ensure_default_document_types_and_schemas
from apps.workspaces.models import Workspace, WorkspaceMembership
from services.llm_gateway.prompts import build_structured_extraction_prompt
from services.schema_validation.validators import SchemaValidationError, validate_schema_definition


pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def isolated_media_root(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path / "media"


def make_workspace():
    user = get_user_model().objects.create_user(username="owner", password="pass")
    workspace = Workspace.objects.create(name="Schema Ops", created_by=user)
    WorkspaceMembership.objects.create(
        workspace=workspace,
        user=user,
        role=WorkspaceMembership.Role.OWNER,
    )
    ensure_default_document_types_and_schemas(workspace, user)
    return user, workspace


def pdf_content(text):
    pdf = fitz.open()
    page = pdf.new_page()
    page.insert_text((72, 72), text)
    content = pdf.tobytes()
    pdf.close()
    return content


def make_processed_document(user, workspace):
    content = pdf_content("Acme Supplies\nInvoice INV-1001\nDate 2026-06-27\nTotal 42.50")
    document = UploadedDocument.objects.create(
        workspace=workspace,
        title="Invoice",
        file_type="PDF",
        uploaded_by=user,
        file_size=len(content),
    )
    document.file.save("invoice.pdf", ContentFile(content), save=True)
    process_document(document.pk)
    document.refresh_from_db()
    return document


def test_default_receipt_and_invoice_schemas_are_created():
    _user, workspace = make_workspace()

    assert workspace.document_types.filter(slug="receipt").exists()
    assert workspace.document_types.filter(slug="invoice").exists()
    assert workspace.document_types.filter(slug="other").exists()
    assert workspace.extraction_schemas.filter(document_type__slug="other", name="Resume Profile").exists()
    assert workspace.extraction_schemas.count() == 3


def test_schema_definition_validation_rejects_bad_field_type():
    with pytest.raises(SchemaValidationError):
        validate_schema_definition({"fields": [{"name": "total", "type": "money"}]})


def test_structured_extraction_prompt_contains_contract():
    prompt = build_structured_extraction_prompt(
        "Total 42.50",
        {"fields": [{"name": "total_amount", "type": "decimal", "required": True}]},
    )

    assert "Return valid JSON only" in prompt
    assert "total_amount" in prompt
    assert "Total 42.50" in prompt


def test_structured_extraction_creates_run_and_fields():
    user, workspace = make_workspace()
    document = make_processed_document(user, workspace)
    schema = ExtractionSchema.objects.get(workspace=workspace, document_type__slug="invoice")

    run = run_structured_extraction(document, schema)

    assert run.status == ExtractionRun.Status.NEEDS_REVIEW
    assert run.fields.filter(field_name="total_amount", normalized_value="42.50").exists()
    assert run.fields.filter(field_name="invoice_number", normalized_value="INV-1001").exists()
    assert ExtractedField.objects.filter(document=document).count() == 4
    assert ReviewTask.objects.filter(document=document, status=ReviewTask.Status.OPEN).exists()


def test_resume_schema_extracts_profile_fields():
    user, workspace = make_workspace()
    content = pdf_content(
        "Rao Abdul Rehman\n"
        "rao789rehman@gmail.com | +92-312-3882829\n"
        "Professional Summary\n"
        "Odoo ERP Developer and Technical Consultant.\n"
        "Technical Skills\n"
        "Python, JavaScript, SQL, XML, Odoo.sh\n"
        "Professional Experience\n"
        "Odoo Technical Consultant, Odolution\n"
        "Education\n"
        "Bachelor of Engineering, NED University\n"
        "Certifications\n"
        "Crash Course on Python\n"
        "Languages\n"
        "Urdu and English\n"
    )
    document = UploadedDocument.objects.create(
        workspace=workspace,
        title="Resume",
        file_type="PDF",
        uploaded_by=user,
        file_size=len(content),
        document_type="other",
    )
    document.file.save("resume.pdf", ContentFile(content), save=True)
    process_document(document.pk)
    schema = ExtractionSchema.objects.get(workspace=workspace, document_type__slug="other")

    run = run_structured_extraction(document, schema)

    assert run.fields.filter(field_name="candidate_name", normalized_value="Rao Abdul Rehman").exists()
    assert run.fields.filter(field_name="email", normalized_value="rao789rehman@gmail.com").exists()
    assert run.fields.filter(field_name="phone_number", normalized_value="+92-312-3882829").exists()
    skills = run.fields.get(field_name="technical_skills")
    assert "Python" in skills.normalized_value
    assert run.status == ExtractionRun.Status.COMPLETED


def test_document_extract_api_returns_fields(client):
    user, workspace = make_workspace()
    document = make_processed_document(user, workspace)
    schema = ExtractionSchema.objects.get(workspace=workspace, document_type__slug="invoice")
    client.force_login(user)

    response = client.post(
        reverse("api-document-extract", kwargs={"pk": document.pk}),
        {"schema_id": schema.pk},
        content_type="application/json",
    )

    assert response.status_code == 201
    assert response.json()["fields"]


def test_schema_list_view_requires_manager(client):
    user, workspace = make_workspace()
    client.force_login(user)

    response = client.get(reverse("schema-list", kwargs={"workspace_slug": workspace.slug}))

    assert response.status_code == 200
    assert "Default Invoice" in response.content.decode()
