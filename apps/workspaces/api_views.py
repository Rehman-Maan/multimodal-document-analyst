from rest_framework import generics, permissions

from apps.workspaces.models import Workspace
from apps.workspaces.serializers import WorkspaceSerializer


class WorkspaceListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = WorkspaceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            Workspace.objects.filter(memberships__user=self.request.user)
            .select_related("created_by")
            .distinct()
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context
