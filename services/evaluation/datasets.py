import json
from pathlib import Path


def load_gold_dataset(path: str | Path) -> list[dict]:
    dataset_path = Path(path)
    with dataset_path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, list):
        raise ValueError("Evaluation dataset must be a list of items.")
    return data
