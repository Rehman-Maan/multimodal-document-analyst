from rest_framework import serializers

from apps.documents.models import UploadedDocument
from apps.documents.processing import enqueue_document_processing
from apps.workspaces.models import Workspace
from services.file_validation.validators import validate_uploaded_document


class UploadedDocumentSerializer(serializers.ModelSerializer):
    workspace_slug = serializers.SlugRelatedField(
        queryset=Workspace.objects.all(),
        slug_field="slug",
        source="workspace",
        write_only=True,
    )
    uploaded_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = UploadedDocument
        fields = [
            "id",
            "workspace_slug",
            "workspace",
            "title",
            "file",
            "file_type",
            "document_type",
            "status",
            "uploaded_by",
            "page_count",
            "file_size",
            "error_message",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "workspace",
            "file_type",
            "status",
            "uploaded_by",
            "page_count",
            "file_size",
            "error_message",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        workspace = attrs.get("workspace")
        request = self.context["request"]
        if workspace and not workspace.user_can_view(request.user):
            raise serializers.ValidationError("You do not have access to this workspace.")
        return attrs

    def validate_file(self, uploaded_file):
        self.validated_upload = validate_uploaded_document(uploaded_file)
        return uploaded_file

    def create(self, validated_data):
        request = self.context["request"]
        upload = self.validated_upload
        document = UploadedDocument.objects.create(
            uploaded_by=request.user,
            file_type=upload.file_type,
            file_size=upload.size_bytes,
            status=UploadedDocument.Status.UPLOADED,
            **validated_data,
        )
        enqueue_document_processing(document)
        return document
