# Teaching Ship

[Back to the instructor guide](README.md)

**Participant entry:** [Ship workshop lab](../labs/02-ship/lab.md).

## Learning focus

Teach participants to connect an evaluation decision to a controlled release.
Emphasize four actions: deploy the candidate, evaluate its exact version,
approve the reviewed commit, and invoke the exact released version.

State the identity limitation accurately. The test and release agents are
different identities with independently assigned versions. The current
documented `azd ai agent` commands do not promote one immutable version between
those identities. The lab records source-and-configuration equivalence in a
release manifest and does not claim binary artifact identity.

## Prepare the session

1. Read the Ship deck and speaker notes.
2. Read the Ship workshop lab.
3. Select GitHub Actions or Azure Pipelines.
4. Complete [Ship preparation](../pre-work/technical-setup.md#ship).
5. Grant the pipeline identity **Foundry User** and **Contributor** on the
   existing target Foundry project.
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

Microsoft currently marks the Foundry agents extension and hosted agents as
preview. The lab pins `azure.ai.agents` `1.0.0-beta.23` and prints
`azd ai agent version` in the pipeline. Rehearse again before delivery if the
pinned version is no longer available.

## Present the module

Allow 60 minutes for the presentation. Ask participants to distinguish:

- the pipeline sign-in identity from the hosted-agent runtime identity;
- the test agent identity from the release agent identity;
- source equivalence from immutable artifact promotion; and
- an evaluation pass from permission to release.

Use the release manifest to connect the commit, candidate version, approval,
released version and smoke-test evidence.

## Facilitate the hands-on lab

Allow 75 to 90 minutes elapsed for the lab. Participants perform about 60
minutes of work. Cloud deployment and evaluation can consume 10 to 20 minutes
per run.

During the first wait:

1. Ask participants to find the candidate identity and version.
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
6. Point to the two agent identities and two versions.
7. Explain the recovery sequence: restrict, retain evidence, revert, rerun all
   four stages, approve, and restore access.

If a live run fails, read the first failed task with the group. Do not start
unplanned runs to fill the time.

## Close

Ask who monitors the released identity, who can restrict its endpoint, and
which evidence an operator needs before recovery. Use those answers to
introduce Observe and Operate.
