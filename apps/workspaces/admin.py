from django.contrib import admin

from apps.workspaces.models import Workspace, WorkspaceMembership


class WorkspaceMembershipInline(admin.TabularInline):
    model = WorkspaceMembership
    extra = 0
    autocomplete_fields = ["user"]


@admin.register(Workspace)
class WorkspaceAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "created_by", "created_at", "updated_at"]
    search_fields = ["name", "slug", "created_by__username", "created_by__email"]
    prepopulated_fields = {"slug": ("name",)}
    autocomplete_fields = ["created_by"]
    inlines = [WorkspaceMembershipInline]


@admin.register(WorkspaceMembership)
class WorkspaceMembershipAdmin(admin.ModelAdmin):
    list_display = ["workspace", "user", "role", "created_at"]
    list_filter = ["role", "created_at"]
    search_fields = ["workspace__name", "user__username", "user__email"]
    autocomplete_fields = ["workspace", "user"]
