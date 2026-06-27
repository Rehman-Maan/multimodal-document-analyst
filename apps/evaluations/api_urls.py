from django.urls import path

from apps.evaluations.api_views import EvaluationRunCreateAPIView, EvaluationRunListAPIView


urlpatterns = [
    path("evaluations/", EvaluationRunListAPIView.as_view(), name="api-evaluation-list"),
    path(
        "workspaces/<slug:workspace_slug>/evaluations/run/",
        EvaluationRunCreateAPIView.as_view(),
        name="api-evaluation-run-create",
    ),
]
