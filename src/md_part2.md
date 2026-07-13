
---

## 2. Azure Service Bus

### 2.1 What It Is

Fully managed enterprise message broker supporting **queues** (point-to-point) and **topics/subscriptions** (publish-subscribe). Decouples producers from consumers, providing load-leveling, ordering, and reliable delivery over **AMQP 1.0**.

### 2.2 Queues vs. Topics

- **Queue:** One logical consumer group; messages pulled by **competing consumers**; each message processed by one receiver. Provides temporal decoupling and load leveling.
- **Topic + subscriptions:** Publisher sends once; each subscription gets an independent copy. Subscriptions support **filters** (SQL filters, correlation filters, boolean filters) and **actions** (modify properties), enabling content-based routing.

### 2.3 Tiers

| Tier | Highlights |
|---|---|
| **Basic** | Queues only, 256 KB messages, no topics |
| **Standard** | Topics, sessions, transactions, dedup; shared capacity; 256 KB messages |
| **Premium** | Dedicated Messaging Units, predictable latency, 100 MB messages (large message support), VNet/private endpoints, availability zones, Geo-DR, CMK encryption, JMS 2.0 |

**Exam signal:** "predictable performance," "private endpoints," "geo-disaster recovery," or ">1 MB messages" → **Premium**.

### 2.4 Key Messaging Features

- **Receive modes:**
  - **Peek-lock (at-least-once):** Message locked (default 60s, renewable); consumer must Complete/Abandon/Dead-letter/Defer. Failure → lock expiry → redelivery.
  - **Receive-and-delete (at-most-once):** Fastest, but message lost if consumer crashes.
- **Dead-letter queue (DLQ):** Automatic sub-queue per entity for poison messages (MaxDeliveryCount exceeded, TTL expired, filter evaluation errors). Path: `queue/$deadletterqueue`.
- **Sessions:** Guarantee **FIFO ordering** and stateful processing for related messages sharing a `SessionId`. Required for strict ordering in Service Bus. Session state can persist workflow progress.
- **Duplicate detection:** Dedupes by `MessageId` within a configurable time window (idempotent enqueue).
- **Scheduled delivery:** Enqueue now, deliver at a future time.
- **Deferral:** Set aside a message to retrieve later by sequence number.
- **Transactions:** Atomically group operations against a single messaging entity (and cross-entity with transfer/send-via).
- **Auto-forwarding:** Chain queues/subscriptions (fan-in patterns, decoupling).
- **Prefetch + batching:** Throughput optimization.
- **Message TTL**, **auto-delete on idle**, **max delivery count**.

### 2.5 Reliability

- **Availability zones:** Automatic in regions that support them (Premium replicates across zones).
- **Geo-Disaster Recovery (Premium):** Namespace-level metadata pairing + alias; **metadata only** — messages are NOT replicated (know this!). Failover promotes secondary.
- **Geo-replication (Premium):** Newer full-data replication feature for supported regions.
- Client-side resilience: retry policies, idempotent handlers, DLQ monitoring.

### 2.6 Choosing the Right Messaging Service (classic exam question)

| Service | Model | Use when |
|---|---|---|
| **Service Bus** | Broker: queues + pub/sub, transactions, ordering, DLQ | Enterprise messaging, commands, financial transactions, ordered workflows |
| **Event Grid** | Reactive **discrete events**, push delivery, serverless | React to state changes ("blob created"), event-driven automation, fan-out to handlers |
| **Event Hubs** | **Event streaming**, partitioned log, millions of events/sec | Telemetry, clickstreams, big-data ingestion, Kafka workloads |
| **Storage Queues** | Simple, cheap, massive queue (>80 GB) | Basic queueing, no ordering/dedup/sessions needed, audit log of all transactions via storage logs |

Rule of thumb: **events** (fact happened, lightweight) → Event Grid/Event Hubs; **messages** (payload with contract, sender expects processing) → Service Bus.

### 2.7 Messaging Patterns

- **Competing consumers:** Multiple workers pull from one queue → horizontal scale + load leveling.
- **Publish-subscribe:** Topic fan-out to independent subscribers.
- **Claim-check:** Store large payload in Blob Storage; send message with reference (avoids size limits).
- **Saga / process manager:** Long-running distributed transactions coordinated via messages with compensating actions.
- **Queue-based load leveling:** Buffer between spiky producers and steady consumers.
- **Sequential convoy:** Sessions to process related message groups in order.
- **Dead-letter handling:** Automated DLQ processor with alerting; never let DLQs grow silently.

### 2.8 Security

- **Entra ID + RBAC (preferred):** `Azure Service Bus Data Owner / Sender / Receiver` roles, scoped to namespace/queue/topic. Use **managed identities** from compute.
- **SAS (legacy/compat):** Namespace or entity-scoped policies (Send/Listen/Manage). Rotate keys; prefer Entra ID.
- **Network:** Private endpoints (Premium), service tags, IP firewall, disable public network access.

---

## 3. Azure RBAC & Governance

### 3.1 RBAC Fundamentals

Azure RBAC = **authorization system** on Azure Resource Manager. An assignment is: **security principal + role definition + scope**.

- **Security principals:** user, group, service principal, managed identity.
- **Scopes (hierarchy):** Management group → Subscription → Resource group → Resource. Assignments **inherit downward**.
- **Role definition:** JSON with `Actions`, `NotActions`, `DataActions`, `NotDataActions`, `AssignableScopes`.
  - `Actions` = control-plane operations (ARM).
  - `DataActions` = data-plane operations (e.g., read blob content, receive Service Bus message).
  - `NotActions` = subtracted from Actions (NOT a deny — just not granted).
- **Deny assignments:** Explicit deny (created by Azure via managed apps/Blueprints/deployment stacks, not directly user-creatable). Deny wins over allow.
- **Effective permissions** = union of all role assignments minus deny assignments.

### 3.2 Key Built-in Roles

| Role | Grants |
|---|---|
| **Owner** | Everything + assign roles |
| **Contributor** | Everything except role assignment / sharing |
| **Reader** | View only |
| **User Access Administrator** | Manage role assignments only |
| **Role Based Access Control Administrator** | Assign roles (more constrained than UAA) |
| Data roles (examples) | Storage Blob Data Reader/Contributor, Key Vault Secrets User, Service Bus Data Sender/Receiver, AcrPull/AcrPush |

**Least privilege:** Prefer narrow built-in data roles over Owner/Contributor; scope as low as possible; assign to **groups**, not users; use **PIM** for eligibility instead of standing access.

### 3.3 Custom Roles & ABAC

- **Custom roles:** When no built-in role fits. Define JSON; `AssignableScopes` limits where it can be assigned. Limit: 5,000 custom roles per tenant.
- **ABAC (attribute-based access control):** Role assignment **conditions** that filter based on resource attributes (e.g., blob tags), request attributes, or principal attributes. Currently focused on Storage data actions. Adds fine-grained control on top of RBAC.

### 3.4 Entra ID Roles vs. Azure RBAC (classic confusion)

- **Entra ID roles** (Global Administrator, User Administrator, Application Administrator) govern the **directory/identity plane**.
- **Azure RBAC roles** govern **Azure resources**.
- They are separate systems. A Global Administrator has NO Azure resource access by default but can **elevate access** (gain User Access Administrator at root `/`) in emergencies.

### 3.5 Managed Identities

- **System-assigned:** Lifecycle tied to the resource; 1:1; deleted with the resource.
- **User-assigned:** Standalone resource; shareable across many resources; survives resource deletion; pre-provision permissions before compute exists (better for fleets and blue-green).
- Use for: Key Vault access, Service Bus send/receive, ACR pulls, SQL auth, APIM→backend auth, ACA→anything. **No secrets to manage or rotate.**

### 3.6 Privileged Identity Management (PIM)

- **Just-in-time** role activation with approval workflows, MFA, justification, time-bounded assignments, access reviews, and audit history.
- Applies to both Entra ID roles and Azure RBAC roles.
- Exam signal: "reduce standing privileged access," "time-limited access with approval" → PIM.

### 3.7 Governance Toolbox (AZ-305 core)

| Tool | Purpose |
|---|---|
| **Management groups** | Hierarchy above subscriptions for policy/RBAC inheritance |
| **Azure Policy** | Enforce/audit resource compliance (deny, audit, append, modify, deployIfNotExists); initiatives = policy sets |
| **RBAC** | Who can do what |
| **Resource locks** | CanNotDelete / ReadOnly, protect critical resources |
| **Tags** | Metadata for cost/ownership/environment; enforce via Policy |
| **Microsoft Defender for Cloud** | CSPM: secure score, regulatory compliance, workload protection |
| **Azure landing zones (CAF)** | Prescriptive MG hierarchy, platform/workload subscriptions, policy-driven guardrails |
| **Deployment stacks** | Manage resource collections as a unit with deny settings (successor to Blueprints, which are deprecated) |

**RBAC vs. Policy:** RBAC controls *who* can act; Policy controls *what/how* resources may be configured regardless of who. They complement, not overlap.
