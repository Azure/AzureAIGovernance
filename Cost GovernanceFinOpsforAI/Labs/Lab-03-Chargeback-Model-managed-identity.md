# Lab 3 - Chargeback Model for Azure AI (Managed Identity)

> **Objective:** Build an end-to-end chargeback/showback model that tracks AI costs by team, project, and model - from tagging resources, to emitting usage metrics, to generating chargeback reports.
>
> **Authentication:** Uses **APIM Managed Identity** (not API keys) to authenticate to Azure OpenAI.
>
> **Duration:** 60-75 minutes
>
> **Prerequisites:** Complete [00-Prerequisites-managed-identity.md](00-Prerequisites-managed-identity.md). Labs 1 and 2 are recommended but not required.

---

## Lab Variables

**Critical: Use exact APIM subscription names for key retrieval.** Copy this recovery block and run it first:

```powershell
# === RECOVER ALL VARIABLES ===
$RESOURCE_GROUP  = "rg-ai-finops-labs"
$AOAI_NAME       = "aoai-finops-lab"
$APIM_NAME       = az apim list --resource-group $RESOURCE_GROUP --query "[0].name" --output tsv
$APIM_GATEWAY    = az apim show --name $APIM_NAME --resource-group $RESOURCE_GROUP --query "gatewayUrl" --output tsv

# === RETRIEVE KEYS FROM APIM (exact subscription names: lowercase with hyphen) ===
$SUBSCRIPTION_ID = az account show --query id --output tsv
$BASE_MGMT = "https://management.azure.com/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.ApiManagement/service/$APIM_NAME"

# Use exact subscription names (IDs) as shown in APIM portal
$KEY_CUSTOMERAI  = az rest --method POST --uri "$BASE_MGMT/subscriptions/customerai-team/listSecrets?api-version=2022-08-01" --query primaryKey -o tsv
$KEY_INTERNALOPS = az rest --method POST --uri "$BASE_MGMT/subscriptions/internalops-team/listSecrets?api-version=2022-08-01" --query primaryKey -o tsv
$KEY_RESEARCH    = az rest --method POST --uri "$BASE_MGMT/subscriptions/research-team/listSecrets?api-version=2022-08-01" --query primaryKey -o tsv

# Verify all keys loaded (must all show 32)
Write-Host "CustomerAI:  $($KEY_CUSTOMERAI.Length)  chars (expected: 32)"
Write-Host "InternalOps: $($KEY_INTERNALOPS.Length) chars (expected: 32)"
Write-Host "Research:    $($KEY_RESEARCH.Length)    chars (expected: 32)"
```

> **IMPORTANT MAPPING:**
> - **APIM Subscription ID** (for key retrieval): `customerai-team` → **PowerShell Variable**: `$KEY_CUSTOMERAI`
> - **APIM Subscription ID** (for key retrieval): `internalops-team` → **PowerShell Variable**: `$KEY_INTERNALOPS`
> - **APIM Subscription ID** (for key retrieval): `research-team` → **PowerShell Variable**: `$KEY_RESEARCH`
>
> These are **APIM subscription keys** (for client→APIM authentication), NOT Azure OpenAI API keys.
> APIM uses its managed identity to authenticate to Azure OpenAI automatically.

> **Note:** These are APIM subscription keys for client authentication.
> No Azure OpenAI API keys are needed - APIM managed identity handles that automatically.

---

## Part 1 - Understand the Chargeback Architecture

### Step 1.1 - Review the End-to-End Chargeback Flow

```
End-to-End Flow:
- Teams call APIM gateway (authenticated via APIM subscription keys)
- APIM authenticates to Azure OpenAI using system-assigned managed identity
- Azure OpenAI processes request
- Usage data (tokens, deployment, etc.) flows back through APIM
- Cost Management and Billing system tracks resource tags and usage
- Reports and chargebacks generated based on tags and usage

Tagging enables the chargeback:
- CostCenter: Routes costs to finance department
- Team: Identifies which team used the service
- Project: Tracks costs per project/product
- Environment: Separates production vs lab vs dev costs
- Owner: Identifies responsible party for cost optimization
```

### Step 1.2 - Review Chargeback vs Showback

| Model | Description | When to Use |
|-------|-------------|------------|
| **Showback** | Teams see their costs but aren't billed | Getting started; building cost awareness |
| **Chargeback** | Costs are allocated to team budgets/cost centers | Mature FinOps; teams have P&L responsibility |

In this lab, we'll build the infrastructure for both. You can decide which model to implement.

---

## Part 2 - Resource Tagging Strategy

### Step 2.1 - Define the Tagging Standard

A solid chargeback model starts with consistent tags.

| Tag Name | Purpose | Example Values |
|----------|---------|----------------|
| `CostCenter` | Finance cost center code | `CC-5001`, `CC-5002`, `CC-5003` |
| `Team` | Consuming team | `CustomerAI`, `InternalOps`, `Research` |
| `Environment` | Deployment environment | `Production`, `Staging`, `Lab` |
| `Owner` | Responsible person/group | `ai-platform@contoso.com` |
| `Project` | Project or product name | `Copilot-V2`, `InternalBot`, `AIResearch` |

### Step 2.2 - Apply Tags to Azure OpenAI Resource

```powershell
# Apply the full tagging standard
az resource tag `
    --resource-group $RESOURCE_GROUP `
    --name $AOAI_NAME `
    --resource-type "Microsoft.CognitiveServices/accounts" `
    --tags `
        CostCenter="CC-5001" `
        Team="AI-Platform" `
        Environment="Lab" `
        Owner="ai-platform@contoso.com" `
        Project="CostGovernanceLab"

Write-Host "Tags applied successfully."
```

### Step 2.3 - Apply Tags to APIM Resource

```powershell
az resource tag `
    --resource-group $RESOURCE_GROUP `
    --name $APIM_NAME `
    --resource-type "Microsoft.ApiManagement/service" `
    --tags `
        CostCenter="CC-5001" `
        Team="AI-Platform" `
        Environment="Lab" `
        Owner="ai-platform@contoso.com" `
        Project="CostGovernanceLab"

Write-Host "APIM tags applied successfully."
```

### Step 2.4 - Verify Tags

```powershell
# Verify tags on both resources
Write-Host "=== Azure OpenAI Tags ==="
az resource show `
    --resource-group $RESOURCE_GROUP `
    --name $AOAI_NAME `
    --resource-type "Microsoft.CognitiveServices/accounts" `
    --query "tags" --output json

Write-Host "`n=== APIM Tags ==="
az resource show `
    --resource-group $RESOURCE_GROUP `
    --name $APIM_NAME `
    --resource-type "Microsoft.ApiManagement/service" `
    --query "tags" --output json
```

> **Expected Result:** Both resources show all 5 tags with correct values.

---

## Part 3 - Enforce Tags with Azure Policy

### Step 3.1 - Create a Tag Enforcement Policy (Audit Mode)

Start with **Audit** mode to detect untagged resources without blocking deployments:

```powershell
# Create a policy assignment that audits resources missing the CostCenter tag
$policyDefinitionId = "/providers/Microsoft.Authorization/policyDefinitions/871b6d14-10aa-478d-b466-cc659e4a0ae5"

# This is the built-in "Require a tag on resources" policy
az policy assignment create `
    --name "audit-costcenter-tag" `
    --display-name "Audit: Require CostCenter tag on resources" `
    --policy $policyDefinitionId `
    --scope "/subscriptions/$(az account show --query id --output tsv)/resourceGroups/$RESOURCE_GROUP" `
    --params "{ \`"tagName\`": { \`"value\`": \`"CostCenter\`" } }" `
    --enforcement-mode "DoNotEnforce"

Write-Host "Policy assignment created in Audit mode."
```

> **Note:** `DoNotEnforce` means the policy will flag non-compliant resources but won't block creation.

### Step 3.2 - Check Policy Compliance

```powershell
# Trigger a compliance scan
az policy state trigger-scan `
    --resource-group $RESOURCE_GROUP `
    --no-wait

Write-Host "Compliance scan triggered. Results available in 5-10 minutes."
Write-Host "Check: Azure Portal - Policy - Compliance"
```

### Step 3.3 - View Compliance Results (Portal)

1. Go to **Azure Portal** - **Policy** - **Compliance**
2. Filter by **Resource Group:** `rg-ai-finops-labs`
3. Click on `Audit: Require CostCenter tag on resources`
4. View which resources are compliant vs non-compliant

> **Expected Result:** Your Azure OpenAI and APIM resources should be **compliant** (you tagged them in Step 2.2/2.3). Any other untagged resources in the resource group will be flagged.

---

## Part 4 - Track Per-Team Usage with APIM Logs

### Step 4.1 - Enable APIM Logging to Application Insights

In the Azure Portal:

1. Go to **API Management** - your APIM instance
2. Navigate to **Diagnostics settings**
3. Click **+ Add diagnostic setting**
4. **Details:**
   - Name: `AI-Usage-Logging`
   - Select **Send to Log Analytics workspace** (or Application Insights)
   - Log categories: 
     - GatewayLogs (gateway traffic)
   - Metrics: (optional, check if desired)
5. Click **Save**

> This allows APIM to log all API calls with metadata (team, timestamp, tokens, etc.).

### Step 4.2 - Create a Test Script to Generate Usage Data

```powershell
function Send-TestRequest {
    param(
        [string]$TeamKey,
        [string]$TeamName,
        [int]$Count = 5
    )

    for ($i = 1; $i -le $Count; $i++) {
        $headers = @{
            "Content-Type"                   = "application/json"
                "api-key"                        = $TeamKey
        }
        $body = @{
            messages = @(
                @{ role = "user"; content = "What is Azure AI? Provide a detailed explanation." }
            )
            max_tokens = 150
        } | ConvertTo-Json

        try {
            $response = Invoke-WebRequest `
                -Uri "$APIM_GATEWAY/aoai-finops-lab/openai/deployments/gpt-4o/chat/completions?api-version=2024-10-21" `
                -Method POST `
                -Headers $headers `
                -Body $body

            $result = $response.Content | ConvertFrom-Json
            Write-Host "[$TeamName] Request $i OK - Tokens: $($result.usage.total_tokens)"
        }
        catch {
            Write-Host "[$TeamName] Request $i FAILED - $($_.Exception.Message)" -ForegroundColor Red
        }
        
        Start-Sleep -Milliseconds 500
    }
}

# Generate usage data for all teams
Write-Host "=== Generating usage data ==="
Send-TestRequest -TeamKey $KEY_CUSTOMERAI -TeamName "CustomerAI" -Count 5
Send-TestRequest -TeamKey $KEY_INTERNALOPS -TeamName "InternalOps" -Count 5
Send-TestRequest -TeamKey $KEY_RESEARCH -TeamName "Research" -Count 5

Write-Host "`nUsage data generated. Check APIM Logs Analytics in 2-3 minutes."
```

### Step 4.3 - Query Usage Data from Logs Analytics

In Azure Portal - your APIM instance - **Logs** (Analytics):

```kusto
// Query APIM logs for per-team usage
GatewayLogs
| where TimeGenerated > ago(1h)
| where isnotempty(SubscriptionId)
| summarize 
    RequestCount = count(),
    AvgResponseTime = avg(ResponseTime),
    MaxResponseTime = max(ResponseTime)
    by SubscriptionName, OperationId
| sort by RequestCount desc
```

> **Expected Result:** Table showing requests grouped by subscription (team) and operation.

---

## Part 5 - Query Costs from Cost Management

### Step 5.1 - View AI Costs in Cost Management

1. Go to **Azure Portal** - **Cost Management + Billing**
2. Click **Cost Analysis**
3. Filter by:
   - **Service name:** `Azure OpenAI Service`
   - **Resource group:** `rg-ai-finops-labs`
   - **Time period:** `Last 7 days`
4. Click **View by:** `Resource`
5. View costs broken down by Azure OpenAI instance

### Step 5.2 - Add Tag Dimension to Cost Analysis

1. In **Cost Analysis**, click **Group by** - **Tag**
2. Select tag: `Team`
3. View costs aggregated per team (CustomerAI, InternalOps, Research)

> **Expected Result:** Costs split by team, showing which team drove the most AI spend.

### Step 5.3 - Export Costs to CSV

```powershell
# Export cost data for further analysis
# In Azure Portal - Cost Management - Exports
# Create a new export:
# - Metric: Amortized Cost
# - Time period: Monthly (previous month)
# - Filter: Service name = "Azure OpenAI Service"
# - Storage: Use an Azure Storage account
# - Format: CSV
# - Recurrence: Monthly

Write-Host "Manual step: Create export in Azure Portal - Cost Management - Exports"
Write-Host "Select 'Last month' amortized costs for 'Azure OpenAI Service'"
Write-Host "Export file will be available in your storage account"
```

---

## Part 6 - Create a Chargeback Report (Excel/Power BI)

### Step 6.1 - Build a Chargeback Calculation Spreadsheet

Conceptual spreadsheet structure:

| Team | Deployment | Hours | Tokens Used | Unit Cost | Chargeback Amount | Department | Cost Center |
|------|-----------|-------|-------------|-----------|-------------------|------------|-------------|
| CustomerAI | gpt-4o | 720 | 5,000,000 | $0.00150 | $7,500 | Sales | CC-5001 |
| InternalOps | gpt-4o | 720 | 2,000,000 | $0.00150 | $3,000 | Engineering | CC-5002 |
| Research | gpt-4o | 720 | 500,000 | $0.00150 | $750 | R&D | CC-5003 |

**Formulas:**
- `Chargeback Amount = Tokens Used * Unit Cost`
- `Total Cost = SUM(Chargeback Amount)`

### Step 6.2 - Pull Actual Data via Azure CLI

```powershell
# Get actual token usage from Azure OpenAI metrics
$RESOURCE_ID = az cognitiveservices account show `
    --name $AOAI_NAME `
    --resource-group $RESOURCE_GROUP `
    --query id --output tsv

# Get total tokens processed in the last 7 days
az monitor metrics list `
    --resource $RESOURCE_ID `
    --metric "GeneratedCompletionTokens" `
    --interval PT1H `
    --start-time (Get-Date).AddDays(-7).ToString("yyyy-MM-ddTHH:mm:ssZ") `
    --end-time (Get-Date).ToString("yyyy-MM-ddTHH:mm:ssZ") `
    --query "value[0].timeseries[0].data[*].{Time:timeStamp, Tokens:total}" `
    --output table
```

### Step 6.3 - Calculate Pricing

Azure OpenAI GPT-4o pricing (as of lab creation):
- **Prompt tokens:** $0.00015 per 1K tokens
- **Completion tokens:** $0.00060 per 1K tokens
- **Combined average:** ~$0.00150 per 1K tokens (rough estimate)

**Chargeback formula:**
```
Monthly Chargeback = (Prompt Tokens * $0.00015 + Completion Tokens * $0.00060) / 1000
```

---

## Part 7 - Implement Showback Dashboards

### Step 7.1 - Create Power BI Dashboard (Optional)

If you have Power BI Premium:

1. In Power BI, create a new report
2. Connect to Cost Management data (via Azure Cost Management connector)
3. Create visualizations:
   - Bar chart: `Costs by Team`
   - Pie chart: `Cost distribution by deployment`
   - Table: `Top 10 projects by cost`
   - Trend: `Daily cost trend (last 30 days)`
4. Share dashboard with team for transparency

### Step 7.2 - Create a Monthly Chargeback Email

Send each team manager a monthly email with:

```
Subject: AI Usage Chargeback Report - February 2025

Hi Team Leads,

Your team's Azure AI usage for February 2025:

Customer AI Team:
- Tokens Processed: 5,000,000
- Estimated Cost: $7,500
- Primary Model: gpt-4o
- Top Project: Copilot-V2

InternalOps Team:
- Tokens Processed: 2,000,000
- Estimated Cost: $3,000
- Primary Model: gpt-4o
- Top Project: InternalBot

Research Team:
- Tokens Processed: 500,000
- Estimated Cost: $750
- Primary Model: gpt-4o
- Top Project: AIResearch-Exp

---
Total Organization Cost: $11,250

Questions? Contact: ai-finops@contoso.com
```

---

## Part 8 - Governance and Cost Controls

### Step 8.1 - Set Budget Alerts

In Azure Portal:

1. Go to **Cost Management + Billing** - **Budgets**
2. Click **+ Create**
3. **Budget Details:**
   - Name: `AI Team Budget - Q1 2025`
   - Reset period: `Monthly`
   - Creation date: `Today`
   - Expiration date: `March 31, 2025`
   - Amount: `$12,000`
4. **Set alerts:**
   - Alert at 50% threshold: email `ai-platform-team@contoso.com`
   - Alert at 100% threshold: email `finance-team@contoso.com`
5. Click **Create**

### Step 8.2 - Establish Quota Limits (Quota vs Budget)

- **Quotas (technical):** Enforce at Azure OpenAI service level (TPM/RPM limits)
- **Budgets (financial):** Alert when spend crosses thresholds
- **Rate Limiting (fairness):** APIM policies ensure fair token distribution per team

---

## Summary

You have successfully implemented a complete chargeback model:

1. ✓ Tagged Azure resources for cost tracking
2. ✓ Enforced tagging policies with Azure Policy
3. ✓ Enabled logging for per-team usage tracking
4. ✓ Queried costs from Cost Management
5. ✓ Built chargeback calculations and reports
6. ✓ Created showback dashboards
7. ✓ Set up budget alerts and governance

**Key differences from API key approach:**
- Authentication no longer requires managing API keys for each team
- APIM MI handles authentication centrally
- Cost tracking still works the same (tags, metrics, Cost Management)
- Chargeback methodology unchanged - based on token usage and team attribution

**Benefits of this approach:**
- Simpler authentication (managed identity, no key rotation)
- Better security (no API keys in configuration)
- Same cost governance and chargeback capabilities
- Audit trail of MI authentication for compliance

---

## Next Steps

- Deploy these labs to production after testing
- Extend to other AI services (Azure Cognitive Search, Document Intelligence, etc.)
- Implement automated monthly chargeback reports
- Set up cross-team cost optimization reviews
- Archive historical cost data for trend analysis

