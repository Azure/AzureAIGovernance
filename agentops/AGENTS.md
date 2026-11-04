# AgentOps contributor guidance

## Scope

These instructions apply to all files under `agentops/`.

This file is the canonical source of contribution instructions for AgentOps
content. Tool-specific instruction files should reference this file instead of
duplicating its rules.

## AgentOps Value Based Delivery

AgentOps is the discipline of evaluating, releasing, observing, and operating AI
agents through repeatable activities across the agent lifecycle.

AgentOps Value Based Delivery is part of the AI Governance Value Based Delivery.
It has two complementary components:

- **Workshop:** teaches AgentOps concepts and provides guided practice.
- **Implementation guidance:** explains how teams can establish AgentOps in an
  organization.

AgentOps covers Evaluate, Ship, Observe, and Operate. For content delivery,
organize them into three modules:

1. Evaluate
2. Ship
3. Observe and Operate

Observe and Operate remain distinct even though they share one deck, lab, and
implementation guide.

## Platform scope

Microsoft Foundry is the implementation platform for the current AgentOps VBD
materials.

- Use current Microsoft Foundry terminology and capabilities.
- Ground product claims in current first-party Microsoft documentation.
- Use descriptive links that identify their destination.
- Give pages of about 200 lines or more an **On this page** index after the
  introduction, linking each `##` section. Use a light numbered list with a short
  description per item, not a table.
- Present AgentOps Accelerator as a practical reference implementation alongside
  native Microsoft Foundry capabilities.
- Lead workshop explanations with Microsoft Foundry and the learning activity.
  Present the Accelerator as supporting tooling, not the focus of the workshop.
  Do not bold its name or include its version in learner-facing narrative.
  Keep version pins and compatibility details in dependency files and TOOLING.md;
  retain versioned source links where needed for technical accuracy.
- Do not present AgentOps Accelerator as the Microsoft Foundry product contract
  or as a replacement for native capabilities.
- Do not introduce alternative agent-building platforms or future platform
  plans.

## Content architecture

### Workshop

Workshop content consists of:

- one workshop one-pager;
- a Markdown instructor guide with general and module-specific facilitation;
- three decks; and
- three core labs maintained in GitHub; and
- one optional advanced lab.

Maintain one deck and one lab for each content module.

The Ship lab may provide equivalent instructions for two pipeline tools,
GitHub Actions and Azure Pipelines. Call them pipeline tools, not tracks.
Select one before delivery and keep their learning objectives and expected
artifact aligned.

Keep the Ship class repository seed (`02-ship/class-repo`) complete, so the
instructor only copies that folder and pushes it. Its `src/helpdesk/` and
`turns.jsonl` are copies of the shared agent and the Evaluate test requests;
update them together, and keep the lab test that compares them passing.

Keep `shared/helpdesk-agent` a ready azd project (`azure.yaml` and
`.agentignore` included), so the instructor deploys straight from the clone
without downloading samples or copying files.

Make the learning order visible in the lab folders: `01-evaluate`, `02-ship`,
`03-observe-operate`, and optional `04-advanced`. Keep `shared` unnumbered:
it contains reusable agent code and assets, not an extra module.
Use `workshop/labs/README.md` as the participant entry point, linking to
pre-work before the numbered labs. Keep the instructor guide as the teaching
entry point and explain folder purposes in `agentops/README.md`.
Numbering indicates the full-workshop sequence, not mandatory attendance at
earlier modules. Agent/environment preparation belongs to instructor/admin
pre-work, not a participant "build an agent" module.
Within Ship, make `github-actions` and `azure-pipelines` alternative entry
points to the same lab and output, not consecutive labs. Do not turn outlines
into runnable instructions merely to populate the folders.

The optional advanced lab may combine content from multiple modules. Keep it
outside the six-hour core workshop and use it for closed-loop scenarios that
require additional time, such as alerts, runbook execution, trace-to-dataset,
and release-gate updates.

Workshop content must:

- focus on learning and guided practice;
- keep terminology and examples aligned across the one-pager, decks, and labs;
- name the learning artifact produced by each module; and
- avoid becoming an implementation plan or detailed product runbook.

The workshop supports two delivery modes:

- **Hands-on:** 60 minutes of presentation followed by a 60-minute participant
  lab.
- **Demo:** 60 minutes of presentation followed by a 20-minute instructor
  demonstration.

Select the delivery mode before the session. Provisioning and troubleshooting
are not part of workshop time.

### Workshop document responsibilities

Apply this separation to Evaluate, Ship, Observe and Operate, and the optional
advanced lab whenever authoring or revising them. It does not require expanding
scope-only labs into complete exercises before they are ready.

- **Participant `lab.md`:** the execution guide, not a preparation checklist or
  authoring log. Open with the objective, participant duration, scenario,
  learning artifact, a link to pre-work, and short tool roles. Follow promptly
  with numbered actions, commands where needed, and expected results or evidence
  to inspect. End with the decision/output and handoff or retention instructions.
  Starting an already prepared learner workspace belongs in the lab;
  installation, authentication, permissions and provisioning do not.
- **Workshop pre-work:** installation, authentication, permissions, deployment,
  workspace preparation, environment readiness, instructor evidence preparation,
  and owner-approved cleanup. Explicitly separate **PARTICIPANT** tasks from
  **INSTRUCTOR/ADMIN** responsibilities. Keep delivery prerequisites and their
  acceptance checks here, not the author's current validation status.
  Organize shared pre-work as common preparation followed by requirements for
  Evaluate, Ship, Observe and Operate, and the optional advanced lab. Attendees
  complete only their selected modules; provide prior-module artifacts for
  standalone delivery. Do not present Evaluate-specific setup as mandatory for
  every module or treat one module's readiness as readiness for the whole workshop.
  Keep the pre-work README a concise participant landing page. Put deployment,
  workspace initialization, technical metadata, evidence generation and
  packaging in a linked instructor guide, not below participant steps in the
  same long page.
- **Workshop one-pager:** a description of the whole workshop for participants.
  Explain its purpose, audience, outcomes, modules, duration, formats,
  prerequisites and what participants receive. Keep the PDF genuinely one page.
  Do not include instructor tasks, module-specific facilitation, technical
  preparation or internal authoring status.
- **Workshop instructor guide:** the starting point for a new instructor.
  Explain the workshop, what to read first, how to prepare and how to teach
  each module. Keep it in Markdown under `workshop/instructor-guide/`.
  Separate first reading from preparation: ask readers to finish the general
  guide before opening linked materials. Keep its opening module overview
  free of guide and lab links, and place module-guide links in a final handoff.
  Present other resource links as references for the relevant preparation stage,
  not as a checklist to open during the first reading.
  Make it the single entry point: understand the lesson before installing
  tools, find reusable assets, prepare only what is missing, rehearse with
  participant access, distribute the files, then teach. Name the destination
  and completion condition for linked tasks so readers know when to return
  and continue. Separate first-time material authoring from routine delivery.
  Include hands-on and demonstration guidance, discussion prompts and module
  transitions. Give overall activity durations and allow the instructor to
  adapt the pace; avoid minute-by-minute micromanagement. Link to technical
  pre-work rather than duplicating its commands. Mark unfinished activities
  honestly without expanding them into invented procedures.
- **Module `TOOLING.md`:** versions, tool selection and design rationale,
  capability boundaries, authoring history and validation/readiness status.
  This is workshop tooling documentation, not organizational implementation
  guidance. Do not duplicate internal authoring status or migration narration
  in the participant lab.
- **Evidence assets/README:** the evidence contract, provenance labels and
  result-review references; link to pre-work for preparation actions.
- **Implementation guidance:** organizational adoption and operating practices,
  not the storage location for workshop setup, tooling notes or facilitation.

Keep runtime information required for correct execution in the lab even when
TOOLING explains the underlying limitation: costs, failure handling, no blind
resubmission, baseline-versus-threshold semantics, completeness and critical-case
review, and the limits of a passing gate. Clearly distinguish authored examples,
instructor evidence review and live participant results; missing evidence is a
gap, not a pass.

Keep one-pager Markdown and generated PDF synchronized. Ensure its renderer
includes all participant-facing content in the source, regenerate after source changes,
and verify page count, extracted content, links and visual readability. Update
the README's relevant artifact descriptions and links when responsibilities move.

### Modular delivery

Each deck contains the shared AgentOps foundation slides so the module can be
delivered independently. This repetition is intentional.

Instructor notes must explain that:

- the foundation section supports standalone module delivery;
- facilitators may use it as a recap when delivering multiple modules; and
- familiar foundation slides may be skipped according to participant needs.

### Implementation guidance

Provide one implementation guide for each content module:

- Evaluate
- Ship
- Observe and Operate

Implementation guidance must:

- translate the covered content into a clear implementation workflow;
- describe decisions, activities, evidence, and expected outputs;
- connect the content to Microsoft Foundry capabilities;
- remain concise, practical, technically grounded, and reusable;
- remain organization-agnostic;
- avoid becoming a Statement of Work, commercial scope, or product runbook; and
- avoid duplicating workshop content.

## Artifact locations

Store files under:

```text
agentops/
├── workshop/
│   ├── one-pager/
│   ├── instructor-guide/
│   ├── pre-work/
│   ├── decks/
│   ├── assets/
│   └── labs/
│       ├── README.md
│       ├── 01-evaluate/
│       ├── 02-ship/
│       │   ├── github-actions/
│       │   └── azure-pipelines/
│       ├── 03-observe-operate/
│       ├── 04-advanced/
│       └── shared/
└── implementation-guidance/
```

Additional rules:

- Keep labs in Markdown.
- Keep decks in PowerPoint.
- Keep the one-pager Markdown source beside its generated PDF.
- Keep supporting assets with their corresponding content group.
- Update `agentops/README.md` whenever an artifact is added, renamed, moved, or
  removed.
- Ensure every link in `agentops/README.md` resolves to the intended artifact.

## Deck standards

Decks must:

- use instructor notes for timing, delivery mode, modular delivery, and lab
  transitions;
- identify whether an activity is a participant lab, instructor demo, or
  optional deep dive;
- use substantial filled card headers with white title text and lightly tinted
  card bodies;
- avoid thin colored bars above otherwise empty cards;
- use descriptive hyperlink labels rather than generic labels;
- expand uncommon acronyms on first use; and
- avoid text overflow, awkward wrapping, low contrast, and inconsistent spacing.

## Writing standards

- Keep content practical, concise, clear, and professional.
- Refer to people attending the workshop as "participants", not with commercial
  labels. Use "workshop organizer" when discussing session planning and "team"
  or "organization" when discussing implementation and production environments.
- When first introducing a document, page, tool, package or folder, explain
  what it contains or does and when the reader should use it. Use descriptive
  link labels rather than assuming the reader already knows the material.
- Make the course welcoming to a first-time reader. Use direct, encouraging
  language without assuming the reader knows internal engineering vocabulary.
  A short sentence is not clear if it only compresses unexplained terms.
  Name the person or software, what it must do, and how to see the result.
  Replace phrases such as "runtime identity access" with the specific account
  or agent and the action it needs permission to perform. Explain necessary
  technical terms briefly where first used; do not add a separate glossary
  instead of fixing the instruction.
- Before a non-obvious download, command block, configuration change or review,
  briefly explain its purpose and where the output will be used next. Use a
  short note such as "Why this step" or "What this does", not line-by-line
  narration. Learners should understand the task, not merely copy commands.
  Prefer adding the missing reason to existing prose over repeating the
  instruction.
- Labs mirror daily practice: participants clone the repository and generate
  their own results by running the steps in the shared sandbox project. Do not
  distribute ZIPs of prepared settings or someone else's results for learners to
  review in place of running the activity. The instructor's own rehearsal
  results are only an on-screen fallback, labelled **instructor demonstration**.
  Use a ZIP for convenience only with the VBD owner's (Paulo's) prior approval,
  and explain what it contains. In Ship, the instructor prepares one class
  repository once; each participant creates and runs their own pipeline in it.
- Explain the reader's goal before the implementation mechanics: why the step
  is needed, what it enables next and what result the reader will use.
  Describing variable assignments or translating commands into prose is not
  a substitute for that purpose. When implementation detail is useful, describe
  it accurately; do not say a script "remembers", "understands" or "takes care of"
  an unspecified task.
- Put one short sentence immediately before every command or code block saying
  its purpose. Mention side effects only when they matter: it deploys to Azure
  or could be mistaken for doing so. Do not add spending-approval notes to
  workshop pages. Do not narrate
  each step, and keep the surrounding text to what the reader must act on.
- Keep section headings aligned with any order table or step list that links
  to them: same wording, same numbering and same order.
- Refer to each material by its page title every time (for example
  "Instructor technical setup", "participant pre-work", "Teaching Evaluate"),
  never by alternate names. In reading-flow pages, name materials in bold and
  collect their links in a final reference table or "what to open next" list.
- Do not add readiness, status or "not yet available" sections to published
  material; the material is released only when complete.
- Do not use "check", "confirm", "verify" or "make sure" as a substitute for a
  procedure. Give the reader a short path to the file or screen, the action to
  perform, the value or status to look for and what to do on failure. Link to
  a nearby worked procedure when repeating it would make the main flow too long.
- Use portable Markdown for notes: a bold descriptive label and ordinary
  paragraphs. Do not depend on GitHub-only alert markers or a browser extension's
  optional features to convey instructions.
- Use the workshop's illustrated banners at guide openings and a few meaningful
  transitions. Keep them relevant, readable and consistent with the friendly
  hand-drawn style. Include descriptive alt text and editable source files.
  Banners support the instructions; they must not hide costs, prerequisites,
  unfinished exercises or missing evidence.
- Give each numbered step one short action. Group related steps under clear
  headings; put required-file lists, expected results and failure actions in
  separate blocks. Avoid procedural tables with paragraph-sized cells and
  repeated warnings. Shorten the rendered content, not just its source lines.
- Treat pre-work as preparation for a normal course, not a software-authoring
  audit. Separate routine class preparation from first-time environment and
  material creation. Reuse prepared assets; require only tools used by the
  selected exercise. Keep optional editors, extensions and local debugging
  optional. Do not add manual encoding, hash collection or metadata forms when
  native tools and retained artifacts already handle the need.
- Make the first-time instructor route complete and visible: provision or
  explicitly reuse the Foundry project, deploy models, assign access, deploy
  the agent, obtain actual tool records, prepare evaluation settings and results,
  package, then rehearse with participant permissions. Local CLI installation
  does not satisfy cloud setup. Name the guide for each stage and its completion
  condition; do not send readers back to prerequisites that depend on a later step.
- If the exercise inspects executed tools, prepare their real records as part
  of the main run. Do not add optional lab supplements that participants only
  watch.
- Write preparation and execution steps for someone opening the workshop for
  the first time: identify the responsible role, starting folder, required
  files/inputs and where to obtain them, exact commands or UI clicks, observable
  successful result, and the first action if it fails.
- Never use "install requirements", "prepare the pipeline", or "verify readiness"
  as a complete instruction. Link to the specific installer/tutorial, explain
  unfamiliar terms, and name the resulting file, screen, or evidence.
- Never leave the starting source as "reviewed archive", "exact repository
  revision" or "instructor-provided link" without a retrieval path. Name the
  actual repository/download, exact distributed filename, invitation field
  or package README label, extraction destination and missing-file action.
  Session-specific URLs and identities must be populated by the instructor
  from named portal/CLI outputs; do not invent them. Define how the instructor
  creates/distributes a package before telling participants to download it.
  Separate unfinished authoring requirements from executable preparation.
- Define reusable paths explicitly. Use environment-specific executables for
  Python and CLIs; do not assume activation, an unexplained working-directory
  change, or permission to change execution policy. Stop after installation or
  configuration errors; preserve useful evaluation failure codes and reports.
- Authors own initial workspace configuration and provenance; instructors reuse
  it and check the class assignment. Participants receive
  a reviewed native workspace and evidence bundle, not a JSON template or metadata
  transcription exercise. Do not introduce a custom bootstrap runner to hide
  setup complexity. Keep instructor-only recipes outside participant sections.
- Walk the participant path from a fresh terminal before finalizing it. Remove
  unnecessary actions instead of explaining ever-longer scripts. Do not ask
  learners to paste PowerShell variable names into editor/file-picker dialogs;
  give a visible folder path or say how to display the actual path. Keep the
  instructions accessible while learners open datasets and reports.
- Distinguish local checks, authenticated service checks and actions that change
  Azure resources.
  Use assigned resource values, never invented identifiers or unreviewed default
  subscriptions. Keep secrets out of commands, screenshots and transcripts.
- State when distributed files require an instructor-supplied revision/archive;
  do not imply unpublished work is available on the default branch. Identify
  outline-only activities and missing evidence instead of claiming runnable labs.
- Keep headings descriptive and direct.
- Write participant worksheets as short, plain-language questions with one
  clear purpose per field. Explain necessary terms and say where to find an
  answer. Link to retained evidence instead of asking learners to transcribe
  hashes, technical identifiers or compound metadata fields.
- For questions requiring judgment, include where to look, what to check,
  how to choose an answer, and a clearly labelled illustrative response.
  Explain unfamiliar terms at first use and provide an explicit answer space.
  Examples must not be mistaken for actual run results or prefilled passes.
- Use organization-neutral language.
- Do not include secrets, tenant identifiers, or production data.
- Do not use em dashes or en dashes as title or emphasis separators.
- Use a colon, period, or parentheses instead.
- Keep terminology consistent across all AgentOps artifacts.

## Validation

Before completing a change:

1. Confirm alignment between the one-pager, deck, lab, and implementation guide.
2. Verify the four-part and three-module structure.
3. Verify all documentation and artifact links.
4. Check for obsolete, inconsistent, or organization-specific terminology.
5. Open every modified PowerPoint file successfully.
6. Render every modified slide and inspect it visually.
7. Check for clipping, overlap, poor contrast, awkward wrapping, and
   inconsistent card styles.
8. Confirm that the README still links to every artifact.
9. Remove temporary Office lock files and generated QA artifacts.
