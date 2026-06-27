from django.urls import path

from apps.workspaces.views import (
    WorkspaceCreateView,
    WorkspaceDashboardView,
    WorkspaceListView,
    workspace_home,
)


urlpatterns = [
    path("", workspace_home, name="workspace-home"),
    path("workspaces/", WorkspaceListView.as_view(), name="workspace-list"),
    path("workspaces/new/", WorkspaceCreateView.as_view(), name="workspace-create"),
    path("workspaces/<slug:slug>/", WorkspaceDashboardView.as_view(), name="workspace-dashboard"),
]
