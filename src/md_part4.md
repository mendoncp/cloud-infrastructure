
---

## 6. Authentication & Authorization Patterns (Entra ID)

### 6.1 Protocol Foundations

- **OAuth 2.0** = authorization (delegated access via access tokens). **OpenID Connect (OIDC)** = authentication layer on top (ID tokens).
- **Tokens:** **ID token** (who the user is, for the client), **access token** (presented to APIs; validate audience/issuer/signature/expiry/claims), **refresh token** (get new tokens silently).
- **Microsoft identity platform** = Entra ID's OAuth2/OIDC implementation + MSAL libraries.

### 6.2 Choose the Right Flow (exam-critical)

| Scenario | Flow |
|---|---|
| Web app / SPA / mobile signing in users | **Authorization code + PKCE** |
| Service-to-service (daemon, no user) | **Client credentials** (secret or better: certificate / managed identity / workload identity federation) |
| API calling a downstream API on the user's behalf | **On-Behalf-Of (OBO)** |
| Input-constrained device (TV, CLI) | **Device code** |
| Legacy username/password | **ROPC — avoid** (blocked by MFA/CA, no modern security) |
| Implicit flow | **Deprecated** — use auth code + PKCE |

### 6.3 App Registrations, Scopes & App Roles

- **App registration** defines the identity of an app/API in Entra; **service principal** is its instance in a tenant; **enterprise application** = the SP view.
- **Expose an API:** define **scopes** (delegated permissions, e.g., `api://orders/Orders.Read`) consumed with user context, and **app roles** (application permissions for daemons, or role claims for users/groups).
- **Consent:** delegated permissions require user/admin consent; application permissions always require **admin consent**.
- **Validate in the API:** audience (`aud`), issuer (`iss`), signature (JWKS from OpenID metadata), expiry, then authorize on `scp` (delegated) or `roles` (app permissions). `scp` vs `roles` distinction is a classic exam trap.

### 6.4 Gateway-Centric AuthN/Z Pattern (enterprise APIs)

1. Client obtains access token from Entra ID (auth code + PKCE or client credentials).
2. Calls APIM with `Authorization: Bearer <token>` (+ subscription key for identification/analytics).
3. APIM `validate-jwt` / `validate-azure-ad-token` checks issuer, audience, and claims; rejects at the edge (defense in depth: backend validates again — zero trust).
4. APIM policy can do fine-grained authorization (claims → operations), token exchange, or `send-request` introspection.
5. APIM → backend using **managed identity** (`authentication-managed-identity` policy) or mTLS client certificate; backend locked to APIM via network (internal VNet/private endpoint) + identity.
6. Backend → data plane (SQL, Service Bus, Storage) via **managed identity + RBAC data roles**. No connection-string secrets anywhere; Key Vault for what remains.

### 6.5 Other Identity Patterns

- **Managed identities everywhere:** eliminate secrets for Azure-to-Azure calls.
- **Workload identity federation:** external workloads (GitHub Actions, other clouds, AKS pods) exchange their native tokens for Entra tokens — no stored credentials in CI/CD.
- **Microsoft Entra External ID (successor to Azure AD B2C):** CIAM — customer sign-up/sign-in, social identities, custom branding.
- **B2B guests:** invite partner users into your tenant; govern with entitlement management + access reviews.
- **Conditional Access:** policy engine (signals: user, device, location, risk → require MFA, compliant device, block). Pairs with **Identity Protection** risk detection.
- **SAS vs. Entra:** For Service Bus/Storage prefer Entra ID + RBAC; SAS only for constrained delegation scenarios (time-boxed, scoped URLs) or legacy.
- **mTLS:** client certificates for high-assurance service-to-service (APIM validates client certs; backends require APIM's cert).
- **Zero trust:** verify explicitly (every hop authenticates), least privilege (narrow scopes/roles, PIM), assume breach (segmentation, private networking, logging).

---

## 7. Enterprise API Architecture & Design Patterns

### 7.1 Reference Architecture (secure enterprise API platform)

```
Internet
  │
Azure Front Door Premium (global LB, CDN, WAF, TLS)
  │  (Private Link origin)
API Management — Premium, internal VNet, zone-redundant, multi-region
  │  validate-jwt • rate-limit • cache • transform
  ├─► Container Apps (internal env)  ─┐
  ├─► AKS (private cluster)          ├─ managed identities
  └─► Functions / App Service        ─┘
        │ async
      Service Bus Premium (private endpoint)
        │
      Worker apps (ACA jobs / Functions)
        │
  SQL / Cosmos / Storage — private endpoints, CMK
  Key Vault • ACR • Log Analytics • App Insights
Hub VNet: Azure Firewall (egress), Bastion, ExpressRoute/VPN, DNS resolver
```

### 7.2 Core Cloud Design Patterns (Azure Architecture Center)

| Pattern | Problem it solves |
|---|---|
| **Gateway (APIM)** | Single entry: cross-cutting auth, throttling, transformation |
| **Backends for Frontends (BFF)** | Per-client-tailored APIs (mobile vs web) |
| **Strangler Fig** | Incrementally migrate a monolith by routing slices via the gateway |
| **Gateway Offloading / Routing / Aggregation** | TLS, routing, response composition at the gateway |
| **Queue-Based Load Leveling** | Buffer bursts with Service Bus between tiers |
| **Competing Consumers** | Scale-out message processing |
| **Publisher-Subscriber** | Decoupled event distribution |
| **Claim-Check** | Large payloads via Blob + message reference |
| **Saga** | Distributed transactions via compensating steps |
| **CQRS + Event Sourcing** | Separate read/write models; event log as source of truth |
| **Retry + Circuit Breaker + Bulkhead** | Transient fault handling, stop cascading failures, isolate pools |
| **Cache-Aside** | Load-on-miss caching (Redis) |
| **Throttling** | Protect services under load (APIM rate-limit/quota) |
| **Health Endpoint Monitoring** | Probes for LB/orchestrator decisions |
| **Sidecar / Ambassador** | Offload connectivity/observability (Dapr) |
| **Anti-Corruption Layer** | Isolate new systems from legacy semantics |
| **Deployment Stamps** | Repeatable scale units per tenant/region |
| **Geode / active-active multi-region** | Global low latency + resilience |

### 7.3 Well-Architected Framework (WAF pillars — memorize)

1. **Reliability** — SLAs, redundancy (zones/regions), RTO/RPO, failure mode analysis, chaos testing.
2. **Security** — zero trust, identity as perimeter, encryption, network segmentation, Defender for Cloud.
3. **Cost Optimization** — right-size, reservations/savings plans, scale to zero, cost alerts.
4. **Operational Excellence** — IaC (Bicep/Terraform), CI/CD, observability, runbooks, safe deployment (rings, canary).
5. **Performance Efficiency** — scale out not up, caching, partitioning, async patterns, load testing.

Composite SLA math: serial components multiply (99.95% × 99.9% = 99.85%); redundant parallel components: 1−(1−A)². Region pair + zone redundancy raises availability.

### 7.4 AZ-305 Exam Blueprint (updated April 17, 2026)

| Domain | Weight |
|---|---|
| Design identity, governance, and monitoring solutions | 25–30% |
| Design data storage solutions | 25–30% |
| Design business continuity solutions | 10–15% |
| Design infrastructure solutions | 30–35% |

- Passing score **700/1000**; ~50 questions incl. case studies; scenario/"you need to recommend" style.
- **Prerequisite for the Expert cert:** AZ-104 (Azure Administrator Associate).
- Question style: *requirements → best-fit service*. Learn the **decision trees** (compute, messaging, load balancing, storage, identity) and *cheapest-that-meets-requirements* logic.

### 7.5 Study & Practice Resources

**Official (free):**

- Exam page & registration: https://learn.microsoft.com/credentials/certifications/exams/az-305/
- Official study guide (skills measured): https://learn.microsoft.com/credentials/certifications/resources/study-guides/az-305
- **Free official Practice Assessment:** https://learn.microsoft.com/credentials/certifications/exams/az-305/practice/assessment
- MS Learn AZ-305 learning paths (Design identity/governance, storage, BC, infrastructure): https://learn.microsoft.com/training/courses/az-305t00
- Azure Architecture Center (patterns + reference architectures): https://learn.microsoft.com/azure/architecture/
- Well-Architected Framework: https://learn.microsoft.com/azure/well-architected/
- Cloud Adoption Framework: https://learn.microsoft.com/azure/cloud-adoption-framework/
- APIM docs: https://learn.microsoft.com/azure/api-management/
- Service Bus docs: https://learn.microsoft.com/azure/service-bus-messaging/
- Container Apps docs: https://learn.microsoft.com/azure/container-apps/
- Exam sandbox (question-format demo): https://aka.ms/examdemo

**Practice tests & courses (paid/freemium):**

- MeasureUp (Microsoft's official practice test partner): https://www.measureup.com
- Whizlabs AZ-305: https://www.whizlabs.com/microsoft-azure-certification-az-305/
- Tutorials Dojo AZ-305: https://tutorialsdojo.com/courses/az-305-microsoft-azure-solutions-architect-practice-exams/
- Udemy — John Savill / Scott Duffy / practice test sets: https://www.udemy.com
- John Savill's AZ-305 YouTube study playlist (highly recommended, free): https://www.youtube.com/c/NTFAQGuy
- ExamTopics community questions (verify answers yourself): https://www.examtopics.com/exams/microsoft/az-305/

**Hands-on:**

- Azure free account ($200 credit): https://azure.microsoft.com/free/
- Microsoft Learn sandboxes (free, in-browser subscriptions inside modules)
- Build this guide's reference architecture yourself with Bicep — the single best prep activity.

### 7.6 8-Week Study Plan

| Week | Focus |
|---|---|
| 1 | Identity & governance: Entra ID, RBAC, PIM, Policy, management groups, landing zones |
| 2 | Networking: VNets, hub-spoke, private endpoints, load-balancing decision tree, hybrid |
| 3 | Compute: ACA vs AKS vs App Service vs Functions; APIM deep dive |
| 4 | Data: SQL/Cosmos/Storage tiers, HA/DR options, analytics (Synapse/Fabric basics) |
| 5 | Messaging & integration: Service Bus, Event Grid, Event Hubs, Logic Apps; app architecture patterns |
| 6 | Business continuity: backup, ASR, RTO/RPO design, multi-region patterns |
| 7 | Monitoring + Well-Architected review; MS Learn practice assessment until consistently >85% |
| 8 | Case-study drills, MeasureUp/Tutorials Dojo full mocks, weak-area review, sit the exam |
