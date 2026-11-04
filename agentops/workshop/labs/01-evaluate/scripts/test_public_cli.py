"""Offline authoring checks through the released CLI, never a cloud eval."""

import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import unittest
from unittest.mock import patch
import uuid


LAB = Path(__file__).resolve().parents[1]
ASSETS = LAB / "assets"
TARGET = (
    "https://offline-fixture.services.ai.azure.com/api/projects/offline-fixture"
    "/agents/offline-helpdesk/versions/1"
)


class PublicCliTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workspace = LAB / ".local" / f"offline-cli-{uuid.uuid4().hex}"
        cls.workspace.mkdir(parents=True)
        cls.env = {
            key: value for key, value in os.environ.items()
            if not key.startswith(("AZURE_", "AGENTOPS_", "APPLICATIONINSIGHTS_",
                                   "OTEL_", "FOUNDRY_", "OPENAI_"))
        }
        cls.env.update(
            NO_COLOR="1", TERM="dumb", COLUMNS="180", PYTHONUTF8="1",
            OTEL_SDK_DISABLED="true",
        )
        cls.addClassCleanup(shutil.rmtree, cls.workspace)
        shutil.copyfile(ASSETS / "turns.jsonl", cls.workspace / "turns.jsonl")
        result = cls.cli(
            "init", "--no-prompt", "--dir", str(cls.workspace),
            "--project-endpoint",
            "https://offline-fixture.services.ai.azure.com/api/projects/offline-fixture",
            "--agent", TARGET, "--dataset", "turns.jsonl",
        )
        if result.returncode:
            raise AssertionError(result.stdout)
        config = (ASSETS / "agentops.yaml").read_text(encoding="utf-8")
        template_target = next(
            line for line in config.splitlines() if line.startswith("agent:")
        )
        cls.config = config.replace(template_target, f"agent: {TARGET}")
        (cls.workspace / "agentops.yaml").write_text(cls.config, encoding="utf-8")

    @classmethod
    def cli(cls, *args, env=None):
        return subprocess.run(
            [sys.executable, "-m", "agentops", *args],
            cwd=cls.workspace, env=cls.env if env is None else env,
            text=True, encoding="utf-8",
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=90,
            check=False,
        )

    def test_release_and_public_flags(self):
        result = self.cli("--version")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("0.15.0", result.stdout)
        for command, flags in (
            (("eval", "run"), ("--config", "--output", "--baseline", "--agent")),
            (("report", "generate"), ("--in", "--out")),
        ):
            with self.subTest(command=command):
                result = self.cli(*command, "--help")
                self.assertEqual(result.returncode, 0, result.stdout)
                for flag in flags:
                    self.assertIn(flag, result.stdout)

    def test_workspace_and_config_analysis(self):
        env_file = self.workspace / ".agentops" / ".env"
        self.assertFalse(env_file.read_bytes().startswith(b"\xef\xbb\xbf"))
        result = self.cli("init", "show")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("offline-fixture", result.stdout)
        result = self.cli("eval", "analyze", "--dir", ".", "--format", "json")
        self.assertEqual(result.returncode, 0, result.stdout)
        analysis = json.loads(result.stdout)
        serialized = json.dumps(analysis)
        self.assertIn("foundry_hosted", serialized)
        self.assertIn("turns.jsonl", serialized)
        self.assertEqual(analysis["config_status"], "ready")
        self.assertEqual(analysis["dataset_status"], "ready")
        self.assertEqual(analysis["warnings"], [])

    def test_prepared_native_settings_and_process_override(self):
        env_file = self.workspace / ".agentops" / ".env"
        original = env_file.read_bytes()
        self.addCleanup(env_file.write_bytes, original)
        env_file.write_text(
            "AZURE_AI_FOUNDRY_PROJECT_ENDPOINT="
            "https://offline-fixture.services.ai.azure.com/api/projects/offline-fixture\n"
            "AZURE_OPENAI_DEPLOYMENT=offline-judge\n",
            encoding="utf-8",
        )
        prepared = env_file.read_bytes()
        stale = dict(self.env)
        stale["AZURE_AI_FOUNDRY_PROJECT_ENDPOINT"] = (
            "https://stale-project.services.ai.azure.com/api/projects/stale-project"
        )
        result = self.cli("init", "show", env=stale)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("stale-project", result.stdout)
        self.assertIn("process-env", result.stdout)

        for key in (
            "AGENTOPS_AGENT", "AZURE_AI_FOUNDRY_PROJECT_ENDPOINT",
            "AZURE_OPENAI_DEPLOYMENT", "AZURE_AI_MODEL_DEPLOYMENT_NAME",
        ):
            stale.pop(key, None)
        result = self.cli("init", "show", env=stale)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("offline-fixture", result.stdout)
        self.assertIn("agentops-env", result.stdout)
        self.assertNotIn("stale-project", result.stdout)
        self.assertEqual(env_file.read_bytes(), prepared)

    def test_invalid_mode_rejected_before_execution(self):
        invalid = self.workspace / "invalid.yaml"
        invalid.write_text(
            self.config.replace("execution: cloud", "execution: not-a-mode"),
            encoding="utf-8",
        )
        result = self.cli("eval", "run", "--config", str(invalid))
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("failed to load", result.stdout)
        self.assertIn("execution", result.stdout)
        self.assertFalse((self.workspace / ".agentops" / "results").exists())

    @unittest.skipUnless(shutil.which("pwsh"), "Documented Windows setup needs PowerShell")
    def test_documented_learner_startup_preserves_prepared_files(self):
        root = self.workspace / "learner"
        prepared = root / ".local" / "workspace"
        (prepared / ".agentops").mkdir(parents=True)
        (prepared / "agentops.yaml").write_text(self.config, encoding="utf-8")
        env_file = prepared / ".agentops" / ".env"
        env_file.write_text(
            "AZURE_AI_FOUNDRY_PROJECT_ENDPOINT="
            "https://offline-fixture.services.ai.azure.com/api/projects/offline-fixture\n"
            "AZURE_OPENAI_DEPLOYMENT=offline-judge\n", encoding="utf-8",
        )
        before = {path.name: path.read_bytes() for path in
                  (prepared / "agentops.yaml", env_file)}
        startup = re.search(
            r"```powershell\n(.*?)\n```",
            (LAB / "lab.md").read_text(encoding="utf-8"), re.S,
        ).group(1)
        # Reuse the tested CLI installation, not a second package install.
        scripts = str(Path(sys.executable).parent).replace("'", "''")
        startup = startup.replace(
            "$env:Path = (Join-Path $EvaluateRoot '.venv\\Scripts') + ';' + $env:Path",
            f"$env:Path = '{scripts}' + ';' + $env:Path",
        )
        startup = startup.replace(
            "python -m pip check",
            "Write-Output 'No broken requirements found.'; $global:LASTEXITCODE = 0",
        )
        env = dict(self.env, AZURE_AI_FOUNDRY_PROJECT_ENDPOINT="https://stale.invalid")
        result = subprocess.run(
            ["pwsh", "-NoProfile", "-Command", startup],
            cwd=root, env=env, capture_output=True, text=True, encoding="utf-8",
            input="https://prompted.example\nbaseline\ncandidate\nprompted-judge\n",
            timeout=90, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("offline-fixture", result.stdout)
        self.assertIn("offline-judge", result.stdout)
        self.assertNotIn("stale.invalid", result.stdout)
        for path in (prepared / "agentops.yaml", env_file):
            self.assertEqual(path.read_bytes(), before[path.name])
        self.assertFalse((root / ".local" / "runs").exists())

    def test_missing_baseline_rejected_before_cloud_submission(self):
        result = self.cli(
            "eval", "run", "--config", "agentops.yaml",
            "--baseline", "does-not-exist.json",
            "--output", str(self.workspace / "not-produced"),
        )
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("baseline file not found", result.stdout)
        self.assertFalse((self.workspace / "not-produced" / "results.json").exists())

    def test_report_renders_recorded_pass_fail_and_error_without_mutation(self):
        fixture = json.loads(
            (Path(__file__).parent / "fixtures" / "offline-results.json")
            .read_text(encoding="utf-8")
        )
        for state in ("pass", "fail", "error"):
            with self.subTest(state=state):
                payload = json.loads(json.dumps(fixture))
                if state != "pass":
                    payload["summary"]["overall_passed"] = False
                    payload["summary"]["thresholds_passed"] = 0
                    payload["summary"]["threshold_pass_rate"] = 0
                    payload["thresholds"][0]["passed"] = False
                    payload["thresholds"][0]["actual"] = "2"
                    payload["aggregate_metrics"]["coherence"] = 2
                    payload["rows"][0]["metrics"][0]["value"] = 2
                if state == "error":
                    payload["rows"][0]["error"] = "OFFLINE FIXTURE invocation error"
                    payload["rows"][0]["metrics"][0].update(
                        value=None, error="OFFLINE FIXTURE grader error"
                    )
                    payload["aggregate_metrics"] = {}
                    payload["thresholds"][0]["actual"] = "missing"
                    payload["summary"].update(items_passed_all=0, items_pass_rate=0)
                source = self.workspace / f"{state}.json"
                output = self.workspace / f"{state}.md"
                source.write_text(json.dumps(payload), encoding="utf-8")
                original = source.read_bytes()
                result = self.cli(
                    "report", "generate", "--in", str(source), "--out", str(output)
                )
                self.assertEqual(result.returncode, 0, result.stdout)
                report = output.read_text(encoding="utf-8")
                self.assertIn("OFFLINE FIXTURE", report)
                self.assertIn("PASS" if state == "pass" else "FAIL", report)
                self.assertIn("coherence", report)
                self.assertEqual(source.read_bytes(), original)
                if state == "error":
                    self.assertIn("Failed Invocations", report)
                    self.assertIn("coherence=ERR", report)

    def test_corrupt_report_input_is_rejected(self):
        source = self.workspace / "corrupt.json"
        source.write_text('{"version": 1}', encoding="utf-8")
        result = self.cli(
            "report", "generate", "--in", str(source),
            "--out", str(self.workspace / "corrupt.md"),
        )
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertFalse((self.workspace / "corrupt.md").exists())


class TeachingAssetTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("pwsh"), "Documented Windows setup needs PowerShell")
    def test_instructor_source_setup_accepts_complete_and_rejects_missing_files(self):
        repo = LAB.parents[3]
        guide = LAB.parents[1] / "pre-work" / "technical-setup.md"
        setup = next(
            block for block in re.findall(
                r"```powershell\n(.*?)\n```", guide.read_text(encoding="utf-8"), re.S,
            )
            if "Read-Host" in block and "Repository:" in block
        )
        incomplete = LAB / ".local" / f"incomplete-source-{uuid.uuid4().hex}"
        incomplete.mkdir(parents=True)
        self.addCleanup(shutil.rmtree, incomplete)
        for root, expected in ((repo, 0), (incomplete, 1)):
            with self.subTest(complete=expected == 0):
                path = str(root).replace("'", "''")
                result = subprocess.run(
                    ["pwsh", "-NoProfile", "-Command",
                     f"function Read-Host {{ '{path}' }}\n{setup}"],
                    capture_output=True, text=True, encoding="utf-8",
                    timeout=30, check=False,
                )
                self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
                if expected == 0:
                    self.assertIn(f"Repository: {repo}", result.stdout)
                    self.assertIn(f"Local work: {LAB / '.local'}", result.stdout)
                else:
                    self.assertIn("Course file missing:", result.stderr)
                    self.assertEqual(list(incomplete.iterdir()), [])

    def test_main_dataset_is_eight_live_agent_inputs(self):
        rows = [
            json.loads(line) for line in
            (ASSETS / "turns.jsonl").read_text(encoding="utf-8").splitlines()
        ]
        self.assertEqual(len(rows), 8)
        self.assertEqual(len({row["id"] for row in rows}), 8)
        for row in rows:
            self.assertTrue(row["input"])
            self.assertTrue(row["expected"])
            self.assertTrue(row["expected_behavior"])
            self.assertIn(row["critical"], {"yes", "no"})
            self.assertEqual(row.keys(), rows[0].keys())
            self.assertTrue(all(isinstance(value, str) for value in row.values()))
            self.assertFalse({"response", "prediction", "output", "answer"} & row.keys())
        config = (ASSETS / "agentops.yaml").read_text(encoding="utf-8")
        self.assertIn("execution: cloud", config)
        self.assertIn("protocol: responses", config)
        self.assertIn("mode: inline", config)
        self.assertIn("- CoherenceEvaluator", config)
        self.assertIn("- SimilarityEvaluator", config)
        self.assertIn('coherence: ">=3"', config)
        self.assertIn('similarity: ">=3"', config)
        self.assertNotIn("response_source: dataset", config)
        self.assertNotIn("input_mapping", config)

    def test_lab_action_cards_meet_structure_standard(self):
        lab = (LAB / "lab.md").read_text(encoding="utf-8")
        cards = re.findall(
            r"(?ms)^### Action \d+:[^\n]+\n(.*?)(?=^### Action \d+:|^## |\Z)",
            lab,
        )
        self.assertGreaterEqual(len(cards), 10)
        required = (
            "**Purpose:**", "**Result:**", "**If it fails:**",
            "**Save:**", "**Time:**",
        )
        complete = 0
        for card in cards:
            has_action_path = (
                "**Command:**" in card
                or "**Navigation:**" in card
                or "**Command or navigation:**" in card
            )
            if has_action_path and all(label in card for label in required):
                complete += 1
        self.assertGreaterEqual(complete / len(cards), 0.8)

    def test_lab_requires_exact_targets_and_strict_critical_policy(self):
        lab = (LAB / "lab.md").read_text(encoding="utf-8")
        for text in (
            "baseline_expected=$BaselineAgent",
            "baseline_actual=$($BaselineResult.target.raw)",
            "candidate_expected=$CandidateAgent",
            "candidate_actual=$($CandidateResult.target.raw)",
            "Baseline result target does not match",
            "Candidate result target does not match",
            "Baseline and candidate must be versions of the same agent",
            "Workspace candidate differs from the invitation",
            "Workspace project differs from the invitation",
            "Workspace scoring model differs from the invitation",
            "Strict critical-case policy",
            "NO-SHIP: INSUFFICIENT EVIDENCE",
            "Response ID",
            "Trace ID",
            "python -m pip check",
            "Native Microsoft Foundry product path",
        ):
            self.assertIn(text, lab)

    def test_durable_decision_record_captures_action_evidence(self):
        record = (ASSETS / "decision-record.md").read_text(encoding="utf-8")
        for text in (
            "Baseline expected target",
            "Baseline actual target",
            "Candidate expected target",
            "Candidate actual target",
            "password-basic",
            "vpn-ticket",
            "privileged-request",
            "private-ticket",
            "Response ID",
            "Trace ID",
            "lookup_article",
            "create_ticket",
            "NO-SHIP: INSUFFICIENT EVIDENCE",
        ):
            self.assertIn(text, record)

    def test_fallback_requires_matching_exact_evidence(self):
        lab = (LAB / "lab.md").read_text(encoding="utf-8")
        evidence = (ASSETS / "evidence" / "README.md").read_text(encoding="utf-8")
        instructor = (
            LAB.parents[1] / "instructor-guide" / "evaluate.md"
        ).read_text(encoding="utf-8")
        for document in (lab, evidence, instructor):
            self.assertIn("instructor demonstration", document)
            self.assertIn("NO-SHIP: INSUFFICIENT EVIDENCE", document)
        self.assertIn("targets.txt", evidence)
        self.assertIn("exact", instructor.lower())

    def test_controlled_tools_preserve_teaching_defects(self):
        path = LAB.parent / "shared" / "helpdesk-agent" / "tools.py"
        spec = importlib.util.spec_from_file_location("helpdesk_tools_test", path)
        tools = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(tools)
        with patch.dict(os.environ, {"HELPDESK_VARIANT": "baseline"}):
            self.assertEqual(
                json.loads(tools.lookup_article("password"))["source"], "KB-PASSWORD-v1"
            )
            self.assertEqual(
                json.loads(tools.create_ticket("vpn"))["queue"], "Network Support"
            )
        with patch.dict(os.environ, {"HELPDESK_VARIANT": "candidate"}):
            self.assertNotIn("source", json.loads(tools.lookup_article("password")))
            self.assertEqual(
                json.loads(tools.create_ticket("vpn"))["queue"], "Software Support"
            )
        self.assertTrue(json.loads(tools.check_service_status("vpn"))["simulated"])
        self.assertIn("error", json.loads(tools.create_ticket("unknown")))

    def test_no_obsolete_bridge_or_imports(self):
        for filename in ("lab.py", "evidence.py", "test_lab.py"):
            self.assertFalse((LAB / "scripts" / filename).exists())
        for path in (LAB / "scripts").glob("*.py"):
            text = path.read_text(encoding="utf-8")
            self.assertNotRegex(text, r"(?m)^\s*(?:from|import)\s+agentops(?:\.|\s)")

    def test_ship_seed_copies_match_their_originals(self):
        labs = LAB.parent
        seed = labs / "02-ship" / "class-repo"
        pairs = [(ASSETS / "turns.jsonl", seed / "turns.jsonl")]
        for name in ("main.py", "tools.py", "instructions.md", "knowledge.json", "requirements.txt"):
            pairs.append((labs / "shared" / "helpdesk-agent" / name, seed / "src" / "helpdesk" / name))
        for original, copy in pairs:
            self.assertEqual(original.read_bytes().replace(b"\r\n", b"\n"),
                             copy.read_bytes().replace(b"\r\n", b"\n"), copy)


if __name__ == "__main__":
    unittest.main()
