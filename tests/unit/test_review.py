import pytest
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.urls import reverse

from apps.audit.models import AuditEvent
from apps.documents.models import UploadedDocument
from apps.extraction.models import ExtractedField, ExtractionRun
from apps.review.models import ReviewTask
from apps.review.services import approve_document_if_ready, correct_field, route_review_tasks
from apps.schemas.models import ExtractionSchema, ensure_default_document_types_and_schemas
from apps.workspaces.models import Workspace, WorkspaceMembership


pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def isolated_media_root(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path / "media"


def make_workspace(role=WorkspaceMembership.Role.OWNER):
    user = get_user_model().objects.create_user(username="reviewer", password="pass")
    workspace = Workspace.objects.create(name="Review Ops", created_by=user)
    WorkspaceMembership.objects.create(workspace=workspace, user=user, role=role)
    ensure_default_document_types_and_schemas(workspace, user)
    return user, workspace


def make_document(user, workspace):
    document = UploadedDocument.objects.create(
        workspace=workspace,
        title="Invoice",
        file_type="PDF",
        uploaded_by=user,
        file_size=11,
        status=UploadedDocument.Status.PROCESSED,
    )
    document.file.save("invoice.pdf", ContentFile(b"hello world"), save=True)
    return document


def make_run_with_field(user, workspace, confidence=0.40, validation_errors=None):
    document = make_document(user, workspace)
    schema = ExtractionSchema.objects.get(workspace=workspace, document_type__slug="invoice")
    run = ExtractionRun.objects.create(
        document=document,
        schema=schema,
        status=ExtractionRun.Status.COMPLETED,
    )
    field = ExtractedField.objects.create(
        run=run,
        document=document,
        field_name="vendor_name",
        raw_value="Acm",
        normalized_value="Acm",
        confidence=confidence,
        source_page=1,
        source_text="Acm",
        validation_errors=validation_errors or [],
    )
    return document, run, field


def test_low_confidence_field_creates_review_task_and_audit_event():
    user, workspace = make_workspace()
    document, run, field = make_run_with_field(user, workspace)

    tasks = route_review_tasks(run)

    document.refresh_from_db()
    run.refresh_from_db()
    assert len(tasks) == 1
    assert tasks[0].field == field
    assert tasks[0].status == ReviewTask.Status.OPEN
    assert "Low confidence" in tasks[0].reason
    assert run.status == ExtractionRun.Status.NEEDS_REVIEW
    assert document.status == UploadedDocument.Status.NEEDS_REVIEW
    assert AuditEvent.objects.filter(
        workspace=workspace,
        document=document,
        event_type="review_tasks_created",
    ).exists()


def test_correct_field_approves_task_updates_field_and_returns_document_to_processed():
    user, workspace = make_workspace()
    document, run, field = make_run_with_field(user, workspace)
    task = route_review_tasks(run)[0]

    correct_field(task, "Acme Supplies", user, "Verified from page preview.")

    task.refresh_from_db()
    field.refresh_from_db()
    document.refresh_from_db()
    assert task.status == ReviewTask.Status.APPROVED
    assert task.corrected_value == "Acme Supplies"
    assert field.normalized_value == "Acme Supplies"
    assert field.raw_value == "Acme Supplies"
    assert field.confidence == pytest.approx(0.95)
    assert field.validation_errors == []
    assert document.status == UploadedDocument.Status.PROCESSED
    assert AuditEvent.objects.filter(event_type="review_task_approved", actor_user=user).exists()


def test_document_approval_is_blocked_until_open_tasks_are_resolved():
    user, workspace = make_workspace()
    document, run, _field = make_run_with_field(user, workspace)
    task = route_review_tasks(run)[0]

    assert approve_document_if_ready(document, user) is False
    document.refresh_from_db()
    assert document.status == UploadedDocument.Status.NEEDS_REVIEW

    correct_field(task, "Acme Supplies", user)
    assert approve_document_if_ready(document, user) is True
    document.refresh_from_db()
    assert document.status == UploadedDocument.Status.APPROVED
    assert AuditEvent.objects.filter(event_type="document_approved", document=document).exists()


def test_review_task_api_allows_reviewer_to_approve_task(client):
    user, workspace = make_workspace(role=WorkspaceMembership.Role.REVIEWER)
    _document, run, _field = make_run_with_field(user, workspace)
    task = route_review_tasks(run)[0]
    client.force_login(user)

    response = client.post(
        reverse("api-review-task-approve", kwargs={"pk": task.pk}),
        {"corrected_value": "Acme Supplies", "reviewer_note": "Looks good."},
        content_type="application/json",
    )

    assert response.status_code == 200
    task.refresh_from_db()
    assert task.status == ReviewTask.Status.APPROVED
    assert task.corrected_value == "Acme Supplies"


def test_review_task_api_hides_tasks_from_non_reviewers(client):
    reviewer, workspace = make_workspace()
    _document, run, _field = make_run_with_field(reviewer, workspace)
    route_review_tasks(run)
    viewer = get_user_model().objects.create_user(username="viewer", password="pass")
    WorkspaceMembership.objects.create(
        workspace=workspace,
        user=viewer,
        role=WorkspaceMembership.Role.VIEWER,
    )
    client.force_login(viewer)

    response = client.get(reverse("api-review-task-list"))

    assert response.status_code == 200
    assert response.json() == []
