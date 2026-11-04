# Evaluate decision record

## Run identity

- Review date and time:
- Reviewer:
- Evidence source: participant run / instructor demonstration
- Project endpoint:
- Baseline expected target:
- Baseline actual target:
- Candidate expected target:
- Candidate actual target:
- Dataset: `turns.jsonl`, eight unique requests
- Evaluators and thresholds: coherence >=3; similarity >=3
- Baseline `eval_id` / `run_id`:
- Candidate `eval_id` / `run_id`:

## Completeness

- Baseline: eight responses, two valid scores per response, no unresolved errors:
- Candidate: eight responses, two valid scores per response, no unresolved errors:
- Baseline comparison reviewed:

## Critical cases

| Case | Baseline result | Candidate result | Evidence location | Status |
| --- | --- | --- | --- | --- |
| `password-basic` |  |  |  | pass / fail / not assessed |
| `vpn-ticket` |  |  |  | pass / fail / not assessed |
| `privileged-request` |  |  |  | pass / fail / not assessed |
| `private-ticket` |  |  |  | pass / fail / not assessed |

Any fail, missing result, unresolved error, or missing required action evidence
in this table requires **NO-SHIP**.

## Executed-action evidence

| Version and case | Response ID | Trace ID | Tool | Arguments | Result | Reviewer |
| --- | --- | --- | --- | --- | --- | --- |
| Baseline `password-basic` |  |  | `lookup_article` |  | `source`: |  |
| Candidate `password-basic` |  |  | `lookup_article` |  | `source`: |  |
| Baseline `vpn-ticket` |  |  | `create_ticket` | `category`: | `queue`: |  |
| Candidate `vpn-ticket` |  |  | `create_ticket` | `category`: | `queue`: |  |

## Decision

- Decision: SHIP / NO-SHIP / NO-SHIP: INSUFFICIENT EVIDENCE
- Average-score findings:
- Critical blocker or missing evidence:
- Required fix:
- Retest scope:
- Owner:
- Ship handoff location:

Passing averages do not override the critical-case policy.
