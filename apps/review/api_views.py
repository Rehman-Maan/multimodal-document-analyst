from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.extraction.models import ExtractedField
from apps.review.models import ReviewTask
from apps.review.serializers import ReviewTaskSerializer
from apps.review.services import correct_field, reject_task
from apps.workspaces.models import WorkspaceMembership


REVIEWER_ROLES = [
    WorkspaceMembership.Role.OWNER,
    WorkspaceMembership.Role.ADMIN,
    WorkspaceMembership.Role.REVIEWER,
]


class ReviewerPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        workspace = obj.document.workspace
        membership = workspace.membership_for(request.user)
        return bool(membership and membership.can_review_documents)


class ReviewTaskListAPIView(generics.ListAPIView):
    serializer_class = ReviewTaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            ReviewTask.objects.filter(
                document__workspace__memberships__user=self.request.user,
                document__workspace__memberships__role__in=REVIEWER_ROLES,
            )
            .select_related("document", "field", "assigned_to")
            .distinct()
        )


class ReviewTaskRetrieveAPIView(generics.RetrieveAPIView):
    serializer_class = ReviewTaskSerializer
    permission_classes = [permissions.IsAuthenticated, ReviewerPermission]

    def get_queryset(self):
        return ReviewTask.objects.filter(document__workspace__memberships__user=self.request.user).distinct()


class ReviewTaskApproveAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        task = generics.get_object_or_404(
            ReviewTask.objects.filter(
                document__workspace__memberships__user=request.user,
                document__workspace__memberships__role__in=REVIEWER_ROLES,
            ).distinct(),
            pk=pk,
        )
        corrected_value = request.data.get("corrected_value") or (
            task.field.normalized_value if task.field else ""
        )
        correct_field(task, corrected_value, request.user, request.data.get("reviewer_note", ""))
        return Response(ReviewTaskSerializer(task).data)


class ReviewTaskRejectAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        task = generics.get_object_or_404(
            ReviewTask.objects.filter(
                document__workspace__memberships__user=request.user,
                document__workspace__memberships__role__in=REVIEWER_ROLES,
            ).distinct(),
            pk=pk,
        )
        reject_task(task, request.user, request.data.get("reviewer_note", ""))
        return Response(ReviewTaskSerializer(task).data)


class FieldReviewAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk):
        field = generics.get_object_or_404(
            ExtractedField.objects.filter(
                document__workspace__memberships__user=request.user,
                document__workspace__memberships__role__in=REVIEWER_ROLES,
            ).distinct(),
            pk=pk,
        )
        task = field.review_tasks.filter(status=ReviewTask.Status.OPEN).first()
        if task is None:
            task = ReviewTask.objects.create(
                document=field.document,
                extraction_run=field.run,
                field=field,
                reason="Manual field correction",
            )
        correct_field(
            task,
            request.data.get("corrected_value", field.normalized_value),
            request.user,
            request.data.get("reviewer_note", ""),
        )
        return Response({"status": "reviewed", "field_id": field.pk}, status=status.HTTP_200_OK)
