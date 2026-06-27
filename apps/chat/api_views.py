from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.chat.serializers import ChatSessionSerializer
from apps.chat.services import get_or_create_active_session
from apps.documents.models import UploadedDocument
from services.retrieval.answers import answer_document_question
from services.retrieval.indexing import index_document


class DocumentChatAskAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        document = UploadedDocument.objects.filter(
            pk=pk,
            workspace__memberships__user=request.user,
        ).first()
        if document is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        question = (request.data.get("question") or "").strip()
        if not question:
            return Response({"question": ["This field is required."]}, status=status.HTTP_400_BAD_REQUEST)
        if not document.chunks.exists():
            index_document(document)
        session = get_or_create_active_session(document.workspace, document, request.user)
        answer_document_question(session, question)
        return Response(ChatSessionSerializer(session).data, status=status.HTTP_201_CREATED)


class DocumentIndexAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        document = UploadedDocument.objects.filter(
            pk=pk,
            workspace__memberships__user=request.user,
        ).first()
        if document is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        count = index_document(document)
        return Response({"document_id": document.pk, "chunk_count": count})
