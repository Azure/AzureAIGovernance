# Lab 1 – Token Rate Limiting with Azure API Management

> **Objective:** Configure APIM policies to enforce per-team token rate limits on Azure OpenAI API calls, observe throttling behavior, and analyze token consumption metrics.
>
> **Duration:** 45–60 minutes
>
> **Prerequisites:** Complete [00-Prerequisites.md](00-Prerequisites.md)

---

## Lab Variables

Set these at the start of the lab (from prerequisites):

```powershell
$RESOURCE_GROUP  = "rg-ai-finops-labs"
$APIM_NAME       = "<your-apim-name>"
$APIM_GATEWAY    = "<your-apim-gateway-url>"
$AOAI_ENDPOINT   = "<your-aoai-endpoint>"
$AOAI_KEY        = "<your-aoai-key>"
$KEY_CUSTOMERAI  = "<subscription-key-for-CustomerAI>"
$KEY_INTERNALOPS = "<subscription-key-for-InternalOps>"
$KEY_RESEARCH    = "<subscription-key-for-Research>"
```

---

## Part 1 – Understand Token-Based Rate Limiting

### Step 1.1 – Review How Token Limits Work

Unlike traditional API rate limiting (requests per second), Azure AI workloads need **token-based** limits because:

- A single request can consume 10 tokens or 10,000 tokens
- Cost is directly proportional to token usage
- Request-count limits don't protect against a single expensive call

APIM provides the `azure-openai-token-limit` policy that:
- Reads token counts from the **Azure OpenAI response headers**
- Tracks consumption per **subscription key** (i.e., per team)
- Returns **HTTP 429** when the token budget is exceeded
- Uses a **sliding window** that refills over time

### Step 1.2 – Review the Token Limit Architecture

```
┌──────────────┐    ┌─────────────────────────────────────┐    ┌──────────────┐
│ CustomerAI   │───▶│  APIM AI Gateway                    │───▶│ Azure OpenAI │
│ (Key A)      │    │                                     │    │  gpt-4o-mini │
├──────────────┤    │  ┌─────────────────────────────────┐ │    └──────────────┘
│ InternalOps  │───▶│  │ azure-openai-token-limit policy │ │
│ (Key B)      │    │  │ - 5,000 TPM for CustomerAI      │ │
├──────────────┤    │  │ - 3,000 TPM for InternalOps     │ │
│ Research     │───▶│  │ - 2,000 TPM for Research        │ │
│ (Key C)      │    │  └─────────────────────────────────┘ │
└──────────────┘    └─────────────────────────────────────┘
```

---

## Part 2 – Configure Token Rate Limiting Policy

### Step 2.1 – Open the APIM Policy Editor

1. Go to **Azure Portal** → **API Management** → your APIM instance
2. Navigate to **APIs** → **Azure OpenAI** → **Chat Completions** operation
3. Click the **`</>`** (code editor) icon in the **Inbound processing** section

### Step 2.2 – Add the Token Limit Policy

Replace the `<inbound>` section with the following policy:

```xml
<inbound>
    <base />
    <!-- Pass-through the API key to Azure OpenAI -->
    <set-header name="api-key" exists-action="override">
        <value>{{aoai-key}}</value>
    </set-header>

    <!-- Token-based rate limiting: 5,000 tokens per minute per subscription -->
    <azure-openai-token-limit
        tokens-per-minute="5000"
        counter-key="@(context.Subscription.Id)"
        estimate-prompt-tokens="true"
        tokens-consumed-header-name="x-]tokens-consumed"
        remaining-tokens-header-name="x-tokens-remaining" />
</inbound>
```

4. Click **Save**

### Step 2.3 – Understand the Policy Attributes

| Attribute | Value | Purpose |
|-----------|-------|---------|
| `tokens-per-minute` | `5000` | Max tokens any single subscription can consume per minute |
| `counter-key` | `context.Subscription.Id` | Each APIM subscription (team) gets its own counter |
| `estimate-prompt-tokens` | `true` | Estimates input tokens before forwarding (pre-check) |
| `tokens-consumed-header-name` | `x-tokens-consumed` | Response header showing tokens used |
| `remaining-tokens-header-name` | `x-tokens-remaining` | Response header showing remaining budget |

> **Why `estimate-prompt-tokens="true"`?** This estimates the prompt token count *before* sending to Azure OpenAI, allowing APIM to reject requests early if the budget is already exhausted — saving you money.

---

## Part 3 – Test Token Rate Limiting

### Step 3.1 – Send a Normal Request (CustomerAI Team)

```powershell
$headers = @{
    "Content-Type"       = "application/json"
    "Ocp-Apim-Subscription-Key" = $KEY_CUSTOMERAI
}
$body = @{
    messages = @(
        @{ role = "user"; content = "What is Azure?" }
    )
    max_tokens = 100
} | ConvertTo-Json

$response = Invoke-WebRequest `
    -Uri "$APIM_GATEWAY/openai/deployments/gpt-4o-mini/chat/completions?api-version=2024-10-21" `
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

### Step 3.2 – Exhaust the Token Budget

Send multiple large requests rapidly to exhaust the token limit:

```powershell
# Function to send a request and report status
function Send-AIRequest {
    param([string]$TeamKey, [string]$TeamName, [string]$Prompt)

    $headers = @{
        "Content-Type"       = "application/json"
        "Ocp-Apim-Subscription-Key" = $TeamKey
    }
    $body = @{
        messages = @(
            @{ role = "user"; content = $Prompt }
        )
        max_tokens = 500
    } | ConvertTo-Json

    try {
        $response = Invoke-WebRequest `
            -Uri "$APIM_GATEWAY/openai/deployments/gpt-4o-mini/chat/completions?api-version=2024-10-21" `
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

### Step 3.3 – Verify Other Teams Are NOT Affected

While CustomerAI is rate-limited, verify that other teams can still make calls:

```powershell
Write-Host "`n=== Testing InternalOps Team (should succeed) ==="
Send-AIRequest -TeamKey $KEY_INTERNALOPS -TeamName "InternalOps" -Prompt "What is 2+2?"

Write-Host "`n=== Testing Research Team (should succeed) ==="
Send-AIRequest -TeamKey $KEY_RESEARCH -TeamName "Research" -Prompt "What is 2+2?"
```

> **Expected Result:** Both InternalOps and Research return HTTP 200 successfully. Token limits are tracked **per subscription key**, so one team's exhaustion doesn't affect others.

### Step 3.4 – Wait for Token Budget Refill

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

## Part 4 – Differentiated Token Limits Per Team

### Step 4.1 – Apply Team-Specific Token Budgets

Different teams have different usage patterns. Let's assign differentiated limits:

| Team | Tokens Per Minute | Rationale |
|------|-------------------|-----------|
| CustomerAI | 10,000 TPM | Production-facing, highest priority |
| InternalOps | 5,000 TPM | Internal tools, medium priority |
| Research | 2,000 TPM | Experimentation, lowest priority |

### Step 4.2 – Update the Policy with Conditional Limits

Go back to the APIM policy editor and replace the `<inbound>` section:

```xml
<inbound>
    <base />
    <!-- Pass-through the API key to Azure OpenAI -->
    <set-header name="api-key" exists-action="override">
        <value>{{aoai-key}}</value>
    </set-header>

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

### Step 4.3 – Test Differentiated Limits

```powershell
# Test each team and observe the different remaining token counts

Write-Host "=== CustomerAI (10,000 TPM limit) ==="
Send-AIRequest -TeamKey $KEY_CUSTOMERAI -TeamName "CustomerAI" -Prompt "Explain Azure briefly."

Write-Host "`n=== InternalOps (5,000 TPM limit) ==="
Send-AIRequest -TeamKey $KEY_INTERNALOPS -TeamName "InternalOps" -Prompt "Explain Azure briefly."

Write-Host "`n=== Research (2,000 TPM limit) ==="
Send-AIRequest -TeamKey $KEY_RESEARCH -TeamName "Research" -Prompt "Explain Azure briefly."
```

> **Expected Result:** Each team shows a different `x-tokens-remaining` value reflecting their respective TPM budgets.

---

## Part 5 – Add Token Metrics Emission

### Step 5.1 – Emit Token Usage to Application Insights

Add the `azure-openai-emit-token-metric` policy to track consumption metrics.

In the **Outbound** section of the policy editor, add:

```xml
<outbound>
    <base />
    <!-- Emit token metrics to Application Insights -->
    <azure-openai-emit-token-metric
        namespace="AzureOpenAI">
        <dimension name="Subscription" value="@(context.Subscription.Name)" />
        <dimension name="Operation" value="ChatCompletion" />
        <dimension name="Model" value="gpt-4o-mini" />
    </azure-openai-emit-token-metric>
</outbound>
```

Click **Save**.

### Step 5.2 – Enable Application Insights on APIM

1. Go to your APIM instance → **Application Insights**
2. Click **+ Add** → Create a new Application Insights resource or link an existing one
3. Go to **APIs** → **Azure OpenAI** → **Settings** tab
4. Enable **Application Insights** → Set sampling to **100%** (for lab purposes)
5. Click **Save**

### Step 5.3 – Generate Traffic from All Teams

```powershell
# Generate traffic from each team
$prompts = @(
    "Explain microservices architecture",
    "What is Kubernetes?",
    "Describe event-driven design patterns",
    "How does Azure Functions work?",
    "Explain the CAP theorem"
)

foreach ($prompt in $prompts) {
    Send-AIRequest -TeamKey $KEY_CUSTOMERAI -TeamName "CustomerAI" -Prompt $prompt
    Send-AIRequest -TeamKey $KEY_INTERNALOPS -TeamName "InternalOps" -Prompt $prompt
    Send-AIRequest -TeamKey $KEY_RESEARCH -TeamName "Research" -Prompt $prompt
    Start-Sleep -Seconds 2
}

Write-Host "`nTraffic generation complete. Wait 2-3 minutes for metrics to appear."
```

### Step 5.4 – View Token Metrics in Application Insights

1. Go to **Application Insights** resource
2. Navigate to **Metrics**
3. Select:
   - **Metric Namespace:** `AzureOpenAI`
   - **Metric:** `Total Tokens`
   - **Split by:** `Subscription`
4. Set the time range to **Last 30 minutes**

> **Expected Result:** You should see a chart showing token consumption broken down by team (CustomerAI, InternalOps, Research).

---

## Part 6 – Custom Error Response for Rate-Limited Requests

### Step 6.1 – Add a Friendly 429 Error Response

In the `<on-error>` section of the policy, add:

```xml
<on-error>
    <base />
    <choose>
        <when condition="@(context.Response.StatusCode == 429)">
            <return-response>
                <set-status code="429" reason="Token Limit Exceeded" />
                <set-header name="Content-Type" exists-action="override">
                    <value>application/json</value>
                </set-header>
                <set-header name="Retry-After" exists-action="override">
                    <value>60</value>
                </set-header>
                <set-body>@{
                    return new JObject(
                        new JProperty("error", new JObject(
                            new JProperty("code", "TokenLimitExceeded"),
                            new JProperty("message", "Your team has exceeded the allocated token budget. Please retry after 60 seconds."),
                            new JProperty("team", context.Subscription.Name),
                            new JProperty("retry_after_seconds", 60)
                        ))
                    ).ToString();
                }</set-body>
            </return-response>
        </when>
    </choose>
</on-error>
```

Click **Save**.

### Step 6.2 – Test the Custom Error Response

Exhaust a team's token budget and observe the friendly error:

```powershell
# Rapidly send requests to exhaust Research team's small 2,000 TPM budget
for ($i = 1; $i -le 10; $i++) {
    Write-Host "--- Request $i ---"
    Send-AIRequest -TeamKey $KEY_RESEARCH -TeamName "Research" -Prompt $longPrompt
}
```

> **Expected Result:** After exhaustion, you should see a JSON response with `TokenLimitExceeded` error code, team name, and retry guidance instead of a generic 429.

---

## Summary

In this lab you:

| Step | What You Did |
|------|--------------|
| Part 1 | Understood why token-based rate limiting is needed for AI workloads |
| Part 2 | Configured the `azure-openai-token-limit` policy in APIM |
| Part 3 | Tested rate limiting and verified per-team isolation |
| Part 4 | Applied differentiated token budgets per team |
| Part 5 | Added token metric emission to Application Insights for monitoring |
| Part 6 | Created a friendly custom error response for rate-limited requests |

### Key Takeaways

- **Token limits > Request limits** for AI workloads (cost is per token, not per request)
- **Per-subscription counters** ensure one team can't consume another's budget
- **Prompt estimation** catches over-budget requests before they reach Azure OpenAI
- **Metrics emission** gives you visibility into who's consuming what
- **Custom errors** improve developer experience and help teams self-manage

---

> **Next:** Proceed to [Lab 2 – Quota Limiting](Lab-02-Quota-Limiting.md)
