# Lab 2 – Azure OpenAI Quota Limiting

> **Objective:** Configure and manage Azure OpenAI quota (TPM/RPM) at the subscription, model, and deployment level. Observe quota enforcement, test dynamic quota, and set up alerts for quota utilization.
>
> **Duration:** 45–60 minutes
>
> **Prerequisites:** Complete [00-Prerequisites.md](00-Prerequisites.md)

---

## Lab Variables

Set these at the start of the lab (from prerequisites):

```powershell
$RESOURCE_GROUP = "rg-ai-finops-labs"
$AOAI_NAME      = "aoai-finops-lab"
$AOAI_ENDPOINT  = "<your-aoai-endpoint>"
$AOAI_KEY       = "<your-aoai-key>"
```

---

## Part 1 – Understand Azure OpenAI Quota Architecture

### Step 1.1 – Review the Quota Hierarchy

Azure OpenAI enforces quota at multiple levels:

```
┌─────────────────────────────────────────────────────────┐
│                  Azure Subscription                      │
│  ┌───────────────────────────────────────────────────┐   │
│  │     Region Quota (e.g., East US)                  │   │
│  │  ┌──────────────────────────────────────────────┐ │   │
│  │  │   Model Quota (e.g., gpt-4o-mini)            │ │   │
│  │  │  ┌────────────────┐  ┌────────────────────┐  │ │   │
│  │  │  │ Deployment A   │  │ Deployment B       │  │ │   │
│  │  │  │ (30K TPM)      │  │ (20K TPM)          │  │ │   │
│  │  │  └────────────────┘  └────────────────────┘  │ │   │
│  │  │      Total ≤ Model Quota                     │ │   │
│  │  └──────────────────────────────────────────────┘ │   │
│  └───────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

**Key concepts:**
- **TPM** (Tokens Per Minute): Primary quota unit — how many tokens a deployment can process per minute
- **RPM** (Requests Per Minute): Secondary limit — auto-calculated from TPM (typically TPM ÷ 6)
- **Deployment quota**: Allocated from the model's regional quota pool
- **Dynamic quota**: Allows temporary bursts above allocation when capacity is available

### Step 1.2 – View Your Current Quota

```powershell
# View current model quota usage for the subscription
az cognitiveservices usage list `
    --location "eastus" `
    --query "[?contains(name.value, 'OpenAI')].{Model:name.value, Current:currentValue, Limit:limit}" `
    --output table
```

> **Expected Result:** A table showing each model's current quota usage and limits for your subscription in East US.

### Step 1.3 – View Deployment Quota Allocation

```powershell
# List deployments and their quota allocations
az cognitiveservices account deployment list `
    --name $AOAI_NAME `
    --resource-group $RESOURCE_GROUP `
    --query "[].{Name:name, Model:properties.model.name, TPM:sku.capacity, Status:properties.provisioningState}" `
    --output table
```

> **Expected Result:** Shows your `gpt-4o-mini` deployment with 30 (= 30K TPM) capacity.

---

## Part 2 – Test Quota Enforcement

### Step 2.1 – Understand Quota vs Rate Limiting

| Aspect | Azure OpenAI Quota | APIM Token Limit (Lab 1) |
|--------|-------------------|--------------------------|
| **Enforced by** | Azure OpenAI service | APIM gateway |
| **Scope** | Per deployment | Per APIM subscription |
| **Unit** | TPM at deployment level | TPM at team level |
| **Error code** | HTTP 429 with `quota` reason | HTTP 429 with custom message |
| **Purpose** | Protects Azure's shared infrastructure | Governs your internal teams |

### Step 2.2 – Create a Helper Function

```powershell
function Invoke-AOAIRequest {
    param(
        [string]$Prompt,
        [int]$MaxTokens = 200,
        [string]$Label = "Test"
    )

    $headers = @{
        "Content-Type" = "application/json"
        "api-key"      = $AOAI_KEY
    }
    $body = @{
        messages = @(
            @{ role = "user"; content = $Prompt }
        )
        max_tokens = $MaxTokens
    } | ConvertTo-Json

    try {
        $response = Invoke-WebRequest `
            -Uri "$($AOAI_ENDPOINT)openai/deployments/gpt-4o-mini/chat/completions?api-version=2024-10-21" `
            -Method POST `
            -Headers $headers `
            -Body $body

        $result = $response.Content | ConvertFrom-Json
        $remaining = $response.Headers['x-ratelimit-remaining-tokens']
        Write-Host "[$Label] Status: 200 | Tokens: $($result.usage.total_tokens) | Remaining TPM: $remaining" -ForegroundColor Green
        return $result
    }
    catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        if ($statusCode -eq 429) {
            $retryAfter = $_.Exception.Response.Headers | Where-Object { $_.Key -eq "Retry-After" }
            Write-Host "[$Label] Status: 429 QUOTA EXCEEDED | Retry after: $($retryAfter.Value)s" -ForegroundColor Red
        }
        else {
            Write-Host "[$Label] Status: $statusCode | Error: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
}
```

### Step 2.3 – Send Requests and Observe Quota Headers

```powershell
# Send a single request and examine the rate limit headers
$headers = @{
    "Content-Type" = "application/json"
    "api-key"      = $AOAI_KEY
}
$body = @{
    messages = @(
        @{ role = "user"; content = "What is Azure?" }
    )
    max_tokens = 100
} | ConvertTo-Json

$response = Invoke-WebRequest `
    -Uri "$($AOAI_ENDPOINT)openai/deployments/gpt-4o-mini/chat/completions?api-version=2024-10-21" `
    -Method POST `
    -Headers $headers `
    -Body $body

# Examine all rate-limit response headers
Write-Host "`n=== Rate Limit Headers ==="
$response.Headers.GetEnumerator() | Where-Object { $_.Key -like "*ratelimit*" -or $_.Key -like "*retry*" } | ForEach-Object {
    Write-Host "$($_.Key): $($_.Value)"
}
```

> **Expected Result:** You should see headers like:
> - `x-ratelimit-remaining-tokens`: Tokens remaining in current window
> - `x-ratelimit-remaining-requests`: Requests remaining in current window
> These reflect your deployment's 30K TPM allocation.

### Step 2.4 – Stress Test the Quota

```powershell
# Send rapid requests to approach the quota limit
Write-Host "=== Sending 20 rapid requests to test quota boundary ==="

for ($i = 1; $i -le 20; $i++) {
    Invoke-AOAIRequest `
        -Prompt "Write a detailed paragraph about cloud computing trend number $i. Include specific technologies, market data, and predictions for the next 5 years." `
        -MaxTokens 500 `
        -Label "Req-$i"
}
```

> **Expected Result:** As you approach the deployment's TPM limit, you'll see the `Remaining TPM` decrease. If you exceed it, you'll get HTTP 429 responses with a `Retry-After` header.

---

## Part 3 – Modify Deployment Quota

### Step 3.1 – Reduce Quota to Observe Limiting Faster

Lower the deployment quota to make rate limiting more visible in the lab:

```powershell
# Reduce deployment to 10K TPM (minimum for testing)
az cognitiveservices account deployment create `
    --name $AOAI_NAME `
    --resource-group $RESOURCE_GROUP `
    --deployment-name "gpt-4o-mini" `
    --model-name "gpt-4o-mini" `
    --model-version "2024-07-18" `
    --model-format "OpenAI" `
    --sku-capacity 10 `
    --sku-name "Standard"
```

> **Note:** This updates the existing deployment in-place. The `--sku-capacity 10` means 10K TPM.

### Step 3.2 – Verify the New Quota

```powershell
# Confirm the new capacity
az cognitiveservices account deployment list `
    --name $AOAI_NAME `
    --resource-group $RESOURCE_GROUP `
    --query "[].{Name:name, TPM:sku.capacity}" `
    --output table
```

> **Expected Result:** The `gpt-4o-mini` deployment should now show capacity of `10`.

### Step 3.3 – Test With Reduced Quota

```powershell
# Repeat the stress test — should hit limits faster
Write-Host "=== Testing with reduced 10K TPM quota ==="
for ($i = 1; $i -le 15; $i++) {
    Invoke-AOAIRequest `
        -Prompt "Explain in detail the architecture of a distributed microservices system for e-commerce, including all components." `
        -MaxTokens 500 `
        -Label "Reduced-$i"
}
```

> **Expected Result:** You should hit 429 errors sooner than before since the quota is now 10K TPM instead of 30K TPM.

---

## Part 4 – Create Multiple Deployments with Quota Allocation

### Step 4.1 – Create a Second Deployment (Team-Specific)

Simulate per-team quota by creating separate deployments:

```powershell
# Create a separate deployment for "Research" with lower quota
az cognitiveservices account deployment create `
    --name $AOAI_NAME `
    --resource-group $RESOURCE_GROUP `
    --deployment-name "gpt-4o-mini-research" `
    --model-name "gpt-4o-mini" `
    --model-version "2024-07-18" `
    --model-format "OpenAI" `
    --sku-capacity 5 `
    --sku-name "Standard"
```

### Step 4.2 – View Total Quota Distribution

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

> **Expected Result:** Two deployments visible — `gpt-4o-mini` at 10K TPM and `gpt-4o-mini-research` at 5K TPM. Total: 15K TPM.

### Step 4.3 – Compare Quota Between Deployments

```powershell
# Test the main deployment
Write-Host "=== Main deployment (10K TPM) ==="
Invoke-AOAIRequest -Prompt "Hello" -MaxTokens 50 -Label "Main"

# Test the research deployment (using the second deployment name)
$headers = @{
    "Content-Type" = "application/json"
    "api-key"      = $AOAI_KEY
}
$body = @{
    messages = @(
        @{ role = "user"; content = "Hello" }
    )
    max_tokens = 50
} | ConvertTo-Json

$response = Invoke-WebRequest `
    -Uri "$($AOAI_ENDPOINT)openai/deployments/gpt-4o-mini-research/chat/completions?api-version=2024-10-21" `
    -Method POST `
    -Headers $headers `
    -Body $body

$remaining = $response.Headers['x-ratelimit-remaining-tokens']
Write-Host "[Research] Status: 200 | Remaining TPM: $remaining" -ForegroundColor Green
```

> **Expected Result:** The Research deployment shows a lower `remaining-tokens` count (from 5K TPM pool) compared to the main deployment (from 10K TPM pool).

---

## Part 5 – Monitor Quota Utilization

### Step 5.1 – View Quota Metrics in Azure Portal

1. Go to **Azure Portal** → your Azure OpenAI resource (`aoai-finops-lab`)
2. Navigate to **Monitoring** → **Metrics**
3. Add these metrics:

| Metric | Aggregation | Purpose |
|--------|-------------|---------|
| `Azure OpenAI Requests` | Count | Total requests processed |
| `Generated Completion Tokens` | Sum | Output tokens generated |
| `Processed Prompt Tokens` | Sum | Input tokens processed |
| `Token Transaction` | Sum | Total token throughput |

4. Set the time range to **Last 1 hour**
5. Click **Apply splitting** → Split by **ModelDeploymentName**

> **Take a screenshot** — this shows per-deployment token consumption.

### Step 5.2 – Check Quota Utilization via Azure Monitor

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

### Step 5.3 – Create a Quota Utilization Alert

Set up an alert that fires when quota utilization exceeds 80%:

1. Go to **Azure OpenAI resource** → **Alerts** → **+ Create alert rule**
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

### Step 5.4 – Trigger the Alert (Verification)

```powershell
# Generate enough 429s to trigger the alert
Write-Host "=== Generating 429 errors to trigger alert ==="

# Use the reduced 10K TPM deployment
for ($i = 1; $i -le 25; $i++) {
    Invoke-AOAIRequest `
        -Prompt "Write an extremely detailed 2000-word essay about distributed computing including all subtopics, frameworks, and implementation patterns." `
        -MaxTokens 800 `
        -Label "Alert-Test-$i"
}

Write-Host "`nAlert should fire within 5 minutes if enough 429s were generated."
Write-Host "Check Azure Portal → Alerts to verify."
```

> **Expected Result:** After 5+ 429 responses within 5 minutes, the alert triggers and sends an email notification.

---

## Part 6 – Quota Management Best Practices

### Step 6.1 – Restore Quota for Production

```powershell
# Restore the main deployment to 30K TPM
az cognitiveservices account deployment create `
    --name $AOAI_NAME `
    --resource-group $RESOURCE_GROUP `
    --deployment-name "gpt-4o-mini" `
    --model-name "gpt-4o-mini" `
    --model-version "2024-07-18" `
    --model-format "OpenAI" `
    --sku-capacity 30 `
    --sku-name "Standard"

Write-Host "Main deployment restored to 30K TPM."
```

### Step 6.2 – Review Quota Allocation Strategy

Document the quota distribution for your organization:

| Deployment | Model | TPM | Use Case | Team |
|------------|-------|-----|----------|------|
| `gpt-4o-mini` | gpt-4o-mini | 30K | Production workloads | CustomerAI |
| `gpt-4o-mini-research` | gpt-4o-mini | 5K | Experimentation | Research |
| *Future* | gpt-4o | 50K | Premium scenarios | CustomerAI |
| *Future* | gpt-4o-mini | 10K | Internal tools | InternalOps |

### Step 6.3 – Enable Dynamic Quota (Optional)

Dynamic Quota lets deployments temporarily burst above their allocated TPM when regional capacity is available.

1. Go to **Azure Portal** → **Azure OpenAI** → **Deployments**
2. Click on `gpt-4o-mini` deployment
3. Under **Advanced options**, enable **Dynamic Quota**
4. Click **Save**

> **Note:** Dynamic Quota is charged at standard PAYG rates — no premium for burst capacity.

---

## Part 7 – Clean Up Research Deployment

```powershell
# Delete the research deployment (optional — keep if proceeding to Lab 3)
# az cognitiveservices account deployment delete `
#     --name $AOAI_NAME `
#     --resource-group $RESOURCE_GROUP `
#     --deployment-name "gpt-4o-mini-research"
```

---

## Summary

In this lab you:

| Step | What You Did |
|------|--------------|
| Part 1 | Explored the Azure OpenAI quota hierarchy (subscription → region → model → deployment) |
| Part 2 | Tested quota enforcement and observed 429 responses with rate-limit headers |
| Part 3 | Modified deployment quota to control per-deployment TPM allocation |
| Part 4 | Created multiple deployments to simulate per-team quota distribution |
| Part 5 | Set up monitoring metrics and a quota utilization alert |
| Part 6 | Reviewed quota management best practices and Dynamic Quota |

### Key Takeaways

- **Quota operates at the deployment level** — each deployment gets its own TPM allocation from the model's regional pool
- **429 headers are your friends** — `x-ratelimit-remaining-tokens` tells you exactly where you stand
- **Multiple deployments = per-team quota** — use separate deployments to enforce team-level limits at the Azure OpenAI layer
- **Dynamic Quota** provides burst capacity at no extra cost when available
- **Monitor and alert** — set up alerts on 429 count to detect quota pressure before users complain
- **Quota + APIM = defense in depth** — Lab 1's APIM token limits + Lab 2's Azure OpenAI quota = two layers of protection

---

> **Next:** Proceed to [Lab 3 – Chargeback Model](Lab-03-Chargeback-Model.md)
