from django.urls import path

from apps.review.api_views import (
    FieldReviewAPIView,
    ReviewTaskApproveAPIView,
    ReviewTaskListAPIView,
    ReviewTaskRejectAPIView,
    ReviewTaskRetrieveAPIView,
)


urlpatterns = [
    path("fields/<int:pk>/review/", FieldReviewAPIView.as_view(), name="api-field-review"),
    path("review/tasks/", ReviewTaskListAPIView.as_view(), name="api-review-task-list"),
    path("review/tasks/<int:pk>/", ReviewTaskRetrieveAPIView.as_view(), name="api-review-task-detail"),
    path("review/tasks/<int:pk>/approve/", ReviewTaskApproveAPIView.as_view(), name="api-review-task-approve"),
    path("review/tasks/<int:pk>/reject/", ReviewTaskRejectAPIView.as_view(), name="api-review-task-reject"),
]
