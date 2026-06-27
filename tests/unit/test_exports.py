import csv
import json
from io import StringIO

import pytest
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.urls import reverse

from apps.audit.models import AuditEvent
from apps.documents.models import UploadedDocument
from apps.exports.models import ExportRecord
from apps.exports.services import create_export_record
from apps.extraction.models import ExtractedField, ExtractionRun
from apps.workspaces.models import Workspace, WorkspaceMembership
from services.export_builder.builders import build_csv_export, build_export_payload


pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def isolated_media_root(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path / "media"


def make_workspace():
    user = get_user_model().objects.create_user(username="export_user", password="pass")
    workspace = Workspace.objects.create(name="Export Ops", created_by=user)
    WorkspaceMembership.objects.create(
        workspace=workspace,
        user=user,
        role=WorkspaceMembership.Role.OWNER,
    )
    return user, workspace


def make_document_with_fields(user, workspace):
    document = UploadedDocument.objects.create(
        workspace=workspace,
        title="Invoice 1001",
        file_type="PDF",
        uploaded_by=user,
        file_size=11,
        status=UploadedDocument.Status.APPROVED,
    )
    document.file.save("invoice.pdf", ContentFile(b"hello world"), save=True)
    run = ExtractionRun.objects.create(
        document=document,
        status=ExtractionRun.Status.COMPLETED,
        model_name="test-model",
    )
    ExtractedField.objects.create(
        run=run,
        document=document,
        field_name="vendor_name",
        raw_value="Acm",
        normalized_value="Acme Supplies",
        confidence=0.95,
        source_page=1,
        source_text="Acme Supplies",
    )
    ExtractedField.objects.create(
        run=run,
        document=document,
        field_name="total_amount",
        raw_value="42.50",
        normalized_value="42.50",
        confidence=0.99,
        source_page=1,
        source_text="Total 42.50",
    )
    return document, run


def test_export_payload_uses_reviewed_normalized_values():
    user, workspace = make_workspace()
    document, _run = make_document_with_fields(user, workspace)

    payload = build_export_payload(document)

    assert payload["field_values"] == {
        "total_amount": "42.50",
        "vendor_name": "Acme Supplies",
    }
    assert payload["document"]["status"] == UploadedDocument.Status.APPROVED


def test_create_json_export_record_writes_file_and_audit_event():
    user, workspace = make_workspace()
    document, run = make_document_with_fields(user, workspace)

    record = create_export_record(document, ExportRecord.Format.JSON, user)

    assert record.format == ExportRecord.Format.JSON
    assert record.extraction_run == run
    assert record.field_count == 2
    assert record.file.name.endswith(".json")
    payload = json.loads(record.file.read().decode("utf-8"))
    assert payload["field_values"]["vendor_name"] == "Acme Supplies"
    assert AuditEvent.objects.filter(
        workspace=workspace,
        document=document,
        actor_user=user,
        event_type="document_exported",
    ).exists()


def test_csv_export_contains_rows_for_each_field():
    user, workspace = make_workspace()
    document, _run = make_document_with_fields(user, workspace)

    content = build_csv_export(document).decode("utf-8")
    rows = list(csv.DictReader(StringIO(content)))

    assert len(rows) == 2
    assert rows[0]["document_title"] == "Invoice 1001"
    assert {row["field_name"] for row in rows} == {"total_amount", "vendor_name"}


def test_export_download_view_returns_file(client):
    user, workspace = make_workspace()
    document, _run = make_document_with_fields(user, workspace)
    record = create_export_record(document, ExportRecord.Format.CSV, user)
    client.force_login(user)

    response = client.get(reverse("export-download", kwargs={"workspace_slug": workspace.slug, "pk": record.pk}))

    assert response.status_code == 200
    assert "attachment" in response["Content-Disposition"]


def test_document_export_api_creates_export_record(client):
    user, _workspace = make_workspace()
    document, _run = make_document_with_fields(user, document_workspace := user.created_workspaces.first())
    client.force_login(user)

    response = client.post(
        reverse("api-document-export-create", kwargs={"pk": document.pk, "export_format": "json"})
    )

    assert response.status_code == 201
    assert response.json()["field_count"] == 2
    assert ExportRecord.objects.filter(document=document, format=ExportRecord.Format.JSON).exists()
    assert document_workspace.export_records.count() == 1
