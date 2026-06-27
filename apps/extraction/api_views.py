from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.documents.models import UploadedDocument
from apps.extraction.models import ExtractedField
from apps.extraction.serializers import ExtractedFieldSerializer, ExtractionRunSerializer
from apps.extraction.services import run_structured_extraction
from apps.schemas.models import ExtractionSchema


class DocumentExtractAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        document = generics.get_object_or_404(
            UploadedDocument.objects.filter(workspace__memberships__user=request.user).distinct(),
            pk=pk,
        )
        schema = generics.get_object_or_404(
            ExtractionSchema.objects.filter(workspace=document.workspace, active=True),
            pk=request.data.get("schema_id"),
        )
        run = run_structured_extraction(document, schema)
        return Response(ExtractionRunSerializer(run).data, status=status.HTTP_201_CREATED)


class DocumentFieldsAPIView(generics.ListAPIView):
    serializer_class = ExtractedFieldSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ExtractedField.objects.filter(
            document_id=self.kwargs["pk"],
            document__workspace__memberships__user=self.request.user,
        ).distinct()
