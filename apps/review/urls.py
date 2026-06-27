from django.urls import path

from apps.review.views import (
    ReviewTaskDetailView,
    ReviewTaskListView,
    approve_document,
    approve_review_task,
    reject_review_task,
)


urlpatterns = [
    path("", ReviewTaskListView.as_view(), name="review-task-list"),
    path("tasks/<int:pk>/", ReviewTaskDetailView.as_view(), name="review-task-detail"),
    path("tasks/<int:pk>/approve/", approve_review_task, name="review-task-approve"),
    path("tasks/<int:pk>/reject/", reject_review_task, name="review-task-reject"),
    path("documents/<int:pk>/approve/", approve_document, name="document-approve"),
]
