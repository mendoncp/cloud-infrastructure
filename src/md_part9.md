
---

## 16. Hands-On Labs (CLI + Bicep, with Validation & Troubleshooting)

Do these in an Azure free account or MS Learn sandbox. Each lab: goal → commands → validation checklist → a deliberately broken configuration to diagnose. Clean up with `az group delete` after each lab. Replace `$RG`, `$LOC` (e.g., `westeurope`) throughout.

### Lab 1 — APIM: Publish, Protect, and Throttle an API

**Goal:** Front a public demo API with APIM, add a rate limit and JWT validation.

```bash
az group create -n $RG -l $LOC
az apim create -n apim-lab-$RANDOM -g $RG --publisher-email you@example.com \
  --publisher-name "Lab" --sku-name Consumption      # Consumption = fast + cheap for labs

# Import a demo OpenAPI backend
az apim api import -g $RG --service-name <apim-name> --path conference \
  --specification-url https://conferenceapi.azurewebsites.net?format=json \
  --specification-format OpenApiJson --api-id conf
```

Portal → API → All operations → Inbound policy:

```xml
<inbound>
  <base />
  <rate-limit-by-key calls="5" renewal-period="30"
      counter-key="@(context.Request.IpAddress)" />
</inbound>
```

**Validate:** ☐ Calling the API 6× in 30 s from one IP returns **429** on the 6th. ☐ Trace (Ocp-Apim-Trace) shows the policy firing. ☐ A subscription key is required (or API set to open intentionally).

**Troubleshoot this:** A teammate reports every caller shares one rate-limit bucket. *Find 3 issues:* (1) `rate-limit` used instead of `rate-limit-by-key`; (2) counter-key set to a constant string; (3) policy placed at product scope after `<base/>` of an API that already short-circuits with `return-response`. 

### Lab 2 — Service Bus: Queues, DLQ, and Sessions

```bash
az servicebus namespace create -n sb-lab-$RANDOM -g $RG -l $LOC --sku Standard
az servicebus queue create -n orders -g $RG --namespace-name <ns> \
  --max-delivery-count 3 --enable-dead-lettering-on-message-expiration true \
  --default-message-time-to-live PT5M
az servicebus queue create -n orders-fifo -g $RG --namespace-name <ns> \
  --enable-session true
# Send/receive without keys: assign yourself data roles
az role assignment create --assignee <your-upn> \
  --role "Azure Service Bus Data Owner" --scope <namespace-resource-id>
```

Send test messages with the portal's Service Bus Explorer: send 1 message, receive in **peek-lock** and abandon it 3 times.

**Validate:** ☐ After 3 abandons the message appears in the **DLQ** with reason `MaxDeliveryCountExceeded`. ☐ Messages sent to `orders-fifo` without a SessionId are rejected. ☐ Two messages with SessionId `A` are received in order.

**Troubleshoot this:** Consumers process duplicates and messages vanish under load. *Find 3 issues:* (1) receive-and-delete mode used, so crashes lose messages; (2) lock duration 30 s but processing takes 90 s with no lock renewal → redelivery duplicates; (3) TTL 5 min silently expires backlog — no one monitors the DLQ.

### Lab 3 — RBAC & Managed Identity: Zero-Secret Storage Access

```bash
az group create -n $RG -l $LOC
az storage account create -n stlab$RANDOM -g $RG --sku Standard_LRS --min-tls-version TLS1_2
az vm create -n vm-lab -g $RG --image Ubuntu2204 --size Standard_B1s \
  --assign-identity --generate-ssh-keys           # system-assigned MI

# Grant ONLY data-plane read at container scope (least privilege)
az role assignment create \
  --assignee <vm-principal-id> \
  --role "Storage Blob Data Reader" \
  --scope "<storage-id>/blobServices/default/containers/docs"
```

On the VM: get a token from IMDS and read a blob — no keys anywhere:

```bash
curl -s 'http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=https://storage.azure.com/' -H Metadata:true
```

**Validate:** ☐ Blob GET with the token succeeds. ☐ Blob PUT fails (Reader ≠ Contributor). ☐ `az role assignment list --scope <storage-id>` shows no broader grants. ☐ Storage account keys were never used.

**Troubleshoot this:** The app on the VM gets 403s. *Find 3 issues:* (1) role assigned at the wrong scope (another container); (2) role is Reader (control plane) not Storage Blob **Data** Reader; (3) token requested for the wrong resource/audience (`https://management.azure.com/`).

### Lab 4 — Hub-Spoke with Private Endpoint & Private DNS

```bash
az network vnet create -n vnet-hub -g $RG --address-prefix 10.0.0.0/16 -l $LOC \
  --subnet-name AzureFirewallSubnet --subnet-prefix 10.0.1.0/26
az network vnet create -n vnet-spoke -g $RG --address-prefix 10.1.0.0/16 -l $LOC \
  --subnet-name app --subnet-prefix 10.1.1.0/24
az network vnet peering create -n hub-to-spoke -g $RG --vnet-name vnet-hub \
  --remote-vnet vnet-spoke --allow-vnet-access
az network vnet peering create -n spoke-to-hub -g $RG --vnet-name vnet-spoke \
  --remote-vnet vnet-hub --allow-vnet-access

# Private endpoint for a storage account into the spoke
az storage account create -n stpe$RANDOM -g $RG --public-network-access Disabled
az network private-endpoint create -n pe-blob -g $RG --vnet-name vnet-spoke \
  --subnet app --connection-name blobconn \
  --private-connection-resource-id <storage-id> --group-id blob
az network private-dns zone create -g $RG -n privatelink.blob.core.windows.net
az network private-dns link vnet create -g $RG -n link-spoke \
  --zone-name privatelink.blob.core.windows.net --virtual-network vnet-spoke \
  --registration-enabled false
az network private-endpoint dns-zone-group create -g $RG \
  --endpoint-name pe-blob -n zg --private-dns-zone privatelink.blob.core.windows.net \
  --zone-name blob
```

**Validate:** ☐ From a VM in the spoke, `nslookup <account>.blob.core.windows.net` returns a **10.1.1.x** address. ☐ Blob access works from the VNet, fails from the internet. ☐ Peering state shows **Connected** both ways.

**Troubleshoot this:** VM resolves the storage FQDN to a public IP. *Find 3 issues:* (1) private DNS zone not linked to the VM's VNet; (2) DNS zone group missing so no A record was created; (3) VM uses custom DNS servers that don't forward to Azure DNS (168.63.129.16).

### Lab 5 — Container Apps: Revisions, Traffic Split, KEDA Scale on Service Bus

```bash
az containerapp env create -n aca-env -g $RG -l $LOC
az containerapp create -n web -g $RG --environment aca-env \
  --image mcr.microsoft.com/k8se/quickstart:latest \
  --ingress external --target-port 80 \
  --min-replicas 0 --max-replicas 5 --revisions-mode multiple

# New revision + canary
az containerapp update -n web -g $RG --set-env-vars VERSION=v2
az containerapp ingress traffic set -n web -g $RG \
  --revision-weight <rev1>=90 <rev2>=10

# Scale a worker on queue length
az containerapp create -n worker -g $RG --environment aca-env \
  --image <your-worker-image> --min-replicas 0 --max-replicas 10 \
  --scale-rule-name sbqueue --scale-rule-type azure-servicebus \
  --scale-rule-metadata queueName=orders namespace=<ns> messageCount=5 \
  --scale-rule-auth connection=sb-conn --secrets sb-conn=<connection-string>
```

**Validate:** ☐ `az containerapp revision list` shows two revisions with 90/10 weights; ~10% of curls return v2. ☐ With 0 messages the worker shows **0 replicas**; enqueue 50 messages → replicas grow; drain → back to 0. ☐ App scales to zero after idle (check replica count, note the cold-start on next request).

**Troubleshoot this:** The canary never receives traffic and the worker never scales. *Find 3 issues:* (1) app left in **single** revision mode so weights are ignored; (2) scale rule references the wrong queue name; (3) min-replicas set to 1 masks scale-to-zero claims while the KEDA auth secret is invalid (check `az containerapp logs`).

### Lab 6 — Entra ID: Protect an API with App Roles (validate-jwt end-to-end)

```bash
# API app registration exposing a role
az ad app create --display-name orders-api
az ad app update --id <api-app-id> --identifier-uris api://orders-api
# add appRole "Orders.Read" via portal (Manifest) or Graph
# Client credentials grant for a daemon client:
az ad app create --display-name orders-client
az ad app credential reset --id <client-app-id>       # secret for lab only
# Admin-consent the client's application permission to Orders.Read
```

Get a token and inspect it:

```bash
curl -X POST https://login.microsoftonline.com/<tenant>/oauth2/v2.0/token \
  -d "client_id=<client-app-id>&client_secret=<secret>" \
  -d "grant_type=client_credentials&scope=api://orders-api/.default"
# paste access_token into jwt.ms → check aud + roles claims
```

Then attach the `validate-jwt` policy from §1.4 to the Lab 1 APIM API requiring `roles` contains `Orders.Read`.

**Validate:** ☐ Token shows `aud: api://orders-api` and `roles: ["Orders.Read"]`. ☐ APIM returns 401 with no/expired token, 401 with wrong audience, 200 with the right one. ☐ In real projects the client uses **managed identity/federation**, not the lab secret.

**Troubleshoot this:** Every token is rejected with 401. *Find 3 issues:* (1) policy audience checks the client app ID instead of the API's; (2) openid-config URL uses the wrong tenant; (3) client requested `scope=api://orders-api/Orders.Read` with client_credentials — app-only flows must use `/.default`.

### Lab 7 — Backup & DR Drill: SQL PITR + Storage Recovery

```bash
az sql server create -n sql-lab-$RANDOM -g $RG -l $LOC -u labadmin -p '<strong-pw>'
az sql db create -n appdb -g $RG -s <server> --service-objective GP_S_Gen5_1 \
  --backup-storage-redundancy Zone
# create a table, insert rows, note the time, then DROP the table (the "disaster")
az sql db restore -g $RG -s <server> -n appdb --dest-name appdb-restored \
  --time "2026-07-17T10:30:00Z"                      # restore to before the drop
```

Storage protection drill:

```bash
az storage account blob-service-properties update -n <account> -g $RG \
  --enable-delete-retention true --delete-retention-days 7 \
  --enable-versioning true
# upload a blob, overwrite it, delete it — then recover both the version and the deleted blob
```

**Validate:** ☐ Restored DB contains the dropped table (restore is to a **new** database — plan the app cutover). ☐ Deleted blob is recoverable within retention; the pre-overwrite version restores. ☐ You know your measured RTO for this restore — write it down; that number *is* your DR documentation.

**Troubleshoot this:** A real incident recovers nothing. *Find 3 issues:* (1) soft delete enabled *after* the deletion happened; (2) restore attempted to the same DB name (unsupported) losing time; (3) retention 7 days but the corruption was noticed on day 9 — retention must exceed detection time.

### Lab 8 — IaC: Bicep + Deployment Stack with Deny Settings

```bicep
// main.bicep — a governed stamp
param location string = resourceGroup().location
resource sa 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: 'stack${uniqueString(resourceGroup().id)}'
  location: location
  sku: { name: 'Standard_ZRS' }
  kind: 'StorageV2'
  properties: { minimumTlsVersion: 'TLS1_2', allowBlobPublicAccess: false }
}
```

```bash
az deployment group what-if -g $RG --template-file main.bicep    # preview first
az stack group create -n lab-stack -g $RG --template-file main.bicep \
  --deny-settings-mode denyWriteAndDelete --action-on-unmanage deleteResources
# Now try to change the account in the portal → blocked by the stack's deny assignment
```

**Validate:** ☐ `what-if` showed the plan before deploy. ☐ Portal edit of the storage account is denied. ☐ Removing the resource from the template and updating the stack deletes it (managed lifecycle). ☐ `az stack group show` lists managed resources.

**Troubleshoot this:** Drift keeps appearing in prod. *Find 3 issues:* (1) stack created with `--deny-settings-mode none`; (2) an Owner is in the deny-settings excluded principals; (3) hotfixes applied in the portal instead of via the pipeline — the process, not the tool, is broken.

### Lab 9 — SQL Failover Group + Storage Lifecycle

```bash
az sql server create -g rg-data -n sqllab9-pri -l westeurope -u azadmin -p '<pwd>'
az sql server create -g rg-data -n sqllab9-sec -l northeurope -u azadmin -p '<pwd>'
az sql db create -g rg-data -s sqllab9-pri -n appdb --service-objective S0
az sql failover-group create -g rg-data -s sqllab9-pri -n fg-lab9 \
  --partner-server sqllab9-sec --add-db appdb --failover-policy Automatic --grace-period 1

# Storage lifecycle: cool after 30d, archive 90d, delete 365d
az storage account management-policy create --account-name <acct> -g rg-data --policy '{
 "rules":[{"name":"tier","enabled":true,"type":"Lifecycle","definition":{
  "filters":{"blobTypes":["blockBlob"]},
  "actions":{"baseBlob":{
    "tierToCool":{"daysAfterModificationGreaterThan":30},
    "tierToArchive":{"daysAfterModificationGreaterThan":90},
    "delete":{"daysAfterModificationGreaterThan":365}}}}}]}'
```

**Validate:** ☐ Connect via `fg-lab9.database.windows.net` (the listener, not the server name). ☐ `az sql failover-group set-primary` on the secondary completes and the same connection string still works. ☐ Lifecycle policy appears in `az storage account management-policy show`.

**Troubleshoot this:** (a) the app breaks after failover; (b) blobs never move to Cool; (c) reading an archived blob fails. *Answers:* (a) the app connects to `sqllab9-pri...` directly instead of the failover-group listener; (b) last-modified dates too recent / the policy runs ~daily — wait a cycle, or filters exclude the container prefix; (c) archived blobs must be rehydrated before read — that's by design.

### Lab 10 — Monitoring & Alerting

```bash
az monitor log-analytics workspace create -g rg-mon -n law-lab10
az monitor diag-settings create --resource <apimOrAppResourceId> -n ds-lab10 \
  --workspace law-lab10 --logs '[{"categoryGroup":"allLogs","enabled":true}]' \
  --metrics '[{"category":"AllMetrics","enabled":true}]'
az monitor action-group create -g rg-mon -n ag-oncall --short-name oncall \
  --action email admin you@example.com
az monitor scheduled-query create -g rg-mon -n alert-5xx \
  --scopes <workspaceId> --condition "count > 5" \
  --condition-query "requests | where success == false | where timestamp > ago(15m)" \
  --evaluation-frequency 5m --window-size 15m --action-groups ag-oncall
```

**Validate:** ☐ KQL `requests | summarize count() by resultCode` returns data. ☐ Forced failures trigger the alert and the email arrives. ☐ App Insights Application Map shows the dependency chain.

**Troubleshoot this:** (a) no data in the workspace; (b) the alert never fires though failures occur; (c) workspace cost spikes. *Answers:* (a) diagnostic settings missing/pointed elsewhere, or 5–10 min ingestion latency; (b) query window/frequency mismatch or threshold too high — test the KQL manually first; (c) verbose categories (allLogs on chatty resources) — switch tables to Basic plan, add sampling, set a daily cap.

> **Capstone:** rebuild the §7.1 reference architecture end-to-end with Bicep + GitHub Actions OIDC. If you can explain every resource's purpose to a colleague, you're exam-ready for the design questions.

> **Lab habit for the exam:** after every lab ask the AZ-305 question — *"which requirement (cost, RTO, isolation, least privilege) did each flag serve?"* The exam tests the why, not the syntax.
