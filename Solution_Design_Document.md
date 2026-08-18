# SOLUTION DESIGN DOCUMENT
## HR Agentic Solution (MVP 1) — Team 12

---

## Document Control

| Field | Value |
| :--- | :--- |
| **Document Title** | Enterprise Solution Design Document — HR Agentic Solution (MVP 1) |
| **Project Name** | Project Elevate — HR Agentic Solution |
| **Team** | Team 12 |
| **Author(s)** | Zuhaib Parvez & Team 12 Architecture Group |
| **Date** | August 18, 2026 |
| **Status** | Approved & Production-Ready |
| **Target Audience** | Enterprise Architecture Review Board, HR Leadership, IT Operations, Lead Engineers |

### Revision History
| Version | Date | Description |
| :--- | :--- | :--- |
| **1.0** | 2026-08-18 | Initial Complete Architecture, ADK Multi-Agent, FastMCP Integration, Security & UAT |
| **1.1** | 2026-08-18 | Added Architectural Design Choices (Why & How), Argolis Identity Bridge & 3-Column UI |
| **1.2** | 2026-08-18 | Added Dynamic Policy Ingestion Pipeline, Peak Resiliency & Tier-2 Human Escalation (HITL) |
| **1.3** | 2026-08-18 | **Streamlined Executive Edition**: Added Tiered Rate Limiting, Schema Drift Plan, Distributed Tracing, Verification Loops, and Phased Roadmap |

---

## 1. Executive Summary & Scope

### 1.1. Business Problem & Objectives
Enterprise employees lose hours navigating disconnected systems (HCM, ITSM, static PDF portals) for basic HR tasks. Over 45% of HR/IT tickets are repetitive inquiries regarding leave balances, policy clauses, and standard IT requests.

**Core Objectives:**
* **Deflect >40% of Tier 1 Inquiries**: Enable instant, conversational self-service across HR Policies, WorkWeek (HCM), and ServiceImmediately (ITSM).
* **Sub-Second Execution**: Complete cross-system multi-step workflows (Policy $\rightarrow$ Leave $\rightarrow$ Ticket) in $<1.5$ seconds.
* **100% Grounded Answers**: Zero hallucinated rules; all policy answers include verifiable markdown citations.
* **Continuous Policy Freshness**: Dynamic hot-reloading reflects statutory updates in $<60$ seconds with pre-merge verification.
* **Peak-Period Resiliency**: Multi-tier fallback automatically creates tracked human HR escalation tickets when transactions encounter timeouts.

---

### 1.2. Scope Boundaries

| Dimension | In-Scope (MVP 1) | Target State (Phase 2 / 3) |
| :--- | :--- | :--- |
| **Target Systems** | • WorkWeek FastMCP (`/work-week/mcp/`)<br>• ServiceImmediately FastMCP (`/service-immediately/mcp/`)<br>• Dynamic Singapore HR Policy Knowledge Base (38 Categories) | • Production Workday HCM Gateway<br>• Production ServiceNow ITSM API<br>• Vertex AI Search Enterprise RAG |
| **User Interfaces** | • 3-Column Modern Web Workspace (Google Aura)<br>• Google ADK Web View (`adk web`)<br>• Terminal CLI Session (`deploy.sh --cli`) | • Native Slack & Microsoft Teams Bots<br>• Intranet Embedded Chat Widget |
| **Identity & Security** | • FastMCP Token Authorization (`X-MCP-Token`)<br>• Google Cloud ADC IAM Authorization<br>• Dynamic session identity mapping (`EMP-380`) | • Enterprise Okta / Entra ID SSO (OIDC/SAML)<br>• RFC 8693 Token Exchange (OBO)<br>• RFC 7009 Real-time Revocation Blacklist |

---

## 2. Core Architectural Design Choices: The "Why" & "How"

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                         Core Architectural Design Decisions Matrix                       │
├───────────────────────────────┬──────────────────────────────────────────────────────────┤
│ Architectural Decision        │ Key Technology / Pattern Selected                        │
├───────────────────────────────┼──────────────────────────────────────────────────────────┤
│ Multi-Agent Pattern           │ Hierarchical Hub-and-Spoke Orchestration (Google ADK)    │
│ Foundation Model Engine       │ Gemini 2.5 Flash (Temp: 0.2, Top-P: 0.95)                │
│ Enterprise Integration        │ Model Context Protocol (FastMCP Streamable JSON-RPC)     │
│ Policy Ingestion & Grounding  │ Dynamic Hot-Reloading OKF Engine with Atomic Swap        │
│ Peak Resiliency & Fallback    │ Multi-Tier Circuit Breaker & Tier-2 Human Escalation     │
│ API Throttling & Governance   │ Tiered Token-Bucket Rate Limiter with 429 Retry-After    │
│ Schema Drift Management       │ Dynamic Schema Introspection & Automated Contract CI/CD  │
│ Observability & Tracing       │ W3C Trace Context (traceparent) & GCP Correlation IDs    │
│ User Identity & Tenancy       │ Token-Bound Session Context & Identity Bridge            │
│ Presentation & UX             │ 3-Column Morphing Workspace with Google Neon Aura        │
│ Deployment Strategy           │ Dual-Track: Serverless Cloud Run & Gemini Enterprise     │
└───────────────────────────────┴──────────────────────────────────────────────────────────┘
```

### 2.1. Agent Pattern: Hub-and-Spoke Orchestration (`google-adk`)
* **Why**: Prevents context pollution and tool-selection hallucinations by keeping specialized domain tools isolated inside dedicated sub-agents.
* **How**: The root `hr_orchestrator` evaluates intent, coordinates execution across `policy_specialist`, `hcm_specialist`, and `itsm_specialist`, and synthesizes unified responses with deep links.

### 2.2. Model Engine: Gemini 2.5 Flash
* **Why**: Sub-second latency ($<400\text{ms}$ TTFT), superior function calling accuracy, massive context window (1M+ tokens), and unbeatable cost ($<\$0.00035$ per inquiry).
* **How**: Configured across all agents with temperature `0.2` for deterministic schema compliance and factual grounding.

### 2.3. Enterprise Protocol: FastMCP (Model Context Protocol)
* **Why**: Standardizes self-describing tool schemas via JSON-RPC 2.0 and seamlessly bypasses Google Cloud IAP browser popups using programmatic `X-MCP-Token` headers.
* **How**: Python tool clients (`tools/workweek_tools.py` & `tools/serviceimmediately_tools.py`) communicate via HTTP POST to `/work-week/mcp/` and `/service-immediately/mcp/`.

### 2.4. Policy Engine: Dynamic Hot-Reloading Open Knowledge Format (OKF)
* **Why**: Delivers 100% deterministic grounding, zero vector DB hosting fees, and instant updates without service restarts.
* **How**: Monitors directory `mtime` and handles GCS Eventarc webhooks via `refresh_policy_index()`. Uses an **Atomic Double-Buffered Cache (`RWMutex`)** to eliminate stale answers and dropped requests during updates.

### 2.5. Peak Resiliency & Human Escalation (HITL)
* **Why**: Prevents user drop-off during peak traffic timeouts or API errors.
* **How**: If automated retries fail, `escalate_to_human_hr()` automatically opens a Priority "2 - High" support ticket in ServiceImmediately assigned to "HR Support", passing the full conversational transcript and starting a **2-Hour HR Response SLA Timer**.

### 2.6. API Throttling & Downstream Schema Drift Management
* **Why**: Protects downstream SaaS endpoints from cascading failures and shields the agent from breaking API updates.
* **How**:
  * **Rate Limiting**: WorkWeek capped at $60\text{ r/m}$ (read) / $30\text{ r/m}$ (write); ServiceImmediately capped at $120\text{ r/m}$ (read) / $30\text{ r/m}$ (write); Escalations receive $10\text{ r/m}$ priority burst. Circuit breaker trips after 5 failures (30s cooldown).
  * **Schema Drift**: FastMCP `tools/list` introspection auto-absorbs optional fields; breaking changes trigger automated CI alerts and route affected actions to human escalation.

---

## 3. Target Solution Architecture & Flow

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                               Target Solution Architecture                              │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│  [ PRESENTATION LAYER ]                                                                 │
│  ┌───────────────────────────────────────────────────────────────────────────────────┐  │
│  │ Google Aura 3-Column Web UI Workspace (HTML5 / CSS3 / Vanilla JS)                 │  │
│  │ • Left Sidebar: Persistent Chat History & Session Manager (localStorage)          │  │
│  │ • Center Canvas: Google Neon Aura Search Card + Morphing Multi-Turn Chat Stream   │  │
│  │ • Right Sidebar: "My Hub" Live PTO Balances & Incident Tickets Telemetry Feed     │  │
│  └─────────────────────────────────────────┬─────────────────────────────────────────┘  │
│                                            │ REST / SSE Stream (/api/chat, /api/hub)    │
│  [ APPLICATION & API GATEWAY LAYER ]       ▼                                            │
│  ┌───────────────────────────────────────────────────────────────────────────────────┐  │
│  │ FastAPI Server Runtime (ui/server.py — Port 8080 / 8090)                          │  │
│  │ • Async Event Loop Orchestrator Bridge (run_query_traced_async)                   │  │
│  │ • W3C Trace Context (traceparent) & Correlation ID (X-Correlation-ID) Injector    │  │
│  │ • Client-Side Token Bucket Rate Limiter & Circuit Breaker Manager                 │  │
│  └─────────────────────────────────────────┬─────────────────────────────────────────┘  │
│                                            │                                            │
│  [ MULTI-AGENT ORCHESTRATION LAYER ]       ▼                                            │
│  ┌───────────────────────────────────────────────────────────────────────────────────┐  │
│  │ Google Agent Development Kit (ADK) — hr_orchestrator                              │  │
│  │ Foundation Model: Gemini 2.5 Flash (Temp: 0.2, Top-P: 0.95)                       │  │
│  │                                                                                   │  │
│  │        ┌────────────────────────┼────────────────────────┐                        │  │
│  │        ▼                        ▼                        ▼                        │  │
│  │  ┌───────────┐            ┌───────────┐            ┌───────────┐                  │  │
│  │  │  Policy   │            │ WorkWeek  │            │  Service  │                  │  │
│  │  │Specialist │            │HCM Expert │            │Immediately│                  │  │
│  │  └─────┬─────┘            └─────┬─────┘            └─────┬─────┘                  │  │
│  └────────┼────────────────────────┼────────────────────────┼────────────────────────┘  │
│           │                        │                        │                           │
│  [ INTEGRATION LAYER ]             │ Streamable JSON-RPC    │ Streamable JSON-RPC       │
│           │ Dynamic Hot-Reload     │ (X-MCP-Token Header)   │ (X-MCP-Token Header)      │
│           │ (mtime Invalidation)   │ (429 Backoff & Breaker)│ (Tiered Quotas & Breaker) │
│           ▼                        ▼                        ▼                           │
│  ┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐                  │
│  │ OKF Policy Docs │      │ WorkWeek FastMCP│      │ ServiceImmed.   │                  │
│  │ (38 Categories) │      │ (/work-week/mcp)│      │ (/service...mcp)│                  │
│  │ Version-Indexed │      │ 60 req/min Cap  │      │ + Tier-2 Escalat│                  │
│  └─────────────────┘      └────────┬────────┘      └────────┬────────┘                  │
│                                    │                        │                           │
│  [ ENTERPRISE SAAS LAYER ]         ▼                        ▼                           │
│  ┌───────────────────────────────────────────────────────────────────────────────────┐  │
│  │ Mock SaaS Enterprise Portal (https://mock-saas.aishprabhat.demo.altostrat.com)    │  │
│  │ • WorkWeek HCM: Employee Records, Vacation/Sick Accruals, Leave Approvals         │  │
│  │ • ServiceImmediately ITSM: Incident Lifecycle, Activity Comments, Tier-2 Queues  │  │
│  └───────────────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Sub-Agent Responsibilities & Orchestrated Workflow

| Sub-Agent | Primary Role | Core Tools | Output Standards |
| :--- | :--- | :--- | :--- |
| **`hr_orchestrator`** | Central Router & Synthesizer | Sub-agent delegation | Structured answers, multi-system coordination, direct tool deep-links, fallback coordination. |
| **`policy_specialist`** | Grounded Policy Analyst | `list_concepts`, `read_concept`, `refresh_policy_index` | 100% grounded citations (`policy://...`), version & effective date reporting, zero hallucinations. |
| **`hcm_specialist`** | WorkWeek Core HR Operator | `get_balances`, `request_time_off`, `get_personal_info`, `update_personal_info`, `cancel_leave` | Real-time balance verification, leave validation, profile updates, `[🔗 Open in WorkWeek]` links. |
| **`itsm_specialist`** | Service Desk Operator | `list_tickets`, `get_ticket_details`, `create_ticket`, `update_ticket_status`, `escalate_to_human_hr` | Complete ticket profiles (ID, Category, Priority, Status), state machine enforcement, Tier-2 escalation. |

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                     Cross-System Orchestration Flow Example                             │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│ User Request: "I need 2 days sick leave starting tomorrow and need my emails rerouted." │
│                                                                                         │
│ 1. hr_orchestrator routes intent to policy_specialist (Validates Singapore 14d policy).  │
│ 2. hr_orchestrator routes to hcm_specialist (Checks balance & books 2 days in WorkWeek). │
│ 3. hr_orchestrator routes to itsm_specialist (Creates ServiceImmediately routing ticket)│
│ 4. hr_orchestrator synthesizes consolidated summary with live confirmation deep-links.  │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Security, Governance, Data Lifecycle & Tracing

### 5.1. Security & Identity Architecture
* **Token Isolation**: Sessions are dynamically bound to authenticated employee IDs (`EMP-380`). FastMCP requests pass authorized `X-MCP-Token` headers.
* **Secrets Vaulting**: API keys and tokens stored in **Google Cloud Secret Manager** encrypted at rest via **Cloud KMS (CMEK)** with 90-day rotation.
* **Token Revocation (Target State)**: RFC 8693 Token Exchange with real-time RFC 7009 revocation sync via Redis blacklist.
* **Data Sanitization**: Regex filters automatically scrub sensitive SPII (NRIC, credit cards, credentials) prior to logging.

### 5.2. Distributed Tracing & Error Queuing
* **Distributed Tracing**: W3C `traceparent` and `X-Correlation-ID` flow across UI $\rightarrow$ Gateway $\rightarrow$ Orchestrator $\rightarrow$ Sub-Agents $\rightarrow$ FastMCP $\rightarrow$ Cloud Trace.
* **5xx Resiliency & DLQ**: In-process exponential retries (2 attempts) $\rightarrow$ Cloud Tasks / Pub/Sub queue buffer (5 attempts) $\rightarrow$ Dead Letter Queue with automated Tier-2 HR ticket dispatch.

### 5.3. Data Retention Policy (PDPA & GDPR Aligned)
* **Chat Transcripts (Cloud SQL)**: 90 Days hot retention, 1 Year cold archive, then purged.
* **Tool Execution Logs**: 30 Days hot retention, 7 Years encrypted cold archive for compliance audits.
* **SPII / Sensitive PII**: 0 Days (Scrubbed in-flight; never stored).

---

## 6. Implementation Roadmap, FinOps & UAT Matrix

### 6.1. 4-Phase Delivery Roadmap

```
2026 Q3                   2026 Q4                   2027 Q1                   2027 Q2
[ Phase 0: Foundation ]──►[ Phase 1: MVP Pilot ]───►[ Phase 2: Enterprise ]──►[ Phase 3: Scale ]
  • ADK Core Architecture   • Singapore Scope (38 OKF)• Workday Production      • Global Multi-region
  • FastMCP Integration     • Google Aura 3-Col UI    • ServiceNow Live         • 12+ Languages
  • Cloud Run & GE Deployers• HITL Fallback Active    • Okta SSO / OBO Sync     • Voice / Slack Bots
```

### 6.2. FinOps & Operational Cost Analysis
* **LLM Cost per Inquiry**: $\sim 1,850\text{ in} + 420\text{ out tokens} = \mathbf{\$0.000265\ (\sim 0.026\text{ cents})}$.
* **All-Inclusive Cost per Self-Service Query**: $\mathbf{<\$0.00035\ (\sim 0.035\text{ cents})}$ (including Cloud Run compute).
* **ROI Impact**: **$>99.9\%$ cost reduction** compared to traditional human Tier 1 tickets ($\$15.00$).

### 6.3. Key UAT Verification Matrix (14/14 Scenarios Passed)
* **UAT-01 to 04 (Policy & HCM)**: Singapore sick leave citations, live PTO balance retrieval, 2-day leave booking, and excessive leave rejection guardrail.
* **UAT-05 to 07 (ITSM)**: Active ticket querying, ticket creation with priority, and status lifecycle transitions with mandatory resolution notes.
* **UAT-08 to 10 (Orchestration & UX)**: Compound cross-system workflows, out-of-scope redirection, and new-tab deep link navigation (`target="_blank"`).
* **UAT-11 to 14 (Resiliency & Governance)**: Dynamic policy hot-reload verification, peak failure fallback escalation (`INC0002595`), HTTP 429 `Retry-After` backoff, and schema drift absorption.

---

## 7. Conclusion & 1-Click Deployment

The **HR Agentic Solution (MVP 1)** is fully implemented, tested, containerized, and deployable via:
1. **Google Cloud Run (Full-Stack Web App)**: `./deploy_full_gcp.sh` (or `./deploy.sh --gcp`)
2. **Gemini Enterprise (Raw Agent Engine)**: `./deploy_gemini_enterprise.sh` (or `./deploy.sh --ge`)
3. **Local Interactive Session**: `./deploy.sh --ui` (Web) or `./deploy.sh --cli` (Terminal)
