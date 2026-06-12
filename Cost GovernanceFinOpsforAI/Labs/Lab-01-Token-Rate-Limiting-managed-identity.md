# Lab 1 - Token Rate Limiting with Azure API Management (Managed Identity)

> **Objective:** Configure APIM policies to enforce per-team token rate limits on Azure OpenAI API calls, observe throttling behavior, and analyze token consumption metrics.
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
$RESOURCE_GROUP  = "rg-ai-finops-labs"
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

---

## Part 1 - Understand Token-Based Rate Limiting

### Step 1.1 - Review How Token Limits Work

Unlike traditional API rate limiting (requests per second), Azure AI workloads need **token-based** limits because:

- A single request can consume 10 tokens or 10,000 tokens
- Cost is directly proportional to token usage
- Request-count limits don't protect against a single expensive call

APIM provides the `azure-openai-token-limit` policy that:
- Reads token counts from the **Azure OpenAI response headers**
- Tracks consumption per **subscription key** (i.e., per team)
- Returns **HTTP 429** when the token budget is exceeded
- Uses a **sliding window** that refills over time

### Step 1.2 - Review the Token Limit Architecture

```
Architecture Flow:
- Client with APIM subscription key
- Calls APIM gateway (authenticated via subscription key)
- APIM enforces token rate limit policy
- APIM authenticates to Azure OpenAI using system-assigned managed identity
- No API keys passed through; MI handles authentication

Policy Applied at APIM:
- Per-team token budgets:
  - CustomerAI: 5,000 TPM
  - InternalOps: 3,000 TPM
  - Research: 2,000 TPM
- Tokens tracked per subscription ID
- Sliding window that refills every 60 seconds
```

---

## Part 2 - Configure Token Rate Limiting Policy

### Step 2.1 - Open the APIM Policy Editor

1. Go to **Azure Portal** - **API Management** - your APIM instance
2. Navigate to **APIs** - **Azure OpenAI** - **Chat Completions** operation
3. Click the **`</>`** (code editor) icon in the **Inbound processing** section

### Step 2.2 - Add the Token Limit Policy

Replace the `<inbound>` section with the following policy:

```xml
<inbound>
    <base />
    <!-- APIM Managed Identity Authentication: Token rate limiting per team -->
    
    <!-- Token-based rate limiting: 5,000 tokens per minute per subscription -->
    <azure-openai-token-limit
        tokens-per-minute="5000"
        counter-key="@(context.Subscription.Id)"
        estimate-prompt-tokens="true"
        tokens-consumed-header-name="x-tokens-consumed"
        remaining-tokens-header-name="x-tokens-remaining" />
</inbound>
```

4. Click **Save**

> **Key difference from API key version:** No `<set-header name="api-key">` block.
> APIM managed identity handles Azure OpenAI authentication automatically.

### Step 2.3 - Understand the Policy Attributes

| Attribute | Value | Purpose |
|-----------|-------|---------|
| `tokens-per-minute` | `5000` | Max tokens any single subscription can consume per minute |
| `counter-key` | `context.Subscription.Id` | Each APIM subscription (team) gets its own counter |
| `estimate-prompt-tokens` | `true` | Estimates input tokens before forwarding (pre-check) |
| `tokens-consumed-header-name` | `x-tokens-consumed` | Response header showing tokens used |
| `remaining-tokens-header-name` | `x-tokens-remaining` | Response header showing remaining budget |

> **Why `estimate-prompt-tokens="true"`?** This estimates the prompt token count *before* sending to Azure OpenAI, allowing APIM to reject requests early if the budget is already exhausted - saving you money.

---

## Part 3 - Test Token Rate Limiting

### Step 3.1 - Send a Normal Request (CustomerAI Team)

```powershell
# Use APIM subscription key (from prerequisites)
# If you refresh $KEY_CUSTOMERAI, recreate $headers so it picks up the new value.
$headers = @{
    "Content-Type" = "application/json"
    "api-key"      = $KEY_CUSTOMERAI
}
$body = @{
    messages = @(
        @{ role = "user"; content = "What is Azure?" }
    )
    max_tokens = 100
} | ConvertTo-Json

$response = Invoke-WebRequest `
    -Uri "$APIM_GATEWAY/aoai-finops-lab/openai/deployments/gpt-4o/chat/completions?api-version=2024-10-21" `
    -Method POST `
    -Headers $headers `
    -Body $body

# Check the response headers
Write-Host "Status: $($response.StatusCode)"
Write-Host "Tokens Consumed: $($response.Headers['x-tokens-consumed'])"
Write-Host "Tokens Remaining: $($response.Headers['x-tokens-remaining'])"

# Check response body
$result = $response.Content | ConvertFrom-Json
Write-Host "Response: $($result.choices[0].message.content)"
Write-Host "Usage - Prompt: $($result.usage.prompt_tokens), Completion: $($result.usage.completion_tokens)"
```

> **Expected Result:** HTTP 200. The `x-tokens-remaining` header shows your remaining budget out of 5,000.

### Step 3.2 - Exhaust the Token Budget

Send multiple large requests rapidly to exhaust the token limit:

```powershell
# Function to send a request and report status
function Send-AIRequest {
    param([string]$TeamKey, [string]$TeamName, [string]$Prompt)

    $headers = @{
        "Content-Type" = "application/json"
        "api-key"      = $TeamKey
    }
    $body = @{
        messages = @(
            @{ role = "user"; content = $Prompt }
        )
        max_tokens = 500
    } | ConvertTo-Json

    try {
        $response = Invoke-WebRequest `
            -Uri "$APIM_GATEWAY/aoai-finops-lab/openai/deployments/gpt-4o/chat/completions?api-version=2024-10-21" `
            -Method POST `
            -Headers $headers `
            -Body $body

        $result = $response.Content | ConvertFrom-Json
        Write-Host "[$TeamName] Status: $($response.StatusCode) | Tokens Used: $($result.usage.total_tokens) | Remaining: $($response.Headers['x-tokens-remaining'])" -ForegroundColor Green
    }
    catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        if ($statusCode -eq 429) {
            Write-Host "[$TeamName] Status: 429 RATE LIMITED! Token budget exhausted." -ForegroundColor Red
            # Read retry-after header
            $retryAfter = $_.Exception.Response.Headers | Where-Object { $_.Key -eq "Retry-After" }
            if ($retryAfter) {
                Write-Host "[$TeamName] Retry after: $($retryAfter.Value) seconds" -ForegroundColor Yellow
            }
        }
        else {
            Write-Host "[$TeamName] Status: $statusCode - $($_.Exception.Message)" -ForegroundColor Red
        }
    }
}

# Send 15 requests rapidly for CustomerAI team to exhaust 5,000 TPM
$longPrompt = "Explain the complete architecture of Azure Kubernetes Service including networking, storage, identity, monitoring, scaling, security, and disaster recovery. Be thorough and detailed."

for ($i = 1; $i -le 15; $i++) {
    Write-Host "`n--- Request $i ---"
    Send-AIRequest -TeamKey $KEY_CUSTOMERAI -TeamName "CustomerAI" -Prompt $longPrompt
}
```

> **Expected Result:** After several requests, you should see `429 RATE LIMITED` responses. The exact number depends on how many tokens each response uses.

### Step 3.3 - Verify Other Teams Are NOT Affected

While CustomerAI is rate-limited, verify that other teams can still make calls:

```powershell
Write-Host "`n=== Testing InternalOps Team (should succeed) ==="
Send-AIRequest -TeamKey $KEY_INTERNALOPS -TeamName "InternalOps-Team" -Prompt "What is 2+2?"

Write-Host "`n=== Testing Research Team (should succeed) ==="
Send-AIRequest -TeamKey $KEY_RESEARCH -TeamName "Research" -Prompt "What is 2+2?"
```

> **Expected Result:** Both InternalOps and Research return HTTP 200 successfully. Token limits are tracked **per subscription key**, so one team's exhaustion doesn't affect others.

### Step 3.4 - Wait for Token Budget Refill

```powershell
# Wait 60 seconds for the token counter to reset
Write-Host "Waiting 60 seconds for token budget to refill..."
Start-Sleep -Seconds 60

# Retry CustomerAI
Write-Host "`n=== Retrying CustomerAI after 1 minute ==="
Send-AIRequest -TeamKey $KEY_CUSTOMERAI -TeamName "CustomerAI" -Prompt "Hello"
```

> **Expected Result:** After 60 seconds, CustomerAI can make requests again as the sliding window refills tokens.

---

## Troubleshooting: 401 Errors

### Problem: `Status: 401 - Access Denied`

This means the APIM subscription key is **missing, empty, or incorrect**.

**Cause 1: Stale key in PowerShell variable**
When you refresh keys or switch terminal sessions, the variables can become stale.

**Solution:**
```powershell
# Re-run the recovery block from Lab Variables section at the TOP of this file
# This will refresh all three keys:
$SUBSCRIPTION_ID = az account show --query id --output tsv
$BASE_MGMT = "https://management.azure.com/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.ApiManagement/service/$APIM_NAME"

$KEY_CUSTOMERAI  = az rest --method POST --uri "$BASE_MGMT/subscriptions/customerai-team/listSecrets?api-version=2022-08-01" --query primaryKey -o tsv
$KEY_INTERNALOPS = az rest --method POST --uri "$BASE_MGMT/subscriptions/internalops-team/listSecrets?api-version=2022-08-01" --query primaryKey -o tsv
$KEY_RESEARCH    = az rest --method POST --uri "$BASE_MGMT/subscriptions/research-team/listSecrets?api-version=2022-08-01" --query primaryKey -o tsv

# Verify (all must be 32)
Write-Host "CustomerAI:  $($KEY_CUSTOMERAI.Length)"
Write-Host "InternalOps: $($KEY_INTERNALOPS.Length)"
Write-Host "Research:    $($KEY_RESEARCH.Length)"
```

**Cause 2: Wrong function call (missing -TeamKey parameter)**
```powershell
# WRONG - missing -TeamKey parameter
Send-AIRequest -TeamName "Research" -Prompt "What is 2+2?"

# CORRECT - all three parameters required
Send-AIRequest -TeamKey $KEY_RESEARCH -TeamName "Research" -Prompt "What is 2+2?"
```

**Cause 3: Typo in subscription name when retrieving key**
Verify these exact names match your APIM subscription IDs (shown in Azure Portal):
- `customerai-team` (NOT `customerai`, NOT `CustomerAI-Team`)
- `internalops-team` (NOT `internalops`, NOT `InternalOps-Team`)
- `research-team` (NOT `research`, NOT `Research-Team`)

---

## Part 4 - Differentiated Token Limits Per Team

### Step 4.1 - Apply Team-Specific Token Budgets

Different teams have different usage patterns. Let's assign differentiated limits:

| Team | Tokens Per Minute | Rationale |
|------|-------------------|-----------|
| CustomerAI | 10,000 TPM | Production-facing, highest priority |
| InternalOps | 5,000 TPM | Internal tools, medium priority |
| Research | 2,000 TPM | Experimentation, lowest priority |

### Step 4.2 - Update the Policy with Conditional Limits

Go back to the APIM policy editor and replace the `<inbound>` section:

```xml
<inbound>
    <base />
    <!-- APIM Managed Identity Authentication: Differentiated token limits per team -->
    
    <!-- Identify the team from subscription name -->
    <set-variable name="teamName" value="@(context.Subscription.Name)" />

    <!-- Differentiated token limits per team -->
    <choose>
        <when condition="@(context.Variables.GetValueOrDefault<string>("teamName").Contains("CustomerAI"))">
            <azure-openai-token-limit
                tokens-per-minute="10000"
                counter-key="@(context.Subscription.Id)"
                estimate-prompt-tokens="true"
                tokens-consumed-header-name="x-tokens-consumed"
                remaining-tokens-header-name="x-tokens-remaining" />
        </when>
        <when condition="@(context.Variables.GetValueOrDefault<string>("teamName").Contains("InternalOps"))">
            <azure-openai-token-limit
                tokens-per-minute="5000"
                counter-key="@(context.Subscription.Id)"
                estimate-prompt-tokens="true"
                tokens-consumed-header-name="x-tokens-consumed"
                remaining-tokens-header-name="x-tokens-remaining" />
        </when>
        <when condition="@(context.Variables.GetValueOrDefault<string>("teamName").Contains("Research"))">
            <azure-openai-token-limit
                tokens-per-minute="2000"
                counter-key="@(context.Subscription.Id)"
                estimate-prompt-tokens="true"
                tokens-consumed-header-name="x-tokens-consumed"
                remaining-tokens-header-name="x-tokens-remaining" />
        </when>
        <otherwise>
            <!-- Default: strict limit for unknown callers -->
            <azure-openai-token-limit
                tokens-per-minute="1000"
                counter-key="@(context.Subscription.Id)"
                estimate-prompt-tokens="true"
                tokens-consumed-header-name="x-tokens-consumed"
                remaining-tokens-header-name="x-tokens-remaining" />
        </otherwise>
    </choose>

    <!-- Add team name to response header for visibility -->
    <set-header name="x-team-name" exists-action="override">
        <value>@(context.Variables.GetValueOrDefault<string>("teamName"))</value>
    </set-header>
</inbound>
```

Click **Save**.

### Step 4.3 - Test with New Limits

```powershell
# Test each team with the new limits
Write-Host "=== Testing with differentiated limits ==="

# CustomerAI now has 10K TPM
Write-Host "`nCustomerAI (10K TPM limit):"
Send-AIRequest -TeamKey $KEY_CUSTOMERAI -TeamName "CustomerAI" -Prompt "Hello"

# InternalOps now has 5K TPM
Write-Host "`nInternalOps (5K TPM limit):"
Send-AIRequest -TeamKey $KEY_INTERNALOPS -TeamName "InternalOps" -Prompt "Hello"

# Research now has 2K TPM
Write-Host "`nResearch (2K TPM limit):"
Send-AIRequest -TeamKey $KEY_RESEARCH -TeamName "Research" -Prompt "Hello"
```

---

## Summary

You have successfully:
1. ✓ Configured APIM with managed identity authentication to Azure OpenAI
2. ✓ Implemented token-based rate limiting per team
3. ✓ Tested rate limit enforcement and budget refill
4. ✓ Set up differentiated token budgets per team

**Key differences from API key approach:**
- No API keys needed in policies or client code
- APIM managed identity handles Azure OpenAI authentication automatically
- Policies focus on rate limiting logic, not authentication
- Cleaner security model: only APIM MI can access Azure OpenAI

**Next lab:** Proceed to [Lab-02-Quota-Limiting-managed-identity.md](Lab-02-Quota-Limiting-managed-identity.md)

