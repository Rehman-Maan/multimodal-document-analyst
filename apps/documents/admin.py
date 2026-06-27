from django.contrib import admin

from apps.documents.models import DocumentPage, UploadedDocument


class DocumentPageInline(admin.TabularInline):
    model = DocumentPage
    extra = 0
    readonly_fields = ["created_at"]


@admin.register(UploadedDocument)
class UploadedDocumentAdmin(admin.ModelAdmin):
    list_display = ["title", "workspace", "file_type", "status", "uploaded_by", "created_at"]
    list_filter = ["status", "file_type", "document_type", "created_at"]
    search_fields = ["title", "workspace__name", "uploaded_by__username", "uploaded_by__email"]
    autocomplete_fields = ["workspace", "uploaded_by"]
    readonly_fields = ["file_size", "created_at", "updated_at"]
    inlines = [DocumentPageInline]


@admin.register(DocumentPage)
class DocumentPageAdmin(admin.ModelAdmin):
    list_display = ["document", "page_number", "width", "height", "created_at"]
    search_fields = ["document__title", "text_content"]
    autocomplete_fields = ["document"]
