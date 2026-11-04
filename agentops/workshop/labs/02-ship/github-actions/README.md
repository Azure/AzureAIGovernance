# Ship with GitHub Actions

[Lab sequence](../../README.md) | [Ship lab, step 3](../lab.md#3-build-the-four-stage-pipeline)

Replace the generated workflow with the file below. Then replace every `ALIAS`
with your alias. The workflow uses four jobs: candidate, evaluate, release and
verify. The `production` environment pauses the release job for approval.

The instructor must grant the GitHub OpenID Connect (OIDC) identity **Foundry
User** and **Contributor** on the target Foundry project for code deployment.
These roles belong to the pipeline identity. They do not grant an agent access
to other Azure resources. An agent that calls another Azure service needs its
own hosted-agent identity assignment.

The workflow pins `azure.ai.agents` `1.0.0-beta.23`. Microsoft currently marks
the extension and hosted agents as preview. The install step also runs
`azd ai agent version`, so a missing or different extension fails before a
deployment starts.

Reference: [install the Azure Developer CLI Foundry extensions](https://learn.microsoft.com/azure/foundry/agents/how-to/install-cli-foundry-extensions)
and [review hosted-agent deployment permissions](https://learn.microsoft.com/azure/foundry/agents/concepts/hosted-agent-permissions).

**What this block does:** deploys and evaluates the candidate, waits for approval,
rebuilds the release agent from the same commit, invokes its exact version, and
publishes `release-manifest.json`.

```yaml
name: Ship ALIAS

on:
  push:
    branches: [ship/ALIAS]
  workflow_dispatch:

permissions:
  contents: read
  id-token: write

concurrency:
  group: ship-ALIAS-${{ github.ref }}
  cancel-in-progress: false

env:
  AZD_AI_AGENTS_EXTENSION_VERSION: 1.0.0-beta.23
  AZURE_TENANT_ID: ${{ vars.AZURE_TENANT_ID }}
  AZURE_SUBSCRIPTION_ID: ${{ vars.AZURE_SUBSCRIPTION_ID }}
  AZURE_LOCATION: ${{ vars.AZURE_LOCATION }}
  AZURE_RESOURCE_GROUP: ${{ vars.AZURE_RESOURCE_GROUP }}
  AZURE_AI_PROJECT_ID: ${{ vars.AZURE_AI_PROJECT_ID }}
  FOUNDRY_PROJECT_ENDPOINT: ${{ vars.FOUNDRY_PROJECT_ENDPOINT }}
  AZURE_AI_MODEL_DEPLOYMENT_NAME: ${{ vars.AZURE_AI_MODEL_DEPLOYMENT_NAME }}

jobs:
  candidate:
    name: 1. Deploy candidate
    runs-on: ubuntu-latest
    environment: dev
    outputs:
      version: ${{ steps.deploy.outputs.version }}
    steps:
      - uses: actions/checkout@v6
      - uses: Azure/setup-azd@v2
      - uses: azure/login@v3
        with:
          client-id: ${{ vars.AZURE_CLIENT_ID }}
          tenant-id: ${{ vars.AZURE_TENANT_ID }}
          subscription-id: ${{ vars.AZURE_SUBSCRIPTION_ID }}
      - name: Install and identify the Foundry agents extension
        run: |
          azd ext install azure.ai.agents --version "$AZD_AI_AGENTS_EXTENSION_VERSION"
          azd ai agent version
          azd config set auth.useAzCliAuth true
      - name: Deploy candidate
        id: deploy
        run: |
          version=$(bash scripts/deploy-agent.sh helpdesk-ALIAS-test)
          echo "version=$version" >> "$GITHUB_OUTPUT"
          echo "Candidate identity: helpdesk-ALIAS-test; version: $version"

  evaluate:
    name: 2. Evaluate candidate
    needs: candidate
    runs-on: ubuntu-latest
    environment: dev
    steps:
      - uses: actions/checkout@v6
      - uses: azure/login@v3
        with:
          client-id: ${{ vars.AZURE_CLIENT_ID }}
          tenant-id: ${{ vars.AZURE_TENANT_ID }}
          subscription-id: ${{ vars.AZURE_SUBSCRIPTION_ID }}
      - uses: actions/setup-python@v6
        with:
          python-version: "3.11"
      - uses: astral-sh/setup-uv@v7
        with:
          enable-cache: false
      - name: Install AgentOps Accelerator CLI
        run: uv pip install --system "agentops-accelerator==0.15.0"
      - name: Evaluate the exact candidate version
        env:
          AZURE_AI_FOUNDRY_PROJECT_ENDPOINT: ${{ vars.AZURE_AI_FOUNDRY_PROJECT_ENDPOINT }}
          AZURE_OPENAI_ENDPOINT: ${{ vars.AZURE_OPENAI_ENDPOINT }}
          AZURE_OPENAI_DEPLOYMENT: ${{ vars.AZURE_OPENAI_DEPLOYMENT }}
          AZURE_OPENAI_MODEL_NAME: ${{ vars.AZURE_OPENAI_MODEL_NAME }}
          APPLICATIONINSIGHTS_CONNECTION_STRING: ${{ secrets.APPLICATIONINSIGHTS_CONNECTION_STRING || vars.APPLICATIONINSIGHTS_CONNECTION_STRING }}
          AGENTOPS_AGENT: ${{ needs.candidate.outputs.version }}
        run: agentops eval run --config agentops.yaml
      - name: Publish evaluation evidence
        if: always()
        uses: actions/upload-artifact@v7
        with:
          name: agentops-dev-results
          path: .agentops/results/latest
          if-no-files-found: warn

  release:
    name: 3. Approve and release
    needs: [candidate, evaluate]
    runs-on: ubuntu-latest
    environment: production
    outputs:
      version: ${{ steps.deploy.outputs.version }}
    steps:
      - uses: actions/checkout@v6
      - uses: Azure/setup-azd@v2
      - uses: azure/login@v3
        with:
          client-id: ${{ vars.AZURE_CLIENT_ID }}
          tenant-id: ${{ vars.AZURE_TENANT_ID }}
          subscription-id: ${{ vars.AZURE_SUBSCRIPTION_ID }}
      - name: Install and identify the Foundry agents extension
        run: |
          azd ext install azure.ai.agents --version "$AZD_AI_AGENTS_EXTENSION_VERSION"
          azd ai agent version
          azd config set auth.useAzCliAuth true
      - name: Deploy release identity
        id: deploy
        run: |
          version=$(bash scripts/deploy-agent.sh helpdesk-ALIAS)
          echo "version=$version" >> "$GITHUB_OUTPUT"
          echo "Release identity: helpdesk-ALIAS; version: $version"

  verify:
    name: 4. Verify and record release
    needs: [candidate, release]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: Azure/setup-azd@v2
      - uses: azure/login@v3
        with:
          client-id: ${{ vars.AZURE_CLIENT_ID }}
          tenant-id: ${{ vars.AZURE_TENANT_ID }}
          subscription-id: ${{ vars.AZURE_SUBSCRIPTION_ID }}
      - name: Install and identify the Foundry agents extension
        run: |
          azd ext install azure.ai.agents --version "$AZD_AI_AGENTS_EXTENSION_VERSION"
          azd ai agent version
          azd config set auth.useAzCliAuth true
          bash scripts/configure-azd.sh
      - name: Invoke the exact released version
        run: bash scripts/smoke-test.sh helpdesk-ALIAS "${{ needs.release.outputs.version }}"
      - name: Write release manifest
        env:
          RELEASE_PIPELINE_URL: ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}
        run: |
          bash scripts/write-release-manifest.sh \
            helpdesk-ALIAS-test "${{ needs.candidate.outputs.version }}" \
            helpdesk-ALIAS "${{ needs.release.outputs.version }}" \
            release-manifest.json
          cat release-manifest.json
      - name: Publish release manifest
        uses: actions/upload-artifact@v7
        with:
          name: ship-release-manifest
          path: release-manifest.json
```

## Run and recover

### Action: Create and run the GitHub workflow

- **Purpose:** Run the four Ship stages from your branch and retain both evaluation and release evidence.
- **Navigation:** Save the workflow at the exact path in step 1, push it, then use **Actions** and **Review deployments** as described below.
- **Result:** The first run is rejected, the corrected run passes, and both artifacts are downloadable.
- **If it fails:** Open the first failed job and follow the recovery table on this page. Do not approve a run without evaluation evidence.
- **Save:** Keep both run URLs, `agentops-dev-results` and `ship-release-manifest`.
- **Time:** 10 minutes active, plus the pipeline waits described in the Ship lab.

1. Save the file as `.github\workflows\agentops-deploy-dev.yml`.
2. Replace `ALIAS` with your alias.
3. Push your branch.
4. Open **Actions**, select **Ship** plus your alias, and open the current run.
5. Download `agentops-dev-results` before you decide.
6. Select **Review deployments** and reject the first run.
7. Approve the corrected run.
8. Download `ship-release-manifest` after **Verify and record release** passes.

If a job fails, open the first failed step and keep the run. Do not approve a
run with missing evaluation evidence. Fix the branch and push again.

If an incorrect release completes, disable or restrict the released endpoint
according to the class recovery instruction, revert the bad commit, and push.
Run all four jobs again. Do not rerun only the release job because that would
skip the current evaluation and manifest chain.

Return to [step 4 of the Ship lab](../lab.md#4-run-and-reject-the-candidate).
