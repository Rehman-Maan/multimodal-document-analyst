from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, ListView

from apps.evaluations.models import EvaluationRun
from apps.workspaces.models import Workspace
from services.evaluation.reports import run_evaluation


DEFAULT_DATASET = "eval/datasets/invoices_gold.yml"


class WorkspaceEvaluationMixin(LoginRequiredMixin):
    workspace = None

    def dispatch(self, request, *args, **kwargs):
        self.workspace = get_object_or_404(Workspace, slug=kwargs["workspace_slug"])
        membership = self.workspace.membership_for(request.user)
        if not membership or not membership.can_manage_workspace:
            raise PermissionDenied("You do not have access to evaluation reports.")
        return super().dispatch(request, *args, **kwargs)


class EvaluationRunListView(WorkspaceEvaluationMixin, ListView):
    model = EvaluationRun
    template_name = "evaluations/evaluation_list.html"
    context_object_name = "evaluation_runs"

    def get_queryset(self):
        return EvaluationRun.objects.filter(workspace=self.workspace).select_related("created_by")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["workspace"] = self.workspace
        return context


class EvaluationRunDetailView(WorkspaceEvaluationMixin, DetailView):
    model = EvaluationRun
    template_name = "evaluations/evaluation_detail.html"
    context_object_name = "evaluation_run"

    def get_queryset(self):
        return EvaluationRun.objects.filter(workspace=self.workspace).select_related("created_by")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["workspace"] = self.workspace
        return context


@require_POST
def create_evaluation_run(request, workspace_slug):
    workspace = get_object_or_404(Workspace, slug=workspace_slug)
    membership = workspace.membership_for(request.user)
    if not membership or not membership.can_manage_workspace:
        raise PermissionDenied("You do not have access to evaluation reports.")
    run = run_evaluation(DEFAULT_DATASET, workspace, request.user)
    messages.success(request, "Evaluation report created.")
    return redirect("evaluation-detail", workspace_slug=workspace.slug, pk=run.pk)
