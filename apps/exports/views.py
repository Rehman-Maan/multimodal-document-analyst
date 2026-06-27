from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.views.generic import ListView

from apps.documents.models import UploadedDocument
from apps.exports.models import ExportRecord
from apps.exports.services import create_export_record
from apps.workspaces.models import Workspace


class WorkspaceExportMixin(LoginRequiredMixin):
    workspace = None

    def dispatch(self, request, *args, **kwargs):
        self.workspace = get_object_or_404(Workspace, slug=kwargs["workspace_slug"])
        if not self.workspace.user_can_view(request.user):
            raise PermissionDenied("You do not have access to this workspace.")
        return super().dispatch(request, *args, **kwargs)


class ExportHistoryView(WorkspaceExportMixin, ListView):
    model = ExportRecord
    template_name = "exports/export_history.html"
    context_object_name = "exports"
    paginate_by = 25

    def get_queryset(self):
        return ExportRecord.objects.filter(workspace=self.workspace).select_related(
            "document", "created_by", "extraction_run"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["workspace"] = self.workspace
        return context


@require_POST
def create_document_export(request, workspace_slug, pk, export_format):
    workspace = get_object_or_404(Workspace, slug=workspace_slug)
    if not workspace.user_can_view(request.user):
        raise PermissionDenied("You do not have access to this workspace.")
    document = get_object_or_404(UploadedDocument, pk=pk, workspace=workspace)
    record = create_export_record(document, export_format, request.user)
    messages.success(request, f"{record.get_format_display()} export created.")
    return redirect("export-download", workspace_slug=workspace.slug, pk=record.pk)


def download_export(request, workspace_slug, pk):
    workspace = get_object_or_404(Workspace, slug=workspace_slug)
    if not workspace.user_can_view(request.user):
        raise PermissionDenied("You do not have access to this workspace.")
    record = get_object_or_404(ExportRecord, pk=pk, workspace=workspace)
    if not record.file:
        raise PermissionDenied("Export file is unavailable.")
    return FileResponse(record.file.open("rb"), as_attachment=True, filename=record.file.name.rsplit("/", 1)[-1])
