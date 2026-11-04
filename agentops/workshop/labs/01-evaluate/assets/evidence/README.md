# Guide to Evaluate evidence

![Every score has a story. Keep the right evidence. Open the files that show what was tested and what happened.](../../../../assets/banners/evidence.png)

Use this guide to identify evidence from a participant run or an instructor
demonstration. Repository fixtures are test inputs, not evaluation evidence.

## Required evidence set

Keep one timestamped run folder with:

- `targets.txt`: the assigned project, baseline, candidate and scoring model.
- `target-proof.txt`: expected and actual `target.raw` for both runs.
- `baseline\` and `candidate\`: unmodified `results.json`, `report.md`,
  `cloud_evaluation.json` and `cloud_output_items.json`.
- `baseline-terminal.txt` and `candidate-terminal.txt`: submission output.
- `decision.md`: completeness, critical cases, Response ID to Trace ID
  correlation, executed actions, decision, owners and retest scope.

The local folders are normally under
`.local\runs\<timestamp>\baseline` and `candidate`. Foundry retains the native
evaluation and trace records in the shared project.

## Evidence rules

1. Match rows by request ID or full input, not file position.
2. Require eight unique responses and two valid scores per response.
3. Match each downloaded `target.raw` to the exact saved version URL.
4. Record both identifiers: a Response ID identifies an agent response; a
   Trace ID identifies telemetry. Do not treat them as interchangeable.
5. For `password-basic`, retain the `lookup_article` result and its `source`.
6. For `vpn-ticket`, retain the `create_ticket` `category` argument and `queue`
   result.
7. Treat missing or failed critical evidence as **NO-SHIP**, not as a pass.
8. Leave run files unchanged. Put review conclusions in `decision.md`.

The four critical cases are `password-basic`, `vpn-ticket`,
`privileged-request`, and `private-ticket`.

## Instructor fallback

An instructor demonstration is eligible only when its `targets.txt`, exact
agent versions, dataset, evaluators, thresholds and deliberate defects match
the participant lab. Label it **instructor demonstration** in `decision.md`.
Do not copy it into a participant run folder or present it as that
participant's completed run.

If exact evidence is unavailable, record
**NO-SHIP: INSUFFICIENT EVIDENCE** and name the owner and follow-up. Do not use
`scripts\fixtures\offline-results.json`; that file tests report rendering only.

Remove secrets and private data before showing evidence. Do not commit
tenant-specific output.
