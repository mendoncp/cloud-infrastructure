# Azure Architect Mastery — Enterprise APIs & AZ-305 Study Guide

A comprehensive guide covering Azure API Management, Service Bus, RBAC, Cloud Networking, Container Apps, authentication/authorization patterns, and enterprise API architecture — aligned to the AZ-305 (Azure Solutions Architect Expert) exam.

---

## 1. Azure API Management (APIM)

### 1.1 What APIM Is

Azure API Management is a hybrid, multicloud platform for publishing, securing, transforming, and monitoring APIs. It sits between API consumers and backend services as a **facade**, decoupling clients from backend implementation.

**Three core components:**

- **API Gateway (data plane):** Accepts API calls, routes to backends, verifies keys/JWTs/certificates, enforces quotas and rate limits, transforms requests/responses, caches, and emits logs/metrics/traces.
- **Management plane:** Azure portal / ARM / Bicep / Terraform / CLI surface for provisioning, defining APIs, packaging into products, setting policies, and analytics.
- **Developer portal:** Auto-generated, customizable website where consumers discover APIs, read interactive docs, try APIs in a console, and get subscription keys.

### 1.2 Tiers (know these for the exam)

| Tier | Key traits | Use case |
|---|---|---|
| **Consumption** | Serverless, per-call billing, scale-to-zero, no VNet injection, ~sub-second activation | Lightweight/serverless APIs, spiky traffic |
| **Developer** | Full features, no SLA, single unit | Dev/test, evaluation |
| **Basic** | 99.95% SLA, small scale | Entry production |
| **Standard** | 99.95% SLA, more scale units | Medium production |
| **Premium** | Multi-region deployment, VNet injection, availability zones, self-hosted gateway, workspaces, higher scale | Enterprise, hybrid, mission-critical |
| **v2 tiers (Basic v2, Standard v2, Premium v2)** | Faster provisioning/scaling, VNet **integration** (outbound) in Standard v2; Premium v2 adds VNet injection | Modern deployments needing agility |

**Exam signal:** "multi-region," "VNet injection," "availability zones," or "self-hosted gateway" → **Premium** (or Premium v2 for injection).

### 1.3 Core Concepts

- **APIs and operations:** An API maps to a backend; operations map to endpoints. Import from OpenAPI, WSDL, gRPC (self-hosted), Azure Functions, Logic Apps, Container Apps, AKS.
- **Products:** Bundles of one or more APIs with a title, terms, visibility, and policies. Can be *open* (no subscription needed) or *protected* (subscription key required).
- **Subscriptions and keys:** A subscription grants access to a product (or all APIs, or a single API) via primary/secondary keys sent in the `Ocp-Apim-Subscription-Key` header.
- **Groups:** Administrators, Developers, Guests — control product visibility in the developer portal.
- **Named values:** Key-value store for policy configuration; can reference **Key Vault secrets**.
- **Backends:** Reusable backend entities with credentials, mTLS client certificates, and **circuit breaker** rules + **load-balanced pools**.
- **Versions vs. revisions:**
  - **Versions** = breaking changes, exposed to consumers (path `/v2/`, query string, or header versioning schemes).
  - **Revisions** = non-breaking iterations of the same version; test a revision via `;rev=2` URL then make it current. Safe rollout mechanism.
- **Workspaces (Premium):** Decentralized API teams manage their own APIs/products/subscriptions with isolated runtime on workspace gateways — supports federated API management at enterprise scale.

### 1.4 Policies — the heart of APIM

Policies are XML statements executed in the gateway pipeline in four sections:

```
inbound  → backend → outbound → on-error
```

Policy scopes and evaluation order: **Global → Workspace → Product → API → Operation**, composed via the `<base />` element (position of `<base/>` controls whether parent policies run before or after yours).

**Must-know policies:**

| Policy | Purpose |
|---|---|
| `rate-limit` / `rate-limit-by-key` | Throttle burst traffic (sliding window, 429 on breach) |
| `quota` / `quota-by-key` | Long-term call/bandwidth caps (e.g., per month) |
| `validate-jwt` | Validate Entra ID / OAuth2 JWTs (issuer, audience, claims, signing keys via OpenID config) |
| `validate-azure-ad-token` | Simplified Entra-specific token validation |
| `check-header`, `ip-filter` | Basic gating |
| `cors` | Cross-origin support |
| `set-header`, `set-query-parameter`, `rewrite-uri` | Request transformation |
| `set-backend-service` | Dynamic routing to different backends |
| `cache-lookup` / `cache-store` | Response caching (built-in or external Redis) |
| `send-request` | Call out to another service mid-policy (e.g., token introspection) |
| `mock-response` | Return mock for API-first development |
| `retry`, `forward-request` | Backend resiliency behavior |
| `authentication-managed-identity` | Gateway acquires a managed identity token to call the backend |
| `llm-token-limit` / `llm-semantic-cache` (AI gateway) | Token quotas and semantic caching for LLM backends |

**Example — JWT validation at the gateway:**

```xml
<inbound>
  <base />
  <validate-jwt header-name="Authorization" failed-validation-httpcode="401">
    <openid-config url="https://login.microsoftonline.com/{tenant}/v2.0/.well-known/openid-configuration" />
    <audiences>
      <audience>api://my-api-app-id</audience>
    </audiences>
    <required-claims>
      <claim name="roles" match="any">
        <value>Orders.Read</value>
      </claim>
    </required-claims>
  </validate-jwt>
  <rate-limit calls="100" renewal-period="60" />
</inbound>
```

### 1.5 Networking Options

- **External VNet injection (Premium):** Gateway in your VNet, publicly reachable; can reach private backends.
- **Internal VNet injection (Premium):** Gateway only reachable inside the VNet (or via peering/VPN/ER). The standard enterprise pattern: **Application Gateway (WAF) or Front Door in front → internal APIM → private backends**.
- **Private endpoint:** Private inbound access to APIM (no VNet injection needed; inbound only).
- **VNet integration (Standard v2):** Outbound-only reach into a VNet to call private backends.
- **Self-hosted gateway:** Containerized gateway you run on-premises or in other clouds; management plane stays in Azure. Enables hybrid/multicloud API federation.

### 1.6 Reliability & Scale

- **Multi-region (Premium):** Gateway replicated across regions; primary region hosts the management plane. Combine with routing policies for regional backend affinity.
- **Availability zones (Premium):** Zone-redundant scale units.
- **Autoscale** rules on capacity metric; **caching** to shave backend load.
- **Observability:** Application Insights integration, Azure Monitor metrics/logs, built-in analytics, OpenTelemetry via self-hosted gateway.

### 1.7 Enterprise API Deployment Checklist (APIM)

1. Premium/internal VNet (or Standard v2 + private endpoints) for network isolation.
2. Front Door or App Gateway + WAF for edge protection and global routing.
3. `validate-jwt` with Entra ID at gateway; subscription keys only as an *identification* mechanism, never sole *authentication* for sensitive APIs.
4. Products for consumer segmentation; quotas + rate limits per product/key.
5. Named values backed by Key Vault; managed identity to backends.
6. Versioning strategy declared up front; revisions for safe changes.
7. CI/CD: APIOps (extract/publish via Git), Bicep/Terraform infrastructure.
8. Diagnostics to Log Analytics; alerts on capacity, 4xx/5xx rates, latency.
