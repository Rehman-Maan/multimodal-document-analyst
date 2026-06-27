from rest_framework import serializers

from apps.workspaces.models import Workspace, WorkspaceMembership


class WorkspaceSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()

    class Meta:
        model = Workspace
        fields = ["id", "name", "slug", "role", "created_at", "updated_at"]
        read_only_fields = ["id", "slug", "role", "created_at", "updated_at"]

    def get_role(self, obj):
        request = self.context.get("request")
        return obj.user_role(request.user) if request else ""

    def create(self, validated_data):
        request = self.context["request"]
        workspace = Workspace.objects.create(created_by=request.user, **validated_data)
        WorkspaceMembership.objects.create(
            workspace=workspace,
            user=request.user,
            role=WorkspaceMembership.Role.OWNER,
        )
        return workspace
