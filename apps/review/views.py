from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, ListView

from apps.documents.models import UploadedDocument
from apps.review.models import ReviewTask
from apps.review.services import approve_document_if_ready, correct_field, reject_task
from apps.workspaces.models import Workspace


class WorkspaceReviewMixin(LoginRequiredMixin):
    workspace = None

    def dispatch(self, request, *args, **kwargs):
        self.workspace = get_object_or_404(Workspace, slug=kwargs["workspace_slug"])
        membership = self.workspace.membership_for(request.user)
        if not membership or not membership.can_review_documents:
            raise PermissionDenied("You do not have access to review this workspace.")
        return super().dispatch(request, *args, **kwargs)


class ReviewTaskListView(WorkspaceReviewMixin, ListView):
    model = ReviewTask
    template_name = "review/task_list.html"
    context_object_name = "tasks"

    def get_queryset(self):
        return (
            ReviewTask.objects.filter(document__workspace=self.workspace)
            .select_related("document", "field", "assigned_to")
            .order_by("status", "-created_at")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["workspace"] = self.workspace
        return context


class ReviewTaskDetailView(WorkspaceReviewMixin, DetailView):
    model = ReviewTask
    template_name = "review/task_detail.html"
    context_object_name = "task"

    def get_queryset(self):
        return ReviewTask.objects.filter(document__workspace=self.workspace).select_related(
            "document", "field", "extraction_run", "assigned_to"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["workspace"] = self.workspace
        return context


@require_POST
def approve_review_task(request, workspace_slug, pk):
    workspace = get_object_or_404(Workspace, slug=workspace_slug)
    membership = workspace.membership_for(request.user)
    if not membership or not membership.can_review_documents:
        raise PermissionDenied("You do not have access to review this workspace.")
    task = get_object_or_404(ReviewTask, pk=pk, document__workspace=workspace)
    corrected_value = request.POST.get("corrected_value", "")
    if not corrected_value and task.field:
        corrected_value = task.field.normalized_value
    correct_field(task, corrected_value, request.user, request.POST.get("reviewer_note", ""))
    messages.success(request, "Review task approved.")
    return redirect("review-task-detail", workspace_slug=workspace.slug, pk=task.pk)


@require_POST
def reject_review_task(request, workspace_slug, pk):
    workspace = get_object_or_404(Workspace, slug=workspace_slug)
    membership = workspace.membership_for(request.user)
    if not membership or not membership.can_review_documents:
        raise PermissionDenied("You do not have access to review this workspace.")
    task = get_object_or_404(ReviewTask, pk=pk, document__workspace=workspace)
    reject_task(task, request.user, request.POST.get("reviewer_note", ""))
    messages.success(request, "Review task rejected.")
    return redirect("review-task-detail", workspace_slug=workspace.slug, pk=task.pk)


@require_POST
def approve_document(request, workspace_slug, pk):
    workspace = get_object_or_404(Workspace, slug=workspace_slug)
    membership = workspace.membership_for(request.user)
    if not membership or not membership.can_review_documents:
        raise PermissionDenied("You do not have access to review this workspace.")
    document = get_object_or_404(UploadedDocument, pk=pk, workspace=workspace)
    if approve_document_if_ready(document, request.user):
        messages.success(request, "Document approved.")
    else:
        messages.error(request, "Resolve open review tasks before approving this document.")
    return redirect(document.get_absolute_url())
