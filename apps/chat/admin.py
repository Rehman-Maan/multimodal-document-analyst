from django.contrib import admin

from apps.chat.models import ChatMessage, ChatSession, DocumentChunk


@admin.register(DocumentChunk)
class DocumentChunkAdmin(admin.ModelAdmin):
    list_display = ["document", "page_number", "chunk_index", "embedding_model", "created_at"]
    list_filter = ["embedding_model", "created_at"]
    search_fields = ["document__title", "text"]


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ["title", "document", "created_by", "updated_at"]
    search_fields = ["title", "document__title", "created_by__username"]


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ["session", "role", "created_at"]
    list_filter = ["role", "created_at"]
    search_fields = ["content"]
