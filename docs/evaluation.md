# Evaluation

Milestone 9 adds a small evaluation harness for extraction quality.

Datasets live in `eval/datasets/` and contain synthetic gold examples. Each item includes a document type, expected fields, critical fields, and either source text for the local extractor or explicit predicted fields.

Run a command-line score:

```powershell
python manage.py run_extraction_eval eval/datasets/invoices_gold.yml
```

Save a report to a workspace:

```powershell
python manage.py run_extraction_eval eval/datasets/invoices_gold.yml --workspace-slug demo-workspace --username demo_owner --save
```

Tracked metrics include classification accuracy, field exact match, precision, recall, F1, critical-field exact match, missing-field rate, and invalid-output rate.
