from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.documents.models import UploadedDocument
from apps.exports.models import ExportRecord
from apps.exports.serializers import ExportRecordSerializer
from apps.exports.services import create_export_record


class ExportRecordListAPIView(generics.ListAPIView):
    serializer_class = ExportRecordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            ExportRecord.objects.filter(workspace__memberships__user=self.request.user)
            .select_related("document", "extraction_run")
            .distinct()
        )


class DocumentExportCreateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk, export_format):
        document = UploadedDocument.objects.filter(
            pk=pk,
            workspace__memberships__user=request.user,
        ).first()
        if document is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        try:
            record = create_export_record(document, export_format, request.user)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        serializer = ExportRecordSerializer(record, context={"request": request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)
