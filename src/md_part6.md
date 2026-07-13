
---

## 11. Compute Design (Beyond Containers)

### 11.1 Full Compute Decision Tree

| Requirement | Service |
|---|---|
| Full OS control / legacy apps | **VMs** (+ VMSS for scale) |
| Web apps, slots, minimal ops | **App Service** |
| Event-driven code, per-execution billing | **Functions** |
| Microservices without K8s ops | **Container Apps** |
| Full Kubernetes control | **AKS** |
| Single simple container | **ACI** |
| Large-scale parallel/HPC jobs | **Azure Batch** |
| VDI / desktop streaming | **Azure Virtual Desktop** |

### 11.2 VMs & Scale Sets

- **Series:** B (burstable), D (general), E (memory), F (compute), L (storage), N (GPU), M (huge memory).
- **Availability:** single premium-SSD VM 99.9% → availability set (fault/update domains, one DC) 99.95% → **availability zones 99.99%**.
- **VMSS:** autoscale on metrics/schedule; **flexible orchestration** mixes VM types and spreads zones; supports Spot mix.
- **Spot VMs:** up to ~90% discount, evictable — batch/CI/stateless only.
- Disks: Ultra/Premium SSD v2/Premium/Standard SSD/HDD; host caching; ephemeral OS disks.
- Cost levers: reservations (1/3-yr), **savings plans** (flexible compute commit), Azure Hybrid Benefit (Windows/SQL licenses), right-sizing via Advisor.

### 11.3 Azure Functions Hosting

| Plan | Traits |
|---|---|
| **Consumption** | Scale to zero, per-execution, 5–10 min timeout, cold starts |
| **Flex Consumption** | Faster scale, VNet integration, per-instance concurrency |
| **Premium (Elastic)** | Pre-warmed instances (no cold start), VNet, unlimited duration |
| **Dedicated (App Service plan)** | Predictable cost, reuse existing plan |
| **Durable Functions** | Stateful orchestrations: function chaining, fan-out/fan-in, async HTTP, monitor, human interaction, **saga orchestration** |

Triggers/bindings: HTTP, Timer, Service Bus, Event Grid, Event Hubs, Cosmos change feed, Blob, Queue — the glue of event-driven architecture.

### 11.4 AKS Architect View

- **Control plane free/managed;** you pay for nodes. Standard/Premium tiers add uptime SLA.
- Node pools (system/user, Spot, GPU), **cluster autoscaler** + HPA/KEDA, **private cluster** (private API server), Azure CNI vs kubenet/CNI overlay.
- Identity: **Entra workload identity** for pods, managed identity for kubelet, Entra-integrated RBAC + Kubernetes RBAC.
- Ingress: App Gateway for Containers / AGIC, NGINX, or service mesh (Istio add-on).
- Ops: Fleet Manager (multi-cluster), node auto-upgrade channels, Defender for Containers, GitOps via Flux.

---

## 12. Data Integration, Analytics & Migration

### 12.1 Integration & Analytics Services

| Service | Role | Exam signal |
|---|---|---|
| **Azure Data Factory (ADF)** | Managed ETL/ELT orchestration; 90+ connectors; mapping data flows; **self-hosted integration runtime** for on-prem sources | "orchestrate/copy data pipelines, hybrid sources" |
| **Microsoft Fabric** | Unified SaaS analytics: OneLake, Lakehouse/Warehouse, Data Engineering, Real-Time Intelligence, Power BI | "unified analytics platform," successor direction to Synapse |
| **Azure Synapse Analytics** | Dedicated/serverless SQL pools, Spark, pipelines | Existing warehouse workloads (roadmap → Fabric) |
| **Azure Databricks** | First-class Spark platform: data engineering, ML, Delta Lake | "Spark/ML/lakehouse engineering" |
| **Azure Stream Analytics** | SQL-on-streams from Event Hubs/IoT Hub | "real-time SQL queries on event streams" |
| **Azure Data Explorer / ADX** | Telemetry/time-series interactive analytics (KQL) | "sub-second queries over billions of log rows" |
| **Logic Apps** | Low-code workflow integration, 1400+ connectors, B2B | "workflow across SaaS + on-prem, low-code" |
| **Event Grid / Service Bus / Event Hubs** | Messaging backbone (see §2.6) | — |

Logic Apps vs Functions: declarative connector-driven workflows vs code; combine freely (Durable Functions when code-first orchestration).

### 12.2 Migration Framework

**The 5 Rs:** **Rehost** (lift-and-shift IaaS), **Refactor/Repackage** (minor changes → PaaS, e.g., SQL MI, App Service), **Rearchitect** (microservices/containers), **Rebuild** (cloud-native rewrite), **Replace** (SaaS).

**Tooling:**

- **Azure Migrate:** discovery + assessment (dependency mapping, right-size + cost estimates) and migration of servers, databases, web apps, VDI.
- **Database Migration Service (DMS):** online/offline moves to Azure SQL family; pair with **Data Migration Assistant** (compat assessment) and SQL best-practice assessments.
- **Storage Migration Service / AzCopy / Azure File Sync:** file server data.
- **Azure Data Box:** offline bulk transfer (TB–PB) when network transfer is impractical.

Process (CAF Migrate): assess → replicate/test → migrate (cutover) → optimize (right-size, reservations, PaaS modernization).

---

## 13. Platform Extras: Key Vault, Hybrid, IaC

### 13.1 Key Vault Deep Dive

- Objects: **secrets, keys, certificates**. Standard vs **Premium (HSM-backed keys)**; **Managed HSM** = dedicated FIPS 140-2 Level 3 pool for strict compliance.
- **Soft delete (on by default) + purge protection:** recoverable deletions; purge protection blocks permanent delete until retention lapses — required for CMK scenarios.
- Access models: **Azure RBAC (recommended)** vs legacy access policies. Data roles: Key Vault Secrets User/Officer, Crypto User, Certificates Officer, Administrator.
- Per-vault-per-app-per-environment isolation limits blast radius; private endpoints + disable public access; firewall with trusted-services bypass.
- Certificate integration: auto-renewal with integrated CAs, App Service/App GW/APIM pull certs via managed identity.
- Monitor with diagnostic logs (AuditEvent) — alert on anomalous access.
- **App Configuration** complements Key Vault: feature flags + non-secret settings with Key Vault references.

### 13.2 Hybrid & Multicloud: Azure Arc

- **Arc-enabled servers:** project on-prem/other-cloud machines into ARM — Policy, RBAC, tags, Defender, Monitor agents, extensions.
- **Arc-enabled Kubernetes:** GitOps config, Policy for any CNCF cluster.
- **Arc-enabled data services:** SQL MI / PostgreSQL running on your infrastructure with cloud management.
- **Azure Local (HCI):** Azure-managed hyperconverged on-prem infrastructure.
- Exam signal: "manage/govern on-prem + AWS VMs with Azure Policy like Azure resources" → **Arc**.

### 13.3 Infrastructure as Code & Safe Deployment

- **Bicep:** Azure-native DSL over ARM — day-0 resource support, modules, what-if preview. **Terraform:** multicloud, state-file model, huge ecosystem. Either is exam-acceptable; both beat portal clicking.
- **Deployment stacks:** manage a Bicep/ARM deployment as a unit — deny settings (block out-of-band edits) and cleanup of removed resources (Blueprints successor).
- **Template specs:** versioned, RBAC-shared templates in Azure.
- **Azure Verified Modules / landing zone accelerators:** Microsoft-maintained IaC building blocks.
- Safe deployment practice: environments promoted via pipelines (GitHub Actions/Azure DevOps with OIDC federation — no secrets), what-if/plan gates, canary rings, feature flags (App Configuration), automated rollback.
- **Azure Load Testing** (Locust/JMeter managed) + **Chaos Studio** = performance and resilience validation in CI/CD.
