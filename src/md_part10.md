

---

## 17. One-Page Cheat Sheets

### 17.1 Identity & Security

| Need | Answer |
| --- | --- |
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

### 17.2 Storage & Data

| Need | Answer |
| --- | --- |
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

### 17.3 Compute & Containers

| Need | Answer |
| --- | --- |
| Decision ladder | VM → App Service → Functions → ACA → AKS → ACI → Batch |
| VM SLA ladder | 99.9% single → 99.95% avail. set → 99.99% zones |
| Cheap interruptible | Spot · Steady 24/7 → reservations · Flexible commit → savings plan |
| Functions no cold start + VNet | Premium plan |
| Stateful orchestration | Durable Functions (fan-out/fan-in, saga) |
| Microservices, no K8s ops | Container Apps (KEDA scale-to-zero, revisions, Dapr) |
| Full K8s control | AKS (private cluster, workload identity, GitOps) |
| APIM tiers | Consumption (serverless) · Premium (VNet, multi-region, zones, self-hosted GW) · v2 = faster + VNet integration |

### 17.4 Networking

| Need | Answer |
| --- | --- |
| LB decision | L4 regional: LB · L7 regional+WAF: App GW · L7 global HTTP: Front Door · DNS any-protocol: Traffic Manager |
| Private PaaS | Private endpoint + private DNS zone (service endpoint = weaker, no on-prem) |
| Topology | Hub-spoke (firewall, Bastion, gateways, DNS in hub); big scale → Virtual WAN |
| Hybrid | VPN (internet, cheap) · ExpressRoute (private, SLA) · ER+VPN failover |
| Egress control | UDR 0.0.0.0/0 → Azure Firewall (Premium = TLS inspect/IDPS) |
| Peering | Non-transitive; global peering crosses regions/subs |
| Admin access | Bastion (no public IPs) · SNAT scale → NAT Gateway |
| Hybrid DNS | DNS Private Resolver (conditional forwarding both ways) |

### 17.5 BC/DR & Monitoring

| Need | Answer |
| --- | --- |
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
