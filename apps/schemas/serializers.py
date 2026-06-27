from rest_framework import serializers

from apps.schemas.models import DocumentType, ExtractionSchema
from apps.workspaces.models import Workspace
from services.schema_validation.validators import SchemaValidationError, validate_schema_definition


class DocumentTypeSerializer(serializers.ModelSerializer):
    workspace_slug = serializers.SlugRelatedField(
        queryset=Workspace.objects.all(),
        slug_field="slug",
        source="workspace",
        write_only=True,
    )

    class Meta:
        model = DocumentType
        fields = ["id", "workspace_slug", "name", "slug", "description", "active", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate(self, attrs):
        workspace = attrs.get("workspace")
        if workspace and not workspace.user_can_manage(self.context["request"].user):
            raise serializers.ValidationError("You do not have access to manage this workspace.")
        return attrs


class ExtractionSchemaSerializer(serializers.ModelSerializer):
    workspace_slug = serializers.SlugRelatedField(
        queryset=Workspace.objects.all(),
        slug_field="slug",
        source="workspace",
        write_only=True,
    )

    class Meta:
        model = ExtractionSchema
        fields = [
            "id",
            "workspace_slug",
            "document_type",
            "name",
            "version",
            "schema_json",
            "active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, attrs):
        workspace = attrs.get("workspace") or self.instance.workspace
        document_type = attrs.get("document_type") or self.instance.document_type
        if not workspace.user_can_manage(self.context["request"].user):
            raise serializers.ValidationError("You do not have access to manage this workspace.")
        if document_type.workspace_id != workspace.id:
            raise serializers.ValidationError("Document type must belong to the same workspace.")
        try:
            validate_schema_definition(attrs.get("schema_json") or self.instance.schema_json)
        except SchemaValidationError as exc:
            raise serializers.ValidationError(str(exc)) from exc
        return attrs

    def create(self, validated_data):
        return ExtractionSchema.objects.create(created_by=self.context["request"].user, **validated_data)
