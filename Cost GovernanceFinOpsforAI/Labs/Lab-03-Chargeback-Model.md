# Lab 3 - Chargeback Model for Azure AI

> **Objective:** Build an end-to-end chargeback/showback model that tracks AI costs by team, project, and model - from tagging resources, to emitting usage metrics, to generating chargeback reports.
>
> **Duration:** 60-75 minutes
>
> **Prerequisites:** Complete [00-Prerequisites.md](00-Prerequisites.md). Labs 1 and 2 are recommended but not required.

---

## Lab Variables

Set these at the start of the lab (from prerequisites):

```powershell
$RESOURCE_GROUP  = "rg-ai-finops-labs"
$AOAI_NAME       = "aoai-finops-lab"
$AOAI_ENDPOINT   = "<your-aoai-endpoint>"
$AOAI_KEY        = "<your-aoai-key>"
$APIM_NAME       = "<your-apim-name>"
$APIM_GATEWAY    = "<your-apim-gateway-url>"
$KEY_CUSTOMERAI  = "<subscription-key-for-CustomerAI>"
$KEY_INTERNALOPS = "<subscription-key-for-InternalOps>"
$KEY_RESEARCH    = "<subscription-key-for-Research>"
```

---

## Part 1 - Understand the Chargeback Architecture

### Step 1.1 - Review the End-to-End Chargeback Flow

```
                                       ------------------
                                       -  Cost Reports   -
                                       -  (Power BI /    -
                                       -   Excel)        -
                                       -------------------
                                               -
                                        ----------------
                                        - Cost Mgmt    -
                                        - Exports      -
                                        - (Daily CSV)  -
                                        ----------------
                                               -
  --------------------------------------------------------------------
  -                    Azure Cost Management                         -
  -  ----------------  ------------------  ---------------------    -
  -  - Resource Tags -  - Cost Allocation-  - Budget Alerts     -    -
  -  - (Team, CC)   -  - Rules          -  - (per cost center) -    -
  -  ----------------  ------------------  ---------------------    -
  --------------------------------------------------------------------
                                               -
                                               - Tags flow to billing
  ----------------    -------------------    ------------------
  - CustomerAI   ------  APIM Gateway   ------ Azure OpenAI   -
  - Team         -    -  (token metrics) -    - (tagged with   -
  ----------------    -                  -    -  CostCenter,   -
  - InternalOps  ------  Emits metrics   -    -  Team, etc.)   -
  - Team         -    -  per team        -    ------------------
  ----------------    -                  -
  - Research     ------  App Insights    -
  - Team         -    -  logs per call   -
  ----------------    -------------------
```

### Step 1.2 - Review Chargeback vs Showback

| Model | Description | When to Use |
|-------|-------------|-------------|
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

## Part 4 - Track Per-Team Usage with APIM + Application Insights

### Step 4.1 - Configure APIM to Log Team and Token Data

Update the APIM policy to log detailed chargeback data. Go to the APIM policy editor for the **Azure OpenAI** API:

```xml
<policies>
    <inbound>
        <base />
        <set-header name="api-key" exists-action="override">
            <value>{{aoai-key}}</value>
        </set-header>
        <!-- Capture team identity for chargeback -->
        <set-variable name="teamName" value="@(context.Subscription.Name)" />
        <set-variable name="requestTimestamp" value="@(DateTime.UtcNow.ToString("o"))" />
    </inbound>
    <backend>
        <base />
    </backend>
    <outbound>
        <base />
        <!-- Emit token metrics with chargeback dimensions -->
        <azure-openai-emit-token-metric namespace="AIChargeback">
            <dimension name="Team" value="@(context.Variables.GetValueOrDefault<string>("teamName"))" />
            <dimension name="Model" value="gpt-4o-mini" />
            <dimension name="Operation" value="ChatCompletion" />
            <dimension name="Environment" value="Lab" />
        </azure-openai-emit-token-metric>

        <!-- Add chargeback headers to response -->
        <set-header name="x-chargeback-team" exists-action="override">
            <value>@(context.Variables.GetValueOrDefault<string>("teamName"))</value>
        </set-header>
        <set-header name="x-chargeback-model" exists-action="override">
            <value>gpt-4o-mini</value>
        </set-header>

        <!-- Log to Application Insights for detailed chargeback records -->
        <trace source="chargeback" severity="information">
            <message>@{
                var responseBody = context.Response.Body.As<JObject>(preserveContent: true);
                var usage = responseBody?["usage"];
                return new JObject(
                    new JProperty("team", context.Variables.GetValueOrDefault<string>("teamName")),
                    new JProperty("model", "gpt-4o-mini"),
                    new JProperty("prompt_tokens", usage?["prompt_tokens"]),
                    new JProperty("completion_tokens", usage?["completion_tokens"]),
                    new JProperty("total_tokens", usage?["total_tokens"]),
                    new JProperty("timestamp", context.Variables.GetValueOrDefault<string>("requestTimestamp")),
                    new JProperty("operation_id", context.RequestId)
                ).ToString();
            }</message>
        </trace>
    </outbound>
    <on-error>
        <base />
    </on-error>
</policies>
```

Click **Save**.

### Step 4.2 - Generate Chargeback Traffic

Send traffic from all three teams to build up usage data:

```powershell
# Helper function (reuse from Lab 1 or define here)
function Send-ChargebackRequest {
    param([string]$TeamKey, [string]$TeamName, [string]$Prompt, [int]$MaxTokens = 200)

    $headers = @{
        "Content-Type"       = "application/json"
            "api-key"            = $TeamKey
    }
    $body = @{
        messages = @(
            @{ role = "user"; content = $Prompt }
        )
        max_tokens = $MaxTokens
    } | ConvertTo-Json

    try {
        $response = Invoke-WebRequest `
            -Uri "$APIM_GATEWAY/aoai-finops-lab/openai/deployments/gpt-4o-mini/chat/completions?api-version=2024-10-21" `
            -Method POST `
            -Headers $headers `
            -Body $body

        $result = $response.Content | ConvertFrom-Json
        $team = $response.Headers['x-chargeback-team']
        Write-Host "[$TeamName] Tokens: $($result.usage.total_tokens) | Prompt: $($result.usage.prompt_tokens) | Completion: $($result.usage.completion_tokens)" -ForegroundColor Green
        return $result.usage
    }
    catch {
        Write-Host "[$TeamName] Error: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Simulate realistic traffic patterns
# CustomerAI: Heavy usage (production customer-facing)
Write-Host "`n=== CustomerAI Traffic (Heavy) ==="
$customerPrompts = @(
    "Summarize this customer complaint and suggest resolution steps for our support team.",
    "Generate a personalized product recommendation based on browsing history and purchase patterns.",
    "Draft a professional email response to a customer inquiry about our enterprise plan pricing.",
    "Analyze customer sentiment from this review and categorize it.",
    "Create a troubleshooting guide for common product issues."
)
foreach ($prompt in $customerPrompts) {
    Send-ChargebackRequest -TeamKey $KEY_CUSTOMERAI -TeamName "CustomerAI" -Prompt $prompt -MaxTokens 300
    Start-Sleep -Seconds 1
}

# InternalOps: Medium usage (internal productivity)
Write-Host "`n=== InternalOps Traffic (Medium) ==="
$opsPrompts = @(
    "Summarize the key points from this meeting transcript.",
    "Generate a weekly status report template.",
    "Draft an internal announcement about the system maintenance window."
)
foreach ($prompt in $opsPrompts) {
    Send-ChargebackRequest -TeamKey $KEY_INTERNALOPS -TeamName "InternalOps" -Prompt $prompt -MaxTokens 200
    Start-Sleep -Seconds 1
}

# Research: Light usage (experimentation)
Write-Host "`n=== Research Traffic (Light) ==="
$researchPrompts = @(
    "Compare transformer and RNN architectures for sequence modeling.",
    "What are the latest advances in prompt engineering?"
)
foreach ($prompt in $researchPrompts) {
    Send-ChargebackRequest -TeamKey $KEY_RESEARCH -TeamName "Research" -Prompt $prompt -MaxTokens 150
    Start-Sleep -Seconds 1
}

Write-Host "`nTraffic generation complete."
```

### Step 4.3 - Calculate Cost Per Team

```powershell
# Define Azure OpenAI pricing (gpt-4o-mini)
$PRICE_PER_1K_INPUT_TOKENS  = 0.00015   # $0.15 per 1M input tokens
$PRICE_PER_1K_OUTPUT_TOKENS = 0.0006    # $0.60 per 1M output tokens

# Simulated usage summary (replace with your actual numbers from Step 4.2)
$teamUsage = @(
    @{ Team = "CustomerAI";  PromptTokens = 850;  CompletionTokens = 1200 },
    @{ Team = "InternalOps"; PromptTokens = 450;  CompletionTokens = 500 },
    @{ Team = "Research";    PromptTokens = 300;  CompletionTokens = 250 }
)

Write-Host "`n=== Chargeback Cost Calculation ===" -ForegroundColor Cyan
Write-Host ("{0,-15} {1,15} {2,15} {3,15} {4,15}" -f "Team", "Input Tokens", "Output Tokens", "Input Cost", "Output Cost", "Total Cost")
Write-Host ("-" * 80)

$totalCost = 0
foreach ($team in $teamUsage) {
    $inputCost  = ($team.PromptTokens / 1000) * $PRICE_PER_1K_INPUT_TOKENS
    $outputCost = ($team.CompletionTokens / 1000) * $PRICE_PER_1K_OUTPUT_TOKENS
    $teamCost   = $inputCost + $outputCost
    $totalCost += $teamCost

    Write-Host ("{0,-15} {1,15:N0} {2,15:N0} {3,15:C6} {4,15:C6}" -f `
        $team.Team, $team.PromptTokens, $team.CompletionTokens, $inputCost, $outputCost)
}
Write-Host ("-" * 80)
Write-Host ("TOTAL COST: {0:C6}" -f $totalCost)
```

> **Expected Result:** A table showing each team's token consumption and calculated cost. Even small numbers illustrate the chargeback model.

---

## Part 5 - Query Usage Data from Application Insights

### Step 5.1 - Open Application Insights Logs

1. Go to **Azure Portal** - **Application Insights** (linked to APIM)
2. Navigate to **Logs** (Log Analytics)

### Step 5.2 - Run the Chargeback Query

Paste this KQL query to extract per-team usage:

```kql
// Chargeback report: Token usage by team and model
traces
| where message contains "chargeback" or customDimensions contains "team"
| extend chargebackData = parse_json(message)
| extend 
    Team = tostring(chargebackData.team),
    Model = tostring(chargebackData.model),
    PromptTokens = toint(chargebackData.prompt_tokens),
    CompletionTokens = toint(chargebackData.completion_tokens),
    TotalTokens = toint(chargebackData.total_tokens)
| where isnotempty(Team)
| summarize 
    TotalRequests = count(),
    TotalPromptTokens = sum(PromptTokens),
    TotalCompletionTokens = sum(CompletionTokens),
    TotalTokensUsed = sum(TotalTokens),
    AvgTokensPerRequest = avg(TotalTokens)
    by Team, Model
| extend 
    InputCost = (TotalPromptTokens / 1000.0) * 0.00015,
    OutputCost = (TotalCompletionTokens / 1000.0) * 0.0006,
    TotalCost = ((TotalPromptTokens / 1000.0) * 0.00015) + ((TotalCompletionTokens / 1000.0) * 0.0006)
| project Team, Model, TotalRequests, TotalPromptTokens, TotalCompletionTokens, 
          TotalTokensUsed, AvgTokensPerRequest, InputCost, OutputCost, TotalCost
| order by TotalCost desc
```

> **Expected Result:** A table showing each team's total requests, tokens, and calculated cost.

### Step 5.3 - Run the Daily Trend Query

```kql
// Daily chargeback trend
traces
| where message contains "chargeback"
| extend chargebackData = parse_json(message)
| extend 
    Team = tostring(chargebackData.team),
    TotalTokens = toint(chargebackData.total_tokens)
| where isnotempty(Team)
| summarize DailyTokens = sum(TotalTokens), RequestCount = count() by Team, bin(timestamp, 1d)
| order by timestamp desc, Team
```

### Step 5.4 - Run the Cost Breakdown by Operation

```kql
// Token usage by team and operation type
customMetrics
| where name == "Total Tokens" and customDimensions has "Team"
| extend 
    Team = tostring(customDimensions.Team),
    Model = tostring(customDimensions.Model),
    Operation = tostring(customDimensions.Operation)
| summarize 
    TotalTokens = sum(value),
    RequestCount = count()
    by Team, Model, Operation
| order by TotalTokens desc
```

---

## Part 6 - Set Up Azure Cost Management for AI Chargeback

### Step 6.1 - Create Cost Allocation Rules

Cost Allocation Rules redistribute shared resource costs to specific cost centers.

1. Go to **Azure Portal** - **Cost Management** - **Cost allocation (Preview)**
2. Click **+ Add** to create a new rule
3. Configure:
   - **Name:** `AI-Platform-Allocation`
   - **Source:** Resources tagged with `Team = AI-Platform`
   - **Targets:**

| Target | Allocation % | Cost Center |
|--------|-------------|-------------|
| CustomerAI | 50% | CC-5001 |
| InternalOps | 30% | CC-5002 |
| Research | 20% | CC-5003 |

4. Click **Create**

> **Note:** Cost allocation rules take up to **24 hours** to appear in Cost Analysis views.

### Step 6.2 - Create a Cost Management View by Tag

1. Go to **Cost Management** - **Cost analysis**
2. Set the scope to your **resource group** (`rg-ai-finops-labs`)
3. Click **Group by** - **Tag** - `CostCenter`
4. Set the date range to include today
5. **Save** as a custom view: `AI Chargeback by Cost Center`

### Step 6.3 - Create Per-Team Budgets

```powershell
# Get the resource group ID
$rgId = az group show --name $RESOURCE_GROUP --query id --output tsv

# Create budget for CustomerAI team ($100/month)
az consumption budget create `
    --budget-name "Budget-CustomerAI" `
    --amount 100 `
    --time-grain "Monthly" `
    --start-date "$(Get-Date -Format 'yyyy-MM-01')" `
    --end-date "$(Get-Date -Day 1 -Month 1 -Year ((Get-Date).Year + 1) -Format 'yyyy-MM-dd')" `
    --resource-group $RESOURCE_GROUP `
    --category "Cost" `
    --filter "{ \`"Tags\`": { \`"Name\`": \`"CostCenter\`", \`"Values\`": [\`"CC-5001\`"] } }"

# Create budget for InternalOps team ($50/month)
az consumption budget create `
    --budget-name "Budget-InternalOps" `
    --amount 50 `
    --time-grain "Monthly" `
    --start-date "$(Get-Date -Format 'yyyy-MM-01')" `
    --end-date "$(Get-Date -Day 1 -Month 1 -Year ((Get-Date).Year + 1) -Format 'yyyy-MM-dd')" `
    --resource-group $RESOURCE_GROUP `
    --category "Cost" `
    --filter "{ \`"Tags\`": { \`"Name\`": \`"CostCenter\`", \`"Values\`": [\`"CC-5002\`"] } }"

# Create budget for Research team ($25/month)
az consumption budget create `
    --budget-name "Budget-Research" `
    --amount 25 `
    --time-grain "Monthly" `
    --start-date "$(Get-Date -Format 'yyyy-MM-01')" `
    --end-date "$(Get-Date -Day 1 -Month 1 -Year ((Get-Date).Year + 1) -Format 'yyyy-MM-dd')" `
    --resource-group $RESOURCE_GROUP `
    --category "Cost" `
    --filter "{ \`"Tags\`": { \`"Name\`": \`"CostCenter\`", \`"Values\`": [\`"CC-5003\`"] } }"

Write-Host "Team budgets created successfully."
```

### Step 6.4 - Verify Budgets

```powershell
az consumption budget list `
    --resource-group $RESOURCE_GROUP `
    --query "[].{Name:name, Amount:amount, TimeGrain:timeGrain}" `
    --output table
```

> **Expected Result:**
> | Name | Amount | TimeGrain |
> |------|--------|-----------|
> | Budget-CustomerAI | 100 | Monthly |
> | Budget-InternalOps | 50 | Monthly |
> | Budget-Research | 25 | Monthly |

---

## Part 7 - Export Cost Data for Reporting

### Step 7.1 - Create a Cost Management Export

```powershell
# Create a storage account for cost exports
$STORAGE_NAME = "stfinopslabexport$(Get-Random -Maximum 9999)"

az storage account create `
    --name $STORAGE_NAME `
    --resource-group $RESOURCE_GROUP `
    --location "eastus" `
    --sku "Standard_LRS"

# Create a container for exports
az storage container create `
    --name "cost-exports" `
    --account-name $STORAGE_NAME
```

### Step 7.2 - Configure the Export (Portal)

1. Go to **Cost Management** - **Exports**
2. Click **+ Add**
3. Configure:
   - **Name:** `AI-Daily-Chargeback-Export`
   - **Export type:** `Daily export of month-to-date costs`
   - **Storage account:** Select `stfinopslabexportXXXX`
   - **Container:** `cost-exports`
   - **Directory:** `chargeback`
   - **File format:** CSV
4. Click **Create**

### Step 7.3 - Run an Immediate Export

1. In the **Exports** page, find your export
2. Click **Run now**
3. Wait 1-2 minutes for the export to complete

### Step 7.4 - Download and Review the Export

```powershell
# List exported files
az storage blob list `
    --container-name "cost-exports" `
    --account-name $STORAGE_NAME `
    --query "[].name" --output table

# Download the latest export
$blobName = az storage blob list `
    --container-name "cost-exports" `
    --account-name $STORAGE_NAME `
    --query "[-1].name" --output tsv

az storage blob download `
    --container-name "cost-exports" `
    --account-name $STORAGE_NAME `
    --name $blobName `
    --file "chargeback-export.csv"

# Preview the file
Get-Content "chargeback-export.csv" | Select-Object -First 10
```

> **Expected Result:** A CSV file with columns like `Date`, `ResourceName`, `ResourceType`, `Cost`, `Tags`, etc. The `Tags` column contains your `CostCenter`, `Team`, etc.

---

## Part 8 - Build a Chargeback Summary Report

### Step 8.1 - Create a PowerShell Chargeback Report

```powershell
# Generate a formatted chargeback report from the export
$exportData = Import-Csv "chargeback-export.csv"

# Filter for Cognitive Services (Azure OpenAI)
$aiCosts = $exportData | Where-Object {
    $_.MeterCategory -eq "Cognitive Services" -or
    $_.ResourceType -like "*CognitiveServices*"
}

Write-Host "`n" -NoNewline
Write-Host "------------------------------------------------------------" -ForegroundColor Cyan
Write-Host "-          AI COST CHARGEBACK REPORT                      -" -ForegroundColor Cyan
Write-Host "-          Period: $(Get-Date -Format 'MMMM yyyy')                         -" -ForegroundColor Cyan
Write-Host "------------------------------------------------------------" -ForegroundColor Cyan

if ($aiCosts) {
    Write-Host "`n--- Cost by Resource ---"
    $aiCosts | Group-Object ResourceId | ForEach-Object {
        $totalCost = ($_.Group | Measure-Object -Property PreTaxCost -Sum).Sum
        Write-Host ("  {0}: {1:C4}" -f $_.Name.Split('/')[-1], $totalCost)
    }

    Write-Host "`n--- Cost by Tag (CostCenter) ---"
    $aiCosts | ForEach-Object {
        $tags = $_.Tags | ConvertFrom-Json -ErrorAction SilentlyContinue
        [PSCustomObject]@{
            CostCenter = $tags.CostCenter
            Cost = [decimal]$_.PreTaxCost
        }
    } | Group-Object CostCenter | ForEach-Object {
        $totalCost = ($_.Group | Measure-Object -Property Cost -Sum).Sum
        Write-Host ("  {0}: {1:C4}" -f $_.Name, $totalCost)
    }
}
else {
    Write-Host "`nNote: Cost data may take 24-48 hours to appear for new resources."
    Write-Host "For the lab, use the simulated data from Part 4 Step 4.3."
}

Write-Host "`n--- Team Allocation (Based on Token Usage) ---"
Write-Host "  CustomerAI  (CC-5001): 50% of shared AI platform cost"
Write-Host "  InternalOps (CC-5002): 30% of shared AI platform cost"
Write-Host "  Research    (CC-5003): 20% of shared AI platform cost"
Write-Host "`n  Allocation based on actual token consumption via APIM metrics."
Write-Host "  See Application Insights - AIChargeback metrics for real-time data."
```

---

## Part 9 - Automate Monthly Chargeback with Logic Apps (Optional)

### Step 9.1 - Architecture Overview

For production chargeback automation:

```
----------------    ----------------    ----------------    ----------------
- Cost Mgmt    ------ Logic App    ------ Process &    ------ Email Report -
- Daily Export -    - (Monthly     -    - Calculate    -    - to Finance + -
- (CSV to Blob)-    -  Trigger)    -    - Per-Team $   -    - Team Leads   -
----------------    ----------------    ----------------    ----------------
```

### Step 9.2 - Logic App Workflow (Description)

1. **Trigger:** Monthly recurrence (1st of each month)
2. **Action 1:** Read latest cost export CSV from Storage
3. **Action 2:** Filter for Cognitive Services resources
4. **Action 3:** Group costs by `CostCenter` tag
5. **Action 4:** Apply allocation percentages for shared resources
6. **Action 5:** Generate HTML report table
7. **Action 6:** Send email to Finance team + team leads

> **Note:** Full Logic App deployment is beyond this lab scope. The key takeaway is that cost exports + Logic Apps = automated chargeback reports.

---

## Clean Up (Optional)

```powershell
# Remove the policy assignment
az policy assignment delete --name "audit-costcenter-tag" `
    --scope "/subscriptions/$(az account show --query id --output tsv)/resourceGroups/$RESOURCE_GROUP"

# Remove budgets
az consumption budget delete --budget-name "Budget-CustomerAI" --resource-group $RESOURCE_GROUP
az consumption budget delete --budget-name "Budget-InternalOps" --resource-group $RESOURCE_GROUP
az consumption budget delete --budget-name "Budget-Research" --resource-group $RESOURCE_GROUP

# Remove storage account for exports
# az storage account delete --name $STORAGE_NAME --resource-group $RESOURCE_GROUP --yes

Write-Host "Lab resources cleaned up."
```

---

## Summary

In this lab you:

| Step | What You Did |
|------|--------------|
| Part 1 | Understood the end-to-end chargeback architecture |
| Part 2 | Applied a consistent tagging strategy to AI resources |
| Part 3 | Enforced tagging with Azure Policy (audit mode) |
| Part 4 | Tracked per-team usage via APIM token metrics and Application Insights |
| Part 5 | Queried chargeback data using KQL in Application Insights |
| Part 6 | Set up Cost Management views, cost allocation rules, and per-team budgets |
| Part 7 | Created cost exports to storage for reporting |
| Part 8 | Built a PowerShell chargeback summary report |
| Part 9 | Reviewed automation architecture for monthly chargeback |

### Key Takeaways

- **Tags are the foundation** - without consistent tagging, chargeback is impossible
- **Azure Policy enforces compliance** - start with audit mode, graduate to deny mode
- **APIM metrics bridge the gap** - Azure Cost Management shows resource cost, APIM metrics show per-team consumption
- **Cost allocation rules** handle shared resources - split shared AI platform costs to consuming teams
- **Exports enable automation** - daily CSV exports + Logic Apps = monthly chargeback reports
- **Two layers of cost data** - Azure Cost Management (billing data, 24-48h delay) + Application Insights (real-time token metrics)

### Chargeback Maturity Model

| Level | Capability | You Built This |
|-------|-----------|----------------|
| 1 - Visibility | See total AI spend | - Part 6 |
| 2 - Allocation | Attribute costs to teams | - Parts 2, 4, 5 |
| 3 - Showback | Teams can see their own costs | - Parts 5, 6 |
| 4 - Chargeback | Costs flow to team P&Ls | - Parts 6, 7, 8 |
| 5 - Optimization | Teams actively reduce costs | Requires ongoing FinOps practice |

---

> **Congratulations!** You have completed all three labs. You now have hands-on experience with:
> - **Lab 1:** Token rate limiting at the API gateway layer
> - **Lab 2:** Quota management at the Azure OpenAI service layer  
> - **Lab 3:** End-to-end chargeback/showback for AI costs

