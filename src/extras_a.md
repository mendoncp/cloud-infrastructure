%%SECTION 1|APIM%%

### 🧊 Whiteboard Challenges — APIM

**W1. A bank wants to expose 40 internal APIs to fintech partners with per-partner quotas, OAuth security, and zero public exposure of backends. Sketch the architecture and name the APIM features you'd use.**

> **Model answer:** Front Door Premium (WAF, global TLS) → APIM Premium in **internal VNet mode** → private backends. Partners are onboarded via the **developer portal**; each gets a **subscription** under a partner-tier **product** carrying `quota` and `rate-limit-by-key` policies. `validate-jwt` against Entra ID (client credentials for partner apps) at global scope; `authentication-managed-identity` toward backends; Key Vault-backed **named values** for any residual secrets. Per-partner analytics come free from subscription attribution. Justify Premium: internal VNet + AZ redundancy; everything else would work on Standard v2 with VNet integration if injection weren't needed.

**W2. During Black Friday, one consumer's buggy retry loop takes down the product API for everyone. Whiteboard the layered protections you should have had.**

> **Model answer:** Edge: WAF rate limiting + bot rules. Gateway: `rate-limit-by-key` (keyed on subscription/JWT sub) so one consumer exhausts only their bucket — the **throttling** pattern; `quota` for longer-horizon caps; **circuit breaker** on the backend entity so APIM stops hammering a degraded backend; `retry` policy with backoff only for idempotent GETs. Backend: **bulkhead** — separate ACA revisions/pools per consumer tier; **queue-based load leveling** for writes via Service Bus. Monitoring: alert on 429 ratio per subscription to catch the loop early. Key exam point: 429 the abuser, don't scale to absorb them.

### 📚 Key Resources — APIM

- [APIM documentation home](https://learn.microsoft.com/azure/api-management/)
- [APIM policy reference (every policy)](https://learn.microsoft.com/azure/api-management/api-management-policies)
- [APIM tiers & feature comparison](https://learn.microsoft.com/azure/api-management/api-management-features)
- [APIM VNet integration options](https://learn.microsoft.com/azure/api-management/virtual-network-concepts)
- [APIM landing zone accelerator (Architecture Center)](https://learn.microsoft.com/azure/architecture/example-scenario/integration/app-gateway-internal-api-management-function)
- [APIOps guidance](https://learn.microsoft.com/azure/architecture/example-scenario/devops/automated-api-deployments-apiops)

%%SECTION 2|ServiceBus%%

### 🧊 Whiteboard Challenges — Service Bus

**W1. An airline's booking system must process seat reservations strictly in order per flight, survive consumer crashes without losing bookings, and never double-charge on retries. Whiteboard the messaging design.**

> **Model answer:** Service Bus **queue with sessions**, `SessionId = flightNumber` → FIFO per flight while different flights process in parallel (sequential convoy). **Peek-lock** receive with explicit Complete → at-least-once; consumers renew locks for long work. Producer sets deterministic `MessageId = bookingId` + **duplicate detection** window → idempotent enqueue; consumer-side idempotency (upsert by bookingId) guards double-charging on redelivery. `MaxDeliveryCount` + **DLQ** with an alerted DLQ processor for poison bookings. Premium tier if private endpoints/zone redundancy are required.

**W2. Design the messaging backbone for an e-commerce order flow: order placed → inventory, payments, and email must all react; payment failures must be compensated; invoices are 20 MB PDFs.**

> **Model answer:** Order service publishes to a **topic** `orders` with three filtered **subscriptions** (inventory, payments, notifications) — pub/sub fan-out, correlation filters on event type. Payment failure triggers a **saga**: compensating messages (release inventory, cancel order) rather than distributed transactions. Invoices use **claim-check**: PDF to Blob Storage, message carries the URI. Email service scales with **competing consumers**; the whole chain is buffered (queue-based load leveling) so Black Friday bursts don't topple payments. Everything authenticated with managed identities + Service Bus data roles.

### 📚 Key Resources — Service Bus

- [Service Bus documentation home](https://learn.microsoft.com/azure/service-bus-messaging/)
- [Queues, topics & subscriptions concepts](https://learn.microsoft.com/azure/service-bus-messaging/service-bus-queues-topics-subscriptions)
- [Compare messaging services (SB vs Event Grid vs Event Hubs)](https://learn.microsoft.com/azure/service-bus-messaging/compare-messaging-services)
- [Sessions & FIFO](https://learn.microsoft.com/azure/service-bus-messaging/message-sessions)
- [Dead-letter queues](https://learn.microsoft.com/azure/service-bus-messaging/service-bus-dead-letter-queues)
- [Asynchronous messaging patterns (Architecture Center)](https://learn.microsoft.com/azure/architecture/patterns/category/messaging)

%%SECTION 3|RBAC%%

### 🧊 Whiteboard Challenges — RBAC & Governance

**W1. A 200-subscription enterprise has admins with permanent Owner everywhere and no configuration guardrails. Whiteboard the target governance model and the migration steps.**

> **Model answer:** Draw the **landing zone MG hierarchy**: Root → Platform (identity/connectivity/management) + Landing Zones (corp/online) + Sandbox + Decommissioned. Attach **Policy initiatives** at MG level (allowed regions, required tags, deny public storage, Defender on). Replace standing Owner with **PIM eligible** assignments (approval + MFA + 8h max), Reader as standing access, quarterly **access reviews**; assign everything to **Entra groups**. Break-glass accounts excluded from CA. Migration: inventory assignments → map to groups/roles → move subscriptions under MGs (policies in audit mode first) → flip to enforce → remove direct assignments.

**W2. An auditor asks: "Prove that a compromised web app in subscription X could not have read the HR database in subscription Y." Whiteboard your answer using the RBAC model.**

> **Model answer:** Walk the evaluation: the app's **managed identity** has role assignments only at X's resource group scope (least privilege, `DataActions` on its own storage only). No assignment exists at any scope covering Y — RBAC is **deny-by-default**; effective permissions = union of assignments, and none exist. Add layered evidence: Y's SQL has **private endpoint** + public access disabled (network), requires Entra auth (no SQL logins), and **Policy** denies public exposure. Show the audit trail: `az role assignment list` at each scope + Entra sign-in logs proving no token was ever issued for Y's resources.

### 📚 Key Resources — RBAC & Governance

- [Azure RBAC documentation](https://learn.microsoft.com/azure/role-based-access-control/)
- [Built-in roles reference](https://learn.microsoft.com/azure/role-based-access-control/built-in-roles)
- [Azure Policy documentation](https://learn.microsoft.com/azure/governance/policy/)
- [PIM documentation](https://learn.microsoft.com/entra/id-governance/privileged-identity-management/pim-configure)
- [Managed identities overview](https://learn.microsoft.com/entra/identity/managed-identities-azure-resources/overview)
- [Azure landing zones (CAF)](https://learn.microsoft.com/azure/cloud-adoption-framework/ready/landing-zone/)

%%SECTION 4|Networking%%

### 🧊 Whiteboard Challenges — Networking

**W1. Whiteboard a hub-spoke network for a company with 2 regions, on-prem ExpressRoute, mandatory egress inspection, and PaaS services that must never be publicly reachable. Label every routing decision.**

> **Model answer:** Per region: hub VNet (Azure Firewall Premium zone-redundant, ER gateway, Bastion, DNS Private Resolver) + workload spokes peered to hub. **UDR 0.0.0.0/0 → firewall** on every spoke subnet (egress inspection); spoke↔spoke also via firewall (peering non-transitive). ER private peering into both hubs, **VPN failover**. PaaS: **private endpoints** in spoke PE-subnets, public access disabled by Policy, **private DNS zones** linked to all VNets, on-prem resolution via Private Resolver inbound endpoint + conditional forwarders. Cross-region: hub-to-hub global peering. Address plan: carve a /16 per region up front.

**W2. Your global HTTP app is slow for Asian users and went down during a regional outage last month. Whiteboard the traffic path from user to backend that fixes both, naming each load-balancing layer.**

> **Model answer:** User → **Front Door** (anycast edge nearest the user: TLS termination, caching for static assets, WAF, health-probed **priority/latency routing** across regional origins) → regional **Application Gateway** (WAF_v2, path-based routing, zone-redundant) → AKS/ACA backends across 3 zones (internal **Azure LB** under the ingress). Asia latency: Front Door edge + caching + (optionally) an Asian region origin. Outage: Front Door probes fail → automatic origin failover. Note the exam contrast: Traffic Manager would be DNS-only failover (slower, TTL-bound) and adds no WAF/caching.

### 📚 Key Resources — Networking

- [Virtual network documentation](https://learn.microsoft.com/azure/virtual-network/)
- [Hub-spoke reference architecture](https://learn.microsoft.com/azure/architecture/networking/architecture/hub-spoke)
- [Private Link & private endpoints](https://learn.microsoft.com/azure/private-link/)
- [Private endpoint DNS integration](https://learn.microsoft.com/azure/private-link/private-endpoint-dns)
- [Load-balancing options decision guide](https://learn.microsoft.com/azure/architecture/guide/technology-choices/load-balancing-overview)
- [Azure Firewall documentation](https://learn.microsoft.com/azure/firewall/)
- [ExpressRoute documentation](https://learn.microsoft.com/azure/expressroute/)

%%SECTION 5|ContainerApps%%

### 🧊 Whiteboard Challenges — Container Apps

**W1. A startup with 8 microservices and no Kubernetes skills asks you to design their platform: private APIs, async order processing, nightly reports, minimal idle cost. Whiteboard it on ACA.**

> **Model answer:** One **internal ACA environment** in their VNet (workload profiles). HTTP APIs: internal ingress, **HTTP scale rules**, minReplicas 1 for the customer-facing API (no cold start), 0 for admin APIs. Order worker: **KEDA Service Bus scale rule**, minReplicas 0 — scales with queue depth, free when idle. Nightly reports: **ACA Job** (cron). **Dapr** pub/sub over Service Bus for service-to-service async; managed identity for ACR pulls (AcrPull) and Key Vault references. Exposure: APIM Standard v2 with VNet integration in front. Cost story: scale-to-zero everywhere except one API.

**W2. The team wants zero-downtime releases with instant rollback and gradual rollout, without building custom deployment tooling. Whiteboard the release flow on ACA.**

> **Model answer:** Set the app to **multiple revision mode**. Pipeline (GitHub Actions with OIDC federation — no secrets) builds → pushes to ACR → `az containerapp update` creates revision N+1 → **traffic split** 95/5 → watch App Insights failure rate/latency for the canary label → shift 50/50 → 0/100 → deactivate old revision. Rollback = set traffic 100% to revision N (instant, it's still warm). Draw the revisions as immutable snapshots behind Envoy ingress doing weighted routing. Mention session affinity caveat for stateful clients and health probes gating the new revision.

### 📚 Key Resources — Container Apps

- [Container Apps documentation](https://learn.microsoft.com/azure/container-apps/)
- [Revisions & traffic splitting](https://learn.microsoft.com/azure/container-apps/revisions)
- [Scaling (KEDA rules)](https://learn.microsoft.com/azure/container-apps/scale-app)
- [Dapr integration](https://learn.microsoft.com/azure/container-apps/dapr-overview)
- [Networking & internal environments](https://learn.microsoft.com/azure/container-apps/networking)
- [Compute service decision tree](https://learn.microsoft.com/azure/architecture/guide/technology-choices/compute-decision-tree)

%%SECTION 6|Auth%%

### 🧊 Whiteboard Challenges — Auth & Identity

**W1. Whiteboard the complete token journey when a doctor uses a hospital SPA to view lab results: SPA → API gateway → results API → downstream FHIR API. Name every flow and every validation.**

> **Model answer:** SPA signs the doctor in with **auth code + PKCE** → gets ID token (for the SPA) + access token (audience = results API, scope `Results.Read`). SPA calls APIM with the bearer token; APIM **validate-jwt** (signature via JWKS, iss, aud, exp, scp claim) rejects at the edge. Results API **re-validates** the token (zero trust), authorizes on `scp`, then uses **On-Behalf-Of** to exchange it for a FHIR-API token preserving the doctor's identity (audit trail shows the human, not a service account). APIM→backend locked with managed identity/mTLS + internal network. Conditional Access enforced MFA + compliant device at sign-in.

**W2. A partner's nightly batch job and your own AKS pods both need to call your inventory API. Whiteboard the identity design with zero stored secrets anywhere.**

> **Model answer:** Expose the API with **app roles** (e.g., `Inventory.Sync`) — application permissions with admin consent. Partner batch: their workload federates via **workload identity federation** (their cloud/CI token exchanged for your Entra tenant's token; multi-tenant app registration + admin consent) — no shared secret to rotate. AKS pods: **Entra Workload Identity** (federated service accounts) → tokens with `roles: Inventory.Sync`. API validates signature/iss/aud/exp then authorizes on `roles` (not `scp` — no user context). Rotate nothing; revoke by disabling the federated credential or SP. Monitor with sign-in logs per SP.

### 📚 Key Resources — Auth & Identity

- [Microsoft identity platform documentation](https://learn.microsoft.com/entra/identity-platform/)
- [OAuth 2.0 / OIDC flows overview](https://learn.microsoft.com/entra/identity-platform/v2-oauth2-auth-code-flow)
- [On-Behalf-Of flow](https://learn.microsoft.com/entra/identity-platform/v2-oauth2-on-behalf-of-flow)
- [Workload identity federation](https://learn.microsoft.com/entra/workload-id/workload-identity-federation)
- [Conditional Access documentation](https://learn.microsoft.com/entra/identity/conditional-access/)
- [Zero Trust guidance center](https://learn.microsoft.com/security/zero-trust/)
- [APIM validate-jwt policy](https://learn.microsoft.com/azure/api-management/validate-jwt-policy)

%%SECTION 7|Patterns,Exam%%

### 🧊 Whiteboard Challenges — Architecture & Patterns

**W1. Whiteboard the strangler-fig migration of a monolithic insurance system to microservices over 18 months, showing what exists at month 0, 6, and 18.**

> **Model answer:** Month 0: APIM (the facade) routes 100% to the monolith — deploying the gateway first is the key move. Month 6: `/claims` and `/quotes` carved out to Container Apps (highest-change, best-bounded contexts first); APIM routes those paths to new services, everything else to the monolith; an **anti-corruption layer** translates legacy models; shared data still in the legacy DB with a sync/change-feed bridge. Month 18: monolith reduced to a residual module or retired; each service owns its store (CQRS where read/write shapes diverge); Service Bus events between services; the facade never changed from the consumer's view — that's the pattern's whole point.

**W2. Your CEO asks: "Why does our 99.99% target cost 4× more than 99.9%?" Whiteboard the explanation an architect gives.**

> **Model answer:** Draw the serial chain: FD 99.99 × APIM 99.95 × app 99.95 × SQL 99.99 ≈ **99.88%** — a chain is weaker than its weakest link, so 99.9 is roughly the single-region ceiling. Getting to 99.99 means **parallel redundancy**: zone-redundant everything (small premium) then a second active region (1−(1−A)²) — doubling infrastructure, adding data replication (Cosmos multi-write or SQL FG), global routing, and the ops cost of failover testing. Show the availability ladder vs cost curve and the honest alternative: negotiate the SLO per workload tier — most workloads don't need 99.99.

### 📚 Key Resources — Architecture & Patterns

- [Cloud design patterns catalog](https://learn.microsoft.com/azure/architecture/patterns/)
- [Azure Well-Architected Framework](https://learn.microsoft.com/azure/well-architected/)
- [Azure Architecture Center (reference architectures)](https://learn.microsoft.com/azure/architecture/)
- [Microservices on Azure guide](https://learn.microsoft.com/azure/architecture/microservices/)
- [AZ-305 study guide (official)](https://learn.microsoft.com/credentials/certifications/resources/study-guides/az-305)
- [Free AZ-305 practice assessment](https://learn.microsoft.com/credentials/certifications/exams/az-305/practice/assessment)
