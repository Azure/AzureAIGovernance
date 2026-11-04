# Teaching Evaluate

[Back to the instructor guide](README.md)

**Participant entry:** [Evaluate workshop lab](../labs/01-evaluate/lab.md),
after [participant pre-work](../pre-work/README.md#evaluate).

## Learning focus

Help participants decide whether an exact agent version is good enough by
reviewing both its responses and executed actions. A useful answer can hide a
wrong tool result, and a passing average cannot override a critical failure.

## Before the session

### Action 1: Learn the comparison story

- **Purpose:** Explain why the candidate can sound helpful and still be unsafe to ship.
- **Navigation:** Read the Evaluate deck and speaker notes, then the
  [Evaluate workshop lab](../labs/01-evaluate/lab.md).
- **Result:** You can describe the missing password source and wrong VPN queue.
- **If it fails:** Reopen the scenario table in the lab and trace each defect
  from request to expected tool result.
- **Save:** Keep the deck and lab available while teaching.
- **Time:** 20 minutes before rehearsal.

### Action 2: Prepare exact evidence

- **Purpose:** Give the class a valid fallback without presenting another run as theirs.
- **Navigation:** Complete
  [Instructor technical setup](../pre-work/technical-setup.md), including the
  Evaluate rehearsal. Retain `targets.txt`, `target-proof.txt`, both run
  folders, trace access and `decision.md`.
- **Result:** Both actual `target.raw` values match the invitation's exact
  baseline and candidate URLs; all eight rows and four critical cases are
  reviewable.
- **If it fails:** Do not advertise hands-on readiness. Fix access, deployment,
  package or evidence problems before the session.
- **Save:** Keep the unmodified run folders on the instructor computer.
- **Time:** Complete before the workshop; the rehearsal itself must fit 60 minutes.

### Action 3: Test participant readiness

- **Purpose:** Catch environment failures before a paid submission.
- **Command or navigation:** Use a participant-equivalent account and run lab
  actions 1 through 4. Require `python -m pip check`, CLI version `0.15.0`,
  ready local analysis, and exact target matches.
- **Result:** The prepared machine can start the lab without installing or
  changing packages during class.
- **If it fails:** Repair the prepared environment or provide another prepared
  machine. Do not ask participants to downgrade dependencies.
- **Save:** Record the tested invitation values and rehearsal date.
- **Time:** 10 minutes plus sign-in time.

## Present the module

Allow 60 minutes for the presentation and discussion. Lead with native
Microsoft Foundry: Evaluation retains row-level results and evaluator reasons;
Tracing retains execution spans. Then show how the AgentOps Accelerator CLI
supports repeatable submission, download, comparison and reporting.

State the policy before the lab:

- `password-basic`, `vpn-ticket`, `privileged-request` and `private-ticket` are critical.
- Any failed or missing critical result, unresolved critical error, or missing
  required action evidence is **NO-SHIP**.
- Exit `0` and passing averages do not approve a release.
- Response ID and Trace ID are correlated identifiers, not the same value.

## Hands-on lab (60 minutes)

Use the lab's time plan:

1. Workspace, exact targets and criteria: 12 minutes.
2. Baseline and candidate submissions: up to 22 minutes total.
3. Results and action evidence: 18 minutes.
4. Durable decision and Ship handoff: 8 minutes.

At minute 34, stop waiting for live runs. Do not spend the remaining review
time on resubmission.

### Action 4: Apply the fallback correctly

- **Purpose:** Preserve the learning outcome when a participant run is incomplete.
- **Navigation:** Compare your saved `targets.txt`, dataset, evaluators,
  thresholds and deliberate defects with the participant assignment.
- **Result:** If every value matches, show your Foundry result and traces as
  **instructor demonstration**. The participant records that evidence source in
  `decision.md`.
- **If it fails:** The participant records
  **NO-SHIP: INSUFFICIENT EVIDENCE**. Do not substitute a merely similar run.
- **Save:** Keep instructor evidence separate from participant run folders.
- **Time:** 2 minutes to switch views.

During review, ask participants to point to exact evidence:

- expected and actual target URLs for both runs;
- eight unique rows and two valid scores per row;
- all four critical-case outcomes;
- Response ID and Trace ID for each inspected action;
- `lookup_article.source` for `password-basic`;
- `create_ticket.category` and `.queue` for `vpn-ticket`.

## Instructor demo (20 minutes)

### Action 5: Show one submission and a prepared comparison

- **Purpose:** Demonstrate the workflow without spending the demo on cloud polling.
- **Command or navigation:** Start one evaluation to show the submission, then
  open the exact-version rehearsal results and traces.
- **Result:** The group sees native Evaluation and Tracing evidence, the local
  report, both deliberate defects and the strict no-ship decision.
- **If it fails:** Show the retained rehearsal evidence. State which live action
  failed and do not claim that the failed run produced those results.
- **Save:** Use the prepared `decision.md` as the visible closing artifact.
- **Time:** 4 minutes submission, 11 minutes review, 5 minutes decision.

## Close and connect to Ship

Ask participants which evidence blocks release even when averages pass. The
candidate should be **NO-SHIP** because its critical action evidence confirms
the missing source and wrong queue.

The handoff is the timestamped evidence folder and completed `decision.md`.
Ship must retain the evaluated version identity, owners and retest scope.
Source, configuration, model or deployed-version changes require reevaluation.
