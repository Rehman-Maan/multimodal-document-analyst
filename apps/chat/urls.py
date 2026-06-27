from django.urls import path

from apps.chat.views import DocumentChatView, ask_document_question, reindex_document


urlpatterns = [
    path(
        "documents/<int:document_pk>/chat/",
        DocumentChatView.as_view(),
        name="document-chat",
    ),
    path(
        "documents/<int:document_pk>/chat/ask/",
        ask_document_question,
        name="document-chat-ask",
    ),
    path(
        "documents/<int:document_pk>/chat/reindex/",
        reindex_document,
        name="document-chat-reindex",
    ),
]
