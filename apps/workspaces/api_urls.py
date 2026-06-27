from django.urls import path

from apps.workspaces.api_views import WorkspaceListCreateAPIView


urlpatterns = [
    path("workspaces/", WorkspaceListCreateAPIView.as_view(), name="api-workspace-list"),
]
