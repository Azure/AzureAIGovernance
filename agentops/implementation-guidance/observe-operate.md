# AgentOps Observe and Operate Implementation Guidance

## Purpose and intended audience

This implementation guide helps implementation teams establish post-deployment
observability and operations for Microsoft Foundry agents. It is intended for
architects, agent engineers, site reliability and operations teams, service
owners, security teams, Responsible AI practitioners, support teams, and
implementation leads.

This module combines two distinct practices. **Observe** establishes the
telemetry, quality signals, traces, dashboards, and diagnostic evidence needed
to understand agent behavior and service health. **Operate** establishes the
ownership, alerting, incident response, maintenance, and improvement processes
needed to manage the service over time.

Use it to define operational outcomes and signals, select tooling, prepare
telemetry and response procedures, execute monitoring and operational readiness,
and establish a continuous improvement loop.

This is practical execution guidance. It is not a Statement of Work, a
commercial scope, a Definition of Use, or a detailed product runbook.

**On this page**

1. [Microsoft Foundry observability boundary](#microsoft-foundry-observability-boundary):
   Native and extended signals, quality evidence, and incident learning.
2. [Implementation outcomes](#implementation-outcomes): Capabilities and
   evidence established by the workstream.
3. [Implementation outline](#implementation-outline): Six-phase workflow from
   discovery through ownership transfer.
4. [Phase 1 - Discover operational outcomes and signals](#phase-1---discover-operational-outcomes-and-signals):
   Define service expectations, dependencies, risks, and operator decisions.
5. [Phase 2 - Select observability and operations tooling](#phase-2---select-observability-and-operations-tooling):
   Choose supported Foundry and Azure Monitor evidence paths.
6. [Phase 3 - Prepare telemetry, alerts, and runbooks](#phase-3---prepare-telemetry-alerts-and-runbooks):
   Instrument critical paths and prepare actionable response guidance.
7. [Phase 4 - Execute observability and operational readiness](#phase-4---execute-observability-and-operational-readiness):
   Test signal correlation, alerting, access, and response.
8. [Phase 5 - Operationalize continuous improvement](#phase-5---operationalize-continuous-improvement):
   Convert production evidence into evaluation and release improvements.
9. [Phase 6 - End the project and transfer knowledge](#phase-6---end-the-project-and-transfer-knowledge):
   Rehearse operations and transfer ownership.
10. [Roles and responsibilities](#roles-and-responsibilities): Accountabilities
    for service health, quality, safety, and response.
11. [Completion criteria](#completion-criteria): Conditions for accepting the
    workstream.
12. [Knowledge transfer and handoff checklist](#knowledge-transfer-and-handoff-checklist):
    Evidence required for operational handoff.
13. [References](#references): First-party Foundry, Azure Monitor, and AgentOps
    resources.

## Microsoft Foundry observability boundary

| Area | Guidance |
| --- | --- |
| Native operational view | Foundry traces and the preview Agent Monitoring Dashboard connected to Azure Monitor Application Insights |
| Extended telemetry | OpenTelemetry and Application Insights for application, model, tool, dependency, and custom operational signals |
| Quality in production | Preview recurring evaluation where supported, correlated with traces and agent versions |
| Incident learning | Reviewed trace and evaluation evidence promoted into regression coverage |
| AgentOps Accelerator | Foundry-specific reference for reading Foundry and Application Insights signals, readiness findings, and evidence packaging |

Preserve the native operational source, agent and version identity, retention,
and access model. Aggregate only the signals needed for operational decisions.

## Implementation outcomes

By the end of the workstream, the organization should have:

1. Operational outcomes, service objectives, and critical user journeys.
2. A signal catalog covering quality, safety, reliability, performance, cost,
   adoption, and business outcomes.
3. Telemetry, dashboards, alerts, and privacy controls appropriate to the
   selected platform.
4. Incident triage and runbook outlines linked to agent evidence.
5. A production-readiness and operational rehearsal record.
6. A process for turning production learning into evaluation and release
   improvements.
7. Named owners for platform, service, quality, safety, and support.

## Implementation outline

| Phase | Implementation question | Expected evidence |
| --- | --- | --- |
| 1. Discover outcomes and signals | What must operators know to protect users and business outcomes? | Operational charter, service objectives, signal catalog |
| 2. Select tooling | Which native and extended telemetry surfaces provide trustworthy, supportable evidence? | Tooling decision record, data-flow and access design |
| 3. Prepare telemetry, alerts, and runbooks | Is the agent diagnosable and are responders ready before production? | Instrumentation plan, dashboards, alert design, runbook outlines |
| 4. Execute observability and operations | Do signals arrive, alerts work, and responders resolve realistic failures? | Verification record, alert tests, incident rehearsal |
| 5. Operationalize continuous improvement | How will production learning change tests, controls, and releases? | Review cadence, feedback loop, prioritized improvements |
| 6. End the project and transfer knowledge | Can the designated teams operate the service without the implementation team? | Handoff pack, operator rehearsal, owner acceptance |

## Phase 1 - Discover operational outcomes and signals

### Objective

Define observability from organizational outcomes and operational decisions,
not from the list of available dashboards.

### Discovery questions

#### Outcomes and service expectations

- Which user and business outcomes must the agent achieve in production?
- Which journeys are critical, regulated, revenue-affecting, or safety-sensitive?
- What are acceptable availability, latency, error, completion, escalation, and
  recovery expectations?
- Which channels, languages, geographies, personas, and event triggers require
  separate monitoring?
- What is the expected traffic pattern, concurrency, seasonality, and growth?
- What is the support model and who owns the service outside business hours?

#### Agent behavior and dependencies

- Which models, tools, actions, child agents, knowledge sources, connectors, and
  external services are on the critical path?
- Which failures are visible to users and which can silently degrade quality?
- Which identity, permission, quota, capacity, network, or data freshness issues
  can change behavior?
- How are agent versions, source commits, solution versions, and environment
  identities represented in telemetry?

#### Quality, safety, and business signals

- Which quality dimensions should be monitored after deployment?
- What constitutes unsafe, disallowed, over-permissioned, or anomalous behavior?
- Which user feedback, reaction, outcome, abandonment, escalation, or task
  completion signals matter?
- Which signals require human review rather than automated interpretation?
- What cost or token behavior requires alerting or review?

#### Privacy and governance

- Which prompts, responses, tool arguments, transcripts, and identifiers may
  contain personal, confidential, or regulated data?
- What may be collected, sampled, redacted, exported, and retained?
- Who can view analytics, transcripts, traces, and raw content?
- Which evidence must be preserved for audit or incident response?

**Implementation resources**

- [Configure Foundry tracing security, privacy, content capture, retention, and cost](https://learn.microsoft.com/azure/foundry/observability/how-to/trace-agent-setup)
- [Restrict access to sensitive Log Analytics tables](https://learn.microsoft.com/azure/azure-monitor/logs/protected-tables-configure)

### Activities

1. Map critical journeys to service objectives and operator decisions.
2. Build a signal catalog across:
   - service health and availability;
   - latency and throughput;
   - model, tool, connector, and knowledge dependency health;
   - quality and safety;
   - user outcomes, adoption, and feedback;
   - consumption and cost;
   - release and version identity.
3. Classify each signal as symptom, cause, diagnostic context, or business
   outcome.
4. Define a target, warning level, critical condition, owner, review cadence, and
   response for each actionable signal.
5. Identify blind spots and unsupported expectations before implementation.

**Implementation resources**

- [Plan monitoring outcomes, signals, responsibilities, and response across an Azure estate](https://learn.microsoft.com/azure/cloud-adoption-framework/manage/monitor)
- [Review operational, quality, safety, and evaluation signals in Foundry](https://learn.microsoft.com/azure/foundry/concepts/observability)

### Expected outputs and evidence

- Operational charter and critical journey map
- Service objectives and error-budget principles where applicable
- Signal and dependency catalog
- Quality and safety monitoring requirements
- Data classification, access, retention, and redaction requirements
- Support and escalation model

## Phase 2 - Select observability and operations tooling

### Objective

Select the minimum set of native and extended tools needed to answer operational
questions and support incident response.

### Selection criteria

- Native platform visibility and supportability
- Required trace, session, transcript, dependency, and business context
- Telemetry latency and retention
- Query, dashboard, alert, and export needs
- Identity, role, and transcript access controls
- Data residency, privacy, and sensitive-content handling
- Cost, sampling, and ingestion limits
- Integration with incident, on-call, work-item, and release systems

**Implementation resources**

- [Manage resource, workspace, and table-level access to Log Analytics data](https://learn.microsoft.com/azure/azure-monitor/logs/manage-access)
- [Configure analytics and long-term retention for Log Analytics tables](https://learn.microsoft.com/azure/azure-monitor/logs/data-retention-configure)
- [Analyze Azure Monitor billing, telemetry usage, and cost](https://learn.microsoft.com/azure/azure-monitor/fundamentals/cost-usage)

### Microsoft Foundry implementation path

1. Use Foundry tracing to understand agent, model, and tool execution.
2. Connect the Foundry project to Application Insights for the Agent Monitoring
   Dashboard and Azure Monitor analysis.
3. Use OpenTelemetry instrumentation for custom application logic not captured
   by platform-side tracing.
4. Use scheduled or continuous evaluation where supported to add sampled quality
   and safety signals to production monitoring.
5. Use Azure Monitor alerts and organization-standard dashboards for actionable
   operational signals.
6. Treat the [AgentOps Accelerator](https://aka.ms/agentops-accelerator) as an
   optional **Foundry-specific** reference for reading Foundry/Application
   Insights evidence and producing readiness findings. It does not replace
   Azure Monitor or native Foundry capabilities.

**Implementation resources**

- [Connect Application Insights and enable Foundry agent tracing](https://learn.microsoft.com/azure/foundry/observability/how-to/trace-agent-setup)
- [Monitor agent operations and configure continuous evaluation](https://learn.microsoft.com/azure/foundry/observability/how-to/how-to-monitor-agents-dashboard)
- [Schedule cloud evaluations and evaluate production traces](https://learn.microsoft.com/azure/foundry/how-to/develop/cloud-evaluation)

### Expected outputs and evidence

- Tooling decision record and platform boundary
- Telemetry and analytics data-flow diagram
- Workspace, project, environment, and resource inventory
- Access and role model
- Sampling, retention, and cost decision
- Integration points with incident and release management

## Phase 3 - Prepare telemetry, alerts, and runbooks

### Objective

Make the agent diagnosable and prepare responders before production traffic
arrives.

### Telemetry preparation

1. Define stable service, agent, version, environment, conversation/session, and
   release identifiers.
2. Instrument the critical path across agent invocation, model calls, tool/action
   use, retrieval, connectors, and downstream dependencies where supported.
3. Capture status, duration, dependency outcome, usage, and safe business context.
4. Avoid placing secrets, access tokens, unnecessary prompts/responses, personal
   data, or sensitive tool payloads in telemetry.
5. Configure redaction, sampling, retention, access, and export controls.
6. Generate controlled traffic and verify end-to-end correlation before release.

**Implementation resources**

- [Connect Application Insights and instrument Microsoft Foundry agent tracing](https://learn.microsoft.com/azure/foundry/observability/how-to/trace-agent-setup)
- [Sample OpenTelemetry telemetry while preserving useful Application Insights diagnostics](https://learn.microsoft.com/azure/azure-monitor/app/opentelemetry-sampling)
- [Review the prompts, responses, tool interactions, and evaluation fields stored in AppGenAIContent](https://learn.microsoft.com/azure/azure-monitor/reference/tables/appgenaicontent)

### Dashboard preparation

Build role-oriented views rather than one universal dashboard:

- **Service owner:** availability, success, latency, volume, cost, and releases.
- **Agent engineer or maker:** failed sessions/runs, model and tool behavior,
  knowledge/retrieval issues, and version comparison.
- **Quality and Responsible AI:** evaluation trends, critical-scenario failures,
  safety signals, feedback, and escalation.
- **Support:** user-visible symptom, session/trace lookup, recent changes,
  dependency status, and escalation path.
- **Business owner:** adoption, completion, resolution, escalation, satisfaction,
  and value indicators.

**Implementation resources**

- [Interpret and configure the Foundry Agent Monitoring Dashboard](https://learn.microsoft.com/azure/foundry/observability/how-to/how-to-monitor-agents-dashboard)
- [Build interactive Azure Workbooks for role-specific operational views](https://learn.microsoft.com/azure/azure-monitor/visualize/workbooks-overview)

### Alert preparation

1. Alert only on conditions that require action.
2. Combine symptom and diagnostic context where possible.
3. Define severity, threshold, evaluation window, suppression, owner, and
   escalation.
4. Include links to the relevant dashboard, query, session/trace search, recent
   release, and runbook.
5. Distinguish no-traffic/no-data from healthy behavior.
6. Test access from the on-call identity, not only the implementer's account.

**Implementation resources**

- [Review how Azure Monitor evaluates signals and creates alert instances](https://learn.microsoft.com/azure/azure-monitor/alerts/alerts-overview)
- [Route notifications and trigger automated response with action groups](https://learn.microsoft.com/azure/azure-monitor/alerts/action-groups)

### Runbook outline preparation

Prepare concise decision guidance for:

- agent unavailable or elevated failure rate;
- latency or timeout increase;
- model, quota, or capacity issue;
- tool, connector, authentication, or permission failure;
- knowledge freshness, retrieval, or grounding regression;
- quality or safety signal degradation;
- unexpected cost or usage increase;
- release regression;
- telemetry silence or analytics delay;
- privacy, security, or harmful-output escalation.

Each outline should identify detection evidence, first checks, containment,
escalation, rollback or disablement options, communications, and the evidence to
preserve. Link to product runbooks rather than duplicating every product step in
this field guide.

**Implementation resources**

- [Design incident roles, escalation, communications, mitigation, recovery, and post-incident learning](https://learn.microsoft.com/azure/well-architected/operational-excellence/incident-response)

### Microsoft Foundry preparation

- Connect Application Insights to the Foundry project.
- Verify server-side traces and Agent Monitoring Dashboard data.
- Confirm Application Insights and Log Analytics access.
- Add client-side OpenTelemetry instrumentation for custom logic where needed.
- Define scheduled or continuous evaluation where supported and appropriate.

**Implementation resources**

- [Connect Foundry to Application Insights and validate trace ingestion](https://learn.microsoft.com/azure/foundry/observability/how-to/trace-agent-setup)
- [Configure operational, quality, safety, and red-teaming monitoring for agents](https://learn.microsoft.com/azure/foundry/observability/how-to/how-to-monitor-agents-dashboard)

### Expected outputs and evidence

- Instrumentation and correlation specification
- Verified telemetry sample
- Role-oriented dashboards
- Actionable alert catalog
- Runbook outlines and escalation matrix
- Privacy, access, sampling, and retention configuration record

## Phase 4 - Execute observability and operational readiness

### Objective

Verify that evidence is complete, alerts are actionable, and responders can
diagnose realistic failures.

### Execution activities

1. Generate representative traffic for critical journeys, failures, refusals,
   tool use, and dependency degradation.
2. Verify that every critical journey can be located by agent, version,
   environment, and session or trace identity.
3. Confirm dashboards distinguish success, failure, no-data, and delayed-data
   states.
4. Trigger alerts in a controlled environment and confirm routing, deduplication,
   acknowledgement, and context.
5. Run operational game days covering at least:
   - a release regression;
   - a dependency or permission failure;
   - a quality or safety concern;
   - telemetry silence.
6. Measure detection, triage, containment, and recovery time.
7. Confirm that responders can access necessary evidence without overbroad
   permissions.
8. Record gaps and repeat the rehearsal after remediation.

**Implementation resources**

- [Investigate agent traces and correlate Foundry evidence with Application Insights](https://learn.microsoft.com/azure/foundry/observability/how-to/trace-agent-setup)
- [Organize alert-driven investigation, automation, and responder access in Azure Monitor](https://learn.microsoft.com/azure/azure-monitor/alerts/alerts-overview)
- [Rehearse incident detection, response, recovery, and review](https://learn.microsoft.com/azure/well-architected/operational-excellence/incident-response)

### Microsoft Foundry evidence

- Foundry trace and agent version
- Application Insights operation/trace identity
- Agent Monitoring Dashboard and relevant Azure Monitor query
- Evaluation result or continuous-evaluation evidence when used
- Release identity and deployment timestamp

### Expected outputs and evidence

- End-to-end telemetry verification record
- Dashboard and query validation
- Alert delivery and actionability results
- Game-day timeline and findings
- Updated runbook outlines
- Operational readiness decision

## Phase 5 - Operationalize continuous improvement

### Objective

Use production evidence to improve the agent, evaluation coverage, release
controls, and operating practice.

### Activities

1. Establish daily, weekly, monthly, and release-based review cadences according
   to signal urgency.
2. Review trends by agent and release version, channel, user journey, language,
   tool, and dependency.
3. Sample and human-review quality or safety cases according to approved privacy
   rules.
4. Promote reviewed incidents, failed traces, user feedback, and edge cases into
   maintained evaluation datasets.
5. Link improvements to the originating evidence and verify them with the same
   regression case.
6. Tune alerts when they are noisy, late, unactionable, or blind to meaningful
   failures.
7. Review telemetry cost, sampling, retention, and access.
8. Review platform changes, preview status, deprecations, model changes,
   connector changes, and policy updates.
9. Conduct periodic service reviews across product, engineering, operations,
   quality, safety, and business stakeholders.

**Implementation resources**

- [Review operational, token, quality, safety, and red-teaming trends in Foundry](https://learn.microsoft.com/azure/foundry/observability/how-to/how-to-monitor-agents-dashboard)
- [Tune OpenTelemetry sampling as traffic and diagnostic needs change](https://learn.microsoft.com/azure/azure-monitor/app/opentelemetry-sampling)
- [Analyze and optimize Azure Monitor ingestion and retention cost](https://learn.microsoft.com/azure/azure-monitor/fundamentals/cost-usage)

### Microsoft Foundry improvement loop

Review traces and monitoring, convert approved production evidence into
evaluation coverage, rerun Foundry evaluations, and feed the results into
release gates.

**Implementation resources**

- [Evaluate sampled production traces and schedule recurring Foundry evaluations](https://learn.microsoft.com/azure/foundry/how-to/develop/cloud-evaluation)
- [Use Foundry Insights to turn production trace patterns into improvement evidence](https://learn.microsoft.com/azure/foundry/observability/how-to/agent-insights)

### Expected outputs and evidence

- Continuous improvement backlog with evidence links
- Production-derived regression cases
- Trend and service review record
- Alert and dashboard tuning history
- Updated quality, safety, and operational thresholds
- Retired or remediated blind spots

## Phase 6 - End the project and transfer knowledge

### Objective

Ensure designated teams can monitor, diagnose, respond, and improve independently.

### Knowledge transfer activities

1. Walk through the operational charter, signal catalog, data flow, and platform
   boundaries.
2. Demonstrate trace/session lookup from an alert through likely root cause and
   release identity.
3. Have designated operators run a game-day scenario using
   organization-managed access.
4. Review privacy, transcript, trace, and sensitive-data handling.
5. Review recurring service, quality, safety, cost, and access reviews.
6. Transfer dashboards, queries, alerts, runbook outlines, and evaluation links.
7. Record ownership, support paths, escalation contacts, and next review dates.

**Implementation resources**

- [Transfer monitoring ownership through explicit scope, responsibilities, processes, and review practices](https://learn.microsoft.com/azure/cloud-adoption-framework/manage/monitor)
- [Assign least-privilege access to Log Analytics evidence](https://learn.microsoft.com/azure/azure-monitor/logs/manage-access)
- [Document and rehearse the incident management process that operators inherit](https://learn.microsoft.com/azure/well-architected/operational-excellence/incident-response)

## Roles and responsibilities

| Role | Primary responsibilities |
| --- | --- |
| Product or service owner | Defines service outcomes, priorities, and operational acceptance |
| Agent engineer | Maintains instrumentation context, diagnoses behavior, and implements fixes |
| Platform/observability engineer | Owns telemetry resources, dashboards, alerts, access, retention, and cost controls |
| Operations or SRE lead | Owns on-call, incident process, game days, reliability reviews, and runbooks |
| Support lead | Triage user reports, collect evidence, and escalate with session/release context |
| Evaluation and quality lead | Maintains production quality measures and regression coverage |
| Responsible AI and safety lead | Reviews safety signals, harmful-output escalations, and adversarial learning |
| Security, privacy, and compliance | Approves data collection, access, retention, export, and incident evidence |
| Business owner | Reviews adoption, outcomes, satisfaction, and value indicators |
| Implementation lead | Coordinates the workflow, demonstrates supported paths, manages dependencies, and transfers knowledge |

Incident command, production changes, and risk acceptance remain organizational
responsibilities.

## Completion criteria

The Observe and Operate workstream is complete when:

- Critical journeys, service objectives, dependencies, and actionable signals
  are documented.
- The Foundry observability path and data boundaries are explicit.
- Telemetry, analytics, dashboards, and alerts are verified with controlled
  traffic.
- Sensitive-data, access, sampling, retention, and export controls are approved.
- Alerts link to actionable evidence and response guidance.
- Operators have completed realistic failure and telemetry-silence rehearsals.
- Production learning has a defined path into evaluation and release controls.
- Designated owners have accepted dashboards, alerts, runbook outlines, and review
  cadences.

## Knowledge transfer and handoff checklist

- [ ] Operational charter, objectives, and signal catalog transferred
- [ ] Platform-specific telemetry and analytics boundaries documented
- [ ] Agent, version, release, and session/trace correlation demonstrated
- [ ] Dashboards, queries, and alert ownership transferred
- [ ] Analytics, transcript, Application Insights, and Log Analytics roles reviewed
- [ ] Sensitive-data, sampling, retention, and export controls documented
- [ ] Alert delivery and escalation paths tested with approved operator identities
- [ ] Runbook outlines and rollback/containment paths rehearsed
- [ ] Quality and safety escalation procedures accepted
- [ ] Production-to-regression feedback loop demonstrated
- [ ] Service review cadence and named owners recorded
- [ ] Open blind spots, risks, and backlog accepted

## References

### AgentOps references

- [AgentOps Accelerator](https://aka.ms/agentops-accelerator) - Foundry-specific
  reference implementation
- [AgentOps Accelerator: Foundry operations workbook](https://azure.github.io/agentops/foundry-ops-workbook/)
- [AgentOps Accelerator: Operate](https://azure.github.io/agentops/operate/)

### Microsoft Foundry and Azure Monitor

- [Observability in generative AI](https://learn.microsoft.com/azure/foundry/concepts/observability)
- [Set up tracing in Microsoft Foundry](https://learn.microsoft.com/azure/foundry/observability/how-to/trace-agent-setup)
- [Monitor agents with the Agent Monitoring Dashboard](https://learn.microsoft.com/azure/foundry/observability/how-to/how-to-monitor-agents-dashboard)
- [Run cloud and trace evaluations](https://learn.microsoft.com/azure/foundry/how-to/develop/cloud-evaluation)
- [Application Insights overview](https://learn.microsoft.com/azure/azure-monitor/app/app-insights-overview)
- [Azure Monitor alerts overview](https://learn.microsoft.com/azure/azure-monitor/alerts/alerts-overview)
