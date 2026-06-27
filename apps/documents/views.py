from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DetailView, ListView

from apps.documents.forms import UploadedDocumentForm
from apps.documents.models import UploadedDocument
from apps.documents.processing import enqueue_document_processing
from apps.extraction.services import run_structured_extraction
from apps.schemas.models import ExtractionSchema
from apps.workspaces.models import Workspace


class WorkspaceDocumentMixin(LoginRequiredMixin):
    workspace = None

    def dispatch(self, request, *args, **kwargs):
        self.workspace = get_object_or_404(Workspace, slug=kwargs["workspace_slug"])
        if not self.workspace.user_can_view(request.user):
            raise PermissionDenied("You do not have access to this workspace.")
        return super().dispatch(request, *args, **kwargs)


class DocumentListView(WorkspaceDocumentMixin, ListView):
    model = UploadedDocument
    template_name = "documents/document_list.html"
    context_object_name = "documents"
    paginate_by = 25

    def get_queryset(self):
        return (
            UploadedDocument.objects.filter(workspace=self.workspace)
            .select_related("workspace", "uploaded_by")
            .order_by("-created_at")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["workspace"] = self.workspace
        return context


class DocumentUploadView(WorkspaceDocumentMixin, CreateView):
    model = UploadedDocument
    form_class = UploadedDocumentForm
    template_name = "documents/document_upload.html"

    def form_valid(self, form):
        validated_upload = form.validated_upload
        form.instance.workspace = self.workspace
        form.instance.uploaded_by = self.request.user
        form.instance.file_type = validated_upload.file_type
        form.instance.file_size = validated_upload.size_bytes
        form.instance.status = UploadedDocument.Status.UPLOADED
        response = super().form_valid(form)
        enqueue_document_processing(self.object, self.request)
        return response

    def get_success_url(self):
        return self.object.get_absolute_url()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["workspace"] = self.workspace
        return context


class DocumentDetailView(WorkspaceDocumentMixin, DetailView):
    model = UploadedDocument
    template_name = "documents/document_detail.html"
    context_object_name = "document"

    def get_queryset(self):
        return UploadedDocument.objects.filter(workspace=self.workspace).select_related(
            "workspace", "uploaded_by"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["workspace"] = self.workspace
        context["pages"] = self.object.pages.all()
        context["schemas"] = ExtractionSchema.objects.filter(
            workspace=self.workspace, active=True
        ).select_related("document_type")
        latest_run = self.object.extraction_runs.select_related("schema").first()
        context["latest_run"] = latest_run
        context["extracted_fields"] = latest_run.fields.all() if latest_run else []
        context["review_tasks"] = self.object.review_tasks.select_related("field", "assigned_to")
        context["open_review_tasks"] = self.object.review_tasks.filter(
            status__in=["open", "in_progress"]
        )
        context["export_records"] = self.object.export_records.select_related(
            "created_by", "extraction_run"
        )[:5]
        membership = self.workspace.membership_for(self.request.user)
        context["can_review"] = bool(membership and membership.can_review_documents)
        context["library_url"] = reverse("document-list", kwargs={"workspace_slug": self.workspace.slug})
        return context


@require_POST
def process_document_view(request, workspace_slug, pk):
    workspace = get_object_or_404(Workspace, slug=workspace_slug)
    if not workspace.user_can_view(request.user):
        raise PermissionDenied("You do not have access to this workspace.")
    document = get_object_or_404(UploadedDocument, pk=pk, workspace=workspace)
    enqueue_document_processing(document, request)
    return redirect(document.get_absolute_url())


@require_POST
def extract_document_view(request, workspace_slug, pk):
    workspace = get_object_or_404(Workspace, slug=workspace_slug)
    if not workspace.user_can_view(request.user):
        raise PermissionDenied("You do not have access to this workspace.")
    document = get_object_or_404(UploadedDocument, pk=pk, workspace=workspace)
    schema = get_object_or_404(
        ExtractionSchema,
        pk=request.POST.get("schema_id"),
        workspace=workspace,
        active=True,
    )
    run_structured_extraction(document, schema)
    messages.success(request, "Structured extraction completed.")
    return redirect(document.get_absolute_url())
