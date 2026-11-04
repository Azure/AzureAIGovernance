# AgentOps Evaluate Implementation Guidance

## Purpose and intended audience

This implementation guide helps architects, engineers, makers, data scientists, Responsible AI
practitioners, operations teams, and implementation leads establish a repeatable
evaluation practice for AI agents built with Microsoft Foundry. It covers the
full journey from defining what good looks like and selecting the right
evaluation approach to preparing test data, interpreting results, and
establishing operational ownership.

> Throughout this guide, a help desk agent is used as an end-to-end example. The
> implementation uses Microsoft Foundry to establish quality and safety
> measures, governed test data, repeatable evaluation runs, release evidence,
> tracing, and ongoing evaluation.

**On this page**

1. [Implementation outcomes](#implementation-outcomes): Capabilities and
   evidence established by the workstream.
2. [Implementation outline](#implementation-outline): Six-phase workflow from
   discovery through ownership transfer.
3. [Phase 1 - Discover evaluation outcomes and risks](#phase-1---discover-evaluation-outcomes-and-risks):
   Define success, critical journeys, risks, and decision rules.
4. [Phase 2 - Select evaluation methods and tooling](#phase-2---select-evaluation-methods-and-tooling):
   Choose supported Foundry capabilities and required controls.
5. [Phase 3 - Prepare evaluation data and controls](#phase-3---prepare-evaluation-data-and-controls):
   Build governed test sets, mappings, thresholds, and run configuration.
6. [Phase 4 - Execute evaluation and release gates](#phase-4---execute-evaluation-and-release-gates):
   Run the identified candidate, analyze failures, and record a decision.
7. [Phase 5 - Operationalize ongoing evaluation](#phase-5---operationalize-ongoing-evaluation):
   Establish recurring triggers, triage, and production feedback.
8. [Phase 6 - End the project and transfer knowledge](#phase-6---end-the-project-and-transfer-knowledge):
   Rehearse the process and transfer ownership.
9. [Roles and responsibilities](#roles-and-responsibilities): Accountabilities
   for evaluation design, operation, and acceptance.
10. [Completion criteria](#completion-criteria): Conditions for accepting the
    workstream.
11. [Knowledge transfer and handoff checklist](#knowledge-transfer-and-handoff-checklist):
    Evidence required for operational handoff.
12. [References](#references): First-party Foundry and AgentOps resources.

## Implementation outcomes

By the end of the workstream, the following outcomes should be in place:

1. A clear evaluation plan.
2. Selected metrics and tests for quality, safety, and Responsible AI.
3. A versioned test set with representative scenarios.
4. Evaluation tools, access, and permissions configured.
5. A repeatable evaluation workflow, automated where appropriate.
6. A baseline with thresholds, findings, and improvement actions.
7. Ongoing evaluation configured and owned.

## Implementation outline

| Phase | Implementation question | Expected evidence |
| --- | --- | --- |
| 1. Discover outcomes and risks | What should be evaluated, and which results affect release or risk decisions? | Evaluation charter, scenario inventory, measure contracts |
| 2. Select methods and tooling | Which supported methods provide trustworthy, maintainable evidence? | Tooling decision record, Foundry architecture, prerequisites |
| 3. Prepare data and controls | Are the test sets, mappings, thresholds, identities, and environments ready? | Approved datasets, coverage summary, run configuration, readiness record |
| 4. Execute evaluation and gates | Did the identified candidate meet the approved criteria? | Run record, row-level evidence, findings, release decision |
| 5. Operationalize evaluation | When will evaluation run again, and what happens when evidence is missing or fails? | Trigger matrix, triage workflow, production feedback process |
| 6. End the project and transfer knowledge | Can designated owners maintain and operate the evaluation practice? | Handoff pack, rehearsal, owner acceptance |

## Phase 1 - Discover evaluation outcomes and risks

![A cartoon robot uses a ruler and clipboard to plan what good looks like before testing.](assets/evaluation-phase-1-plan.svg)

### Objective

Translate the use case into measurable expectations. Start with business
outcomes and user journeys, then identify the agent behaviors and risks that can
affect those outcomes.

### Discovery questions

#### Use case and users

| Question | Example |
| --- | --- |
| What outcome should the agent improve? | Employees resolve common password, VPN, and software questions in Teams. Unresolved requests reach the correct support queue with the conversation context attached. |
| Which user journeys matter most? | The first release covers password resets, VPN connection problems, and approved software requests. Hardware failures are routed directly to the help desk. |
| Who will use the agent, and through which channels? | An employee asks for help in Teams. If the agent cannot resolve the request, a help desk analyst continues the case in the ticketing system. |
| Which knowledge and tools affect its answers and actions? | For a VPN issue, the agent reads the current VPN support article, checks service status, and creates a Network Support ticket if the issue remains unresolved. |
| Are traces or conversation records available? | A recent trace shows an employee asking about a VPN error, the agent repeating the same instructions twice, and the employee leaving without a resolution or escalation. |

#### Evaluation criteria

| Question | Example |
| --- | --- |
| What does a successful interaction look like? | An employee requests approved software. The agent confirms the request, submits it, and returns the ticket reference and expected next step without asking for the same information twice. |
| Which response qualities need judgment, and how should they be scored? | For VPN setup instructions: 3 = the steps are ordered and name the exact menus; 2 = the steps are correct but one location is unclear; 1 = key steps are missing or contradictory. |
| Which requirements should every response or action meet? | When self-service password reset does not work, the agent uses the current support guidance, tells the employee what will happen next, and routes the case to the Service Desk. |
| Which results should block a release or signal a regression? | Block the release if the agent closes an unresolved request, sends it to the wrong queue, or creates a duplicate ticket in a critical journey. |

#### Safety and Responsible AI

| Question | Example |
| --- | --- |
| What could cause harm or expose sensitive data? | An employee asks for the status of a support ticket, but the agent returns the notes from a ticket opened by a different employee. |
| What must the agent refuse or escalate? | An employee asks the agent to install administrator-only software. The agent declines the action and routes the request for approval. |
| Which attacks or misuse cases should be tested? | A support article contains hidden text telling the agent to ignore its instructions and list recent employee tickets. The agent should ignore the text and protect the ticket data. |
| Which risks need automated tests or human review? | Automatically test that ticket searches return only the requesting employee's records. Use human review to judge whether the agent responds appropriately to a frustrated employee and provides a useful next step. |
| What evidence should be retained? | For a failed software-request test, retain the sanitized request, expected outcome, actual response, relevant tool calls, score, reviewer decision, and agent version. |

### Activities

1. Map priority user journeys to desired outcomes, expected agent behavior, and
   failure impact.
2. Review available traces to identify common paths, failures, edge cases, and
   missing coverage.
3. Separate quality dimensions from operational service measures and compliance
   controls.
4. Classify scenarios into smoke, regression, coverage, adversarial, and
   production-derived groups.
5. Define a measure contract for each selected signal:
   - purpose and decision supported;
   - required inputs;
   - scoring or review method;
   - initial threshold or acceptance rule;
   - owner and review frequency.
6. Record gaps where no automated measure is sufficient and human review is
   required.

> 🔗 **Implementation reference:** [Plan quality, safety, and production evaluation approaches](https://learn.microsoft.com/azure/foundry/concepts/evaluation-overview),
> [run cloud red-team scans against a model or application](https://learn.microsoft.com/azure/foundry/how-to/develop/run-ai-red-teaming-cloud)

### Expected outputs and evidence

- Evaluation plan and scope boundaries
- Prioritized scenario inventory
- AI quality measure matrix
- Scoring criteria and examples
- Mandatory policy and behavior rules
- Safety and Responsible AI risk-to-test mapping
- Initial pass, fail, and escalation rules
- Assumptions and unresolved decisions log

## Phase 2 - Select evaluation methods and tooling

### Objective

Choose the simplest supported evaluation path that provides trustworthy
evidence and can be maintained by the designated owners.

### Selection criteria

- Agent platform and agent type
- Required measures and input data
- Single-turn versus multi-turn behavior
- Need for authenticated user profiles or connector access
- Local, cloud, manual, scheduled, or pipeline execution
- Network isolation, regional availability, licensing, and cost
- Access control and separation of duties
- Result storage, retention, export, and audit requirements
- Integration with source control, release gates, and incident management

### Microsoft Foundry implementation path

1. Select built-in evaluators that match the scenario and available inputs.
   Consider general quality, retrieval-augmented generation (RAG), agent
   behavior, safety, and operational measures only when their required data is
   available.
2. Use custom evaluators for domain-specific expectations that built-in measures
   cannot represent. Define a clear rubric and calibrate it with human-reviewed
   examples.
3. Choose portal or SDK execution based on scale, repeatability, and integration
   needs. Cloud evaluation is the preferred path for scalable preproduction and
   CI/CD scenarios.
4. Connect tracing and Application Insights when production traces will inform
   evaluation or root-cause analysis.
5. Treat the [AgentOps Accelerator](https://aka.ms/agentops-accelerator) as an
   optional **Foundry-specific** reference implementation for repo-side gates,
   safety checks, baselines, and evidence packs. It is not the product contract
   and does not replace native Foundry evaluation capabilities.

> 🔗 **Implementation reference:** [Choose built-in evaluators and their required inputs](https://learn.microsoft.com/azure/foundry/concepts/built-in-evaluators),
> [create rubric-based custom evaluators](https://learn.microsoft.com/azure/foundry/concepts/evaluation-evaluators/custom-evaluators),
> [configure and run repeatable cloud evaluations](https://learn.microsoft.com/azure/foundry/observability/how-to/cloud-evaluation)

> 🔗 **Implementation reference:** [Connect Application Insights and instrument agent tracing](https://learn.microsoft.com/azure/foundry/observability/how-to/trace-agent-setup)

### Expected outputs and evidence

- Tooling decision record with rejected alternatives
- Foundry evaluation architecture and execution path
- Access, role, connection, licensing, region, and cost prerequisites
- Data handling and result retention decision
- Automation and release integration decision

## Phase 3 - Prepare evaluation data and controls

### Objective

Create representative, governed test evidence and prepare a reproducible run
before applying release criteria.

### Dataset and test-set preparation

1. Start from approved user journeys, reviewed traces, known failures, support
   cases, subject matter expert examples, and synthetic edge cases.
2. Include normal, boundary, negative, refusal, escalation, multilingual, and
   adversarial cases in proportion to business risk.
3. Capture only the fields needed by the selected methods, such as:
   - user input or conversation;
   - expected answer or expected behavior;
   - source context or grounding evidence;
   - expected tools or actions;
   - persona, language, channel, and risk tags;
   - reviewer decision and rationale.
4. Remove or protect secrets, credentials, personal data, and production content
   that is not approved for evaluation.
5. Version the data and record provenance, approvals, known limitations, and the
   agent version or configuration it validates.
6. Keep a small smoke set for fast feedback and a broader regression set for
   release confidence.
7. In Microsoft Foundry, traces can be converted into an evaluation dataset
   where the preview capability is available. Review, redact, label, and approve
   the generated cases before adding them to a maintained test set.

> 🔗 **Implementation reference:** [Create and manage versioned evaluation datasets](https://learn.microsoft.com/azure/foundry/observability/how-to/evaluation-datasets),
> [convert reviewed agent traces into evaluation datasets](https://learn.microsoft.com/azure/foundry/observability/how-to/traces-to-dataset),
> [understand how Foundry processes and protects model data](https://learn.microsoft.com/azure/foundry/responsible-ai/openai/data-privacy)

### Run and gate preparation

1. Map dataset fields to the selected evaluator and target inputs.
2. Identify the exact agent version, environment, model, tools, knowledge
   configuration, and source revision under evaluation.
3. Configure organization-managed identities, connections, roles, and result
   storage.
4. Define thresholds, critical-case rules, human-review rules, and the authority
   that can approve an exception.
5. Define invalid-run behavior. Missing scores, unavailable dependencies,
   incomplete outputs, or mapping errors must block the affected decision rather
   than appear as a pass.
6. Run a small readiness sample to validate mappings, permissions, evaluator
   behavior, result retention, and trace correlation.

> 🔗 **Implementation reference:** [Assign the permissions required for evaluation workflows](https://learn.microsoft.com/azure/foundry/observability/how-to/evaluation-permissions)

### Expected outputs and evidence

- Approved evaluation dataset and data dictionary
- Scenario coverage and risk mapping
- Evaluator and target configuration
- Threshold, critical-case, and human-review rules
- Identity, connection, and result-retention record
- Readiness sample and resolved preparation findings

## Phase 4 - Execute evaluation and release gates

### Objective

Execute the approved evaluation against an identified candidate, interpret the
evidence, and record the decision supported by the run.

### Execution activities

1. Calibrate AI-assisted measures against human-reviewed examples. Investigate
   systematic disagreement before using a score as a gate.
2. Run the approved baseline against the identified agent version and
   environment.
3. Review aggregate scores and row-level evidence. Cluster failures by likely
   cause, such as instructions, retrieval, tool use, knowledge, safety controls,
   permissions, or test design.
4. Distinguish agent defects from evaluator, dataset, environment, or dependency
   failures.
5. Apply aggregate thresholds, critical-case rules, required human review, and
   exception policy.
6. Assign remediation owners and rerun the same versioned set after changes.
7. Preserve the run identity, agent identity, dataset/test-set version, methods,
   thresholds, results, exceptions, and approval decision.

> 🔗 **Implementation reference:** [Run agent evaluations and integrate acceptance thresholds into delivery workflows](https://learn.microsoft.com/azure/foundry/observability/how-to/evaluate-agent#integrate-into-your-workflow),
> [inspect aggregate metrics and row-level evaluation results](https://learn.microsoft.com/azure/foundry/how-to/evaluate-results)

### Microsoft Foundry evidence

- Foundry project and agent version
- Evaluator names and versions
- Dataset name and version
- Evaluation run identity
- Threshold and release decision
- Trace or response IDs where used

### Expected outputs and evidence

- Reproducible baseline run
- Aggregate and row-level evidence
- Failure analysis and prioritized remediation backlog
- Recorded ship, no-ship, or conditional decision
- Approved exception record with owner and expiry when applicable

## Phase 5 - Operationalize ongoing evaluation

### Objective

Turn evaluation from a one-time activity into a maintained quality and safety
feedback loop.

### Activities

1. Define triggers for recurring evaluation where the preview capability is available:
   - prompt, instruction, model, knowledge, tool, connector, or policy change;
   - pull request or release candidate;
   - scheduled regression run;
   - production quality, safety, latency, or error signal;
   - incident, complaint, escalation, or new misuse pattern.
2. Define the production sampling and review policy. Include privacy, consent,
   data minimization, retention, and human-review requirements.
3. Assign owners for test-set curation, evaluator maintenance, failed-run triage,
   safety review, and release decisions.
4. Establish a controlled process for promoting reviewed production cases into
   the regression set.
5. Track score trends by agent version and investigate changes in both aggregate
   and critical-scenario results.
6. Define failure behavior for automation. A missing score, inaccessible
   dependency, or incomplete run must not appear as a passing evaluation.
7. Review thresholds periodically as coverage, usage patterns, and risk evolve.

> 🔗 **Implementation reference:** [Configure telemetry retention for the Log Analytics workspace](https://learn.microsoft.com/azure/azure-monitor/logs/data-retention-configure)

### Microsoft Foundry considerations

- Use scheduled or continuous evaluation where supported and appropriate.
- Enable tracing and retain the identifiers needed to connect agent behavior,
  evaluation results, and active versions.
- Use reviewed traces to generate or refresh evaluation datasets where the
  preview capability is available.
- Correlate evaluation results with traces to investigate agent, model, tool, and
  retrieval behavior.
- Use Application Insights and the Foundry monitoring dashboard for production
  operational and evaluation signals.
- If the AgentOps Accelerator is adopted, keep it in the Foundry track and
  document which Accelerator artifacts are authoritative for the release
  process.

> 🔗 **Implementation reference:** [Monitor agent quality and configure continuous evaluation](https://learn.microsoft.com/azure/foundry/observability/how-to/how-to-monitor-agents-dashboard#set-up-continuous-evaluation)

### Expected outputs and evidence

- Evaluation cadence and trigger matrix
- Automation or recurring-run design
- Production sampling and privacy rules
- Triage workflow and service-level expectations
- Regression-set promotion process
- Trend review and threshold governance schedule

## Phase 6 - End the project and transfer knowledge

### Objective

Ensure the designated owners can run, interpret, maintain, and improve the
evaluation system.

### Knowledge transfer activities

1. Walk through the evaluation plan, measure rationale, Foundry path, and
   known limitations.
2. Demonstrate one complete run from data selection through decision and defect
   triage.
3. Have the designated owners execute a run and explain the result
   independently.
4. Review how to add, approve, retire, and version test cases.
5. Review safety escalation, privacy, and human-review procedures.
6. Assign access through managed groups and workload identities rather than
   personal accounts.
7. Record the next evaluation review date and the backlog owner.

> 🔗 **Implementation reference:** [Apply least-privilege Foundry role assignments](https://learn.microsoft.com/azure/foundry/concepts/rbac-foundry),
> [configure authentication for users and workload identities](https://learn.microsoft.com/azure/foundry/concepts/authentication-authorization-foundry)

## Roles and responsibilities

| Role | Primary responsibilities |
| --- | --- |
| Product owner | Defines business outcomes, critical journeys, and acceptance decisions |
| Business/domain subject matter expert | Supplies representative scenarios and validates expected behavior |
| Agent engineer | Identifies agent versions, implements fixes, and supports reproducible runs |
| Evaluation lead or data scientist | Designs measures, datasets, calibration, analysis, and trend review |
| Responsible AI or safety lead | Owns harm analysis, safety test strategy, exceptions, and escalation |
| Security, privacy, and compliance | Approves data use, retention, access, and regulated controls |
| Platform administrator | Provides environments, roles, connections, APIs, and operational prerequisites |
| Operations owner | Triages recurring failures and feeds production evidence into regression coverage |
| Implementation lead | Coordinates the workflow, demonstrates supported paths, manages dependencies, and transfers knowledge |

Use a RACI or equivalent ownership record when one person holds multiple roles.
Release acceptance and risk acceptance remain with the accountable
organizational owners.

## Completion criteria

The evaluation workstream is complete when:

- Business outcomes, critical scenarios, quality dimensions, and safety risks are
  documented and approved.
- The selected Foundry evaluation path and its capability boundaries are clear.
- The dataset is representative, versioned, access-controlled, and
  approved for use.
- The baseline run is reproducible and tied to an identified agent version.
- Thresholds, review rules, and handling of missing or invalid results are
  documented.
- Release decisions apply aggregate thresholds, critical-case rules, required
  human review, and authorized exceptions.
- Findings have owners and agreed next actions.
- Recurring evaluation triggers, ownership, and production feedback are defined.
- Designated owners have demonstrated that they can run and interpret the
  process.

## Knowledge transfer and handoff checklist

- [ ] Evaluation plan and measure matrix transferred
- [ ] Scenario inventory and risk-to-test mapping transferred
- [ ] Dataset/test-set source, version, ownership, and access documented
- [ ] Baseline run and decision evidence archived in the designated system of record
- [ ] Evaluator/test-method rationale and limitations documented
- [ ] Safety and Responsible AI review path documented
- [ ] Automation identities, permissions, and connections assigned to designated owners
- [ ] Failed-run and regression triage process rehearsed
- [ ] Production-to-regression promotion process documented
- [ ] Named operational owner and next review date recorded
- [ ] Open decisions, technical debt, and backlog items accepted

## References

### AgentOps references

- [AgentOps Accelerator: Evaluation](https://azure.github.io/agentops/evaluation/)
