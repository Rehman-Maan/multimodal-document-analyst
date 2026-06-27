from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.evaluations.models import EvaluationRun
from apps.evaluations.serializers import EvaluationRunSerializer
from apps.evaluations.views import DEFAULT_DATASET
from apps.workspaces.models import Workspace
from services.evaluation.reports import run_evaluation


class EvaluationRunListAPIView(generics.ListAPIView):
    serializer_class = EvaluationRunSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return EvaluationRun.objects.filter(workspace__memberships__user=self.request.user).distinct()


class EvaluationRunCreateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, workspace_slug):
        workspace = Workspace.objects.filter(slug=workspace_slug, memberships__user=request.user).first()
        if workspace is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        membership = workspace.membership_for(request.user)
        if not membership or not membership.can_manage_workspace:
            return Response({"detail": "Forbidden."}, status=status.HTTP_403_FORBIDDEN)
        run = run_evaluation(DEFAULT_DATASET, workspace, request.user)
        return Response(EvaluationRunSerializer(run).data, status=status.HTTP_201_CREATED)
