# Lab Prerequisites - AI Cost Governance Labs

> **Complete these prerequisites BEFORE starting any of the labs.**
> Estimated time: 30-45 minutes

---

## 1. Azure Subscription

### Where to Run Commands

- Run all `powershell` command blocks in a **PowerShell 7 terminal** (recommended: VS Code integrated terminal).
- Keep using the **same terminal session** for this entire document so variables like `$RESOURCE_GROUP`, `$AOAI_ENDPOINT`, and `$APIM_NAME` remain available.
- Sign in with Azure CLI (`az login`) in that same terminal when prompted.
- Steps that say **Azure Portal** must be done in the browser, not in the terminal.

- An active Azure subscription with **Owner** or **Contributor** role
- Billing access (to view Cost Management data)
- If using a sandbox/trial, ensure you have at least **$50 in credits remaining**

### Verify Your Access

```powershell
# Login to Azure
az login

# List subscriptions and confirm your target
az account list --output table

# Set your target subscription
az account set --subscription "<YOUR_SUBSCRIPTION_ID>"
```

---

## 2. Resource Group

Create a dedicated resource group for all labs.

```powershell
# Set variables
$RESOURCE_GROUP = "rg-ai-finops-labs"
$LOCATION = "eastus"

# Create resource group
az group create --name $RESOURCE_GROUP --location $LOCATION
```

---

## 3. Azure OpenAI Resource

### Step 3.1 - Create the Azure OpenAI Resource

```powershell
# Create Azure OpenAI resource (custom domain is optional for labs)
az cognitiveservices account create `
  --name "aoai-finops-lab" `
  --resource-group $RESOURCE_GROUP `
  --location $LOCATION `
  --kind "OpenAI" `
  --sku "S0"
```

### Step 3.2 - Deploy a GPT-4o Model

```powershell
# Deploy gpt-4o (latest, non-deprecated model for labs)
az cognitiveservices account deployment create `
  --name "aoai-finops-lab" `
  --resource-group $RESOURCE_GROUP `
  --deployment-name "gpt-4o" `
  --model-name "gpt-4o" `
  --model-version "2024-11-20" `
  --model-format "OpenAI" `
  --sku-capacity 30 `
  --sku-name "Standard"
```

### Step 3.3 - Get the Endpoint and Key

```powershell
# Get endpoint
$AOAI_ENDPOINT = az cognitiveservices account show `
  --name "aoai-finops-lab" `
  --resource-group $RESOURCE_GROUP `
  --query "properties.endpoint" --output tsv

# Get API key
$AOAI_KEY = az cognitiveservices account keys list `
  --name "aoai-finops-lab" `
  --resource-group $RESOURCE_GROUP `
  --query "key1" --output tsv

# Display (keep these for the labs)
Write-Host "Endpoint: $AOAI_ENDPOINT"
Write-Host "Key: $AOAI_KEY"
```

### Step 3.4 - Test the Deployment

```powershell
# Quick test call
$headers = @{
  "Content-Type"  = "application/json"
  "api-key"       = $AOAI_KEY
}
$body = @{
  messages = @(
    @{ role = "user"; content = "Say hello in one sentence." }
  )
  max_tokens = 50
} | ConvertTo-Json

$response = Invoke-RestMethod `
  -Uri "$($AOAI_ENDPOINT)openai/deployments/gpt-4o/chat/completions?api-version=2024-10-21" `
  -Method POST `
  -Headers $headers `
  -Body $body

Write-Host "Response: $($response.choices[0].message.content)"
Write-Host "Tokens used - Prompt: $($response.usage.prompt_tokens), Completion: $($response.usage.completion_tokens), Total: $($response.usage.total_tokens)"
```

> **Checkpoint:** You should see a response and token count. If you get an error, verify your deployment name is `gpt-4o` and API version is correct.

---

## 4. Azure API Management (APIM)

> **Important:** APIM provisioning takes **15-30 minutes** for Developer tier. Start this early.

### Step 4.1 - Create APIM Instance

```powershell
# Set and keep APIM name in a variable
$APIM_NAME = "apim-finops-lab-$(Get-Random -Maximum 9999)"

# Create APIM instance (Developer tier for labs)
az apim create `
  --name $APIM_NAME `
  --resource-group $RESOURCE_GROUP `
  --location $LOCATION `
  --publisher-name "FinOps Lab" `
  --publisher-email "admin@contoso.com" `
  --sku-name "Developer" `
  --no-wait

Write-Host "APIM Name: $APIM_NAME"
```

> **Note:** The `--no-wait` flag returns immediately. The APIM resource will provision in the background. You can continue with other prerequisite steps while it provisions.
>
> **Expected behavior:** In Azure Portal, you may see messages like **"Service is being activated"** or **"Service is getting ready..."** for several minutes. This is normal for APIM Developer tier provisioning.

### Step 4.2 - Check APIM Provisioning Status

Wait for provisioning state to become **Succeeded** before doing Steps 4.4-4.8 in the portal.

> **Provisioning time:** Developer tier APIM typically takes **15-30 minutes** to reach Succeeded. In rare cases it may take up to 45 minutes. Repeat the status check every 2-3 minutes.

```powershell
# If your terminal session was restarted, re-set required variables first
$RESOURCE_GROUP = "rg-ai-finops-labs"

# Optional recovery: auto-pick APIM name from the resource group when APIM_NAME is empty
if (-not $APIM_NAME) {
  $APIM_NAME = az apim list `
    --resource-group $RESOURCE_GROUP `
    --query "[0].name" --output tsv
}

Write-Host "Checking APIM: $APIM_NAME"

# Check status (repeat until "Succeeded")
# Use single-line form to avoid line-continuation copy/paste issues
az apim show --name $APIM_NAME --resource-group $RESOURCE_GROUP --query "provisioningState" --output tsv
```

If you see **"The system cannot find the file specified."**:

```powershell
# 1) Ensure Azure CLI is available in THIS terminal
Get-Command az

# 2) Re-run in a single line in the same terminal where variables are set
$RESOURCE_GROUP = "rg-ai-finops-labs"; $APIM_NAME = "apim-finops-lab-9091"; az apim show --name $APIM_NAME --resource-group $RESOURCE_GROUP --query "provisioningState" --output tsv
```

### Step 4.3 - Get APIM Gateway URL

```powershell
$APIM_GATEWAY = az apim show `
  --name $APIM_NAME `
  --resource-group $RESOURCE_GROUP `
  --query "gatewayUrl" --output tsv

Write-Host "APIM Gateway: $APIM_GATEWAY"
```

### Step 4.4 - Add Azure OpenAI as a Backend API

Run this step in the **Azure Portal** (browser).

1. Open the **Azure Portal**-> Navigate to your APIM instance
2. Go to **APIs** -> Click **+ Add API**
3. Select **HTTP** (manual definition)
4. Fill in:
   - **Display name:** `Azure OpenAI`
   - **Name:** `azure-openai`
   - **Web service URL:** `<your AOAI endpoint>` (e.g., `https://aoai-finops-lab-1234.openai.azure.com/`)
   - **API URL suffix:** `openai`
5. Click **Create**

### Step 4.5 - Add a Chat Completions Operation

Run this step in the **Azure Portal** (browser).

1. In the newly created API, click **+ Add operation**
2. Fill in:
   - **Display name:** `Chat Completions`
   - **URL:** `POST` `/deployments/{deployment-id}/chat/completions`
3. Add **Template parameter:**
   - Name: `deployment-id`
   - Type: `string`
4. Add **Query parameter:**
   - Name: `api-version`
   - Required: Yes
   - Default value: `2024-10-21`
5. Click **Save**

### Step 4.6 - Configure Backend Authentication

Run this step in the **Azure Portal** (browser).

1. Go to **APIs** -> **Azure OpenAI** ->**All operations**
2. Click **Policies** (code editor `</>`) in the **Inbound processing** section
3. Add the API key header inside `<inbound>`:

```xml
<inbound>
    <base />
    <set-header name="api-key" exists-action="override">
        <value>{{aoai-key}}</value>
    </set-header>
</inbound>
```

4. Create a **Named Value** for the key:
   - Go to **Named values** -> **+ Add**
   - **Name:** `aoai-key`
   - **Type:** Secret
   - **Value:** `<your AOAI API key>`
   - Click **Save**

### Step 4.7 - Create APIM Subscriptions (One Per Team)

```powershell
# Create subscription for "CustomerAI" team
az apim subscription create `
  --resource-group $RESOURCE_GROUP `
  --service-name $APIM_NAME `
  --display-name "CustomerAI-Team" `
  --scope "/apis" `
  --state "active"

# Create subscription for "InternalOps" team
az apim subscription create `
  --resource-group $RESOURCE_GROUP `
  --service-name $APIM_NAME `
  --display-name "InternalOps-Team" `
  --scope "/apis" `
  --state "active"

# Create subscription for "Research" team
az apim subscription create `
  --resource-group $RESOURCE_GROUP `
  --service-name $APIM_NAME `
  --display-name "Research-Team" `
  --scope "/apis" `
  --state "active"
```

### Step 4.8 - Get Subscription Keys

```powershell
# List subscriptions and note the keys
az apim subscription list `
  --resource-group $RESOURCE_GROUP `
  --service-name $APIM_NAME `
  --query "[].{Name:displayName, Key:primaryKey}" `
  --output table
```

> **Save these keys.** You will use them in Labs 1, 2, and 3 to simulate different teams calling the API.

---

## 5. Required Roles

Ensure you have these roles assigned on the subscription:

| Role | Purpose | Needed For |
|------|---------|-----------|
| **Contributor** | Create/manage resources | All labs |
| **Cost Management Reader** | View cost data | Lab 3 (Chargeback) |
| **Cognitive Services Usages Reader** | View quota data | Lab 2 (Quota) |
| **API Management Service Contributor** | Manage APIM policies | Lab 1, 2 |

```powershell
# Verify your role assignments
az role assignment list `
  --assignee $(az ad signed-in-user show --query id --output tsv) `
  --scope "/subscriptions/$(az account show --query id --output tsv)" `
  --query "[].roleDefinitionName" --output table
```

---

## 6. Tools Required

| Tool | Version | Install Command |
|------|---------|----------------|
| **Azure CLI** | 2.60+ | `winget install Microsoft.AzureCLI` |
| **PowerShell** | 7.x | Pre-installed on Windows |
| **VS Code** | Latest | Pre-installed |
| **REST Client** (optional) | - | VS Code extension: `humao.rest-client` |

```powershell
# Verify Azure CLI version
az version --query '"azure-cli"' --output tsv
```

---

## 7. Resource Tags (For Lab 3)

Apply tags to the Azure OpenAI resource now - Lab 3 will use these for chargeback.

```powershell
# Tag the Azure OpenAI resource
az resource tag `
  --resource-group $RESOURCE_GROUP `
  --name "aoai-finops-lab" `
  --resource-type "Microsoft.CognitiveServices/accounts" `
  --tags `
    Department="AI-Platform" `
    CostCenter="CC-5001" `
    Environment="Lab" `
    Owner="FinOps-Team" `
    Project="CostGovernanceLab"
```

---

## Summary of Resources Created

After completing prerequisites, you should have:

| Resource | Name | Purpose |
|----------|------|---------|
| Resource Group | `rg-ai-finops-labs` | Container for all lab resources |
| Azure OpenAI | `aoai-finops-lab` | AI model endpoint |
| Model Deployment | `gpt-4o-mini` | Chat completions model |
| API Management | `apim-finops-lab-XXXX` | AI Gateway for policies |
| APIM API | `azure-openai` | API definition pointing to AOAI |
| APIM Subscriptions | 3 team subscriptions | Simulate multi-team access |

## Variables to Carry Forward

Save these values - you'll need them in every lab:

```powershell
# Copy and fill in these variables at the start of each lab
$RESOURCE_GROUP = "rg-ai-finops-labs"
$AOAI_ENDPOINT  = "<your-aoai-endpoint>"
$AOAI_KEY       = "<your-aoai-key>"
$APIM_NAME      = "<your-apim-name>"
$APIM_GATEWAY   = "<your-apim-gateway-url>"
$KEY_CUSTOMERAI  = "<subscription-key-for-CustomerAI>"
$KEY_INTERNALOPS = "<subscription-key-for-InternalOps>"
$KEY_RESEARCH    = "<subscription-key-for-Research>"
```

---

> **You are now ready to start the labs. Proceed to Lab 1.**
