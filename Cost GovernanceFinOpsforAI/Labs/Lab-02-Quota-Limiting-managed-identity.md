# Lab 2 - Azure OpenAI Quota Limiting (Managed Identity)

> **Objective:** Configure and manage Azure OpenAI quota (TPM/RPM) at the subscription, model, and deployment level. Observe quota enforcement, test dynamic quota, and set up alerts for quota utilization.
>
> **Authentication:** Uses **APIM Managed Identity** (not API keys) to authenticate to Azure OpenAI.
>
> **Duration:** 45-60 minutes
>
> **Prerequisites:** Complete [00-Prerequisites-managed-identity.md](00-Prerequisites-managed-identity.md)

---

## Lab Variables

**Critical: Use exact APIM subscription names for key retrieval.** Copy this recovery block and run it first:

```powershell
# === RECOVER ALL VARIABLES ===
$RESOURCE_GROUP = "rg-ai-finops-labs"
$AOAI_NAME      = "aoai-finops-lab"
$APIM_NAME      = az apim list --resource-group $RESOURCE_GROUP --query "[0].name" --output tsv
$APIM_GATEWAY   = az apim show --name $APIM_NAME --resource-group $RESOURCE_GROUP --query "gatewayUrl" --output tsv

# === RETRIEVE KEYS FROM APIM (exact subscription names: lowercase with hyphen) ===
$SUBSCRIPTION_ID = az account show --query id --output tsv
$BASE_MGMT = "https://management.azure.com/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.ApiManagement/service/$APIM_NAME"

# Use exact subscription names (IDs) as shown in APIM portal
$KEY_CUSTOMERAI = az rest --method POST --uri "$BASE_MGMT/subscriptions/customerai-team/listSecrets?api-version=2022-08-01" --query primaryKey -o tsv

# Verify key loaded (must show 32)
Write-Host "CustomerAI: $($KEY_CUSTOMERAI.Length) chars (expected: 32)"
```

> **IMPORTANT MAPPING:**
> - **APIM Subscription ID** (for key retrieval): `customerai-team` → **PowerShell Variable**: `$KEY_CUSTOMERAI`
>
> This is an **APIM subscription key** (for client→APIM authentication), NOT an Azure OpenAI API key.
> All authentication to Azure OpenAI goes through APIM managed identity.

---

## Part 1 - Understand Azure OpenAI Quota Architecture

### Step 1.1 - Review the Quota Hierarchy

Azure OpenAI enforces quota at multiple levels:

```
Quota Architecture:
- Azure Subscription level
  - Regional quota (e.g., East US)
    - Model quota (e.g., gpt-4o)
      - Deployment A (30K TPM)
      - Deployment B (20K TPM)
    - Model quota total: sum of all deployments for that model
  - Regional quota total: sum of all models in that region
- Subscription quota total: sum of all regions

Key concepts:
- TPM (Tokens Per Minute): Primary quota unit
- RPM (Requests Per Minute): Secondary limit, auto-calculated from TPM
- Deployment quota: Allocated from the model's regional quota pool
- Dynamic quota: Temporary bursts allowed when capacity available
```

### Step 1.2 - View Your Current Quota

```powershell
# View current model quota usage for the subscription
az cognitiveservices usage list `
    --location "eastus" `
    --query "[?contains(name.value, 'OpenAI')].{Model:name.value, Current:currentValue, Limit:limit}" `
    --output table
```

> **Expected Result:** A table showing each model's current quota usage and limits for your subscription in East US.

### Step 1.3 - View Deployment Quota Allocation

```powershell
# List deployments and their quota allocations
az cognitiveservices account deployment list `
    --name $AOAI_NAME `
    --resource-group $RESOURCE_GROUP `
    --query "[].{Name:name, Model:properties.model.name, TPM:sku.capacity, Status:properties.provisioningState}" `
    --output table
```

> **Expected Result:** Shows your `gpt-4o` deployment with 30 (= 30K TPM) capacity.

---

## Part 2 - Test Quota Enforcement

### Step 2.1 - Understand Quota vs Rate Limiting

| Aspect | Azure OpenAI Quota | APIM Token Limit (Lab 1) |
|--------|-------------------|--------------------------|
| **Enforced by** | Azure OpenAI service | APIM gateway |
| **Scope** | Per deployment | Per APIM subscription |
| **Unit** | TPM at deployment level | TPM at team level |
| **Error code** | HTTP 429 with `quota` reason | HTTP 429 with custom message |
| **Purpose** | Protects Azure's shared infrastructure | Governs your internal teams |

### Step 2.2 - Create a Helper Function

```powershell
function Invoke-AOAIViaAPIM {
    param(
        [string]$Prompt,
        [int]$MaxTokens = 200,
        [string]$Label = "Test",
        [string]$TeamKey = $KEY_CUSTOMERAI
    )

    # Prefer canonical gateway from APIM_NAME to avoid stale APIM_GATEWAY values in long sessions.
    if (-not [string]::IsNullOrWhiteSpace($APIM_NAME)) {
        $gateway = ("https://{0}.azure-api.net" -f $APIM_NAME).TrimEnd('/')
    }
    else {
        $gateway = $APIM_GATEWAY.TrimEnd('/')
    }
    $uri = "$gateway/aoai-finops-lab/openai/deployments/gpt-4o/chat/completions?api-version=2024-10-21"

    $headers = @{
        "Content-Type"                   = "application/json"
        "api-key"                        = $TeamKey
    }
    $body = @{
        messages = @(
            @{ role = "user"; content = $Prompt }
        )
        max_tokens = $MaxTokens
    } | ConvertTo-Json

    try {
        $response = Invoke-WebRequest `
            -Uri $uri `
            -Method POST `
            -Headers $headers `
            -Body $body `
            -SkipHttpErrorCheck

        # APIM can briefly return 404 during gateway config propagation; retry once immediately.
        if ($response.StatusCode -eq 404) {
            $response = Invoke-WebRequest `
                -Uri $uri `
                -Method POST `
                -Headers $headers `
                -Body $body `
                -SkipHttpErrorCheck
        }

        if ($response.StatusCode -ne 200) {
            Write-Host "[$Label] Status: $($response.StatusCode) | Body: $($response.Content)" -ForegroundColor Red
            return $null
        }

        $result = $response.Content | ConvertFrom-Json
        $remaining = $response.Headers['x-ratelimit-remaining-tokens']
        Write-Host "[$Label] Status: 200 | Tokens: $($result.usage.total_tokens) | Remaining TPM: $remaining" -ForegroundColor Green
        return $result
    }
    catch {
        Write-Host "[$Label] Request failed before response parsing: $($_.Exception.Message)" -ForegroundColor Red
    }
}
```

### Step 2.3 - Send Requests and Observe Quota Headers

```powershell
# Send a single request through APIM and examine the rate limit headers
# This block is self-contained: it rebuilds key + URI every run to avoid stale shell variables.
$ErrorActionPreference = 'Stop'
Remove-Variable uri, headers, body, response, gateway, baseMgmt, subscriptionId -ErrorAction SilentlyContinue

$subscriptionId = az account show --query id --output tsv
$resourceGroup = "rg-ai-finops-labs"
$apimName = "apim-finops-lab-9091"
$apimGateway = "https://$apimName.azure-api.net"
$baseMgmt = "https://management.azure.com/subscriptions/$subscriptionId/resourceGroups/$resourceGroup/providers/Microsoft.ApiManagement/service/$apimName"

# Always fetch a fresh key for this step
$KEY_CUSTOMERAI = az rest --method POST --uri "$baseMgmt/subscriptions/customerai-team/listSecrets?api-version=2022-08-01" --query primaryKey -o tsv

$gateway = $apimGateway.TrimEnd('/')
$uri = "$gateway/aoai-finops-lab/openai/deployments/gpt-4o/chat/completions?api-version=2024-10-21"

Write-Host "Using APIM_GATEWAY: $apimGateway"
Write-Host "Request URI: $uri"
Write-Host "KEY_CUSTOMERAI length: $($KEY_CUSTOMERAI.Length)"

if ($KEY_CUSTOMERAI.Length -ne 32) {
    throw "KEY_CUSTOMERAI retrieval failed (expected length 32)."
}

$headers = @{
    "Content-Type"                   = "application/json"
    "api-key"                        = $KEY_CUSTOMERAI
}
$body = @{
    messages = @(
        @{ role = "user"; content = "What is Azure?" }
    )
    max_tokens = 100
} | ConvertTo-Json

$response = Invoke-WebRequest `
    -Uri $uri `
    -Method POST `
    -Headers $headers `
    -Body $body `
    -SkipHttpErrorCheck

Write-Host "Status: $($response.StatusCode)"
if ($response.StatusCode -ne 200) {
    Write-Host "Response body: $($response.Content)"
}

if ($response.StatusCode -eq 404) {
    Write-Host "Troubleshooting hint: 404 indicates APIM did not route to an existing backend path in this request." -ForegroundColor Yellow
    Write-Host "Copy and run this full Step 2.3 block exactly as-is in one execution." -ForegroundColor Yellow
}

# Examine all rate-limit response headers
Write-Host "`n=== Rate Limit Headers from Azure OpenAI (through APIM) ==="
$response.Headers.GetEnumerator() | Where-Object { $_.Key -like "*ratelimit*" -or $_.Key -like "*retry*" } | ForEach-Object {
    Write-Host "$($_.Key): $($_.Value)"
}
```

> **Expected Result:** You should see headers like:
> - `x-ratelimit-remaining-tokens`: Tokens remaining in current window
> - `x-ratelimit-remaining-requests`: Requests remaining in current window
> These reflect your deployment's 30K TPM allocation.

### Step 2.4 - Stress Test the Quota

```powershell
# Send rapid requests to approach the quota limit
Write-Host "=== Sending 20 rapid requests to test quota boundary ==="

$subscriptionId = az account show --query id --output tsv
$resourceGroup = "rg-ai-finops-labs"
$apimName = "apim-finops-lab-9091"
$apimGateway = "https://$apimName.azure-api.net"
$baseMgmt = "https://management.azure.com/subscriptions/$subscriptionId/resourceGroups/$resourceGroup/providers/Microsoft.ApiManagement/service/$apimName"
$keyCustomerAI = az rest --method POST --uri "$baseMgmt/subscriptions/customerai-team/listSecrets?api-version=2022-08-01" --query primaryKey -o tsv

$uri = "$($apimGateway.TrimEnd('/'))/aoai-finops-lab/openai/deployments/gpt-4o/chat/completions?api-version=2024-10-21"

for ($i = 1; $i -le 20; $i++) {
    $headers = @{ "Content-Type" = "application/json"; "api-key" = $keyCustomerAI }
    $body = (@{
        messages = @(
            @{ role = "user"; content = "Write a detailed paragraph about cloud computing trend number $i. Include specific technologies, market data, and predictions for the next 5 years." }
        )
        max_tokens = 500
    } | ConvertTo-Json -Depth 5)

    $response = $null
    for ($attempt = 1; $attempt -le 3; $attempt++) {
        $response = Invoke-WebRequest -Uri $uri -Method POST -Headers $headers -Body $body -SkipHttpErrorCheck
        if ($response.StatusCode -ne 404) { break }
    }

    if ($response.StatusCode -eq 200) {
        $result = $response.Content | ConvertFrom-Json
        $remaining = $response.Headers['x-ratelimit-remaining-tokens']
        Write-Host "[Req-$i] Status: 200 | Tokens: $($result.usage.total_tokens) | Remaining TPM: $remaining" -ForegroundColor Green
    }
    elseif ($response.StatusCode -eq 429) {
        $retryAfter = $response.Headers['Retry-After']
        Write-Host "[Req-$i] Status: 429 QUOTA EXCEEDED | Retry-After: $retryAfter" -ForegroundColor Yellow
    }
    else {
        $apimRequestId = $response.Headers['apim-request-id']
        Write-Host "[Req-$i] Status: $($response.StatusCode) | APIM Request ID: $apimRequestId | Body: $($response.Content)" -ForegroundColor Red
    }
}
```

> If you edited this lab during your session, rerun **Step 2.2** before Step 2.4 so your terminal has the latest function definition.

> **Expected Result:** As you approach the deployment's TPM limit, you'll see the `Remaining TPM` decrease. If you exceed it, you'll get HTTP 429 responses with a `Retry-After` header.

---

## Part 3 - Modify Deployment Quota

### Step 3.1 - Reduce Quota to Observe Limiting Faster

Lower the deployment quota to make rate limiting more visible in the lab:

```powershell
# Reduce deployment to 10K TPM (minimum for testing)
az cognitiveservices account deployment create `
    --name $AOAI_NAME `
    --resource-group $RESOURCE_GROUP `
    --deployment-name "gpt-4o" `
    --model-name "gpt-4o" `
    --model-version "2024-11-20" `
    --model-format "OpenAI" `
    --sku-capacity 10 `
    --sku-name "Standard"
```

> **Note:** This updates the existing deployment in-place. The `--sku-capacity 10` means 10K TPM.

### Step 3.2 - Verify the New Quota

```powershell
# Confirm the new capacity
az cognitiveservices account deployment list `
    --name $AOAI_NAME `
    --resource-group $RESOURCE_GROUP `
    --query "[].{Name:name, TPM:sku.capacity}" `
    --output table
```

> **Expected Result:** The `gpt-4o` deployment should now show capacity of `10`.

### Step 3.3 - Test With Reduced Quota

```powershell
# Repeat the stress test - should hit limits faster
# This block is self-contained to avoid stale variable issues
$subscriptionId = az account show --query id --output tsv
$resourceGroup = "rg-ai-finops-labs"
$apimName = "apim-finops-lab-9091"
$apimGateway = "https://$apimName.azure-api.net"
$baseMgmt = "https://management.azure.com/subscriptions/$subscriptionId/resourceGroups/$resourceGroup/providers/Microsoft.ApiManagement/service/$apimName"
$keyCustomerAI = az rest --method POST --uri "$baseMgmt/subscriptions/customerai-team/listSecrets?api-version=2022-08-01" --query primaryKey -o tsv

$uri = "$($apimGateway.TrimEnd('/'))/aoai-finops-lab/openai/deployments/gpt-4o/chat/completions?api-version=2024-10-21"

Write-Host "=== Testing with reduced 10K TPM quota ==="
for ($i = 1; $i -le 15; $i++) {
    $headers = @{ "Content-Type" = "application/json"; "api-key" = $keyCustomerAI }
    $body = (@{
        messages = @(
            @{ role = "user"; content = "Explain in detail the architecture of a distributed microservices system for e-commerce, including all components." }
        )
        max_tokens = 500
    } | ConvertTo-Json -Depth 5)

    $response = $null
    for ($attempt = 1; $attempt -le 3; $attempt++) {
        $response = Invoke-WebRequest -Uri $uri -Method POST -Headers $headers -Body $body -SkipHttpErrorCheck
        if ($response.StatusCode -ne 404) { break }
    }

    if ($response.StatusCode -eq 200) {
        $result = $response.Content | ConvertFrom-Json
        $remaining = $response.Headers['x-ratelimit-remaining-tokens']
        Write-Host "[Reduced-$i] Status: 200 | Tokens: $($result.usage.total_tokens) | Remaining TPM: $remaining" -ForegroundColor Green
    }
    elseif ($response.StatusCode -eq 429) {
        $retryAfter = $response.Headers['Retry-After']
        Write-Host "[Reduced-$i] Status: 429 QUOTA EXCEEDED | Retry-After: $retryAfter" -ForegroundColor Yellow
    }
    else {
        $apimRequestId = $response.Headers['apim-request-id']
        Write-Host "[Reduced-$i] Status: $($response.StatusCode) | APIM Request ID: $apimRequestId | Body: $($response.Content)" -ForegroundColor Red
    }
}
```

> **Expected Result:** You should hit 429 errors sooner than before since the quota is now 10K TPM instead of 30K TPM.

---

## Part 4 - Create Multiple Deployments with Quota Allocation

### Step 4.1 - Create a Second Deployment (Team-Specific)

Simulate per-team quota by creating separate deployments:

```powershell
# Create a separate deployment for "Research" with lower quota
az cognitiveservices account deployment create `
    --name $AOAI_NAME `
    --resource-group $RESOURCE_GROUP `
    --deployment-name "gpt-4o-research" `
    --model-name "gpt-4o" `
    --model-version "2024-11-20" `
    --model-format "OpenAI" `
    --sku-capacity 5 `
    --sku-name "Standard"
```

### Step 4.2 - View Total Quota Distribution

```powershell
# Show how quota is distributed across deployments
az cognitiveservices account deployment list `
    --name $AOAI_NAME `
    --resource-group $RESOURCE_GROUP `
    --query "[].{Deployment:name, Model:properties.model.name, TPM_Thousands:sku.capacity}" `
    --output table

# Calculate total
$deployments = az cognitiveservices account deployment list `
    --name $AOAI_NAME `
    --resource-group $RESOURCE_GROUP | ConvertFrom-Json

$totalTPM = ($deployments | Measure-Object -Property { $_.sku.capacity } -Sum).Sum
Write-Host "`nTotal TPM allocated: $($totalTPM)K out of your subscription quota"
```

> **Expected Result:** Two deployments visible - `gpt-4o` at 10K TPM and `gpt-4o-research` at 5K TPM. Total: 15K TPM.

### Step 4.3 - Compare Quota Between Deployments

```powershell
# Test the main deployment via APIM (self-contained)
$subscriptionId = az account show --query id --output tsv
$resourceGroup = "rg-ai-finops-labs"
$apimName = "apim-finops-lab-9091"
$apimGateway = "https://$apimName.azure-api.net"
$baseMgmt = "https://management.azure.com/subscriptions/$subscriptionId/resourceGroups/$resourceGroup/providers/Microsoft.ApiManagement/service/$apimName"
$keyCustomerAI = az rest --method POST --uri "$baseMgmt/subscriptions/customerai-team/listSecrets?api-version=2022-08-01" --query primaryKey -o tsv

Write-Host "=== Main deployment (10K TPM) via APIM ==="
$uri = "$($apimGateway.TrimEnd('/'))/aoai-finops-lab/openai/deployments/gpt-4o/chat/completions?api-version=2024-10-21"
$headers = @{ "Content-Type" = "application/json"; "api-key" = $keyCustomerAI }
$body = (@{ messages = @(@{ role = "user"; content = "Hello" }); max_tokens = 50 } | ConvertTo-Json -Depth 5)
$resp = Invoke-WebRequest -Uri $uri -Method POST -Headers $headers -Body $body -SkipHttpErrorCheck
if ($resp.StatusCode -eq 200) {
    $result = $resp.Content | ConvertFrom-Json
    $remaining = $resp.Headers['x-ratelimit-remaining-tokens']
    Write-Host "[Main] Status: 200 | Remaining TPM: $remaining" -ForegroundColor Green
} else {
    Write-Host "[Main] Status: $($resp.StatusCode)" -ForegroundColor Red
}

# Test the research deployment only if it exists
$researchExists = az cognitiveservices account deployment list `
    --resource-group $resourceGroup `
    --name "aoai-finops-lab" `
    --query "[?name=='gpt-4o-research'] | length(@)" `
    --output tsv

if ($researchExists -eq "1") {
    Write-Host "`n=== Research deployment (5K TPM) via APIM ==="
    $uri = "$($apimGateway.TrimEnd('/'))/aoai-finops-lab/openai/deployments/gpt-4o-research/chat/completions?api-version=2024-10-21"
    $resp = Invoke-WebRequest -Uri $uri -Method POST -Headers $headers -Body $body -SkipHttpErrorCheck
    if ($resp.StatusCode -eq 200) {
        $result = $resp.Content | ConvertFrom-Json
        $remaining = $resp.Headers['x-ratelimit-remaining-tokens']
        Write-Host "[Research] Status: 200 | Remaining TPM: $remaining" -ForegroundColor Green
    } else {
        Write-Host "[Research] Status: $($resp.StatusCode) | Body: $($resp.Content)" -ForegroundColor Yellow
    }
} else {
    Write-Host "`n[Research] Skipped: deployment 'gpt-4o-research' does not exist yet" -ForegroundColor Yellow
}
```

> **Expected Result:** The Research deployment shows a lower `remaining-tokens` count (from 5K TPM pool) compared to the main deployment (from 10K TPM pool).

---

## Part 5 - Monitor Quota Utilization

### Step 5.1 - View Quota Metrics in Azure Portal

1. Go to **Azure Portal** - your Azure OpenAI resource (`aoai-finops-lab`)
2. Navigate to **Monitoring** - **Metrics**
3. Add these metrics:

| Metric | Aggregation | Purpose |
|--------|-------------|---------|
| `Azure OpenAI Requests` | Count | Total requests processed |
| `Generated Completion Tokens` | Sum | Output tokens generated |
| `Processed Prompt Tokens` | Sum | Input tokens processed |
| `Token Transaction` | Sum | Total token throughput |

4. Set the time range to **Last 1 hour**
5. Click **Apply splitting** - Split by **ModelDeploymentName**

> **Take a screenshot** - this shows per-deployment token consumption.

### Step 5.2 - Check Quota Utilization via Azure Monitor

```powershell
# View Azure OpenAI metrics via CLI
az monitor metrics list `
    --resource $(az cognitiveservices account show --name $AOAI_NAME --resource-group $RESOURCE_GROUP --query id --output tsv) `
    --metric "TokenTransaction" `
    --interval PT1M `
    --start-time (Get-Date).AddMinutes(-30).ToString("yyyy-MM-ddTHH:mm:ssZ") `
    --end-time (Get-Date).ToString("yyyy-MM-ddTHH:mm:ssZ") `
    --query "value[0].timeseries[0].data[-5:].{Time:timeStamp, Total:total}" `
    --output table
```

### Step 5.3 - Create a Quota Utilization Alert

Set up an alert that fires when quota utilization exceeds quota limits:

1. Go to **Azure OpenAI resource** - **Alerts** - **+ Create alert rule**
2. **Condition:**
   - Signal: `Azure OpenAI Requests`
   - Filter: Status = `429` (rate limited)
   - Aggregation: Count
   - Operator: Greater than
   - Threshold: `5` (fires after 5 rate-limited requests in the window)
   - Evaluation period: 5 minutes
   - Check every: 1 minute
3. **Action:**
   - Select or create an Action Group
   - Add an email notification: `ai-platform-team@contoso.com`
4. **Details:**
   - Alert rule name: `AI Quota Threshold Alert`
   - Severity: **Warning (Sev 2)**
5. Click **Create**

### Step 5.4 - Trigger the Alert (Verification)

```powershell
# Generate enough 429s to trigger the alert (self-contained)
$subscriptionId = az account show --query id --output tsv
$resourceGroup = "rg-ai-finops-labs"
$apimName = "apim-finops-lab-9091"
$apimGateway = "https://$apimName.azure-api.net"
$baseMgmt = "https://management.azure.com/subscriptions/$subscriptionId/resourceGroups/$resourceGroup/providers/Microsoft.ApiManagement/service/$apimName"
$keyCustomerAI = az rest --method POST --uri "$baseMgmt/subscriptions/customerai-team/listSecrets?api-version=2022-08-01" --query primaryKey -o tsv

$uri = "$($apimGateway.TrimEnd('/'))/aoai-finops-lab/openai/deployments/gpt-4o/chat/completions?api-version=2024-10-21"

Write-Host "=== Generating 429 errors to trigger alert ==="
for ($i = 1; $i -le 25; $i++) {
    $headers = @{ "Content-Type" = "application/json"; "api-key" = $keyCustomerAI }
    $body = (@{
        messages = @(
            @{ role = "user"; content = "Write an extremely detailed 2000-word essay about distributed computing including all subtopics, frameworks, and implementation patterns." }
        )
        max_tokens = 800
    } | ConvertTo-Json -Depth 5)

    $response = $null
    for ($attempt = 1; $attempt -le 3; $attempt++) {
        $response = Invoke-WebRequest -Uri $uri -Method POST -Headers $headers -Body $body -SkipHttpErrorCheck
        if ($response.StatusCode -ne 404) { break }
    }

    if ($response.StatusCode -eq 200) {
        $result = $response.Content | ConvertFrom-Json
        $remaining = $response.Headers['x-ratelimit-remaining-tokens']
        Write-Host "[Alert-Test-$i] Status: 200 | Tokens: $($result.usage.total_tokens) | Remaining TPM: $remaining" -ForegroundColor Green
    }
    elseif ($response.StatusCode -eq 429) {
        $retryAfter = $response.Headers['Retry-After']
        Write-Host "[Alert-Test-$i] Status: 429 QUOTA EXCEEDED | Retry-After: $retryAfter" -ForegroundColor Yellow
    }
    else {
        $apimRequestId = $response.Headers['apim-request-id']
        Write-Host "[Alert-Test-$i] Status: $($response.StatusCode) | APIM Request ID: $apimRequestId | Body: $($response.Content)" -ForegroundColor Red
    }
}

Write-Host "`nAlert should fire within 5 minutes if enough 429s were generated."
Write-Host "Check Azure Portal - Alerts to verify."
```

> **Expected Result:** After 5+ 429 responses within 5 minutes, the alert triggers and sends an email notification.

---

## Part 6 - Quota Management Best Practices

### Step 6.1 - Restore Quota for Production

```powershell
# Restore the main deployment to 30K TPM
az cognitiveservices account deployment create `
    --name $AOAI_NAME `
    --resource-group $RESOURCE_GROUP `
    --deployment-name "gpt-4o" `
    --model-name "gpt-4o" `
    --model-version "2024-11-20" `
    --model-format "OpenAI" `
    --sku-capacity 30 `
    --sku-name "Standard"
```

### Step 6.2 - Document Your Quota Plan

Create a quota allocation spreadsheet:

| Deployment | Model | Team | TPM | RPM | Purpose | Owner |
|-----------|-------|------|-----|-----|---------|-------|
| gpt-4o | gpt-4o | Production | 25K | N/A | CustomerAI APIs | ai-platform@contoso.com |
| gpt-4o-research | gpt-4o | Research | 5K | N/A | Experimentation | research@contoso.com |

---

## Summary

You have successfully:
1. ✓ Understood Azure OpenAI quota hierarchy (subscription → region → model → deployment)
2. ✓ Viewed current quota utilization
3. ✓ Modified deployment quotas dynamically
4. ✓ Created multiple deployments with separate quota pools
5. ✓ Set up monitoring and alerts for quota violations

**Key differences from API key approach:**
- Quota limits still apply at Azure OpenAI service level (independent of authentication method)
- APIM MI auth doesn't change quota behavior; it only handles authentication
- All calls through APIM still count against Azure OpenAI deployment quotas

**Next lab:** Proceed to [Lab-03-Chargeback-Model-managed-identity.md](Lab-03-Chargeback-Model-managed-identity.md)

