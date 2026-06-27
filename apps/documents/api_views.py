from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.documents.models import UploadedDocument
from apps.documents.processing import enqueue_document_processing
from apps.documents.serializers import UploadedDocumentSerializer


class UploadedDocumentListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = UploadedDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            UploadedDocument.objects.filter(workspace__memberships__user=self.request.user)
            .select_related("workspace", "uploaded_by")
            .distinct()
        )


class UploadedDocumentRetrieveAPIView(generics.RetrieveAPIView):
    serializer_class = UploadedDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            UploadedDocument.objects.filter(workspace__memberships__user=self.request.user)
            .select_related("workspace", "uploaded_by")
            .distinct()
        )


class UploadedDocumentProcessAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        document = generics.get_object_or_404(
            UploadedDocument.objects.filter(workspace__memberships__user=request.user).distinct(),
            pk=pk,
        )
        enqueue_document_processing(document)
        return Response({"status": "queued"}, status=status.HTTP_202_ACCEPTED)
