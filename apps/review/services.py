from django.utils import timezone

from apps.audit.models import AuditEvent
from apps.documents.models import UploadedDocument
from apps.extraction.models import ExtractionRun
from apps.review.models import ReviewTask


CONFIDENCE_THRESHOLD = 0.60


def route_review_tasks(run: ExtractionRun, threshold: float = CONFIDENCE_THRESHOLD) -> list[ReviewTask]:
    created = []
    for field in run.fields.all():
        reasons = []
        if field.confidence < threshold:
            reasons.append(f"Low confidence: {field.confidence:.2f}")
        reasons.extend(field.validation_errors)
        if not reasons:
            continue
        task, was_created = ReviewTask.objects.get_or_create(
            document=run.document,
            extraction_run=run,
            field=field,
            status=ReviewTask.Status.OPEN,
            defaults={
                "priority": ReviewTask.Priority.HIGH if field.validation_errors else ReviewTask.Priority.NORMAL,
                "reason": "; ".join(reasons),
            },
        )
        if was_created:
            created.append(task)
    if created:
        run.status = ExtractionRun.Status.NEEDS_REVIEW
        run.document.status = UploadedDocument.Status.NEEDS_REVIEW
        run.save(update_fields=["status"])
        run.document.save(update_fields=["status", "updated_at"])
        AuditEvent.objects.create(
            workspace=run.document.workspace,
            document=run.document,
            actor_type=AuditEvent.ActorType.SYSTEM,
            event_type="review_tasks_created",
            payload={"run_id": run.pk, "task_count": len(created)},
        )
    return created


def correct_field(task: ReviewTask, corrected_value: str, reviewer, note: str = "") -> ReviewTask:
    task.corrected_value = corrected_value
    task.reviewer_note = note
    task.assigned_to = reviewer
    task.status = ReviewTask.Status.APPROVED
    task.completed_at = timezone.now()
    task.save(
        update_fields=["corrected_value", "reviewer_note", "assigned_to", "status", "completed_at"]
    )
    if task.field:
        task.field.normalized_value = corrected_value
        task.field.raw_value = corrected_value
        task.field.confidence = max(task.field.confidence, 0.95)
        task.field.validation_errors = []
        task.field.save(
            update_fields=["normalized_value", "raw_value", "confidence", "validation_errors"]
        )
    _after_task_closed(task, reviewer, "review_task_approved")
    return task


def reject_task(task: ReviewTask, reviewer, note: str = "") -> ReviewTask:
    task.reviewer_note = note
    task.assigned_to = reviewer
    task.status = ReviewTask.Status.REJECTED
    task.completed_at = timezone.now()
    task.save(update_fields=["reviewer_note", "assigned_to", "status", "completed_at"])
    _after_task_closed(task, reviewer, "review_task_rejected")
    return task


def approve_document_if_ready(document: UploadedDocument, reviewer) -> bool:
    if document.review_tasks.filter(status__in=[ReviewTask.Status.OPEN, ReviewTask.Status.IN_PROGRESS]).exists():
        return False
    document.status = UploadedDocument.Status.APPROVED
    document.save(update_fields=["status", "updated_at"])
    AuditEvent.objects.create(
        workspace=document.workspace,
        document=document,
        actor_user=reviewer,
        event_type="document_approved",
        payload={"document_id": document.pk},
    )
    return True


def _after_task_closed(task: ReviewTask, reviewer, event_type: str) -> None:
    AuditEvent.objects.create(
        workspace=task.document.workspace,
        document=task.document,
        actor_user=reviewer,
        event_type=event_type,
        payload={
            "task_id": task.pk,
            "field_id": task.field_id,
            "corrected_value": task.corrected_value,
            "note": task.reviewer_note,
        },
    )
    if not task.document.review_tasks.filter(
        status__in=[ReviewTask.Status.OPEN, ReviewTask.Status.IN_PROGRESS]
    ).exists():
        task.document.status = UploadedDocument.Status.PROCESSED
        task.document.save(update_fields=["status", "updated_at"])
