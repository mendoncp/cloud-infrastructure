
---

## 4. Cloud Networking

### 4.1 Virtual Networks

- **VNet:** Isolated private network in a region; address space in CIDR; divided into **subnets**.
- **NSG (Network Security Group):** Stateful L3/L4 allow/deny rules on subnets and/or NICs; processed by priority (100–4096); default rules allow VNet + LB inbound, deny other inbound. Use **service tags** (`AzureCloud`, `Storage`, `Internet`) and **ASGs** (application security groups — group VMs logically so rules reference workloads, not IPs).
- **UDR (route tables):** Override system routing, e.g., 0.0.0.0/0 → Azure Firewall (forced tunneling through an NVA).
- **Peering:** Connect VNets (same or cross-region, cross-subscription). Non-transitive — hub-spoke needs the hub firewall/gateway to route spoke-to-spoke.

### 4.2 Hybrid Connectivity

| Option | Traits |
|---|---|
| **VPN Gateway (S2S)** | IPsec over internet, up to ~10 Gbps aggregate, cheaper, quick to set up |
| **ExpressRoute** | Private dedicated circuit via provider, up to 100 Gbps, SLA, predictable latency; use **ER + VPN failover** for resilience |
| **P2S VPN** | Individual clients (certs, Entra auth) |
| **Virtual WAN** | Microsoft-managed global hub-spoke fabric: branch (SD-WAN/VPN), ER, P2S, hub firewalls, any-to-any routing at scale |

### 4.3 Hub-Spoke Topology (default enterprise answer)

- **Hub:** shared services — Azure Firewall/NVA, VPN/ER gateways, Bastion, DNS.
- **Spokes:** workloads, peered to hub. Spoke↔spoke via hub routing.
- Benefits: centralized security/egress control, cost sharing, isolation. Scales into **Azure landing zones**; at large scale consider **Virtual WAN**.

### 4.4 Private Connectivity to PaaS

- **Private endpoint (Private Link):** NIC with private IP in your subnet mapped to a *specific instance* of a PaaS resource (storage account, SQL, Key Vault, Service Bus Premium, APIM…). Traffic never leaves the Microsoft backbone; works cross-region and from on-prem; enables disabling all public access. Requires **private DNS zones** (e.g., `privatelink.blob.core.windows.net`) so FQDNs resolve to private IPs.
- **Service endpoint:** Subnet identity extended to a PaaS *service* (not instance); traffic stays on backbone but the service keeps a public IP; no on-prem reach. Simpler/cheaper, weaker isolation.
- **Exam rule:** "eliminate public exposure / on-prem access to PaaS / data-exfiltration control" → **Private endpoints + private DNS**.

### 4.5 Load Balancing & Global Delivery (decision tree)

| Service | Layer | Scope | Use |
|---|---|---|---|
| **Azure Load Balancer** | L4 | Regional | TCP/UDP, VM/VMSS backends, HA ports |
| **Application Gateway** | L7 | Regional | HTTP(S), TLS termination, path/host routing, **WAF**, AKS ingress (AGIC) |
| **Azure Front Door** | L7 | **Global** | Anycast edge, CDN, TLS offload, WAF, path routing, multi-region failover for HTTP apps |
| **Traffic Manager** | DNS | Global | DNS-based routing (priority/weighted/performance/geographic), any protocol |

Combos: **Front Door → App Gateway** (global edge + regional WAF/ingress), **Front Door → internal APIM → backends**. Non-HTTP global → Traffic Manager (or Front Door TCP proxying where applicable).

### 4.6 Security Services

- **Azure Firewall:** Stateful managed firewall: L3–L7 rules, FQDN filtering, TLS inspection/IDPS (Premium SKU), threat intelligence. Central egress control in hub.
- **WAF (on App GW/Front Door):** OWASP core rule set, bot protection, custom rules.
- **DDoS Network/IP Protection:** Enhanced mitigation + cost protection on VNet public IPs.
- **Azure Bastion:** Browser-based RDP/SSH without public IPs on VMs.
- **NAT Gateway:** Predictable outbound SNAT at scale, avoids port exhaustion.

### 4.7 DNS

- **Azure DNS:** Public zones.
- **Private DNS zones:** Name resolution inside VNets (+ auto-registration of VM records; link zones to VNets).
- **Azure DNS Private Resolver:** Managed inbound/outbound endpoints for hybrid DNS (replace DNS-forwarder VMs; conditional forwarding on-prem ↔ Azure).

---

## 5. Azure Container Apps (ACA)

### 5.1 What It Is

Serverless container platform built on **AKS + KEDA + Dapr + Envoy** (abstracted away). You bring containers; Azure runs, scales (including **to zero**), and upgrades the infrastructure. No K8s API access — that's the tradeoff vs. AKS.

### 5.2 Compute Selection (AZ-305 favorite)

| Service | Choose when |
|---|---|
| **Container Apps** | Microservices, event-driven jobs, APIs; want K8s-grade capabilities (scale, revisions, service discovery, Dapr) without managing K8s |
| **AKS** | Full Kubernetes API control, custom operators/CRDs, service mesh choice, complex stateful workloads |
| **App Service** | Web apps: PaaS with slots, easy custom domains, mostly HTTP |
| **ACI** | Single containers, burst/batch, simple isolated jobs, virtual nodes for AKS burst |
| **Functions** | Event-driven code with bindings, per-execution model |

### 5.3 Core Concepts

- **Environment:** Isolation + shared VNet and Log Analytics boundary for a set of container apps. Internal (VNet-only ingress) or external. **Workload profiles:** Consumption (serverless) + Dedicated (fixed vCPU/memory, GPU) in one environment.
- **Revisions:** Immutable snapshots of app config+image. **Traffic splitting** across revisions → blue-green and canary deployments. Single vs. multiple revision mode.
- **Ingress:** Managed HTTPS ingress (Envoy), automatic TLS, session affinity, IP restrictions, custom domains, TCP ingress support. Internal-only option for private microservices.
- **Scaling:** KEDA-based scale rules — HTTP concurrency, CPU/memory, or **event-driven scalers** (Service Bus queue length, Event Hubs, Kafka, cron…). Min replicas 0 (scale to zero) → cost-efficient; set min ≥1 to avoid cold starts.
- **Jobs:** Run-to-completion workloads — manual, scheduled (cron), or event-driven (KEDA-triggered) — alongside always-on apps.
- **Dapr integration:** Service invocation (mTLS, retries), state stores, pub/sub (e.g., Service Bus behind Dapr), bindings, observability — enabled per app.
- **Secrets & identity:** App-level secrets, Key Vault references via **managed identity**; system- or user-assigned MI for ACR pulls (no passwords) and Azure resource access.
- **Networking:** Bring your own VNet (infrastructure subnet), internal environments behind private DNS; egress control via UDR + Azure Firewall (workload profiles environments).

### 5.4 Typical Enterprise Pattern

Front Door (WAF) → APIM (internal) → **Container Apps environment (internal ingress)** running APIs → managed identities → Service Bus / SQL / Key Vault via private endpoints, Dapr pub/sub for async, ACR with private endpoint for images, GitHub Actions/Azure DevOps deploying by revision with canary traffic split.
