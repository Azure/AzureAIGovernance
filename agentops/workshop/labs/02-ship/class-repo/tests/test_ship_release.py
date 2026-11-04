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

    def test_release_manifest_records_distinct_identities_and_provenance(self):
        output = self.work / "release-manifest.json"
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
            "helpdesk-test", "7", "helpdesk", "3", output, env=env,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        manifest = json.loads(output.read_text(encoding="utf-8"))
        self.assertFalse(manifest["promotion"]["exact_version_promotion"])
        self.assertEqual(manifest["evaluated"], {"service": "helpdesk-test", "version": "7"})
        self.assertEqual(manifest["released"]["service"], "helpdesk")
        self.assertEqual(manifest["released"]["version"], "3")
        self.assertEqual(manifest["released"]["tool_evidence"]["ticket_reference"], "SIM-VPN-001")
        self.assertEqual(manifest["provenance"]["source_configuration_sha256"], "f" * 64)

    def test_pipeline_guides_keep_stage_and_provenance_contract_aligned(self):
        lab = ROOT.parent / "lab.md"
        guides = [
            ROOT.parent / "github-actions" / "README.md",
            ROOT.parent / "azure-pipelines" / "README.md",
        ]
        stages = (
            "Deploy candidate",
            "Evaluate candidate",
            "Approve and release",
            "Verify and record release",
        )
        for path in [lab, *guides]:
            text = path.read_text(encoding="utf-8")
            for stage in stages:
                self.assertIn(stage, text, f"{stage} missing from {path}")
            lowered = text.lower()
            self.assertNotIn("promotes the same version", lowered)
            self.assertNotIn("reuses the same immutable runtime", lowered)
        lab_text = lab.read_text(encoding="utf-8")
        self.assertIn("different agent identities", lab_text)
        self.assertIn("independently assigned Foundry versions", lab_text)
        for path in guides:
            text = path.read_text(encoding="utf-8")
            self.assertIn("1.0.0-beta.23", text)
            self.assertIn("write-release-manifest.sh", text)
            self.assertIn("smoke-test.sh", text)


if __name__ == "__main__":
    unittest.main()
