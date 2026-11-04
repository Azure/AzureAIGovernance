# Ship class repository seed

This folder is the starting point of the repository in which participants build
their release pipeline during [Ship](../lab.md). The instructor copies it
once, as described in
[technical setup](../../../pre-work/technical-setup.md#ship), and pushes it to
the class GitHub repository or Azure Repos repository. Participants never edit
this seed directly.

## Contents

| Path | Purpose |
| --- | --- |
| `azure.yaml` | Tells azd which agent code to deploy. It defines one `helpdesk-ALIAS` identity and a production endpoint selector pinned to one version at 100 percent. |
| `src/helpdesk/` | The [help desk agent](../../shared/helpdesk-agent/README.md) code. `.agentignore` keeps local files out of uploads. |
| `agentops.yaml` | The Evaluate settings. The pipeline replaces the version `1` with the version it just deployed. |
| `turns.jsonl` | The eight Evaluate test requests. |
| `scripts/deploy-agent.sh` | Keeps the endpoint on its stable version, bootstraps a baseline on the first run, deploys a candidate and saves the previous selector. |
| `scripts/configure-azd.sh` | Selects the existing class Foundry project for deployment and smoke-test commands. Creates no Azure resources. |
| `scripts/smoke-test.sh` | Invokes one expected released version and fails unless the `create_ticket` result contains Network Support and `SIM-VPN-001`. |
| `scripts/agent-version.sh` | Prints the version number azd just deployed for one agent. Used by the other two scripts. |
| `scripts/read-endpoint-selector.sh` | Saves the one-version, 100-percent production selector for rollback. |
| `scripts/set-endpoint-version.sh` | Applies one exact version to the endpoint selector at 100 percent. |
| `scripts/promote-version.sh` | Switches production to the approved candidate without creating another version. |
| `scripts/write-release-manifest.sh` | Records the evaluated and released version, previous selector, commit, source-and-configuration fingerprint, pipeline URL, extension version and smoke-test evidence. |
| `tests/test_ship_release.py` | Runs local tests for version pinning, tool evidence and manifest provenance without calling Azure. |

Participants replace `ALIAS` with their alias on their own branch. The
instructor replaces `FOUNDRY_ENDPOINT` in `agentops.yaml` once, when copying the seed.
The pipeline itself is not part of the seed: each participant generates it with
the AgentOps Accelerator CLI and adapts it during the lab.

The stable and candidate releases are versions of one Foundry agent identity.
The pipeline pins production to the current selector while it deploys and tests
the candidate. Approval changes that selector to the evaluated version at 100
percent. The previous selector remains in the release artifact for rollback.
The workshop deliberately does not teach percentage canaries or split traffic.

Run the local tests from the repository root before you publish the seed.

**What this block does:** tests the Ship scripts without Azure access.

```powershell
python -m unittest discover agentops\workshop\labs\02-ship\class-repo\tests -v
```

`src/helpdesk/` and `turns.jsonl` are copies of the
[shared help desk agent](../../shared/helpdesk-agent/README.md) and the
Evaluate lab's `assets/turns.jsonl`. When you change those originals, copy them
here too.
