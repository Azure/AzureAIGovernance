# Ship with Azure Pipelines

[Lab sequence](../../README.md) | [Ship lab, step 3](../lab.md#3-build-the-four-stage-pipeline)

Rename the generated file, then replace its contents with the pipeline below.
Replace every `ALIAS` with your alias. The stages match the GitHub Actions
version: candidate, evaluate, release and verify. One agent identity holds the
stable and candidate versions.

The instructor must grant the `agentops-azure` service-connection identity
**Foundry User** on the parent Foundry resource for judge-model inference,
plus **Foundry User** and **Contributor** on the target Foundry project for
deployment. These roles belong to the pipeline identity. They do not grant the
hosted agent access to another Azure service. Assign such access to the
hosted-agent identity separately.

The pipeline pins the beta `azure.ai.agents` extension at `1.0.0-beta.23`.
The current endpoint-selector production-promotion guidance is preview. Do not
treat that feature status as a blanket status for all hosted-agent capabilities.
Each deployment stage prints
`azd ai agent version` before it changes the agent.

Reference: [install the Azure Developer CLI Foundry extensions](https://learn.microsoft.com/azure/foundry/agents/how-to/install-cli-foundry-extensions)
and [review hosted-agent deployment permissions](https://learn.microsoft.com/azure/foundry/agents/concepts/hosted-agent-permissions).

Run this command in the PowerShell window from step 1.

**What this block does:** gives your Azure Pipelines file a unique name. Local only.

```powershell
Rename-Item .azuredevops\pipelines\agentops-deploy-dev.yml "ship-$Alias.yml"
```

Replace the renamed file with the pipeline below.

**What this block does:** keeps production pinned to its current version,
deploys and evaluates an exact candidate under the same identity, waits for
approval, selects that version at 100 percent, invokes it, and publishes the
release manifest and rollback selector.

```yaml
trigger:
  branches:
    include: [ship/ALIAS]

pr: none

pool:
  vmImage: ubuntu-latest

variables:
  - group: agentops
  - name: AZURE_SERVICE_CONNECTION
    value: agentops-azure
  - name: AGENTOPS_CONFIG
    value: agentops.yaml
  - name: AZURE_ENV_NAME
    value: dev
  - name: AZD_AI_AGENTS_EXTENSION_VERSION
    value: 1.0.0-beta.23

stages:
  - stage: candidate
    displayName: 1. Deploy candidate
    jobs:
      - job: deploy_candidate
        steps:
          - checkout: self
          - task: AzureCLI@2
            displayName: Deploy candidate
            inputs:
              azureSubscription: $(AZURE_SERVICE_CONNECTION)
              scriptType: bash
              scriptLocation: inlineScript
              inlineScript: |
                set -euo pipefail
                curl -fsSL https://aka.ms/install-azd.sh | bash
                azd ext install azure.ai.agents --version "$(AZD_AI_AGENTS_EXTENSION_VERSION)"
                azd ai agent version
                azd config set auth.useAzCliAuth true
                mkdir -p ship-candidate
                version=$(bash scripts/deploy-agent.sh \
                  helpdesk-ALIAS ship-candidate/candidate-version.txt \
                  ship-candidate/previous-selector.json)
                echo "Candidate identity: helpdesk-ALIAS; version: $version"
          - task: PublishPipelineArtifact@1
            inputs:
              targetPath: ship-candidate
              artifact: ship-candidate
              publishLocation: pipeline

  - stage: evaluate
    displayName: 2. Evaluate candidate
    dependsOn: candidate
    jobs:
      - job: evaluate_candidate
        steps:
          - checkout: self
          - download: current
            artifact: ship-candidate
          - task: UsePythonVersion@0
            inputs:
              versionSpec: "3.11"
          - bash: python -m pip install "agentops-accelerator==0.15.0"
            displayName: Install AgentOps Accelerator CLI
          - task: AzureCLI@2
            displayName: Evaluate the exact candidate version
            inputs:
              azureSubscription: $(AZURE_SERVICE_CONNECTION)
              scriptType: bash
              scriptLocation: inlineScript
              inlineScript: |
                set -euo pipefail
                export AGENTOPS_AGENT
                AGENTOPS_AGENT=$(cat "$(Pipeline.Workspace)/ship-candidate/candidate-version.txt")
                agentops eval run --config "$(AGENTOPS_CONFIG)"
            env:
              AZURE_AI_FOUNDRY_PROJECT_ENDPOINT: $(AZURE_AI_FOUNDRY_PROJECT_ENDPOINT)
              AZURE_OPENAI_ENDPOINT: $(AZURE_OPENAI_ENDPOINT)
              AZURE_OPENAI_DEPLOYMENT: $(AZURE_OPENAI_DEPLOYMENT)
              AZURE_OPENAI_MODEL_NAME: $(AZURE_OPENAI_MODEL_NAME)
              APPLICATIONINSIGHTS_CONNECTION_STRING: $(APPLICATIONINSIGHTS_CONNECTION_STRING)
          - task: PublishPipelineArtifact@1
            condition: always()
            inputs:
              targetPath: .agentops/results/latest
              artifact: agentops-dev-results
              publishLocation: pipeline

  - stage: release
    displayName: 3. Approve and promote
    dependsOn: evaluate
    jobs:
      - deployment: deploy_release
        environment: production
        strategy:
          runOnce:
            deploy:
              steps:
                - checkout: self
                - download: current
                  artifact: ship-candidate
                - task: AzureCLI@2
                  displayName: Promote the approved candidate
                  inputs:
                    azureSubscription: $(AZURE_SERVICE_CONNECTION)
                    scriptType: bash
                    scriptLocation: inlineScript
                    inlineScript: |
                      set -euo pipefail
                      curl -fsSL https://aka.ms/install-azd.sh | bash
                      azd ext install azure.ai.agents --version "$(AZD_AI_AGENTS_EXTENSION_VERSION)"
                      azd ai agent version
                      azd config set auth.useAzCliAuth true
                      bash scripts/configure-azd.sh
                      version=$(cat "$(Pipeline.Workspace)/ship-candidate/candidate-version.txt")
                      bash scripts/promote-version.sh helpdesk-ALIAS "$version"
                      echo "Production identity: helpdesk-ALIAS; version: $version"

  - stage: verify
    displayName: 4. Verify and record release
    dependsOn:
      - candidate
      - release
    jobs:
      - job: verify_release
        steps:
          - checkout: self
          - download: current
            artifact: ship-candidate
          - task: AzureCLI@2
            displayName: Invoke exact version and write manifest
            inputs:
              azureSubscription: $(AZURE_SERVICE_CONNECTION)
              scriptType: bash
              scriptLocation: inlineScript
              inlineScript: |
                set -euo pipefail
                curl -fsSL https://aka.ms/install-azd.sh | bash
                azd ext install azure.ai.agents --version "$(AZD_AI_AGENTS_EXTENSION_VERSION)"
                azd ai agent version
                azd config set auth.useAzCliAuth true
                bash scripts/configure-azd.sh
                candidate_version=$(cat "$(Pipeline.Workspace)/ship-candidate/candidate-version.txt")
                bash scripts/smoke-test.sh helpdesk-ALIAS "$candidate_version"
                mkdir -p ship-release
                RELEASE_PIPELINE_URL="$(System.CollectionUri)$(System.TeamProject)/_build/results?buildId=$(Build.BuildId)" \
                  bash scripts/write-release-manifest.sh \
                    helpdesk-ALIAS "$candidate_version" \
                    "$(Pipeline.Workspace)/ship-candidate/previous-selector.json" \
                    ship-release/release-manifest.json
                cp "$(Pipeline.Workspace)/ship-candidate/previous-selector.json" ship-release/
                cat ship-release/release-manifest.json
          - task: PublishPipelineArtifact@1
            inputs:
              targetPath: ship-release
              artifact: ship-release-manifest
              publishLocation: pipeline
```

## Create, run and recover

### Action: Create and run the Azure Pipeline

- **Purpose:** Bind your branch's YAML to one Azure Pipeline and retain both evaluation and release evidence.
- **Navigation:** Push the branch, then use **Pipelines > New pipeline** and the exact selections below.
- **Result:** The first run is rejected, the corrected run passes, and both pipeline artifacts are downloadable.
- **If it fails:** Open the first failed stage and follow the recovery table on this page. Do not approve a run without evaluation evidence.
- **Save:** Keep both run URLs, `agentops-dev-results` and `ship-release-manifest`.
- **Time:** 15 to 20 minutes active, plus the pipeline waits described in the Ship lab.

1. Push `ship/<your alias>`.
2. Open **Pipelines** and select **New pipeline**.
3. Select **Azure Repos Git**, the class repository, and **Existing Azure
   Pipelines YAML file**.
4. Select your branch and
   `/.azuredevops/pipelines/ship-<your alias>.yml`.
5. Select **Run**.
6. Rename the pipeline to `ship-<your alias>`.
7. On the run **Summary**, open **Related > Published**, select
   **agentops-dev-results**, and select **Download artifacts**. Extract the
   downloaded ZIP and open `report.md` before you decide.
8. Select **Review** on **3. Approve and promote** and reject the first run.
9. Approve the corrected run.
10. After stage 4 passes, return to the run **Summary**, open
    **Related > Published**, select **ship-release-manifest**, and select
    **Download artifacts**. Extract the downloaded ZIP and open
    `release-manifest.json`.

If a stage fails, open its first failed task and keep the run. Do not approve a
run with missing evaluation evidence. Fix the branch and push again.

If an incorrect release completes, disable or restrict the released endpoint
according to the class recovery instruction, revert the bad commit, and push.
Run all four stages again. Do not rerun only stage 3 because that would skip the
current evaluation and manifest chain.

Return to [step 4 of the Ship lab](../lab.md#4-run-and-reject-the-candidate).
