from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import CreateView, DetailView, ListView

from apps.schemas.forms import DocumentTypeForm, ExtractionSchemaForm
from apps.schemas.models import DocumentType, ExtractionSchema, ensure_default_document_types_and_schemas
from apps.workspaces.models import Workspace


class WorkspaceSchemaMixin(LoginRequiredMixin):
    workspace = None

    def dispatch(self, request, *args, **kwargs):
        self.workspace = get_object_or_404(Workspace, slug=kwargs["workspace_slug"])
        if not self.workspace.user_can_manage(request.user):
            raise PermissionDenied("You do not have access to manage schemas in this workspace.")
        return super().dispatch(request, *args, **kwargs)


class SchemaListView(WorkspaceSchemaMixin, ListView):
    model = ExtractionSchema
    template_name = "schemas/schema_list.html"
    context_object_name = "schemas"

    def get_queryset(self):
        return ExtractionSchema.objects.filter(workspace=self.workspace).select_related("document_type")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["workspace"] = self.workspace
        context["document_types"] = DocumentType.objects.filter(workspace=self.workspace)
        return context


class SchemaCreateView(WorkspaceSchemaMixin, CreateView):
    model = ExtractionSchema
    form_class = ExtractionSchemaForm
    template_name = "schemas/schema_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["workspace"] = self.workspace
        return kwargs

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, "Extraction schema saved.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["workspace"] = self.workspace
        return context


class SchemaDetailView(WorkspaceSchemaMixin, DetailView):
    model = ExtractionSchema
    template_name = "schemas/schema_detail.html"
    context_object_name = "schema"

    def get_queryset(self):
        return ExtractionSchema.objects.filter(workspace=self.workspace).select_related("document_type")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["workspace"] = self.workspace
        return context


class DocumentTypeCreateView(WorkspaceSchemaMixin, CreateView):
    model = DocumentType
    form_class = DocumentTypeForm
    template_name = "schemas/document_type_form.html"

    def form_valid(self, form):
        form.instance.workspace = self.workspace
        messages.success(self.request, "Document type saved.")
        return super().form_valid(form)

    def get_success_url(self):
        return self.workspace.get_absolute_url()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["workspace"] = self.workspace
        return context


def seed_default_schemas(request, workspace_slug):
    workspace = get_object_or_404(Workspace, slug=workspace_slug)
    if not workspace.user_can_manage(request.user):
        raise PermissionDenied("You do not have access to manage schemas in this workspace.")
    ensure_default_document_types_and_schemas(workspace, request.user)
    messages.success(request, "Default receipt and invoice schemas are ready.")
    return redirect("schema-list", workspace_slug=workspace.slug)
