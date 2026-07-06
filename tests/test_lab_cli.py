from __future__ import annotations

import json
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from lab.cli import main


def run_cli(*args: str) -> tuple[int, dict]:
    stdout = StringIO()
    with redirect_stdout(stdout):
        code = main(list(args))
    return code, json.loads(stdout.getvalue())


class LabCliTests(unittest.TestCase):
    def test_worker_smoke_uses_default_fixture(self) -> None:
        code, payload = run_cli("worker", "smoke")
        self.assertEqual(code, 0)
        self.assertEqual(payload["domain"], "worker")
        self.assertEqual(payload["document_id"], "sample-intake-packet")

    def test_contract_validation_succeeds_for_default_contract(self) -> None:
        code, payload = run_cli("contract", "validate")
        self.assertEqual(code, 0)
        self.assertTrue(payload["valid"])

    def test_contract_validation_fails_for_incomplete_contract(self) -> None:
        with TemporaryDirectory() as temp_dir:
            bad_contract = Path(temp_dir) / "bad-contract.json"
            bad_contract.write_text('{"name":"broken"}', encoding="utf-8")
            code, payload = run_cli("contract", "validate", str(bad_contract))

        self.assertEqual(code, 1)
        self.assertFalse(payload["valid"])


if __name__ == "__main__":
    unittest.main()
