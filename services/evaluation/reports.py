from pathlib import Path

from apps.evaluations.models import EvaluationRun
from services.evaluation.datasets import load_gold_dataset
from services.evaluation.scoring import score_dataset


def run_evaluation(dataset_path: str | Path, workspace, user=None) -> EvaluationRun:
    items = load_gold_dataset(dataset_path)
    result = score_dataset(items)
    return EvaluationRun.objects.create(
        workspace=workspace,
        dataset_name=Path(dataset_path).name,
        total_items=len(items),
        metrics=result.metrics,
        item_results=result.item_results,
        created_by=user,
    )
