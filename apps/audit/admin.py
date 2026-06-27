from django.contrib import admin

from apps.audit.models import AuditEvent


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ["event_type", "workspace", "document", "actor_user", "actor_type", "created_at"]
    list_filter = ["actor_type", "event_type", "created_at"]
    search_fields = ["event_type", "workspace__name", "document__title", "actor_user__username"]
    autocomplete_fields = ["workspace", "document", "actor_user"]
