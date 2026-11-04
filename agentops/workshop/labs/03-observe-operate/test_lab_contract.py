import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
LAB = (ROOT / "lab.md").read_text(encoding="utf-8")
INSTRUCTOR = (
    ROOT.parent.parent / "instructor-guide" / "observe-operate.md"
).read_text(encoding="utf-8")
AGENT_INSTRUCTIONS = (
    ROOT.parent / "shared" / "helpdesk-agent" / "instructions.md"
).read_text(encoding="utf-8")
PREWORK = (
    ROOT.parent.parent / "pre-work" / "README.md"
).read_text(encoding="utf-8")


class ObserveLabContractTests(unittest.TestCase):
    def test_invocation_pins_and_proves_the_released_version(self):
        self.assertIn("--agent-endpoint $AgentEndpoint", LAB)
        self.assertIn("--version $AgentVersion", LAB)
        self.assertIn("--output raw", LAB)
        self.assertIn("agent-version", LAB)
        self.assertIn("release-manifest.json", LAB)
        self.assertIn("azd ext install azure.ai.agents", PREWORK)
        self.assertIn("azd auth login --tenant-id", PREWORK)

    def test_deterministic_complaint_is_in_agent_contract(self):
        self.assertIn("check_service_status exactly once", AGENT_INSTRUCTIONS)
        self.assertIn('service="outlook"', LAB)
        self.assertIn("Only the simulated VPN service is supported.", LAB)

    def test_actions_use_complete_ste_structure(self):
        actions = re.findall(
            r"^### Action \d+:[^\n]+\n(.*?)(?=^### Action \d+:|^## |\Z)",
            LAB,
            flags=re.MULTILINE | re.DOTALL,
        )
        self.assertGreaterEqual(len(actions), 10)
        required = (
            "- **Purpose:**",
            "- **Navigation:**",
            "- **Result:**",
            "- **If it fails:**",
            "- **Save:**",
            "- **Time:**",
        )
        complete = sum(all(field in action for field in required) for action in actions)
        self.assertGreaterEqual(complete / len(actions), 0.8)

    def test_query_is_structured_and_version_scoped(self):
        self.assertIn("AppGenAIContent", LAB)
        self.assertIn("ToolCallResult", LAB)
        self.assertIn("AgentName == SelectedAgent and VersionAttr == SelectedVersion", LAB)
        self.assertIn("Privileged Monitoring Data Reader", LAB)
        self.assertNotIn('tostring(customDimensions) has "error"', LAB)

    def test_response_trace_and_alert_outcome_are_exact(self):
        self.assertIn("Response ID", LAB)
        self.assertIn("Trace ID", LAB)
        self.assertIn("correlated identifiers, not the same value", LAB)
        self.assertIn("monitor condition\n  **Fired**", LAB)
        self.assertIn("complaint-response.txt", LAB)
        self.assertNotIn("complaint-response.json", LAB)
        self.assertIn("Agents > Traces", LAB)

    def test_artifacts_retention_case_and_follow_ons_exist(self):
        for text in (
            "tool-errors.kql",
            "response-notes.md",
            "Keep your work",
            '"id":"outlook-status-unsupported"',
            "approved status-provider integration",
        ):
            self.assertIn(text, LAB)

    def test_native_dashboard_precedes_supporting_cli(self):
        dashboard = LAB.index("## 3. Start with the native dashboard")
        cli = LAB.index("## 8. Run the health check")
        self.assertLess(dashboard, cli)
        self.assertIn("Lead with the native", INSTRUCTOR)


if __name__ == "__main__":
    unittest.main()
