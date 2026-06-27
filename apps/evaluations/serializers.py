from rest_framework import serializers

from apps.evaluations.models import EvaluationRun


class EvaluationRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = EvaluationRun
        fields = [
            "id",
            "workspace",
            "dataset_name",
            "total_items",
            "metrics",
            "item_results",
            "created_at",
        ]
