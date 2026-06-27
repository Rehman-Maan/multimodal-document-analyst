from django.urls import path

from apps.evaluations.views import (
    EvaluationRunDetailView,
    EvaluationRunListView,
    create_evaluation_run,
)


urlpatterns = [
    path("", EvaluationRunListView.as_view(), name="evaluation-list"),
    path("run/", create_evaluation_run, name="evaluation-run-create"),
    path("<int:pk>/", EvaluationRunDetailView.as_view(), name="evaluation-detail"),
]
