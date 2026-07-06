from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_FIXTURE = ROOT / "evals" / "fixtures" / "sample_extraction.json"


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def summarize_fixture(path: Path) -> dict[str, object]:
    payload = load_json(path)
    inputs = payload.get("inputs", {})
    expected = payload.get("expected", {})
    return {
        "fixture": str(path),
        "document_id": payload.get("document_id"),
        "input_fields": sorted(inputs.keys()),
        "expected_fields": sorted(expected.keys()),
        "model_targets": payload.get("models", []),
    }


def validate_contract(path: Path) -> dict[str, object]:
    contract = load_json(path)
    required = ["name", "version", "inputs", "outputs"]
    missing = [key for key in required if key not in contract]
    return {
        "path": str(path),
        "valid": len(missing) == 0,
        "missing": missing,
    }
