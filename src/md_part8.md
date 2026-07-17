
---

## 15. Real-World Architecture Walkthroughs

Five end-to-end enterprise scenarios. For each: the business context, the design, why each component was chosen, how it fails safely, and where the money is saved.

### 15.1 FinSecure Bank — Hybrid Identity & Governance (10,000 users)

**Context:** A financial services firm with on-prem Active Directory migrates 10,000 users to the cloud. Regulators demand MFA, auditable privileged access, and least privilege. Budget favors minimal new infrastructure.

**Design:**

```
On-prem AD DS ──(Entra Connect: password hash sync)──► Microsoft Entra ID
                                                          │
                     Conditional Access policies ─────────┤
                     (MFA, compliant device, block legacy) │
                                                          ▼
   Management group hierarchy: Root ─ Platform ─ Landing Zones ─ Sandbox
        │ Azure Policy initiatives (allowed regions, required tags, Defender on)
        │ RBAC via Entra groups; PIM for Owner/Contributor; access reviews quarterly
```

**Key decisions & why:**

- **Password hash sync over ADFS/PTA:** cheapest, most resilient (auth works even if on-prem is down), no federation farm to patch. ADFS chosen only when regulators literally forbid hashes in cloud — they rarely do (it syncs a hash *of the hash*).
- **Conditional Access baseline:** require MFA for all users, block legacy authentication (the #1 password-spray vector), require compliant devices for admins.
- **PIM with approval + 4-hour activations** for Owner/Contributor/User Access Administrator; standing access is Reader-only. Access reviews auto-remove stale grants.
- **Break-glass:** two cloud-only emergency accounts, excluded from CA, monitored with alerts on every sign-in.
- **Governance:** management groups carry policy initiatives so every new subscription lands compliant on day one (landing zone pattern).

**Failure modes:** On-prem outage → cloud sign-in unaffected (PHS). Entra Connect server dies → sync pauses, auth continues; rebuild from config export. Admin credential theft → CA blocks unknown device, PIM means no standing privilege to steal, audit logs show the attempt.

**Cost notes:** PHS is free; PIM/CA need Entra ID P2 licenses for admins (scope licenses to who needs them, not all 10,000).

### 15.2 ShopSphere — Global E-Commerce Data Platform (GDPR)

**Context:** E-commerce across EU + US, 40 ms page-load target, GDPR requires EU customer data to stay in the EU. Catalog reads dominate; orders must never be lost.

**Design:**

```
Front Door Premium (WAF, caching)
   ├── EU region: App tier ─ Cosmos DB (catalog, session)  ─ Azure SQL (orders)
   └── US region: App tier ─ Cosmos DB (replica)           ─ Azure SQL (orders)
        Cosmos: multi-region write, Session consistency
        SQL: separate EU/US servers (data residency), zone-redundant, failover groups intra-geo
        Blob + ADLS Gen2 (EU): clickstream → lifecycle to Cool/Archive
        Service Bus: order events → fulfillment workers
```

**Key decisions & why:**

- **Cosmos DB for catalog/session:** global low-latency reads with multi-region writes; **Session consistency** — a shopper always sees their own cart instantly; nobody needs Strong for a product page.
- **Azure SQL for orders:** money needs ACID transactions and joins. **Residency by architecture:** EU orders live on an EU server, US on US — GDPR compliance by design, not by policy document. Failover groups pair within the same geography (EU→EU) so DR never violates residency.
- **Partition keys:** catalog by `productId`, cart by `sessionId` — high cardinality, matches queries.
- **Claim-check + Service Bus:** order-placed messages are small; invoice PDFs go to blob. DLQ monitored with alerts — a silent DLQ is where orders go to die.
- **Lifecycle policies:** clickstream hot 7 days → Cool 30 → Archive 365 → delete at 730 (GDPR minimization).

**Failure modes:** Region loss → Front Door reroutes; Cosmos serves writes from surviving region (RPO≈0); SQL failover group promotes secondary within the geo (seconds of data at risk — measured, accepted RPO). WAF absorbs OWASP attacks; rate limiting at APIM protects checkout APIs. Data corruption → SQL PITR (35 days) + Cosmos continuous backup.

**Cost notes:** Cosmos autoscale RU/s (spiky retail traffic), Front Door caching slashes origin egress, Archive tier for clickstream, reserved capacity on the steady-state SQL tiers.

### 15.3 ForgeWorks — Mission-Critical HA/DR (RTO < 15 min, RPO < 1 h)

**Context:** Manufacturing execution system; every hour of downtime stops the production line. Two regions, strict-but-not-zero recovery targets, limited ops team.

**Design:**

```
Region A (primary, zone-redundant)          Region B (warm standby)
  App Gateway (WAF, zonal) ◄─── Front Door priority routing ───► App Gateway
  VMSS across 3 zones (app)                  VMSS min capacity (scaled-down)
  Azure SQL Business Critical, ZR            Failover group secondary
  ASR replication: legacy VMs  ──────────►   Replica VMs (test failover quarterly)
  Recovery Services vault: daily backups, GRS, immutable, cross-region restore
```

**Key decisions & why:**

- **Zones first, region second:** zone redundancy handles the common failures (single DC) at near-zero design cost; the second region exists only for true regional disaster.
- **Warm standby sizing:** RTO of 15 min forbids cold rebuild-from-IaC (too slow) but doesn't require full active-active (too expensive). Minimal VMSS capacity in B scales out during failover.
- **ASR for the legacy VMs** (continuous replication, scripted recovery plans, RPO minutes); **failover groups** for SQL (listener endpoints — the app config never changes). Both comfortably beat the 1-hour RPO.
- **Backup ≠ DR:** immutable, GRS-replicated backups defend against ransomware — replication alone would faithfully replicate the encryption of your files by an attacker.
- **Quarterly test failovers** into isolated networks; an untested DR plan is a rumor, not a plan.
- **Health model:** availability tests + Service Health alerts trigger the documented failover runbook (automated via Automation runbooks; humans approve).

**Failure modes:** Zone loss → transparent (zonal VMSS + ZR SQL). Region loss → Front Door priority flips, VMSS-B scales, SQL FG fails over, ASR recovery plan boots legacy tier in order: measured RTO ~12 min. Ransomware → immutable backups + MUA restore to clean point.

**Cost notes:** Standby VMSS at minimal instance count; reservations on Region A steady compute; Spot for the batch analytics tier; B-series for the rarely-used jump boxes.

### 15.4 CloudGate SaaS — Secure Hub-Spoke for 50 Customer Environments

**Context:** A B2B SaaS provider hosts 50 isolated customer environments. Customers demand tenant isolation evidence; the provider wants centralized egress control, DNS, and logging without 50 copies of everything.

**Design:**

```
                     Hub VNet
   Azure Firewall Premium (TLS inspect, IDPS)
   ExpressRoute + VPN failover gateways
   Azure Bastion ── Private DNS zones + Private Resolver
   Central Log Analytics workspace
        │ peering (non-transitive: all spoke↔spoke via firewall)
   ┌────┴─────┬──────────┬─ ... ─┐
 Spoke-C01  Spoke-C02  Spoke-C03  (one VNet per customer)
   each: app subnet + private endpoints subnet, NSGs, UDR 0.0.0.0/0 → firewall
   Deployment stamp: Bicep module = VNet + ACA environment + SQL + storage + PEs
```

**Key decisions & why:**

- **Spoke-per-customer = deployment stamp:** hard network isolation satisfies auditors better than logical row-level isolation; one Bicep module stamps out customer N+1 in minutes.
- **All traffic through the hub firewall:** UDRs force spoke egress and spoke↔spoke through Firewall Premium — one place for TLS inspection, IDPS, FQDN allow-lists, and one set of logs.
- **Private endpoints everywhere:** each customer's SQL/storage resolves via central private DNS zones; public access disabled on every PaaS resource. Azure Policy denies public-endpoint creation — governance backs up architecture.
- **Central Log Analytics with resource-context RBAC:** provider SOC sees everything; a customer-facing support role sees only that customer's resources. Table-level retention keeps firewall logs 90 days, app logs 30.
- **Scale watch-outs:** peering and UDR limits, firewall SNAT ports, IP address plan (each spoke gets a /24 from a reserved supernet — plan the whole /16 on day one).

**Failure modes:** Firewall is the choke point → deployed zone-redundant; its failure mode is the top availability risk and is monitored accordingly. Compromised customer app → NSGs + firewall rules prevent lateral movement to other spokes; per-spoke managed identities scope blast radius. DDoS → Network Protection plan on hub public IPs.

**Cost notes:** One firewall/gateway/Bastion set shared across 50 customers is the entire point of hub-spoke: isolation without 50× the platform bill. Firewall Premium justified by compliance; logs tiered aggressively.

### 15.5 RetailRun — Kubernetes at Scale with GitOps

**Context:** A retailer runs 60 microservices on AKS. Requirements: no secrets in pipelines or pods, image provenance, zero-downtime deploys, cluster recreatable in hours.

**Design:**

```
GitHub (app + infra repos)
   │ OIDC federation (no stored cloud secrets)
   ▼
GitHub Actions ── build → scan → push ──► ACR (private endpoint, Defender scans)
   │                                        ▲ AcrPull via kubelet MI
   ▼                                        │
 AKS (private cluster, 3 zones)  ◄── Flux GitOps: cluster state = infra repo
   ├─ system + user + Spot node pools, cluster autoscaler + KEDA
   ├─ Entra Workload Identity: pods → Key Vault (CSI driver) / SQL / Service Bus
   ├─ App Gateway for Containers ingress (WAF)
   └─ Azure Policy for AKS (no privileged pods, approved registries only)
```

**Key decisions & why:**

- **GitOps (Flux) over push deploys:** the cluster pulls its desired state from Git — the cluster is cattle; rebuilding = point Flux at the repo. Drift is auto-corrected, and the Git history is the change log auditors ask for.
- **OIDC federation for CI and Workload Identity for pods:** zero long-lived credentials anywhere in the chain. The pipeline exchanges GitHub's token for Entra tokens; pods exchange service-account tokens the same way.
- **Private everything:** private API server, ACR behind private endpoint, approved-registry policy — supply chain locked to images you built and scanned.
- **Zero-downtime:** rolling updates + PodDisruptionBudgets; blue-green at ingress for risky releases; KEDA scales order processors on Service Bus queue depth (scale on the honest signal, not CPU).
- **Spot node pool** for stateless batch (price-eviction tolerant), tainted so only batch tolerates it.

**Failure modes:** Zone loss → zonal node pools + PDBs keep quorum. Bad deploy → Git revert = rollback. Leaked pipeline? Nothing to leak — federation tokens are minutes-lived. Node compromise → workload identity scopes per-pod, Defender for Containers alerts, network policies limit east-west.

**Cost notes:** Spot pool (~70–90% off) for batch, autoscaler floor low at night, reservations for the steady system pool, ACR Premium only if geo-replication is needed.
