# Teaching Observe and Operate

[Back to the instructor guide](README.md)

**Participant entry:** [03-observe-operate](../labs/03-observe-operate/lab.md).
It closes the core workshop sequence. [04-advanced](../labs/04-advanced/lab.md)
is an optional extension.

## Learning focus

Help participants connect one runtime complaint to an exact response, trace,
version-scoped query, fired alert and owned response. Keep the concepts distinct:
**Observe** establishes what happened. **Operate** chooses and carries out an
approved response, retains evidence and proposes the next evaluation case.

## Before the session

Read the
[Observe and Operate deck and speaker notes](../decks/observe-operate/agentops-observe-operate-workshop.pptx),
the [participant lab](../labs/03-observe-operate/lab.md), and
[module preparation](../pre-work/technical-setup.md#observe-and-operate).

### Action 1: Rehearse the deterministic scenario

- **Purpose:** Give participants a complaint that produces the same tool result.
- **Navigation:** Send the lab's exact Outlook request to the released workshop
  version. Open the response and its correlated trace.
- **Result:** The trace contains one
  `check_service_status(service="outlook")` call and the exact unsupported-service
  result. The answer reports the limitation and offers Service Desk escalation.
- **If it fails:** Redeploy the current shared help desk agent before the
  workshop. Do not teach this scenario with a version that chooses another action.
- **Save:** Keep the rehearsal Response ID, Trace ID, agent name, version and UTC time.
- **Time:** 10 minutes plus telemetry propagation.

### Action 2: Prove the telemetry mapping

- **Purpose:** Prepare a runnable query without assuming attribute names.
- **Navigation:** Use the lab's discovery query against the rehearsal Response
  ID. Record the actual agent identity, version, response, tool name, arguments
  and result keys exported by the prepared hosting version.
- **Result:** The final KQL filters one exact agent and version and reads the
  error from the structured tool-result field.
- **If it fails:** Repair tracing or use a prepared environment whose telemetry
  exposes agent identity and version. Do not provide an unscoped class-wide alert.
- **Save:** Keep the final rehearsal KQL and one exported result.
- **Time:** 10 minutes.

### Action 3: Test a real alert outcome

- **Purpose:** Ensure the class can inspect a fired alert, not only create a rule.
- **Navigation:** Create the version-scoped rule, send the Outlook request, and
  wait through its evaluation window.
- **Result:** Azure Monitor shows an alert instance with condition **Fired**,
  and its time and dimensions match the rehearsal request.
- **If it fails:** Repair the query, lookback, evaluation or permissions before
  delivery. Keep a retained exact-version rehearsal alert as the demonstration
  fallback.
- **Save:** Keep the rule resource ID, alert instance ID, fired time and cleanup owner.
- **Time:** 10 minutes active, up to 15 minutes elapsed.

### Action 4: Set retention and permissions

- **Purpose:** Make evidence handling and cleanup explicit.
- **Navigation:** Set the invitation's **Keep your work until** date. Decide
  whether participants have Monitoring Contributor or whether you create the
  alert on screen. Use no action group unless recipients agreed.
- **Result:** Participants can read traces and logs. One named person can create
  the rule. The workshop organizer owns cloud cleanup after the retention date.
- **If it fails:** Use instructor demonstration mode for alert creation. Do not
  ask participants to work around denied access.
- **Save:** Put the tested agent name, released version, Application Insights
  resource and retention date in **Observe settings**.
- **Time:** 5 minutes.

## Present the module

Allow 60 minutes for presentation and discussion. Lead with the native
Microsoft Foundry Agent Monitoring Dashboard, then move from aggregate health
to one exact trace. Explain why successful requests can still contain failed
business actions. Show how structured OpenTelemetry attributes support scoped
queries, alerts and later evaluation.

Present AgentOps Accelerator as a supporting health check after native
monitoring, not as the product monitoring surface.

## Hands-on lab (60 minutes)

Use the lab's time plan:

1. Target and deterministic complaint: 12 minutes.
2. Native dashboard and exact trace correlation: 12 minutes.
3. Telemetry discovery and scoped query: 14 minutes.
4. Alert creation, health report and response work: 17 minutes active while the
   alert evaluates.
5. Fired-alert evidence, evaluation case and retention: 5 minutes.

Ask participants to point to exact evidence:

- assigned agent and released version;
- Response ID and correlated Trace ID;
- `check_service_status` arguments and structured result;
- agent and version predicates in KQL;
- fired alert instance and time;
- owner, allowed immediate action and product follow-ons; and
- the exact proposed `outlook-status-unsupported` evaluation row.

At minute 45, participants must continue to response notes while the alert
evaluates. Do not spend the remaining lab time repeatedly refreshing Azure
Monitor.

## Instructor demo (20 minutes)

### Action 5: Show the evidence chain

- **Purpose:** Preserve the learning outcome in the shorter delivery mode.
- **Navigation:** Send the exact Outlook request. Open the native dashboard,
  correlate its Response ID to the Trace ID, run the prepared scoped query, and
  open the retained fired alert.
- **Result:** The group sees one continuous chain from complaint to response,
  trace, version-scoped signal, alert and operational decision.
- **If it fails:** Label retained evidence **instructor demonstration** and name
  the failed live action. Do not claim that a failed live action produced it.
- **Save:** Finish on the response notes and exact future evaluation case.
- **Time:** 20 minutes.

## Close the cycle

The immediate workshop decision is to leave the agent running because it states
the limitation honestly. The tool owner must choose the product follow-on:
support Outlook directly or integrate an approved status provider, add a clear
escalation path, and define a production-quality signal. The team then evaluates
the exact regression case before the next release.

Participants keep local evidence until the invitation's retention date and then
delete it. The workshop organizer removes workshop alert rules and cloud
resources under the cleanup plan.
