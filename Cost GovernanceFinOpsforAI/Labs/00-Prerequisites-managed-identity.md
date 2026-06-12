# Lab Prerequisites - AI Cost Governance Labs (Managed Identity Authentication)

> **Complete these prerequisites BEFORE starting any of the labs.**
> 
> **Important:** This version uses **APIM Managed Identity** to authenticate to Azure OpenAI, instead of API keys. 
> This is required when Azure policy enforces `disableLocalAuth=true` on Azure OpenAI.
> 
> Estimated time: 30-45 minutes

---

## 1. Azure Subscription

### Where to Run Commands

- Run all `powershell` command blocks in a **PowerShell 7 terminal** (recommended: VS Code integrated terminal).
- Keep using the **same terminal session** for this entire document so variables like `$RESOURCE_GROUP`, `$AOAI_ENDPOINT`, and `$APIM_NAME` remain available.
- Sign in with Azure CLI (`az login`) in that same terminal when prompted.
- Steps that say **Azure Portal** must be done in the browser, not in the terminal.

> **If you restart or switch terminals**, all variables are lost. Run the block below to restore them before continuing.

### Session Variables (re-run any time you restart the terminal)

```powershell
# Core variables — set these once per terminal session
$RESOURCE_GROUP  = "rg-ai-finops-labs"
$LOCATION        = "eastus"
$SUBSCRIPTION_ID = az account show --query id --output tsv
$DEPLOYMENT      = "gpt-4o"   # model DEPLOYMENT name in your Azure OpenAI resource. Change this if you reuse an existing deployment (e.g. "gpt-4.1").

# Set your actual APIM name (created in Step 4.1, or look it up below)
if (-not $APIM_NAME) {
  $APIM_NAME = az apim list --resource-group $RESOURCE_GROUP --query "[0].name" -o tsv
}
Write-Host "Using APIM: $APIM_NAME"

# Set after APIM is provisioned (Step 4.3)
$APIM_GATEWAY = az apim show --name $APIM_NAME --resource-group $RESOURCE_GROUP --query gatewayUrl -o tsv 2>$null

# Set after subscriptions are created (Step 4.11)
$BASE_MGMT = "https://management.azure.com/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.ApiManagement/service/$APIM_NAME"
$KEY_CUSTOMERAI  = az rest --method POST --uri "$BASE_MGMT/subscriptions/customerai-team/listSecrets?api-version=2022-08-01"  --query primaryKey -o tsv 2>$null
$KEY_INTERNALOPS = az rest --method POST --uri "$BASE_MGMT/subscriptions/internalops-team/listSecrets?api-version=2022-08-01" --query primaryKey -o tsv 2>$null
$KEY_RESEARCH    = az rest --method POST --uri "$BASE_MGMT/subscriptions/research-team/listSecrets?api-version=2022-08-01"    --query primaryKey -o tsv 2>$null

Write-Host "RESOURCE_GROUP : $RESOURCE_GROUP"
Write-Host "APIM_NAME      : $APIM_NAME"
Write-Host "APIM_GATEWAY   : $APIM_GATEWAY"
Write-Host "KEY_CUSTOMERAI : $($KEY_CUSTOMERAI.Length) chars"
Write-Host "KEY_INTERNALOPS: $($KEY_INTERNALOPS.Length) chars"
Write-Host "KEY_RESEARCH   : $($KEY_RESEARCH.Length) chars"
```

> All three keys should show **32 chars**. If any shows `0 chars`, the subscription does not exist yet — complete Step 4.10 first.

### Requirements

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

### Step 3.3 - Get the Endpoint (No API Key Needed)

```powershell
# Get endpoint (you'll use APIM managed identity instead of API keys)
$AOAI_ENDPOINT = az cognitiveservices account show `
  --name "aoai-finops-lab" `
  --resource-group $RESOURCE_GROUP `
  --query "properties.endpoint" --output tsv

# Display endpoint
Write-Host "Azure OpenAI Endpoint: $AOAI_ENDPOINT"
Write-Host "NOTE: API keys are NOT needed - APIM will authenticate using managed identity"
```

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

Wait for provisioning state to become **Succeeded** before doing Steps 4.4-4.8.

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
az apim show --name $APIM_NAME --resource-group $RESOURCE_GROUP --query "provisioningState" --output tsv
```

### Step 4.3 - Get APIM Gateway URL

```powershell
$APIM_GATEWAY = az apim show `
  --name $APIM_NAME `
  --resource-group $RESOURCE_GROUP `
  --query "gatewayUrl" --output tsv

Write-Host "APIM Gateway: $APIM_GATEWAY"
```

### Step 4.4 - Enable APIM Managed Identity

Enable system-assigned managed identity on the APIM instance so it can authenticate to Azure OpenAI:

```powershell
# Enable system-assigned managed identity on APIM
az apim update `
  --name $APIM_NAME `
  --resource-group $RESOURCE_GROUP `
  --set identity.type=SystemAssigned

Write-Host "APIM system-assigned managed identity enabled."
```

### Step 4.5 - Get the APIM Managed Identity ID

```powershell
# Get the APIM managed identity principal ID
$APIM_MI_PRINCIPAL_ID = az apim show `
  --name $APIM_NAME `
  --resource-group $RESOURCE_GROUP `
  --query "identity.principalId" --output tsv

Write-Host "APIM Managed Identity Principal ID: $APIM_MI_PRINCIPAL_ID"
```

### Step 4.6 - Grant APIM MI Permission to Azure OpenAI

Assign the APIM managed identity the "Cognitive Services OpenAI User" role on the Azure OpenAI resource:

```powershell
# Get Azure OpenAI resource ID
$AOAI_RESOURCE_ID = az cognitiveservices account show `
  --name "aoai-finops-lab" `
  --resource-group $RESOURCE_GROUP `
  --query "id" --output tsv

# Assign "Cognitive Services OpenAI User" role to APIM MI on the AOAI resource
az role assignment create `
  --assignee $APIM_MI_PRINCIPAL_ID `
  --role "Cognitive Services OpenAI User" `
  --scope $AOAI_RESOURCE_ID

Write-Host "Role assignment created: APIM MI now has OpenAI User access to Azure OpenAI resource"
```

### Step 4.7 - Add Azure OpenAI as a Backend API

Run this step in the **Azure Portal** (browser).

1. Open the **Azure Portal** -> Navigate to your APIM instance
2. Go to **APIs** -> Click **+ Add API**
3. In **Create an AI API**, select **Microsoft Foundry**
4. In **Select AI Service**:
  - Select your subscription
  - Select the Azure OpenAI resource (for this lab: `aoai-finops-lab`)
  - Click **Next**

### Step 4.8 - Configure Model Route

Run this step in the **Azure Portal** (browser).

1. In **Configure Model Route**, set:
  - **Display name:** `aoai-finops-lab`
  - **Name:** `aoai-finops-lab`
  - **Base path:** `aoai-finops-lab`
2. Under **Client compatibility**, select **Azure OpenAI**
3. Leave **Products** empty for now (or choose your default product if required by your environment)
4. Click **Next** through:
  - **Manage token consumption**
  - **Apply semantic caching**
  - **Set up AI content safety**
5. In **Review + create**, click **Create**

> **Important:** In **Base path**, enter only a suffix such as `aoai-finops-lab`.
> Do NOT paste a full URL. If you paste a full URL, APIM can generate an invalid endpoint like `https://<apim>.azure-api.net/https://<apim>.azure-api.net/...`.
>
> **Note:** The Foundry API operations already include `/openai/...`. If you set base path to `.../openai`, your final route becomes `.../openai/openai/...` and can cause confusion or 404s in test calls.

### Step 4.9 - Configure Backend Authentication (Managed Identity)

Run this step in the **Azure Portal** (browser).

1. Go to **APIs** -> open the newly created Foundry API
2. Open **Settings** and verify the generated endpoint does not contain duplicated host text
3. Open **Policies** and verify there is NO `api-key` header policy
4. Click **Save** if you made any corrections

> **Important:** Notice there is NO `<set-header name="api-key">` block. This is intentional.
> The APIM managed identity handles Azure OpenAI authentication automatically.
> If you include an API key header, it will fail because the resource has `disableLocalAuth=true`.

> **Note:** In many tenants, the Foundry wizard can also enable APIM managed identity and assign the `Cognitive Services OpenAI User` role during creation. If Step 4.6 was already done manually, that is fine.

### Step 4.10 - Create APIM Subscriptions (One Per Team)

These subscriptions are used by **clients** to authenticate to APIM (NOT to Azure OpenAI).

> **Note:** `az apim subscription` is not available in all Azure CLI versions. Use `az rest` with a temp file to avoid PowerShell JSON quoting issues:

```powershell
$SUBSCRIPTION_ID = az account show --query id --output tsv
$BASE = "https://management.azure.com/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.ApiManagement/service/$APIM_NAME/subscriptions"
$tmp = "$env:TEMP\apim-sub.json"

# CustomerAI-Team
'{"properties":{"displayName":"CustomerAI-Team","scope":"/apis","state":"active"}}' | Out-File -Encoding ascii $tmp
az rest --method PUT --uri "$BASE/customerai-team?api-version=2022-08-01" --body "@$tmp" --headers "Content-Type=application/json"

# InternalOps-Team
'{"properties":{"displayName":"InternalOps-Team","scope":"/apis","state":"active"}}' | Out-File -Encoding ascii $tmp
az rest --method PUT --uri "$BASE/internalops-team?api-version=2022-08-01" --body "@$tmp" --headers "Content-Type=application/json"

# Research-Team
'{"properties":{"displayName":"Research-Team","scope":"/apis","state":"active"}}' | Out-File -Encoding ascii $tmp
az rest --method PUT --uri "$BASE/research-team?api-version=2022-08-01" --body "@$tmp" --headers "Content-Type=application/json"

Remove-Item $tmp
```

### Step 4.11 - Get Subscription Keys

Use `listSecrets` to retrieve the actual primary key value for each team. The key is a 32-character secret — **not** the display name.

```powershell
$SUBSCRIPTION_ID = az account show --query id --output tsv
$BASE_MGMT = "https://management.azure.com/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.ApiManagement/service/$APIM_NAME"

# Retrieve primary key for each team (stored in variables, not printed to avoid exposing secrets)
$KEY_CUSTOMERAI  = az rest --method POST --uri "$BASE_MGMT/subscriptions/customerai-team/listSecrets?api-version=2022-08-01"  --query primaryKey -o tsv
$KEY_INTERNALOPS = az rest --method POST --uri "$BASE_MGMT/subscriptions/internalops-team/listSecrets?api-version=2022-08-01" --query primaryKey -o tsv
$KEY_RESEARCH    = az rest --method POST --uri "$BASE_MGMT/subscriptions/research-team/listSecrets?api-version=2022-08-01"    --query primaryKey -o tsv

# Print key lengths only — do not print the actual key values
Write-Host "CustomerAI  key: $($KEY_CUSTOMERAI.Length) chars  (expected: 32)"
Write-Host "InternalOps key: $($KEY_INTERNALOPS.Length) chars  (expected: 32)"
Write-Host "Research    key: $($KEY_RESEARCH.Length) chars  (expected: 32)"
```

> **Save these key values.** They are 32-character hex strings.
> Do NOT use the team display names (e.g. `"CustomerAI-Team"`) as the key - that will cause 404.
> These are APIM subscription keys, NOT Azure OpenAI API keys.

---

## 5. Required Roles

### APIM Managed Identity Roles

- **Azure OpenAI:** APIM MI must have **"Cognitive Services OpenAI User"** role on the Azure OpenAI resource (done in Step 4.6)

### User Roles for Labs

- **Your account:** Must have **Owner** or **Contributor** on the resource group
- This allows you to create policies, run tests, and view diagnostics

---

## 6. Verification

### Step 6.1 - Verify Resources Are Created

```powershell
# Verify all resources exist
Write-Host "=== Resource Verification ==="

# Check Resource Group
$rg = az group show --name $RESOURCE_GROUP --query "{Name:name, Location:location}"
Write-Host "Resource Group: $(($rg | ConvertFrom-Json).Name) in $(($rg | ConvertFrom-Json).Location)"

# Check Azure OpenAI
$aoai = az cognitiveservices account show --name "aoai-finops-lab" --resource-group $RESOURCE_GROUP --query "{Name:name, Status:properties.provisioningState}"
Write-Host "Azure OpenAI: $(($aoai | ConvertFrom-Json).Name) - $(($aoai | ConvertFrom-Json).Status)"

# Check APIM
$apim = az apim show --name $APIM_NAME --resource-group $RESOURCE_GROUP --query "{Name:name, Status:properties.provisioningState}"
Write-Host "APIM: $(($apim | ConvertFrom-Json).Name) - $(($apim | ConvertFrom-Json).Status)"

# Check APIM Managed Identity
$identity = az apim show --name $APIM_NAME --resource-group $RESOURCE_GROUP --query "identity.principalId"
Write-Host "APIM MI Enabled: $identity"

# Check Role Assignment
$roleAssignment = az role assignment list --scope $(az cognitiveservices account show --name "aoai-finops-lab" --resource-group $RESOURCE_GROUP --query id --output tsv) --query "[?principalId=='$APIM_MI_PRINCIPAL_ID'].{Role:roleDefinitionName, Scope:scope}" --output table
Write-Host "Role Assignment: $roleAssignment"
```

### Step 6.2 - Test APIM Connection to Azure OpenAI

**Before running the test, verify all required variables are populated:**

```powershell
# Verify — all three must be non-empty before proceeding
if (-not $APIM_GATEWAY)    { Write-Host "MISSING: APIM_GATEWAY   - re-run Step 4.3" -ForegroundColor Red }
if (-not $KEY_CUSTOMERAI)  { Write-Host "MISSING: KEY_CUSTOMERAI - re-run Step 4.11" -ForegroundColor Red }
if ($KEY_CUSTOMERAI -and $KEY_CUSTOMERAI.Length -ne 32) {
    Write-Host "WARNING: KEY_CUSTOMERAI is $($KEY_CUSTOMERAI.Length) chars - expected 32. You may have used the display name instead of the key secret." -ForegroundColor Yellow
}
if ($APIM_GATEWAY -and $KEY_CUSTOMERAI.Length -eq 32) { Write-Host "Variables OK - ready to test" -ForegroundColor Green }
```

If any variable is missing, run the **Session Variables** block at the top of this document.

**Run the test call:**

```powershell
$body = @{
    messages  = @(@{ role = "user"; content = "Say hello in one sentence." })
    max_tokens = 50
} | ConvertTo-Json

# The subscription key is passed as a query parameter.
# Final URL path: $APIM_GATEWAY/<api-name>/openai/deployments/<deployment>/chat/completions
# where <api-name> is the base path set in Step 4.8 (e.g. aoai-finops-lab)
$headers = @{
  "Content-Type" = "application/json"
  "api-key"      = $KEY_CUSTOMERAI
}
$uri = "$APIM_GATEWAY/aoai-finops-lab/openai/deployments/$DEPLOYMENT/chat/completions?api-version=2024-10-21"

try {
    $response = Invoke-WebRequest -Uri $uri -Method POST -Headers $headers -Body $body
    $result   = $response.Content | ConvertFrom-Json
    Write-Host "SUCCESS" -ForegroundColor Green
    Write-Host "Message    : $($result.choices[0].message.content)"
    Write-Host "Tokens Used: $($result.usage.total_tokens)"
}
catch {
    $status = $_.Exception.Response.StatusCode.value__
    Write-Host "ERROR $status : $($_.Exception.Message)" -ForegroundColor Red
    if ($status -eq 404) { Write-Host "  -> Check that APIM_GATEWAY and KEY_CUSTOMERAI are set (both non-empty, key is 32 chars)." }
    if ($status -eq 401) { Write-Host "  -> Key is present but rejected - re-run Step 4.11 to refresh the key." }
    if ($status -eq 403) { Write-Host "  -> APIM MI role assignment may not have propagated yet - wait 5 min and retry." }
}
```

> **Expected Result:** HTTP 200 with an AI response.

---

## Troubleshooting

### Issue: "The system cannot find the file specified"

**Cause:** Azure CLI not available in the terminal.

**Solution:**
```powershell
# Verify Azure CLI is installed
Get-Command az

# If not found, install: https://learn.microsoft.com/cli/azure/install-azure-cli
```

### Issue: "The API key is invalid"

**Cause:** You're using an Azure OpenAI API key instead of an APIM subscription key.

**Solution:**
- Use only **APIM subscription keys** (from Step 4.11) in the `api-key` header
- Do NOT use Azure OpenAI API keys in client calls - APIM MI handles that

### Issue: "404 Resource not found"

**Most common cause:** URL path mismatch in APIM (for example base path duplication) or an empty `$APIM_GATEWAY` value.

**Solution:**
- Check that both `$APIM_GATEWAY` and `$KEY_CUSTOMERAI` are populated (not empty)
- Re-run the Session Variables block at the top of this document to recover them
- Ensure the URL includes the correct base path: `/aoai-finops-lab/openai/`

**Check:**
```powershell
Write-Host "APIM_GATEWAY  =[$APIM_GATEWAY]"
Write-Host "KEY length    =[$($KEY_CUSTOMERAI.Length)]"  # must be 32
```

**Solution:**
- If either is empty: run the **Session Variables** block at the top of this document.
- If the key length is wrong: you used the display name (e.g. `"CustomerAI-Team"`) instead of the secret. Re-run Step 4.11.
- If variables look correct but still 404: the URL path may be wrong. Verify the API base path in APIM:
  ```powershell
  az apim api list --resource-group $RESOURCE_GROUP --service-name $APIM_NAME --query "[].{Name:name,Path:path}" -o table
  ```
  Then build the URL as: `$APIM_GATEWAY/<path-from-above>/openai/deployments/$DEPLOYMENT/chat/completions?api-version=2024-10-21`

### Issue: "401 missing subscription key" (even when header is set)

**Cause:** The `api-key` header is missing, empty, or sent with the wrong header name.

**Solution:**
- Send APIM subscription key in header: `api-key: <your-team-key>`
- Do NOT use `Ocp-Apim-Subscription-Key` for this APIM API configuration.

### Issue: "Unauthorized: The APIM MI doesn't have permission to Azure OpenAI"

**Cause:** Role assignment failed or hasn't propagated yet.

**Solution:**
```powershell
# Verify role assignment exists
$APIM_MI_PRINCIPAL_ID = az apim show --name $APIM_NAME --resource-group $RESOURCE_GROUP --query "identity.principalId" --output tsv
$AOAI_RESOURCE_ID = az cognitiveservices account show --name "aoai-finops-lab" --resource-group $RESOURCE_GROUP --query "id" --output tsv

az role assignment list `
  --scope $AOAI_RESOURCE_ID `
  --query "[?principalId=='$APIM_MI_PRINCIPAL_ID']" `
  --output table

# If empty, re-run Step 4.6. If it exists, wait 5-10 minutes for replication.
```

---

## Next Steps

1. ✓ Prerequisites complete - Ready for labs
2. Proceed to **Lab-01-Token-Rate-Limiting-managed-identity.md**
3. Then **Lab-02-Quota-Limiting-managed-identity.md**
4. Finally **Lab-03-Chargeback-Model-managed-identity.md**

