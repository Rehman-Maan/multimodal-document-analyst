from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.views.generic import DetailView

from apps.chat.forms import ChatQuestionForm
from apps.chat.models import ChatMessage, ChatSession
from apps.chat.services import get_or_create_active_session
from apps.chat.tasks import index_document_task
from apps.documents.models import UploadedDocument
from apps.workspaces.models import Workspace
from services.retrieval.answers import answer_document_question
from services.retrieval.indexing import index_document


class DocumentChatView(LoginRequiredMixin, DetailView):
    model = ChatSession
    template_name = "chat/session_detail.html"
    context_object_name = "session"

    def dispatch(self, request, *args, **kwargs):
        self.workspace = get_object_or_404(Workspace, slug=kwargs["workspace_slug"])
        self.document = get_object_or_404(
            UploadedDocument,
            pk=kwargs["document_pk"],
            workspace=self.workspace,
        )
        if not self.workspace.user_can_view(request.user):
            raise PermissionDenied("You do not have access to this workspace.")
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        return get_or_create_active_session(self.workspace, self.document, self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["workspace"] = self.workspace
        context["document"] = self.document
        context["form"] = ChatQuestionForm()
        context["exchanges"] = build_chat_exchanges(self.object.messages.all())
        context["chunk_count"] = self.document.chunks.count()
        return context


@require_POST
def ask_document_question(request, workspace_slug, document_pk):
    workspace = get_object_or_404(Workspace, slug=workspace_slug)
    document = get_object_or_404(UploadedDocument, pk=document_pk, workspace=workspace)
    if not workspace.user_can_view(request.user):
        raise PermissionDenied("You do not have access to this workspace.")
    form = ChatQuestionForm(request.POST)
    if form.is_valid():
        session = get_or_create_active_session(workspace, document, request.user)
        if not document.chunks.exists():
            index_document(document)
        answer = answer_document_question(session, form.cleaned_data["question"])
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            user_message = answer.session.messages.filter(role=ChatMessage.Role.USER).latest(
                "created_at"
            )
            return JsonResponse(
                {
                    "question": user_message.content,
                    "answer": answer.content,
                    "citations": answer.citations,
                }
            )
    elif request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"errors": form.errors}, status=400)
    return redirect("document-chat", workspace_slug=workspace.slug, document_pk=document.pk)


@require_POST
def reindex_document(request, workspace_slug, document_pk):
    workspace = get_object_or_404(Workspace, slug=workspace_slug)
    document = get_object_or_404(UploadedDocument, pk=document_pk, workspace=workspace)
    if not workspace.user_can_view(request.user):
        raise PermissionDenied("You do not have access to this workspace.")
    index_document_task.delay(document.pk)
    messages.success(request, "Document chat index queued.")
    return redirect("document-chat", workspace_slug=workspace.slug, document_pk=document.pk)


def build_chat_exchanges(messages):
    exchanges = []
    pending_user = None
    for message in messages.order_by("created_at", "pk"):
        if message.role == ChatMessage.Role.USER:
            if pending_user:
                exchanges.append({"user": pending_user, "assistant": None})
            pending_user = message
            continue
        if pending_user:
            exchanges.append({"user": pending_user, "assistant": message})
            pending_user = None
        else:
            exchanges.append({"user": None, "assistant": message})
    if pending_user:
        exchanges.append({"user": pending_user, "assistant": None})
    return list(reversed(exchanges))
