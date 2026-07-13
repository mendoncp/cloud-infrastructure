
---

## 8. Data Storage Design

### 8.1 Relational: Azure SQL Family

| Option | Traits | Choose when |
|---|---|---|
| **Azure SQL Database** | Fully managed single database; serverless option; Hyperscale | New cloud apps, per-database scaling |
| **SQL Managed Instance** | Near-100% SQL Server compatibility (SQL Agent, cross-DB queries, CLR), VNet-native | Lift-and-shift with instance-level features |
| **SQL Server on VMs** | Full OS/engine control, bring-your-own license | Legacy dependencies, OS access, full control |

**Purchasing models:**

- **DTU** (Basic/Standard/Premium): bundled compute+IO blend; simple, cheaper for small workloads; no serverless.
- **vCore** (General Purpose / Business Critical / Hyperscale): independent compute/storage sizing, **Azure Hybrid Benefit** (reuse SQL licenses), reserved capacity, serverless (auto-pause) in GP.

**Service tiers to know:**

- **General Purpose:** remote storage, 99.99%, budget default.
- **Business Critical:** local SSD + Always On replicas, lowest latency, **built-in readable secondary** (`ApplicationIntent=ReadOnly`), zone-redundant option.
- **Hyperscale:** up to 100+ TB, fast scale-out with named replicas, snapshot-based near-instant backups/restores.
- **Serverless (GP):** auto-scale + **auto-pause** — pay storage only while paused; ideal for intermittent dev/test.
- **Elastic pools:** many variable-usage databases share resources — SaaS multi-tenant cost pattern.

### 8.2 NoSQL: Azure Cosmos DB

- **Multi-model:** NoSQL (Core/SQL API), MongoDB, Cassandra, Gremlin, Table; **PostgreSQL** flavor for distributed relational.
- **Request Units (RU/s):** normalized cost of operations. Provisioned throughput (standard or **autoscale**) or **serverless** (per-request, spiky/low traffic).
- **Partitioning:** logical partitions by **partition key** — choose high-cardinality keys matching dominant query filters; avoid hot partitions. 20 GB logical partition limit.
- **Consistency levels (strongest→weakest):** **Strong → Bounded Staleness → Session (default) → Consistent Prefix → Eventual.** Session = read-your-own-writes per client; the usual sweet spot. Strong across regions costs latency/availability.
- **Global distribution:** turnkey multi-region replication; **multi-region writes** for active-active write availability; automatic/manual failover.
- **SLAs:** up to 99.999% read/write with multi-region; <10 ms point reads/writes at P99.
- Extras: change feed (event sourcing/integration), TTL, unique keys, analytical store (Synapse Link / mirroring to Fabric).

### 8.3 Azure Storage Accounts

**Services:** Blob (objects), ADLS Gen2 (hierarchical namespace for analytics), Files (SMB/NFS shares), Queues, Tables.

**Blob access tiers:** **Hot** (frequent) → **Cool** (≥30 days, lower storage/higher access cost) → **Cold** (≥90 days) → **Archive** (≥180 days, offline, hours to rehydrate). **Lifecycle management policies** auto-tier/delete by age or last access.

**Redundancy (memorize):**

| SKU | Copies | Survives |
|---|---|---|
| **LRS** | 3 in one datacenter | Drive/rack failure |
| **ZRS** | 3 across zones | Datacenter (zone) failure |
| **GRS / RA-GRS** | LRS ×2 regions (async) | Regional disaster (RA- adds read access to secondary) |
| **GZRS / RA-GZRS** | ZRS + LRS in pair region | Zone + regional failure — highest durability |

**Security/data protection:** SSE by default (+ optional CMK, infrastructure/double encryption), immutable storage (WORM legal hold/time-based), soft delete (blob/container/share), versioning, point-in-time restore, private endpoints, SAS (prefer user-delegation), Entra RBAC data roles.

**Azure Files extras:** identity-based SMB auth (Entra Kerberos/AD DS), **Azure File Sync** = cloud tiering + multi-site cache of on-prem file servers.

### 8.4 Choosing a Data Store (decision logic)

- Relational OLTP, strong schema, joins → **Azure SQL** (MI if lift-and-shift needs instance features).
- Global low-latency, flexible schema, massive scale → **Cosmos DB**.
- Objects/files/media, data lake → **Blob / ADLS Gen2**.
- Lift-and-shift SMB shares → **Azure Files (+ File Sync)**.
- Caching/session state → **Azure Cache for Redis**.
- Warehousing/analytics → **Synapse / Fabric**; big-data engineering → **Databricks**.
- Time-series/telemetry at scale → **Data Explorer (ADX)** / Fabric Real-Time Intelligence.

**Exam lens:** match *consistency, latency, scale, query shape, and cost* requirements — the cheapest store that satisfies them wins.

---

## 9. Business Continuity & Disaster Recovery

### 9.1 Definitions

- **RTO** (Recovery Time Objective): max acceptable downtime.
- **RPO** (Recovery Point Objective): max acceptable data loss window.
- **HA** = survive component failures (zones, replicas); **DR** = survive regional failure (pair region, backups); **Backup** = point-in-time recovery from deletion/corruption/ransomware — backups are NOT DR replication and replication is NOT backup.

### 9.2 Azure Backup

- **Recovery Services vault** (VMs, SQL/SAP in VMs, Files, on-prem via MARS/MABS) and **Backup vault** (Blobs, Disks, PostgreSQL).
- Policies define schedule + retention (daily/weekly/monthly/yearly GFS).
- **Soft delete** (retains deleted backups 14+ days), **immutable vaults**, **multi-user authorization** — ransomware defenses.
- **Cross-region restore** with GRS vaults.
- VM backup = app-consistent snapshots; instant restore from local snapshots.

### 9.3 Azure Site Recovery (ASR)

- Continuous **replication** of VMs (Azure↔Azure regions, VMware/Hyper-V/physical→Azure) for regional DR.
- **Recovery plans:** ordered multi-tier failover with scripts/runbooks; **test failover** into isolated networks without impacting production (do this regularly!).
- RPO typically seconds–minutes; RTO minutes (vs hours for restore-from-backup).
- Exam split: **need low RTO/RPO regional DR → ASR; need point-in-time restore → Backup.**

### 9.4 Database HA/DR

| Service | Mechanism |
|---|---|
| **Azure SQL** | Zone redundancy (BC/GP); **auto-failover groups** (RW + RO listener endpoints, group failover across regions); active geo-replication (per-DB readable secondaries, manual failover); PITR 1–35 days + LTR up to 10 years; geo-restore from geo-backups |
| **Cosmos DB** | Multi-region replication, automatic failover, multi-region writes (RPO≈0), continuous backup (PITR) or periodic |
| **MySQL/PostgreSQL Flexible** | Zone-redundant HA standby, read replicas (cross-region), geo-redundant backup |
| **Storage** | GRS/GZRS + customer-initiated account failover; blob object replication |

### 9.5 Multi-Region Application Patterns

- **Active-passive (cold/warm/hot standby):** cheaper, higher RTO; Front Door/Traffic Manager priority routing.
- **Active-active:** both regions serve traffic (weighted/performance routing); needs multi-master or partitioned data (Cosmos multi-write, or SQL failover group with read-locality).
- Sequence: define RTO/RPO per workload criticality tier → pick zone redundancy first (cheap) → add regional DR only where justified → automate failover → **test failover regularly**.
- **Chaos Studio** for resilience fault-injection experiments.

---

## 10. Monitoring & Observability

### 10.1 Azure Monitor Stack

- **Metrics:** numeric time-series (near-real-time), metrics explorer, metric alerts.
- **Logs:** **Log Analytics workspace** — KQL query store for resource logs, activity logs, custom logs.
- **Application Insights:** APM — request/dependency telemetry, exceptions, **distributed tracing** (correlate across APIM→ACA→Service Bus), live metrics, **availability (web) tests**, Application Map, smart detection. Workspace-based (data lands in Log Analytics).
- **Alerts:** metric, log (KQL scheduled), activity-log, smart detection → **action groups** (email, SMS, push, webhook, Logic App, Azure Function, ITSM). **Alert processing rules** suppress/route at scale.
- **Visualize:** workbooks (interactive, parameterized), dashboards, Grafana (managed).
- **Diagnostic settings** per resource route platform logs/metrics to: Log Analytics, Storage (cheap archive), Event Hubs (SIEM/3rd-party export).

### 10.2 Workspace Design (exam scenario)

- **Central workspace** per environment/region = easiest cross-resource correlation + centralized RBAC. Default recommendation.
- Split workspaces for: data sovereignty per region, chargeback isolation, different retention needs.
- **Table-level RBAC / resource-context access** lets teams see only their resources' logs in a shared workspace.
- Control cost: retention settings (interactive vs long-term/archive tiers), daily cap, Basic/Auxiliary table plans, sampling in App Insights.

### 10.3 KQL Survival Kit

```kusto
requests
| where timestamp > ago(1h)
| where success == false
| summarize failures = count() by name, resultCode, bin(timestamp, 5m)
| order by failures desc
```

Know: `where`, `summarize ... by bin()`, `project`, `join`, `render`. AZ-305 tests *choosing* the tool (metric alert vs log alert vs availability test) more than writing KQL.

### 10.4 Security & Health Monitoring

- **Microsoft Defender for Cloud:** CSPM (secure score, regulatory compliance) + workload protection plans (servers, storage, SQL, containers, Key Vault, APIs).
- **Microsoft Sentinel:** cloud-native **SIEM/SOAR** on Log Analytics — connectors, analytics rules, hunting, automation playbooks. Exam signal: "correlate security events across sources / SOC" → Sentinel.
- **Service Health** (Azure platform incidents, planned maintenance — alertable) vs **Resource Health** (your resource's availability).
- **Azure Advisor:** WAF-aligned recommendations (cost, security, reliability, performance, opex).
- **Network Watcher:** NSG flow logs/VNet flow logs, connection monitor, packet capture, IP flow verify.
