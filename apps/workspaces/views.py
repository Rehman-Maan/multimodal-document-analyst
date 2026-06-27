from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.views.generic import CreateView, DetailView, ListView

from apps.workspaces.forms import WorkspaceForm
from apps.workspaces.models import Workspace, WorkspaceMembership
from apps.documents.models import UploadedDocument
from apps.schemas.models import ensure_default_document_types_and_schemas


class WorkspaceListView(LoginRequiredMixin, ListView):
    model = Workspace
    template_name = "workspaces/workspace_list.html"
    context_object_name = "workspaces"

    def get_queryset(self):
        workspaces = (
            Workspace.objects.filter(memberships__user=self.request.user)
            .select_related("created_by")
            .prefetch_related("memberships")
            .distinct()
        )
        for workspace in workspaces:
            workspace.current_user_role = workspace.user_role(self.request.user)
        return workspaces


class WorkspaceCreateView(LoginRequiredMixin, CreateView):
    model = Workspace
    form_class = WorkspaceForm
    template_name = "workspaces/workspace_form.html"

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        WorkspaceMembership.objects.create(
            workspace=self.object,
            user=self.request.user,
            role=WorkspaceMembership.Role.OWNER,
        )
        ensure_default_document_types_and_schemas(self.object, self.request.user)
        messages.success(self.request, "Workspace created.")
        return response


class WorkspaceDashboardView(LoginRequiredMixin, DetailView):
    model = Workspace
    slug_field = "slug"
    slug_url_kwarg = "slug"
    template_name = "workspaces/dashboard.html"
    context_object_name = "workspace"

    def get_queryset(self):
        return Workspace.objects.select_related("created_by").prefetch_related("memberships__user")

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.object.user_can_view(request.user):
            raise PermissionDenied("You do not have access to this workspace.")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["membership"] = self.object.membership_for(self.request.user)
        context["stats"] = {
            "documents_uploaded": self.object.documents.count(),
            "needs_review": self.object.documents.filter(
                status=UploadedDocument.Status.NEEDS_REVIEW
            ).count(),
            "approved": self.object.documents.filter(status=UploadedDocument.Status.APPROVED).count(),
            "failed_jobs": self.object.documents.filter(status=UploadedDocument.Status.FAILED).count(),
        }
        return context


def workspace_home(request):
    if request.user.is_authenticated:
        return redirect("workspace-list")
    return redirect("login")
