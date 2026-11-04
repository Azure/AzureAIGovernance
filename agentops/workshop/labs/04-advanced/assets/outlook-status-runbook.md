# Outlook status incident runbook

## Scope

Use this runbook when the help desk agent reports an Outlook status that the
status tool did not establish, or when the `outlook-status-unsupported` release control
fails.

## Signal and evidence

- [ ] Alert or trace URL:
- [ ] Affected agent and version:
- [ ] First known request time in UTC:
- [ ] Last-good pipeline run and artifact:

## Ownership and authority

- [ ] Incident owner:
- [ ] Person authorized to stop or roll back the agent:
- [ ] Tool owner:
- [ ] Communications owner:

## Contain

1. Open the trace and read the `check_service_status` arguments and result.
2. Stop approval of any candidate that claims an unsupported Outlook status.
3. Leave the released agent running only if it states the limitation honestly
   and the incident owner accepts the user impact.
4. Start a full pipeline run from the selected last-good or revert commit if
   the released agent invents a status.

## Recover

1. Select the last-good source commit or revert the defective commit without
   rewriting branch history.
2. Push a recovery branch or commit and start a complete pipeline run.
3. Run candidate deployment, evaluation, approval, release, exact-version
   verification and manifest generation. Do not rerun only the release job or
   stage.
4. Approve only after the recovery criteria below pass.

## Recovery criteria

- [ ] Evaluation completed with no missing rows or scorer errors.
- [ ] Every `outlook-status-unsupported` score met its configured minimum.
- [ ] The critical-case gate passed every critical dataset case.
- [ ] The exact candidate-version Outlook smoke test stated the limitation and offered escalation.
- [ ] The released-agent VPN smoke test passed.
- [ ] A post-release Outlook trace showed the unsupported-service error.
- [ ] The released answer did not claim that Outlook was operational or unavailable.

## Retained evidence

| Evidence | Last good | Failed candidate | Recovery |
| --- | --- | --- | --- |
| Pipeline run URL |  |  |  |
| Source commit |  |  |  |
| Agent version |  |  |  |
| Foundry evaluation ID / run ID |  |  |  |
| Artifact location |  |  |  |

## Follow-up

- [ ] Trace-to-dataset or continuous-evaluation action:
- [ ] Owner and due date:
- [ ] Privacy review:
- [ ] Acceptance criterion:
