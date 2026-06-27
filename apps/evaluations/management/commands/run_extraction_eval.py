import json
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from apps.workspaces.models import Workspace
from services.evaluation.datasets import load_gold_dataset
from services.evaluation.reports import run_evaluation
from services.evaluation.scoring import score_dataset


class Command(BaseCommand):
    help = "Score a gold extraction dataset and optionally save a workspace evaluation report."

    def add_arguments(self, parser):
        parser.add_argument("dataset", nargs="?", default="eval/datasets/invoices_gold.yml")
        parser.add_argument("--workspace-slug")
        parser.add_argument("--username")
        parser.add_argument("--save", action="store_true")

    def handle(self, *args, **options):
        dataset_path = Path(options["dataset"])
        if not dataset_path.exists():
            raise CommandError(f"Dataset not found: {dataset_path}")
        workspace = None
        user = None
        if options["workspace_slug"]:
            workspace = Workspace.objects.filter(slug=options["workspace_slug"]).first()
            if workspace is None:
                raise CommandError(f"Workspace not found: {options['workspace_slug']}")
        if options["username"]:
            user = get_user_model().objects.filter(username=options["username"]).first()
            if user is None:
                raise CommandError(f"User not found: {options['username']}")
        if options["save"]:
            if workspace is None:
                raise CommandError("--workspace-slug is required with --save")
            run = run_evaluation(dataset_path, workspace, user)
            metrics = run.metrics
            self.stdout.write(self.style.SUCCESS(f"Saved evaluation run {run.pk}"))
        else:
            result = score_dataset(load_gold_dataset(dataset_path))
            metrics = result.metrics
        self.stdout.write(json.dumps(metrics, indent=2, sort_keys=True))
