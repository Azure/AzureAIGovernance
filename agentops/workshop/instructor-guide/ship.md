# Teaching Ship

[Back to the instructor guide](README.md)

**Participant entry:** [Ship workshop lab](../labs/02-ship/lab.md).

## Learning focus

Teach participants to connect an evaluation decision to a controlled release.
Emphasize four actions: deploy the candidate, evaluate its exact version,
approve the exact candidate, switch the production endpoint selector to it at
100 percent, and invoke that same version.

State the identity contract accurately. One agent identity holds the stable and
candidate versions. Candidate deployment leaves production pinned to the
stable version. Approval changes the selector to the evaluated version at 100
percent. The release manifest retains the previous selector for rollback.

## Prepare the session

1. Read the Ship deck and speaker notes.
2. Read the Ship workshop lab.
3. Select GitHub Actions or Azure Pipelines.
4. Complete [Ship preparation](../pre-work/technical-setup.md#ship).
5. Grant the pipeline identity **Foundry User** on the parent Foundry resource
   for judge-model inference. Preserve **Foundry User** and **Contributor** on
   the target Foundry project.
6. Keep the hosted-agent runtime identity separate. Grant it access to another
   Azure service only if the agent calls that service.
7. Create the `dev` and `production` approval environments.
8. Run the local Ship tests from the class-repository seed.

**What this block does:** checks the Ship scripts and manifest behavior without
calling Azure.

```powershell
python -m unittest discover agentops\workshop\labs\02-ship\class-repo\tests -v
```

9. Rehearse one rejected run and one released run.
10. Download the evaluation artifact and release manifest from the rehearsal.
11. Test the invitation with participant-level repository and project access.

The lab pins the beta `azure.ai.agents` extension at `1.0.0-beta.23`. The
endpoint-selector production-promotion guidance is preview. Do not describe
all hosted-agent capabilities as preview. The pipeline prints
`azd ai agent version` in the pipeline. Rehearse again before delivery if the
pinned version is no longer available.

## Present the module

Allow 60 minutes for the presentation. Ask participants to distinguish:

- the pipeline sign-in identity from the hosted-agent runtime identity;
- the stable version from the candidate version under one identity;
- exact-version testing from production endpoint selection; and
- an evaluation pass from permission to release.

Use the release manifest to connect the commit, candidate version, approval,
released version and smoke-test evidence.

## Facilitate the hands-on lab

Allow 90 minutes with GitHub Actions or 120 minutes with Azure Pipelines.
Cloud deployment and evaluation can consume 10 to 20 minutes per run, and the
Azure Pipelines route includes pipeline creation.

During the first wait:

1. Ask participants to find the stable selector and candidate version.
2. Ask them to download the evaluation artifact.
3. Ask them to locate the failed VPN tool result.
4. Ask them to reject the release.

During the second wait:

1. Ask participants to match the evaluated version to the pipeline output.
2. Ask them to approve only after they see `Network Support`.
3. Ask them to match the released version to the exact-version smoke test.
4. Ask them to download and read `release-manifest.json`.

Participants approve their own workshop runs to keep the activity moving.
Explain that a normal production process uses an independent approver.

## Demonstrate in 20 minutes

1. Open the four-stage pipeline.
2. Open the rejected run and its VPN trace.
3. Open the released run and its approval.
4. Open the exact-version smoke-test log.
5. Open `release-manifest.json`.
6. Point to the one identity, candidate version and previous selector.
7. Explain the recovery sequence: restore the previous selector, retain
   evidence, revert, rerun all four stages, approve, and restore access.

If a live run fails, read the first failed task with the group. Do not start
unplanned runs to fill the time.

## Close

Ask who monitors the released identity, who can restrict its endpoint, and
which evidence an operator needs before recovery. Use those answers to
introduce Observe and Operate.
