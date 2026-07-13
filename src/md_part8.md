
---

## 15. Hands-On Labs

Six guided labs mapping to exam objectives. Use a free account or MS Learn sandboxes. Each lab ends with a validation checklist and a troubleshooting challenge (three planted faults — answers at the end of each lab).

### Lab 1 — Identity & Governance (RBAC, PIM, Policy)

```bash
# 1. Create a management-group + policy baseline
az account management-group create --name "corp-workloads"
az policy assignment create --name "allowed-locations" \
  --scope "/providers/Microsoft.Management/managementGroups/corp-workloads" \
  --policy "e56962a6-4747-49cd-b67b-bf8b01975c4c" \
  --params '{"listOfAllowedLocations":{"value":["westeurope","northeurope"]}}'

# 2. Least-privilege data-plane assignment to a group at RG scope
az role assignment create --assignee-object-id <groupObjectId> \
  --assignee-principal-type Group \
  --role "Storage Blob Data Reader" \
  --scope "/subscriptions/<sub>/resourceGroups/rg-lab1"

# 3. Custom role: restart VMs only
az role definition create --role-definition '{
  "Name": "VM Restarter", "IsCustom": true,
  "Actions": ["Microsoft.Compute/virtualMachines/restart/action",
               "Microsoft.Compute/virtualMachines/read"],
  "AssignableScopes": ["/subscriptions/<sub>"] }'
```

**Validate:** deployment to eastus is denied by policy; group member can list blobs but not write; custom role appears with exactly two actions; PIM (portal) shows the role as *eligible*, activation requires MFA + justification.

**Troubleshooting challenge:** a colleague reports: (a) they still can't read blobs despite the assignment; (b) policy isn't blocking eastus deployments in one subscription; (c) the custom role can't be assigned in another subscription.
**Answers:** (a) waited <10 min for RBAC propagation, or they're using account keys disabled by policy — check `az role assignment list`; (b) that subscription isn't under the `corp-workloads` MG; (c) missing from `AssignableScopes`.

### Lab 2 — Hub-Spoke Network with Private Endpoint

```bash
az network vnet create -g rg-net -n vnet-hub --address-prefixes 10.0.0.0/16 \
  --subnet-name AzureFirewallSubnet --subnet-prefixes 10.0.1.0/26
az network vnet create -g rg-net -n vnet-spoke1 --address-prefixes 10.1.0.0/16 \
  --subnet-name snet-app --subnet-prefixes 10.1.1.0/24
az network vnet peering create -g rg-net -n hub-to-spoke1 \
  --vnet-name vnet-hub --remote-vnet vnet-spoke1 --allow-vnet-access
az network vnet peering create -g rg-net -n spoke1-to-hub \
  --vnet-name vnet-spoke1 --remote-vnet vnet-hub --allow-vnet-access

# Private endpoint for a storage account + private DNS
az storage account create -g rg-net -n stlab2$RANDOM --public-network-access Disabled
az network private-dns zone create -g rg-net -n privatelink.blob.core.windows.net
az network private-dns link vnet create -g rg-net -n link-spoke1 \
  --zone-name privatelink.blob.core.windows.net --virtual-network vnet-spoke1 --registration-enabled false
az network private-endpoint create -g rg-net -n pe-blob --vnet-name vnet-spoke1 \
  --subnet snet-app --private-connection-resource-id <storageId> \
  --group-id blob --connection-name conn-blob
```

**Validate:** `nslookup <account>.blob.core.windows.net` from a spoke VM returns a 10.1.1.x IP; public access attempt returns 403; peering state `Connected` both directions.

**Challenge faults:** (a) nslookup still returns a public IP; (b) spoke1 can't reach a VM in spoke2; (c) VM can't reach the internet after adding a UDR.
**Answers:** (a) private DNS zone not linked to the querying VNet (or custom DNS servers bypass it); (b) peering is non-transitive — route via hub firewall with UDRs (or peer directly); (c) UDR next-hop firewall exists but firewall has no allow rule / SNAT for that traffic.

### Lab 3 — APIM + Container Apps Enterprise API

```bash
az containerapp env create -g rg-api -n aca-env --location westeurope
az containerapp create -g rg-api -n orders-api --environment aca-env \
  --image mcr.microsoft.com/azuredocs/containerapps-helloworld:latest \
  --ingress internal --target-port 80 --min-replicas 0 --max-replicas 5

az apim create -g rg-api -n apim-lab3 --publisher-email you@example.com \
  --publisher-name Lab --sku-name Developer
# Import the ACA backend, then apply policy (portal or Bicep):
```

```xml
<inbound>
  <base />
  <validate-jwt header-name="Authorization" failed-validation-httpcode="401">
    <openid-config url="https://login.microsoftonline.com/<tenant>/v2.0/.well-known/openid-configuration" />
    <audiences><audience>api://orders-lab</audience></audiences>
  </validate-jwt>
  <rate-limit calls="10" renewal-period="60" />
</inbound>
```

**Validate:** call without token → 401; with valid token → 200; 11th call in a minute → 429; ACA replica count scales 0→N under load (`az containerapp replica list`).

**Challenge faults:** (a) APIM returns 500 BackendConnectionFailure; (b) valid tokens rejected 401; (c) rate limit never triggers.
**Answers:** (a) ACA ingress is internal and APIM (Developer, non-VNet) can't reach it — use external ingress for the lab or VNet-injected APIM; (b) audience mismatch (token `aud` ≠ policy audience) or wrong tenant in openid-config; (c) policy applied at wrong scope / `<base/>` order swallows it, or calls use different subscription keys (counter is per key).

### Lab 4 — Data: SQL Failover Group + Storage Lifecycle

```bash
az sql server create -g rg-data -n sqllab4-pri -l westeurope -u azadmin -p '<pwd>'
az sql server create -g rg-data -n sqllab4-sec -l northeurope -u azadmin -p '<pwd>'
az sql db create -g rg-data -s sqllab4-pri -n appdb --service-objective S0
az sql failover-group create -g rg-data -s sqllab4-pri -n fg-lab4 \
  --partner-server sqllab4-sec --add-db appdb --failover-policy Automatic --grace-period 1

# Storage lifecycle: cool after 30d, archive 90d, delete 365d
az storage account management-policy create --account-name <acct> -g rg-data --policy '{
 "rules":[{"name":"tier","enabled":true,"type":"Lifecycle","definition":{
  "filters":{"blobTypes":["blockBlob"]},
  "actions":{"baseBlob":{
    "tierToCool":{"daysAfterModificationGreaterThan":30},
    "tierToArchive":{"daysAfterModificationGreaterThan":90},
    "delete":{"daysAfterModificationGreaterThan":365}}}}}]}'
```

**Validate:** connect via `fg-lab4.database.windows.net` (listener, not server name); `az sql failover-group set-primary` on the secondary completes and the same connection string still works; lifecycle policy shows in `az storage account management-policy show`.

**Challenge faults:** (a) app breaks after failover; (b) blobs never move to Cool; (c) archive blob read fails.
**Answers:** (a) app connects to `sqllab4-pri...` directly instead of the failover-group listener; (b) last-modified dates too recent / policy runs ~daily — wait a cycle, or filters exclude the container prefix; (c) archived blobs must be rehydrated before read — that's by design.

### Lab 5 — Backup & DR Drill

```bash
az backup vault create -g rg-bcdr -n rsv-lab5 -l westeurope
az backup vault backup-properties set -n rsv-lab5 -g rg-bcdr \
  --backup-storage-redundancy GeoRedundant --soft-delete-feature-state Enable
az backup protection enable-for-vm -g rg-bcdr -v rsv-lab5 \
  --vm <vmId> --policy-name DefaultPolicy
az backup protection backup-now -g rg-bcdr -v rsv-lab5 \
  -c <containerName> -i <itemName> --retain-until 01-01-2027
```

Then (portal): enable ASR replication for the VM to a secondary region, build a recovery plan, and run a **test failover** into an isolated VNet.

**Validate:** restore point exists; test-failover VM boots in the isolated VNet with no production impact; cleanup test failover completes; deleting a backup leaves it recoverable (soft delete).

**Challenge faults:** (a) backup-now fails with UserErrorGuestAgentStatusUnavailable; (b) test failover VM has no network; (c) restored VM in secondary can't be reached via original DNS name.
**Answers:** (a) VM agent not running/outdated in the guest; (b) recovery plan/test failover not mapped to the isolated test VNet; (c) DNS still points at primary — failover runbooks must update DNS (or use Traffic Manager/Front Door).

### Lab 6 — Monitoring & Alerting

```bash
az monitor log-analytics workspace create -g rg-mon -n law-lab6
az monitor diag-settings create --resource <apimOrAppResourceId> -n ds-lab6 \
  --workspace law-lab6 --logs '[{"categoryGroup":"allLogs","enabled":true}]' \
  --metrics '[{"category":"AllMetrics","enabled":true}]'
az monitor action-group create -g rg-mon -n ag-oncall --short-name oncall \
  --action email admin you@example.com
az monitor scheduled-query create -g rg-mon -n alert-5xx \
  --scopes <workspaceId> --condition "count > 5" \
  --condition-query "requests | where success == false | where timestamp > ago(15m)" \
  --evaluation-frequency 5m --window-size 15m --action-groups ag-oncall
```

**Validate:** KQL `requests | summarize count() by resultCode` returns data; forced failures trigger the alert and the email arrives; App Insights Application Map shows the dependency chain.

**Challenge faults:** (a) no data in the workspace; (b) alert never fires though failures occur; (c) workspace cost spikes.
**Answers:** (a) diagnostic settings missing/pointed elsewhere, or 5–10 min ingestion latency; (b) query window/frequency mismatch or threshold too high — test the KQL manually first; (c) verbose categories (e.g., allLogs on chatty resources) — switch tables to Basic plan, add sampling, set daily cap.

> **Capstone:** rebuild the §7.1 reference architecture end-to-end with Bicep + GitHub Actions OIDC. If you can explain every resource's purpose to a colleague, you're exam-ready for the design questions.

---

## 16. One-Page Cheat Sheets

### 16.1 Identity & Security

| Need | Answer |
|---|---|
| User sign-in flow (web/SPA/mobile) | Auth code + PKCE |
| Daemon | Client credentials (cert/MI/federation > secret) |
| API → downstream API as user | On-Behalf-Of |
| No secrets Azure↔Azure | Managed identity + RBAC data roles |
| No secrets CI/CD | OIDC workload identity federation |
| JIT privileged access | PIM (eligible, approval, MFA, reviews) |
| Enforce MFA/device/location | Conditional Access (+ Identity Protection risk) |
| Consumers (CIAM) | Entra External ID · Partners → B2B guests |
| Delegated vs app permissions | `scp` claim vs `roles` claim; app perms need admin consent |
| Secrets/keys/certs | Key Vault (RBAC model, soft delete + purge protection, PE); FIPS L3 → Managed HSM |

### 16.2 Storage & Data

| Need | Answer |
|---|---|
| Redundancy ladder | LRS → ZRS → GRS/RA-GRS → GZRS/RA-GZRS |
| Tiers | Hot / Cool(30d) / Cold(90d) / Archive(180d, offline) + lifecycle policies |
| WORM compliance | Immutable storage (time-based / legal hold) |
| Data lake | ADLS Gen2 (hierarchical namespace) |
| Lift-and-shift SQL w/ Agent, cross-DB | SQL Managed Instance |
| 100+ TB, instant restore | Hyperscale |
| Intermittent dev/test DB | Serverless (auto-pause) |
| Multi-tenant SaaS DBs | Elastic pools |
| Global NoSQL, RPO≈0 writes | Cosmos DB multi-region writes; Session consistency default |
| Cache | Azure Cache for Redis (cache-aside) |
| Telemetry analytics (KQL) | Azure Data Explorer / Fabric RTI |

### 16.3 Compute & Containers

| Need | Answer |
|---|---|
| Decision ladder | VM → App Service → Functions → ACA → AKS → ACI → Batch |
| VM SLA ladder | 99.9% single → 99.95% avail. set → 99.99% zones |
| Cheap interruptible | Spot · Steady 24/7 → reservations · Flexible commit → savings plan |
| Functions no cold start + VNet | Premium plan |
| Stateful orchestration | Durable Functions (fan-out/fan-in, saga) |
| Microservices, no K8s ops | Container Apps (KEDA scale-to-zero, revisions, Dapr) |
| Full K8s control | AKS (private cluster, workload identity, GitOps) |
| APIM tiers | Consumption (serverless) · Premium (VNet, multi-region, zones, self-hosted GW) · v2 = faster + VNet integration |

### 16.4 Networking

| Need | Answer |
|---|---|
| LB decision | L4 regional: LB · L7 regional+WAF: App GW · L7 global HTTP: Front Door · DNS any-protocol: Traffic Manager |
| Private PaaS | Private endpoint + private DNS zone (service endpoint = weaker, no on-prem) |
| Topology | Hub-spoke (firewall, Bastion, gateways, DNS in hub); big scale → Virtual WAN |
| Hybrid | VPN (internet, cheap) · ExpressRoute (private, SLA) · ER+VPN failover |
| Egress control | UDR 0.0.0.0/0 → Azure Firewall (Premium = TLS inspect/IDPS) |
| Peering | Non-transitive; global peering crosses regions/subs |
| Admin access | Bastion (no public IPs) · SNAT scale → NAT Gateway |
| Hybrid DNS | DNS Private Resolver (conditional forwarding both ways) |

### 16.5 BC/DR & Monitoring

| Need | Answer |
|---|---|
| Definitions | RTO = downtime cap · RPO = data-loss cap |
| Ladder | Zones (cheap, 99.99%) → multi-region (priority/active-active via FD/TM) |
| VM regional DR, low RTO/RPO | ASR + recovery plans + test failovers |
| Point-in-time recovery | Azure Backup (soft delete, immutable vault, MUA vs ransomware) |
| SQL cross-region | Auto-failover groups (listener = no conn-string change); LTR up to 10 yrs |
| Storage DR | (RA-)G(Z)RS + customer-initiated failover (Last Sync Time loss) |
| Composite SLA | Serial: multiply · Parallel: 1−(1−A)² |
| Logs vs metrics | Log Analytics (KQL, log alerts) vs metrics (fast alerts) |
| APM/tracing | App Insights (availability tests, App Map) |
| Export | Diagnostic settings → LA / Storage (archive) / Event Hubs (SIEM) |
| SIEM/SOAR | Sentinel · Posture: Defender for Cloud · Recs: Advisor |
