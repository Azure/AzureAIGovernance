import importlib.util
import json
import shutil
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GATE_PATH = ROOT / "scripts" / "critical-case-gate.py"
MANIFEST_PATH = ROOT / "scripts" / "evidence-manifest.py"
OUTLOOK_CASE_PATH = ROOT / "assets" / "outlook-status.jsonl"
OUTLOOK_SMOKE_PATH = ROOT / "scripts" / "smoke-outlook-status.sh"
OUTLOOK_RUNBOOK_PATH = ROOT / "assets" / "outlook-status-runbook.md"


def load_gate():
    spec = importlib.util.spec_from_file_location("critical_case_gate", GATE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


class AdvancedControlTests(unittest.TestCase):
    def setUp(self):
        self.gate = load_gate()
        self.dataset = [
            {"id": "critical", "input": "critical input", "critical": "yes"},
            {"id": "ordinary", "input": "ordinary input", "critical": "no"},
        ]

    def results(self, score=4, error=None):
        return {
            "evaluators": ["CoherenceEvaluator", "SimilarityEvaluator"],
            "rows": [
                {
                    "input": "critical input",
                    "error": error,
                    "metrics": [
                        {"name": "coherence", "value": score},
                        {"name": "similarity", "value": score},
                    ],
                }
            ],
            "thresholds": [
                {"metric": "coherence", "expected": ">=3"},
                {"metric": "similarity", "expected": ">=3"},
            ],
        }

    def test_gate_passes_complete_critical_case(self):
        report = self.gate.evaluate(self.dataset, self.results(), 3)
        self.assertTrue(report["passed"])
        self.assertEqual(report["critical_cases"][0]["id"], "critical")

    def test_gate_fails_low_critical_score(self):
        report = self.gate.evaluate(self.dataset, self.results(score=2), 3)
        self.assertFalse(report["passed"])
        self.assertIn("below", " ".join(report["critical_cases"][0]["failures"]))

    def test_gate_fails_missing_critical_case(self):
        report = self.gate.evaluate(self.dataset, {"rows": []}, 3)
        self.assertFalse(report["passed"])
        self.assertIn("missing", " ".join(report["critical_cases"][0]["failures"]))

    def test_gate_fails_execution_error(self):
        report = self.gate.evaluate(self.dataset, self.results(error="timeout"), 3)
        self.assertFalse(report["passed"])
        self.assertIn("timeout", " ".join(report["critical_cases"][0]["failures"]))

    def test_gate_fails_missing_evaluator_result(self):
        results = self.results()
        results["rows"][0]["metrics"].pop()
        report = self.gate.evaluate(self.dataset, results, 3)
        self.assertFalse(report["passed"])
        self.assertIn("similarity", " ".join(report["critical_cases"][0]["failures"]))

    def test_manifest_hashes_inputs_and_keeps_run_ids(self):
        root = ROOT / "tests" / ".test-work"
        shutil.rmtree(root, ignore_errors=True)
        root.mkdir()
        try:
            dataset = root / "turns.jsonl"
            config = root / "agentops.yaml"
            results = root / "results.json"
            cloud = root / "cloud.json"
            smoke = root / "smoke.log"
            output = root / "manifest.json"
            dataset.write_text('{"id":"critical"}\n', encoding="utf-8")
            config.write_text("version: 1\n", encoding="utf-8")
            results.write_text(
                json.dumps({"evaluators": ["CoherenceEvaluator"]}), encoding="utf-8"
            )
            cloud.write_text(
                json.dumps({"eval_id": "eval-1", "run_id": "run-1"}),
                encoding="utf-8",
            )
            smoke.write_text("passed\n", encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable,
                    str(MANIFEST_PATH),
                    "--dataset",
                    str(dataset),
                    "--config",
                    str(config),
                    "--results",
                    str(results),
                    "--cloud-run",
                    str(cloud),
                    "--smoke-log",
                    str(smoke),
                    "--output",
                    str(output),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            manifest = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(manifest["foundry_evaluation"]["run_id"], "run-1")
            self.assertEqual(len(manifest["files"]["dataset"]["sha256"]), 64)
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_outlook_case_preserves_observe_lineage(self):
        case = json.loads(OUTLOOK_CASE_PATH.read_text(encoding="utf-8"))
        smoke = OUTLOOK_SMOKE_PATH.read_text(encoding="utf-8")
        runbook = OUTLOOK_RUNBOOK_PATH.read_text(encoding="utf-8")
        self.assertEqual(case["id"], "outlook-status-unsupported")
        self.assertIn(case["input"], smoke)
        self.assertIn("cannot (check|verify|confirm|determine)", smoke)
        self.assertIn("Do not rerun only the release job", runbook)


if __name__ == "__main__":
    unittest.main()
