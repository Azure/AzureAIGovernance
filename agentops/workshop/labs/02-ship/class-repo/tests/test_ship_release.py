import json
import os
from pathlib import Path
import shutil
import subprocess
import unittest
import uuid


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


def find_bash():
    candidates = [
        Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Git" / "bin" / "bash.exe",
        Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Git" / "usr" / "bin" / "bash.exe",
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return shutil.which("bash")


@unittest.skipUnless(find_bash(), "Ship script tests require Bash")
class ShipReleaseTests(unittest.TestCase):
    def setUp(self):
        self.work = ROOT / ".local-tests" / uuid.uuid4().hex
        self.bin = self.work / "bin"
        self.bin.mkdir(parents=True)
        self.addCleanup(shutil.rmtree, self.work, ignore_errors=True)
        fake_azd = self.bin / "azd"
        fake_azd.write_text(
            """#!/usr/bin/env bash
set -euo pipefail
if [ "$1 $2" = "env get-value" ]; then
  printf '%s\n' "${FAKE_VERSION:-7}"
elif [ "$1 $2 $3" = "ai agent show" ]; then
  printf '{"agent":{"version":"%s"}}\n' "${FAKE_VERSION:-7}"
elif [ "$1 $2 $3" = "ai agent endpoint" ] && [ "$4" = "show" ]; then
  printf '{"agentEndpoint":{"versionSelector":{"versionSelectionRules":[{"type":"FixedRatio","agentVersion":"%s","trafficPercentage":100}]}}}\n' "${FAKE_SELECTED_VERSION:-7}"
elif [ "$1 $2 $3" = "ai agent endpoint" ] && [ "$4" = "update" ]; then
  printf 'updated\n'
elif [ "$1 $2 $3" = "ai agent invoke" ]; then
  printf '%s\n' "${FAKE_REPLY:-Ticket SIM-VPN-001 routed to Network Support}"
else
  echo "unexpected azd arguments: $*" >&2
  exit 9
fi
""",
            encoding="utf-8",
            newline="\n",
        )
        fake_azd.chmod(0o755)
        self.env = dict(os.environ)
        self.env["PATH"] = str(self.bin) + os.pathsep + self.env.get("PATH", "")
        self.env["SELECTOR_EVIDENCE_FILE"] = str(self.work / "selected-selector.json")

    def run_script(self, name, *args, env=None):
        return subprocess.run(
            [find_bash(), str(SCRIPTS / name), *map(str, args)],
            cwd=ROOT,
            env=self.env if env is None else env,
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=False,
        )

    def test_smoke_test_pins_version_and_checks_tool_evidence(self):
        result = self.run_script("smoke-test.sh", "helpdesk-test", "7")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("exact target: helpdesk-test version 7", result.stdout)
        self.assertIn("Smoke test passed", result.stdout)

    def test_smoke_test_rejects_version_drift(self):
        result = self.run_script("smoke-test.sh", "helpdesk-test", "6")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not expected version 6", result.stderr)

    def test_smoke_test_rejects_missing_tool_result(self):
        env = dict(self.env, FAKE_REPLY="Network Support replied")
        result = self.run_script("smoke-test.sh", "helpdesk-test", "7", env=env)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("SIM-VPN-001", result.stderr)

    def test_release_manifest_records_single_identity_and_rollback_selector(self):
        output = self.work / "release-manifest.json"
        selector = self.work / "previous-selector.json"
        selector.write_text(
            '{"versionSelectionRules":[{"type":"FixedRatio","agentVersion":"6","trafficPercentage":100}]}\n',
            encoding="utf-8",
        )
        env = dict(
            self.env,
            RELEASE_COMMIT="abc123",
            RELEASE_SOURCE_SHA256="f" * 64,
            RELEASE_CREATED_AT="2026-11-04T12:00:00Z",
            RELEASE_PIPELINE_URL="https://ci.example/runs/42",
            AZD_AI_AGENTS_EXTENSION_VERSION="1.0.0-beta.23",
        )
        result = self.run_script(
            "write-release-manifest.sh",
            "helpdesk", "7", selector, output, env=env,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        manifest = json.loads(output.read_text(encoding="utf-8"))
        self.assertTrue(manifest["promotion"]["exact_version_promotion"])
        self.assertEqual(manifest["promotion"]["selected_traffic_percentage"], 100)
        self.assertEqual(
            manifest["promotion"]["previous_selector"]["versionSelectionRules"][0]["agentVersion"],
            "6",
        )
        self.assertEqual(manifest["evaluated"], {"service": "helpdesk", "version": "7"})
        self.assertEqual(manifest["released"]["service"], "helpdesk")
        self.assertEqual(manifest["released"]["version"], "7")
        self.assertEqual(manifest["released"]["tool_evidence"]["ticket_reference"], "SIM-VPN-001")
        self.assertEqual(manifest["provenance"]["source_configuration_sha256"], "f" * 64)

    def test_endpoint_selector_requires_one_version_at_100_percent(self):
        output = self.work / "selector.json"
        result = self.run_script("read-endpoint-selector.sh", "helpdesk", output)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        selector = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(
            selector["versionSelectionRules"],
            [{"type": "FixedRatio", "agentVersion": "7", "trafficPercentage": 100}],
        )

    def test_pipeline_guides_keep_single_agent_promotion_contract_aligned(self):
        lab = ROOT.parent / "lab.md"
        guides = [
            ROOT.parent / "github-actions" / "README.md",
            ROOT.parent / "azure-pipelines" / "README.md",
        ]
        stages = (
            "Deploy candidate",
            "Evaluate candidate",
            "Approve and promote",
            "Verify and record release",
        )
        for path in [lab, *guides]:
            text = path.read_text(encoding="utf-8")
            for stage in stages:
                self.assertIn(stage, text, f"{stage} missing from {path}")
            self.assertIn("100 percent", text)
        lab_text = lab.read_text(encoding="utf-8")
        self.assertIn("only agent identity", lab_text)
        self.assertIn("previous selector", lab_text)
        self.assertNotIn("helpdesk-ALIAS-test", lab_text)
        for path in guides:
            text = path.read_text(encoding="utf-8")
            self.assertIn("1.0.0-beta.23", text)
            self.assertIn("write-release-manifest.sh", text)
            self.assertIn("smoke-test.sh", text)
            self.assertIn("promote-version.sh", text)

    def test_self_service_clone_and_github_oidc_environment_are_guarded(self):
        lab = (ROOT.parent / "lab.md").read_text(encoding="utf-8")
        github = (ROOT.parent / "github-actions" / "README.md").read_text(encoding="utf-8")
        azure = (ROOT.parent / "azure-pipelines" / "README.md").read_text(encoding="utf-8")
        self.assertIn("git remote get-url origin", lab)
        verify = github[github.index("  verify:"):]
        self.assertIn("environment: dev", verify)
        self.assertIn("actions/download-artifact", verify)
        self.assertIn("scroll to **Artifacts**", github)
        self.assertIn("**Related > Published**", azure)
        self.assertIn("select **Extract all**", lab)


if __name__ == "__main__":
    unittest.main()
