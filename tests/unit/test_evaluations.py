import json
from pathlib import Path

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.urls import reverse

from apps.evaluations.models import EvaluationRun
from apps.workspaces.models import Workspace, WorkspaceMembership
from services.evaluation.datasets import load_gold_dataset
from services.evaluation.reports import run_evaluation
from services.evaluation.scoring import score_dataset, score_item


pytestmark = pytest.mark.django_db


def make_workspace(role=WorkspaceMembership.Role.OWNER):
    user = get_user_model().objects.create_user(username="eval_user", password="pass")
    workspace = Workspace.objects.create(name="Eval Ops", created_by=user)
    WorkspaceMembership.objects.create(workspace=workspace, user=user, role=role)
    return user, workspace


def test_score_item_calculates_precision_recall_f1_and_critical_match():
    item = {
        "id": "invoice_001",
        "document_type": "invoice",
        "expected_fields": {
            "invoice_number": "INV-1001",
            "vendor_name": "Acme Supplies",
            "total_amount": "42.50",
        },
        "critical_fields": ["invoice_number", "total_amount"],
    }
    predicted = {
        "invoice_number": "INV-1001",
        "vendor_name": "Wrong Vendor",
        "total_amount": "42.50",
    }

    result = score_item(item, predicted)

    assert result["field_exact_match_rate"] == pytest.approx(0.6667)
    assert result["field_precision"] == pytest.approx(0.6667)
    assert result["field_recall"] == pytest.approx(0.6667)
    assert result["field_f1"] == pytest.approx(0.6667)
    assert result["critical_exact_match_rate"] == 1.0


def test_score_dataset_runs_local_extractor_from_gold_text():
    items = load_gold_dataset("eval/datasets/invoices_gold.yml")

    result = score_dataset(items)

    assert result.metrics["total_items"] == 2
    assert result.metrics["field_f1"] > 0
    assert result.item_results[0]["id"] == "invoice_001"


def test_run_evaluation_saves_workspace_report():
    user, workspace = make_workspace()

    run = run_evaluation("eval/datasets/forms_gold.yml", workspace, user)

    assert run.workspace == workspace
    assert run.created_by == user
    assert run.total_items == 1
    assert run.metrics["field_f1"] == 1.0


def test_run_extraction_eval_command_outputs_metrics(capsys):
    call_command("run_extraction_eval", "eval/datasets/forms_gold.yml")

    output = capsys.readouterr().out
    metrics = json.loads(output)
    assert metrics["total_items"] == 1
    assert metrics["field_f1"] == 1.0


def test_evaluation_api_creates_report_for_workspace_manager(client):
    user, workspace = make_workspace()
    client.force_login(user)

    response = client.post(
        reverse("api-evaluation-run-create", kwargs={"workspace_slug": workspace.slug})
    )

    assert response.status_code == 201
    assert response.json()["dataset_name"] == Path("eval/datasets/invoices_gold.yml").name
    assert EvaluationRun.objects.filter(workspace=workspace).count() == 1


def test_evaluation_page_requires_manager_role(client):
    user, workspace = make_workspace(role=WorkspaceMembership.Role.VIEWER)
    client.force_login(user)

    response = client.get(reverse("evaluation-list", kwargs={"workspace_slug": workspace.slug}))

    assert response.status_code == 403
