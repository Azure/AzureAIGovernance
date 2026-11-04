# AgentOps Ship Implementation Guidance

## Purpose and intended audience

This implementation guide helps implementation teams establish a controlled,
repeatable release path for Microsoft Foundry agents. It is intended for
architects, agent engineers, platform engineers, release managers, security
teams, testers, operations teams, and implementation leads.

Use it to discover the release topology and controls, select supported platform
and automation tools, prepare source and environments, execute release gates and
promotion, operationalize releases, and transfer ownership.

This is practical execution guidance. It is not a Statement of Work, a
commercial scope, a Definition of Use, or a step-by-step product runbook.

**On this page**

1. [Microsoft Foundry release boundary](#microsoft-foundry-release-boundary):
   Release units, environments, automation, and native evidence.
2. [Implementation outcomes](#implementation-outcomes): Capabilities and
   evidence established by the workstream.
3. [Implementation outline](#implementation-outline): Six-phase workflow from
   discovery through ownership transfer.
4. [Phase 1 - Discover release topology and controls](#phase-1---discover-release-topology-and-controls):
   Define the release unit, environments, controls, and decisions.
5. [Phase 2 - Select tools and the platform path](#phase-2---select-tools-and-the-platform-path):
   Choose supported Foundry deployment and automation mechanisms.
6. [Phase 3 - Prepare source, versioning, and environments](#phase-3---prepare-source-versioning-and-environments):
   Establish reproducibility, identities, dependencies, and readiness.
7. [Phase 4 - Execute the pipeline and release gates](#phase-4---execute-the-pipeline-and-release-gates):
   Promote the identified candidate through required controls.
8. [Phase 5 - Operationalize release management](#phase-5---operationalize-release-management):
   Establish observation windows, recovery, and release learning.
9. [Phase 6 - End the project and transfer knowledge](#phase-6---end-the-project-and-transfer-knowledge):
   Rehearse the release path and transfer ownership.
10. [Roles and responsibilities](#roles-and-responsibilities): Accountabilities
    for engineering, approval, release, and operation.
11. [Completion criteria](#completion-criteria): Conditions for accepting the
    workstream.
12. [Knowledge transfer and handoff checklist](#knowledge-transfer-and-handoff-checklist):
    Evidence required for operational handoff.
13. [References](#references): First-party Foundry and AgentOps resources.

## Microsoft Foundry release boundary

| Area | Guidance |
| --- | --- |
| Release unit | Identified agent source and configuration, infrastructure definition, agent version, model and tool dependencies, and evaluation evidence |
| Environment model | Separate Foundry projects, Azure resources, or governed environments for development, test, and production |
| Deployment automation | Azure Developer CLI, GitHub Actions, Azure Pipelines, or organization-standard Azure deployment tooling supported by the agent type |
| Quality gate | Foundry evaluation, safety checks, functional smoke checks, and authorized approval |
| AgentOps Accelerator | Foundry-specific reference for repository-side evaluation gates, readiness checks, and release evidence |

Keep the exact source, configuration, agent version, dependencies, evaluation
evidence, and target environment traceable through the release. AgentOps
Accelerator evidence supplements native Foundry and pipeline records; it does
not replace them.

## Implementation outcomes

By the end of the workstream, the organization should have:

1. An approved release topology and environment promotion path.
2. A defined release unit, version identity, and source-of-truth strategy.
3. Organization-managed automation identities, permissions, and secrets management.
4. A pipeline or controlled release procedure with explicit quality, safety,
   security, and approval gates.
5. Evidence that the evaluated candidate is the candidate promoted.
6. A rollback, hotfix, and post-release verification approach.
7. Release operations ownership, documentation, and knowledge transfer.

## Implementation outline

| Phase | Implementation question | Expected evidence |
| --- | --- | --- |
| 1. Discover topology and controls | What is released, through which environments, under which controls? | Release topology, control matrix, release-unit definition |
| 2. Select tools and platform path | Which supported tools fit the agent type, engineering model, and governance needs? | Tooling decision record, architecture, prerequisites |
| 3. Prepare source, versioning, and environments | Can the candidate and its dependencies be reproduced and promoted safely? | Source baseline, version contract, environment readiness report |
| 4. Execute pipeline and gates | Did the identified candidate pass required checks and reach the intended target? | Pipeline record, gate evidence, approval, deployment verification |
| 5. Operationalize release management | Can designated teams detect, reverse, and learn from release outcomes? | Runbook outline, rollback test, release metrics and ownership |
| 6. End the project and transfer knowledge | Can designated teams operate the release path independently? | Handoff pack, rehearsal, owner acceptance |

## Phase 1 - Discover release topology and controls

### Objective

Define the release system before selecting pipeline tools. Make the release unit,
environments, evidence, approvals, and failure behavior explicit.

### Discovery questions

#### Release unit and dependencies

- Is the target a Foundry prompt agent, hosted agent, workflow, or combination?
- Which artifacts can change independently: instructions, code, knowledge,
  tools, actions, connections, child agents, models, policies, or
  infrastructure?
- Where is the source of truth for each artifact?
- Which dependencies are versioned, externally managed, or configured after
  deployment?
- How will a release identify the exact agent configuration and commit or
  solution version that was evaluated?

#### Environments and promotion

- Which development, integration, test, preproduction, and production
  environments exist?
- Are environments isolated by subscription, resource group, Foundry project,
  tenant, region, or network?
- Is promotion immutable, rebuilt from source, or manually reconfigured?
- Which knowledge sources, connections, endpoints, environment variables, and
  policies differ by environment?
- Which channels or user rings receive a release first?

#### Controls and decisions

- Which tests, evaluations, safety checks, static checks, and smoke tests block
  promotion?
- Which controls require human approval or separation of duties?
- Who can deploy, approve, roll back, or accept an exception?
- What evidence is required for audit, change management, and incident response?
- What must happen when a metric is missing, an evaluation fails to complete, or
  a dependency is unavailable?
- What are the rollback time objective and maximum acceptable release impact?

### Activities

1. Map source change through build, evaluation, approval, deployment,
   verification, and rollback.
2. Define the release unit and immutable identity carried through every stage.
3. Identify all environment-specific values and post-deployment actions.
4. Create a control matrix with required evidence, gate behavior, owner, and
   exception authority.
5. Identify compliance, network, data residency, identity, and change-management
   constraints.
6. Define the minimum viable release path before adding advanced rings,
   schedules, or orchestration.

### Expected outputs and evidence

- Release topology diagram
- Release-unit and version identity definition
- Environment and dependency inventory
- Promotion and approval model
- Release control matrix
- Failure, exception, rollback, and hotfix principles

## Phase 2 - Select tools and the platform path

### Objective

Select supported release mechanisms that align with the target platform,
available skills, source-control system, and governance model.

### Selection criteria

- Agent type and supported deployment mechanism
- Organization source-control and pipeline standards
- Required environment isolation and approval workflows
- Identity model and secretless authentication options
- Infrastructure-as-code requirements
- Evaluation and safety integration
- Audit evidence and retention
- Rollback and deployment-ring support
- Preview feature tolerance and operational support model

### Microsoft Foundry implementation path

1. Use the deployment and versioning mechanism supported by the agent type.
   Hosted-agent projects can use Azure Developer CLI and generated CI/CD
   integration; other Foundry agent types may use portal, SDK, or approved
   automation patterns documented for that type.
2. Use federated workload identity or another approved secretless
   pattern for pipelines. Grant least privilege at the correct Foundry and Azure
   scopes.
3. Store environment configuration outside source when it contains secrets.
   Keep non-secret deployment configuration versioned and reviewable.
4. Integrate evaluation after the candidate is available and before promotion.
5. Optionally use the
   [AgentOps Accelerator](https://aka.ms/agentops-accelerator) as a
   **Foundry-specific** reference for repository-side gates and evidence. Confirm
   that its branch and environment assumptions fit the operating model rather
   than adopting them unchanged.

### Expected outputs and evidence

- Tooling decision record
- Foundry release architecture
- Pipeline identity and permission model
- Source control and artifact retention decision
- Preview, licensing, region, and support constraints

## Phase 3 - Prepare source, versioning, and environments

### Objective

Make releases reproducible and ensure target environments are ready before the
first pipeline execution.

### Source and version preparation

1. Inventory all source-controlled and externally managed agent components.
2. Define the canonical version identity:
   - repository commit;
   - agent name and version;
   - deployment artifact identity; and
   - infrastructure and configuration version.
3. Protect main and release branches according to organizational policy.
4. Require review for instructions, prompts, tools, knowledge configuration,
   safety controls, and infrastructure changes.
5. Keep evaluation data, gate configuration, and release evidence versioned or
   linked to an immutable storage record.
6. Define dependency pinning and provenance for packages, images, models, custom
   connectors, and external APIs where supported.

### Environment preparation

1. Verify development, test, and production ownership and access boundaries.
2. Configure organization-managed pipeline identities and least-privilege roles.
3. Configure approved secret and certificate storage.
4. Establish environment-specific configuration and connection mappings.
5. Validate network paths, private access, DNS, firewalls, and service
   availability from the pipeline runner.
6. Seed representative nonproduction knowledge and test identities without
   copying unapproved production data.
7. Configure telemetry before production so deployment verification has signal.
8. Confirm quotas, capacity, licenses, connectors, policies, and regional
   support.

### Microsoft Foundry readiness

- Project and agent type identified
- Deployment context and target environment resolved
- Model, tool, and knowledge connections available
- Evaluation target and trace destination configured
- Azure and Foundry roles verified
- Prior known-good version or redeployable artifact identified

### Expected outputs and evidence

- Repository and artifact baseline
- Version and traceability contract
- Environment readiness checklist
- Identity and role-assignment record
- Configuration and dependency manifest
- Rollback candidate or prior known-good version identified

## Phase 4 - Execute the pipeline and release gates

### Objective

Prove that the identified candidate meets release controls and is the same
candidate promoted to the target environment.

### Recommended gate sequence

1. **Source and policy validation**
   - required review and branch policy;
   - artifact integrity and dependency checks;
   - configuration and secret scanning;
   - solution or infrastructure validation.
2. **Build or package**
   - create an immutable candidate;
   - record source, dependency, and configuration identity.
3. **Deploy or stage in a controlled environment**
   - deploy to the intended nonproduction target;
   - capture deployment logs and target identity.
4. **Functional and integration checks**
   - invoke critical paths;
   - validate tools, connectors, permissions, knowledge, and channels.
5. **Evaluation and safety gates**
   - run the approved smoke and regression sets;
   - execute required safety and Responsible AI checks;
   - fail closed when required evidence is missing.
6. **Approval**
   - present evidence and known exceptions to the authorized approver;
   - record the decision and any expiry-bound waiver.
7. **Production promotion**
   - promote the approved artifact or rebuild reproducibly from the approved
     source;
   - prevent unreviewed manual customization.
8. **Post-deployment verification**
   - verify agent identity/version, critical journeys, telemetry, access,
     channel availability, and rollback readiness.

### Microsoft Foundry considerations

- Hosted-agent CI/CD can use Azure Developer CLI with GitHub Actions or Azure
  DevOps as documented by Microsoft.
- Keep separate environment values and roles for each Foundry target.
- Tie evaluation records and traces to the deployed agent version and source
  commit.
- Preserve prior versions or a redeployable known-good artifact according to the
  supported agent lifecycle.
- If the AgentOps Accelerator is used, its gate and evidence output supplements
  the Foundry and pipeline records; it does not replace authorized approval,
  compliance, or platform deployment evidence.

### Expected outputs and evidence

- Successful pipeline or controlled release record
- Immutable candidate and target version identities
- Gate results and evaluation evidence
- Approval and exception record
- Deployment and post-deployment verification evidence
- Rollback point and decision log

## Phase 5 - Operationalize release management

### Objective

Make release outcomes visible, reversible, and continuously improvable.

### Activities

1. Define release health indicators and observation windows for errors, latency,
   task outcomes, quality, safety, adoption, and dependency health.
2. Establish a release calendar, freeze rules, maintenance windows, and
   emergency-change process.
3. Document rollback and roll-forward triggers, authority, communications, and
   evidence requirements.
4. Exercise rollback or redeployment of a known-good version in a nonproduction
   environment.
5. Record release metadata in the designated change and incident systems.
6. Correlate production incidents and regressions with the release identity.
7. Feed reviewed production failures into evaluation and future release gates.
8. Review identity, permissions, secrets, certificates, dependencies, and
   platform deprecations on a defined cadence.

### Expected outputs and evidence

- Release operations outline
- Post-release monitoring and decision window
- Tested rollback or recovery procedure
- Hotfix and exception workflow
- Release metrics and review cadence
- Production-to-evaluation feedback process

## Phase 6 - End the project and transfer knowledge

### Objective

Ensure designated teams can operate, troubleshoot, and evolve the release path.

### Knowledge transfer activities

1. Walk through the topology, release unit, version identity, and control matrix.
2. Demonstrate one release from approved source to post-deployment verification.
3. Run a failure rehearsal, including a blocked gate and rollback decision.
4. Have designated operators perform a nonproduction release using
   organization-managed identities.
5. Review the Foundry agent, deployment, evaluation, tracing, and dependency
   lifecycle.
6. Transfer pipeline, environment, and evidence access to organization-managed
   groups.
7. Record owners, escalation paths, support boundaries, and the next control
   review.

## Roles and responsibilities

| Role | Primary responsibilities |
| --- | --- |
| Product owner | Approves release outcomes, user impact, and business acceptance |
| Agent engineer | Maintains agent artifacts, dependencies, tests, and release fixes |
| Platform engineer or administrator | Owns Foundry and Azure environments, identities, policies, and capacity |
| Release manager | Owns promotion workflow, approvals, change records, schedules, and exceptions |
| Evaluation and Responsible AI leads | Define and review quality, safety, and regression gates |
| Security and compliance | Approve identity, secrets, supply-chain, data, audit, and policy controls |
| Operations or service owner | Owns post-release verification, incidents, rollback, and release health |
| Implementation lead | Coordinates the workflow, demonstrates supported paths, manages dependencies, and transfers knowledge |

The organization retains authority for production approval, policy exceptions,
and risk acceptance.

## Completion criteria

The Ship workstream is complete when:

- The release unit, source of truth, version identity, and environment path are
  documented.
- The selected Foundry path and its capability boundaries are explicit and use
  supported platform mechanisms.
- Organization-managed identities and least-privilege permissions are in place.
- Environment configuration and dependencies are reproducible or have explicit,
  controlled post-deployment steps.
- Required quality, safety, security, functional, and approval gates are
  implemented and evidenced.
- The approved candidate can be traced to the production deployment.
- Post-deployment checks and rollback have been exercised.
- Designated teams have completed a release rehearsal and accepted ownership.

## Knowledge transfer and handoff checklist

- [ ] Release topology and control matrix transferred
- [ ] Release-unit and version identity rules documented
- [ ] Repository, artifact, and environment ownership transferred
- [ ] Pipeline identities and permissions are organization-managed
- [ ] Environment variables, connection references, and secrets documented
- [ ] Quality, safety, security, and approval gates explained
- [ ] Foundry agent type and supported deployment mechanism documented
- [ ] Post-deployment verification and observation window rehearsed
- [ ] Rollback, hotfix, and exception procedures rehearsed
- [ ] Release evidence location and retention documented
- [ ] Open risks, waivers, and backlog accepted by named owners

## References

### AgentOps references

- [AgentOps Accelerator](https://aka.ms/agentops-accelerator) - Foundry-specific
  reference implementation
- [AgentOps Accelerator: Ship](https://azure.github.io/agentops/ship/)
- [AgentOps Accelerator: Operate](https://azure.github.io/agentops/operate/)

### Microsoft Foundry

- [Set up CI/CD for hosted agents with Azure Developer CLI](https://learn.microsoft.com/azure/foundry/agents/how-to/set-up-ci-cd-cli)
- [Deploy a hosted agent](https://learn.microsoft.com/azure/foundry/agents/how-to/deploy-hosted-agent)
- [Foundry agent development lifecycle](https://learn.microsoft.com/azure/foundry/agents/concepts/development-lifecycle)
- [Run cloud evaluations with the Microsoft Foundry SDK](https://learn.microsoft.com/azure/foundry/how-to/develop/cloud-evaluation)
- [Set up tracing in Microsoft Foundry](https://learn.microsoft.com/azure/foundry/observability/how-to/trace-agent-setup)
