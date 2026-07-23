%%SECTION 8|Data%%

### 🧊 Whiteboard Challenges — Data Storage

**W1. A ticketing platform sells globally: 200k reads/sec on event catalogs, strict-consistency seat inventory per venue, and 7-year immutable purchase receipts. Whiteboard the polyglot data design.**

> **Model answer:** Three stores, three jobs. Catalog: **Cosmos DB**, partition key `eventId`, **Session** consistency, multi-region replicas near users, autoscale RU/s (+ Redis cache-aside for the hottest events). Seat inventory: needs serializable "one seat, one buyer" semantics — **Azure SQL** Business Critical zone-redundant with failover groups, or Cosmos with **Bounded Staleness + optimistic concurrency (ETags)** scoped per venue; justify whichever you pick by the consistency requirement, not fashion. Receipts: **Blob with time-based immutability (WORM)** for 7 years, lifecycle to Archive after 180 days, private endpoints throughout. Close with the exam lens: each requirement named the store.

**W2. Your Cosmos bill exploded and p99 latency spiked. The container stores IoT readings with partition key = deviceType (4 values). Whiteboard the diagnosis and the fix, including how you migrate.**

> **Model answer:** Diagnose: 4 logical partitions → **hot partitions**; RU/s divides across physical partitions so the hot one throttles (429s → retries → more RUs), and 20 GB/logical-partition looms. Fix: repartition to high-cardinality key aligned to queries — `deviceId` (or hierarchical/synthetic key `deviceId_day` for time-series). Cosmos keys are immutable → **migrate via change feed**: create new container, dual-write or change-feed copy old→new, backfill, cutover reads, retire old. Add autoscale RU/s and TTL on raw readings; consider ADX for long-range analytics instead of hoarding in Cosmos.

### 📚 Key Resources — Data Storage

- [Azure SQL documentation](https://learn.microsoft.com/azure/azure-sql/)
- [Cosmos DB documentation](https://learn.microsoft.com/azure/cosmos-db/)
- [Cosmos partitioning guidance](https://learn.microsoft.com/azure/cosmos-db/partitioning-overview)
- [Cosmos consistency levels](https://learn.microsoft.com/azure/cosmos-db/consistency-levels)
- [Storage account documentation](https://learn.microsoft.com/azure/storage/)
- [Data store decision guide (Architecture Center)](https://learn.microsoft.com/azure/architecture/guide/technology-choices/data-store-decision-tree)
- [Storage redundancy explained](https://learn.microsoft.com/azure/storage/common/storage-redundancy)

%%SECTION 9|BCDR%%

### 🧊 Whiteboard Challenges — Business Continuity

**W1. The board asks for a DR strategy for 3 workload tiers: payments (RTO 5 min/RPO 0), internal ERP (RTO 4 h/RPO 15 min), archives (RTO 72 h). Whiteboard one slide per tier with services and rough cost logic.**

> **Model answer:** Payments: **active-active** two regions — Cosmos multi-region writes (RPO≈0) or SQL failover groups + zone redundancy everywhere, Front Door health-probe routing; most expensive by far, justified only here. ERP: **warm standby** — ASR-replicated VMs (RPO minutes) + SQL failover group, scaled-down secondary, scripted recovery plan; test failover quarterly; fraction of the cost. Archives: **backup-only** — immutable, GRS-replicated vaults, restore-from-backup meets 72 h; cheapest. Draw the matrix RTO/RPO → pattern → cost; the exam (and the board) reward matching spend to tier, not gold-plating everything.

**W2. Ransomware encrypted production AND the attacker had Owner rights for 6 hours. Whiteboard why your backup design still saves the company, control by control.**

> **Model answer:** Walk the attacker's attempts: delete backups → **soft delete** retains them 14+ days; purge the vault → **immutable vault policy** blocks it; disable protection/change policy → **multi-user authorization** demands a second identity via Resource Guard; encrypt data → replication copies it, but **point-in-time restores** predate infection; tamper region-wide → **GRS vault + cross-region restore**. Recovery: isolate, restore to clean point in an isolated subscription, rotate identities (PIM should have prevented 6-hour standing Owner — note it), forensics from immutable Log Analytics export. Lesson line: replication ≠ backup; immutability + MUA + JIT access is the trio.

### 📚 Key Resources — Business Continuity

- [Azure Backup documentation](https://learn.microsoft.com/azure/backup/)
- [Azure Site Recovery documentation](https://learn.microsoft.com/azure/site-recovery/)
- [SQL auto-failover groups](https://learn.microsoft.com/azure/azure-sql/database/auto-failover-group-sql-db)
- [Well-Architected reliability pillar](https://learn.microsoft.com/azure/well-architected/reliability/)
- [Azure reliability documentation (per-service guides)](https://learn.microsoft.com/azure/reliability/)
- [Backup security features (immutability, MUA)](https://learn.microsoft.com/azure/backup/security-overview)

%%SECTION 10|Monitor%%

### 🧊 Whiteboard Challenges — Monitoring

**W1. Whiteboard the observability design for the enterprise API platform (Front Door → APIM → ACA → Service Bus → SQL): what's collected where, and the 5 alerts you'd ship on day one.**

> **Model answer:** One central **Log Analytics workspace**; diagnostic settings on every layer; **App Insights** (workspace-based) on APIM + ACA with **distributed tracing** so one operation ID crosses the whole chain; Service Bus/SQL metrics + logs in. Day-one alerts: (1) availability web test fails from 3 regions; (2) 5xx ratio > 2% over 15 min (log alert); (3) p95 latency breach per API (metric); (4) **Service Bus DLQ depth > 0** — silent DLQs kill order flows; (5) SQL failover/Service Health event. All fire one **action group** (on-call + Teams webhook + auto-runbook where safe). Workbook for the golden signals; cost guarded by table plans + sampling.

**W2. A tenant of your multi-tenant SaaS demands access to "their logs only," while your SOC needs everything and Finance wants per-tenant cost attribution. Whiteboard the workspace design.**

> **Model answer:** Keep **one central workspace** (SOC correlation beats fragmentation) — Sentinel on top for the SOC. Tenant access: **resource-context RBAC** — tenants get Reader on their own spoke's resources, so queries auto-scope to their logs; or expose curated **workbooks**/exported views instead of raw workspace access. Finance: enforce a `tenantId` tag/custom dimension everywhere; usage queries split ingestion by resource/tag for chargeback; per-table retention keeps costs honest. Only split into separate workspaces if a regulator demands physical separation or sovereignty — name that trade-off explicitly.

### 📚 Key Resources — Monitoring

- [Azure Monitor documentation](https://learn.microsoft.com/azure/azure-monitor/)
- [Application Insights overview](https://learn.microsoft.com/azure/azure-monitor/app/app-insights-overview)
- [KQL tutorial](https://learn.microsoft.com/kusto/query/tutorials/learn-common-operators)
- [Log Analytics workspace design](https://learn.microsoft.com/azure/azure-monitor/logs/workspace-design)
- [Alerts & action groups](https://learn.microsoft.com/azure/azure-monitor/alerts/alerts-overview)
- [Microsoft Sentinel documentation](https://learn.microsoft.com/azure/sentinel/)
- [Defender for Cloud documentation](https://learn.microsoft.com/azure/defender-for-cloud/)

%%SECTION 11|Compute%%

### 🧊 Whiteboard Challenges — Compute

**W1. Map these five workloads to compute services on a whiteboard, defending each in one sentence: legacy COBOL bridge (Windows, registry hacks), customer web portal, video transcoding batch, 60-microservice platform (K8s team), monthly invoice generation triggered by queue.**

> **Model answer:** COBOL bridge → **VM** (registry/OS control; nothing else allows it) with zones or availability set. Portal → **App Service** (slots, certs, no container requirement). Transcoding → **Batch with Spot VMs** (parallel, interruptible = 90% discount; checkpoint jobs). Microservices with a real K8s team → **AKS** (they'll want CRDs/mesh; without the team it'd be ACA). Invoices → **Functions with Service Bus trigger** (per-execution billing, scale to zero) or ACA Job. Close with the decision tree: control ↔ ops burden, and 'cheapest that meets requirements' as the tiebreak.

**W2. Whiteboard the cost optimization review for 300 VMs running 24/7: what do you look at, in what order, and what savings bands do you quote?**

> **Model answer:** Order: (1) **delete zombies** (Advisor idle/unattached disks/IPs — 100% saving); (2) **right-size** overprovisioned SKUs (Advisor CPU/mem data — 30–50%); (3) **schedule** dev/test off-hours (auto-shutdown — ~65% for 8×5 workloads); (4) commit: **reservations** for steady prod (~40–60% at 3-yr) vs **savings plan** where flexibility matters (~30–50%); (5) **Azure Hybrid Benefit** on Windows/SQL (up to ~40% more); (6) refactor candidates → PaaS/containers/Spot for interruptible tiers. Draw the compounding: right-size *then* reserve — reserving an oversized VM locks in waste. Governance: budgets + cost alerts + tags for ownership.

### 📚 Key Resources — Compute

- [Compute decision tree (Architecture Center)](https://learn.microsoft.com/azure/architecture/guide/technology-choices/compute-decision-tree)
- [Virtual machines documentation](https://learn.microsoft.com/azure/virtual-machines/)
- [VMSS documentation](https://learn.microsoft.com/azure/virtual-machine-scale-sets/)
- [Functions hosting options](https://learn.microsoft.com/azure/azure-functions/functions-scale)
- [AKS baseline architecture](https://learn.microsoft.com/azure/architecture/reference-architectures/containers/aks/baseline-aks)
- [Azure reservations & savings plans](https://learn.microsoft.com/azure/cost-management-billing/savings-plan/)

%%SECTION 12|Migration%%

### 🧊 Whiteboard Challenges — Migration & Integration

**W1. A retailer must exit its datacenter in 9 months: 400 VMs, 30 SQL Servers, a 500 TB file archive, and one core app the business wants "modernized." Whiteboard the migration waves.**

> **Model answer:** Frame with CAF + the **5 Rs**. Wave 0 (month 1–2): **Azure Migrate** discovery + dependency mapping; build the **landing zone** first. Wave 1: low-risk **rehost** of dev/test + independent apps via Azure Migrate (momentum + learning). Wave 2: SQL via **DMA assess → DMS online** to SQL MI (refactor — instance features preserved, minimal downtime cutovers). Archive: **Data Box** (500 TB over WAN is months; trucks win) → Blob Cool/Archive with lifecycle. Wave 3: core app **rearchitected** to ACA + Service Bus behind APIM using strangler fig — in parallel, not blocking the exit. Wave 4: optimize (right-size, reservations, decommission). Timeline bar with the datacenter exit dependent only on waves 1–2.

**W2. Whiteboard the analytics pipeline for a retailer that needs: nightly ETL from 12 on-prem systems, real-time dashboard of store sales, and data scientists exploring 5 years of history.**

> **Model answer:** Ingest: **ADF with self-hosted IR** for the 12 on-prem sources (orchestrated nightly ELT) → **ADLS Gen2** raw/curated zones (medallion). Real-time: store POS events → **Event Hubs** → **Stream Analytics** (windowed aggregates) → Power BI real-time / **Fabric Real-Time Intelligence**. Exploration: **Fabric Lakehouse/OneLake** (or Databricks for heavy Spark/ML) over the same lake — one copy of data, multiple engines. Serving: Fabric Warehouse/semantic model for BI. Governance: Purview lineage, private endpoints, managed identities end-to-end. Name why each service and its exam signal.

### 📚 Key Resources — Migration & Integration

- [Cloud Adoption Framework — Migrate](https://learn.microsoft.com/azure/cloud-adoption-framework/migrate/)
- [Azure Migrate documentation](https://learn.microsoft.com/azure/migrate/)
- [Database Migration Service](https://learn.microsoft.com/azure/dms/)
- [Data Factory documentation](https://learn.microsoft.com/azure/data-factory/)
- [Microsoft Fabric documentation](https://learn.microsoft.com/fabric/)
- [Azure Data Box](https://learn.microsoft.com/azure/databox/)

%%SECTION 13|Auth,RBAC,Patterns%%

### 🧊 Whiteboard Challenges — Key Vault, Hybrid & IaC

**W1. Whiteboard the secrets architecture for 40 microservices across dev/test/prod: who can read what, how rotation works, and what an auditor sees.**

> **Model answer:** **Vault-per-app-per-environment** (blast radius) — or at minimum per-team-per-env; all with RBAC model, private endpoints, purge protection. Apps read via **managed identity + Key Vault Secrets User** scoped to their own vault; humans get PIM-eligible Officer roles in prod, standing access only in dev. Most 'secrets' eliminated entirely: managed identities/federation for Azure-to-Azure, so vaults hold only third-party keys + certs. Rotation: Key Vault rotation policies + Event Grid `SecretNearExpiry` → Function rotates; apps fetch latest version at startup/interval. Config vs secrets: **App Configuration** with KV references. Auditor sees: AuditEvent diagnostic logs per access, RBAC assignments, rotation timestamps.

**W2. The platform team deploys by portal-clicking and prod drifts weekly. Whiteboard the target IaC operating model and how you stop the drift — technically, not by policy memo.**

> **Model answer:** Single Git repo of **Bicep modules** (or Terraform) = source of truth; environments as parameter files; PR review + `what-if` output posted to the PR; pipeline (GitHub Actions, **OIDC federation**, no secrets) promotes dev→test→prod with approvals. Drift is stopped mechanically: deploy via **deployment stacks with denyWriteAndDelete** — portal edits are rejected by the platform, not by memo; developers keep Reader in prod, PIM for break-glass (which the stack still constrains). Detection for the rest: what-if drift checks on schedule + Policy audit. Rollback = redeploy previous commit. Load Testing + Chaos Studio as pipeline gates for the critical paths.

### 📚 Key Resources — Key Vault, Hybrid & IaC

- [Key Vault documentation](https://learn.microsoft.com/azure/key-vault/)
- [Key Vault best practices](https://learn.microsoft.com/azure/key-vault/general/best-practices)
- [Azure Arc documentation](https://learn.microsoft.com/azure/azure-arc/)
- [Bicep documentation](https://learn.microsoft.com/azure/azure-resource-manager/bicep/)
- [Deployment stacks](https://learn.microsoft.com/azure/azure-resource-manager/bicep/deployment-stacks)
- [App Configuration documentation](https://learn.microsoft.com/azure/azure-app-configuration/)
