from rest_framework import generics, permissions

from apps.schemas.models import DocumentType, ExtractionSchema
from apps.schemas.serializers import DocumentTypeSerializer, ExtractionSchemaSerializer


class DocumentTypeListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = DocumentTypeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return DocumentType.objects.filter(workspace__memberships__user=self.request.user).distinct()


class ExtractionSchemaListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = ExtractionSchemaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            ExtractionSchema.objects.filter(workspace__memberships__user=self.request.user)
            .select_related("document_type")
            .distinct()
        )


class ExtractionSchemaRetrieveUpdateAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = ExtractionSchemaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            ExtractionSchema.objects.filter(workspace__memberships__user=self.request.user)
            .select_related("document_type")
            .distinct()
        )
