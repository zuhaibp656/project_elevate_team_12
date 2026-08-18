# MVP SOLUTION DESIGN DOCUMENT
## HR Agentic Solution (MVP 1) — Team 12

---

## Document Control

### Document Metadata
| Field | Value |
| :--- | :--- |
| **Document Title** | Enterprise Agentic Solution Design Document — HR Agentic Solution (MVP 1) |
| **Project Name** | Project Elevate — HR Agentic Solution |
| **Team** | Team 12 |
| **Author(s)** | Zuhaib Parvez & Team 12 Architecture Group |
| **Date** | August 18, 2026 |
| **Status** | Approved & Production-Ready |
| **Target Audience** | Enterprise Architecture Review Board, HR Leadership, IT Operations, Lead Engineers |

### Revision History
| Version | Date | Author | Description of Change |
| :--- | :--- | :--- | :--- |
| **0.1** | 2026-08-17 | Team 12 | Initial outline setup & scope alignment |
| **1.0** | 2026-08-18 | Team 12 | Full architecture, ADK multi-agent design, FastMCP live integration, security specifications, FinOps, and UAT framework |
| **1.1** | 2026-08-18 | Team 12 | Comprehensive refinement of architectural design choices (Why & How), multi-tenant Argolis identity resolution, 3-column Web UI workspace, and dual Cloud Run / Gemini Enterprise deployment pipelines |
| **1.2** | 2026-08-18 | Team 12 | **Enterprise Feedback Remediation**: Added Dynamic Policy Ingestion Pipeline (GCS Eventarc trigger, mtime cache invalidation, versioning) and Multi-Tier Peak-Period Transaction Fallback & Human Escalation (HITL) Architecture |

---

## 1. Executive Summary & Scope Boundaries

### 1.1. Business Overview & Context
Enterprise employees routinely navigate fragmented, siloed enterprise systems (Human Capital Management, IT Service Management, and static PDF policy repositories) to resolve routine inquiries and submit standard requests. This fragmentation leads to:
* **High Tier 1 Support Costs**: Over 45% of incoming HR and IT helpdesk tickets are routine, repetitive questions regarding leave balances, policy clauses, profile updates, and standard ticket creation.
* **Operational Delays**: Employees experience average resolution times of 4 to 24 hours for basic administrative tasks that could be handled instantly.
* **Friction & Cognitive Load**: Employees must log into multiple disparate interfaces, manually cross-check policy entitlements against live balances, and manually copy information across systems.

**Strategic Business Objectives:**
* **Deflect Tier 1 HR/IT Inquiries**: Automate and deflect at least **40%** of routine ticket volume within 6 months through conversational self-service.
* **Sub-Second Cross-System Execution**: Deliver end-to-end multi-step actions (e.g., policy check $\rightarrow$ leave booking $\rightarrow$ ticket routing) in a single unified conversational interaction.
* **Zero-Hallucination Governance**: Enforce 100% grounded policy answers with verifiable markdown section citations.
* **Continuous Policy Freshness**: Ensure statutory and internal policy updates are hot-reloaded dynamically with zero application downtime.
* **Peak-Period Resilience & Defined Fallbacks**: Guarantee 100% transaction continuity during peak loads with automated human-in-the-loop (HITL) ticket escalation.

---

### 1.2. Scope Boundaries

| Dimension | In-Scope (MVP 1) | Out-of-Scope (MVP 1 / Post-MVP) |
| :--- | :--- | :--- |
| **Target Systems** | • WorkWeek FastMCP (`/work-week/mcp/`)<br>• ServiceImmediately FastMCP (`/service-immediately/mcp/`)<br>• Singapore HR Policy Knowledge Base (OKF Bundle) | • Payroll execution & compensation alterations<br>• Performance review cycles<br>• External ERPs (SAP SuccessFactors, Oracle Fusion) |
| **Interaction Modalities** | • 3-Column Modern Web UI Workspace (Google Aura)<br>• Google ADK Web View UI (`adk web`)<br>• Interactive Terminal CLI Session (`deploy.sh --cli`) | • Telephony / Voice IVR integration<br>• Third-party chat clients (Slack / MS Teams / WhatsApp) |
| **Language & Locale** | • English (Singapore statutory & Global policy context) | • Multi-lingual localized interfaces |
| **Authentication** | • FastMCP Token Authorization (`X-MCP-Token`)<br>• Google Cloud Application Default Credentials (ADC)<br>• Dynamic session identity resolution (`EMP-380`) | • Enterprise Okta / Entra SAML SSO federated gateway<br>• Cross-organization tenant swapping |

---

## 2. Deep-Dive Architectural & Design Choices: The "Why" and "How"

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                         Core Architectural Design Decisions Matrix                       │
├───────────────────────────────┬──────────────────────────────────────────────────────────┤
│ Architectural Decision        │ Key Technology / Pattern Selected                        │
├───────────────────────────────┼──────────────────────────────────────────────────────────┤
│ Multi-Agent Pattern           │ Hierarchical Hub-and-Spoke Orchestration (Google ADK)    │
│ Foundation Model Engine       │ Gemini 2.5 Flash / Gemini 3.5 Flash                      │
│ Enterprise Integration        │ Model Context Protocol (FastMCP Streamable JSON-RPC)     │
│ Policy Ingestion & Grounding  │ Dynamic Hot-Reloading OKF Engine with Version Tracking   │
│ Peak Resiliency & Fallback    │ Multi-Tier Circuit Breaker & Tier-2 Human Escalation     │
│ User Identity & Tenancy       │ Token-Bound Session Context & Identity Bridge            │
│ Presentation & UX             │ 3-Column Morphing Workspace with Google Neon Aura        │
│ Deployment Strategy           │ Dual-Track: Serverless Cloud Run & Gemini Enterprise     │
└───────────────────────────────┴──────────────────────────────────────────────────────────┘
```

---

### 2.1. Decision 1: Hierarchical Hub-and-Spoke Orchestration vs Monolithic Agent
* **Selected Approach**: Central Multi-Agent Orchestrator (`hr_orchestrator`) delegating to 3 specialized domain sub-agents (`policy_specialist`, `hcm_specialist`, `itsm_specialist`).
* **Why (Rationale)**:
  1. *Prompt Isolation & Context Hygiene*: Monolithic agents loaded with 20+ tool descriptions suffer from tool-selection hallucination and context degradation. Sub-agents keep prompts concise, laser-focused, and bounded to specific domain schemas.
  2. *Strict Governance & Audit Trails*: The orchestrator acts as a single point of enforcement for safety filters, intent validation, and composite multi-system workflows.
  3. *Independent Extensibility*: Adding future sub-agents (e.g., `payroll_specialist`, `procurement_specialist`) requires zero changes to existing sub-agent code.
* **How (Implementation)**:
  Implemented using `google_adk.agents.LlmAgent`. The `hr_orchestrator` holds references to sub-agents in its `sub_agents` array. When a user prompt arrives, the orchestrator determines which specialist to invoke, awaits the specialist's structured response, and synthesizes a polished final output with interactive SaaS deep links.

---

### 2.2. Decision 2: Google Agent Development Kit (ADK) as Core Runtime
* **Selected Approach**: Google Agent Development Kit (`google-adk`).
* **Why (Rationale)**:
  1. *Native Gemini Integration*: First-class support for Gemini 2.5/3.5 function calling protocols and streaming event loops.
  2. *Zero Overhead & Enterprise Portability*: ADK eliminates heavy abstraction layers, providing native deployment commands for Vertex AI Reasoning Engines (`adk deploy agent_engine`) and Cloud Run (`adk deploy cloud_run`).
  3. *Built-in Session & Artifact Services*: Native state management (`InMemorySessionService`, `AgentEngineSessionService`) without requiring external database dependencies for local execution.
* **How (Implementation)**:
  All agents are declared as `LlmAgent` instances. Execution is driven through `Runner.run_async()`, allowing real-time event streaming of thought steps, function calls, and final text responses.

---

### 2.3. Decision 3: Foundation Model Selection (Gemini 2.5 Flash)
* **Selected Approach**: `gemini-2.5-flash` (with configuration support for `gemini-3.5-flash` and `gemini-1.5-pro`).
* **Why (Rationale)**:
  1. *Sub-Second Latency*: Delivers time-to-first-token in under 400ms and complete multi-tool turns in $< 1.5$ seconds.
  2. *Superior Function Calling Accuracy*: Outperforms larger legacy models on multi-step parameter extraction and strict schema compliance.
  3. *Cost Efficiency*: At $\$0.075$ per 1M input tokens, operating costs per deflection are under $\$0.005$, making enterprise-scale rollout economically compelling.
  4. *Large Context Window (1M+ Tokens)*: Easily absorbs complete policy documents and complex JSON-RPC responses without truncation.
* **How (Implementation)**:
  Configured in `agents/config.py` with temperature set to `0.2` for deterministic tool parameter generation and grounded factual synthesis.

---

### 2.4. Decision 4: FastMCP (Model Context Protocol) over Custom REST API Wrappers
* **Selected Approach**: FastMCP Streamable JSON-RPC over HTTP (`POST /work-week/mcp/` and `POST /service-immediately/mcp/`).
* **Why (Rationale)**:
  1. *Standardized Tool Contracts*: FastMCP tools self-describe their parameter schemas via JSON Schema, eliminating brittle custom wrapper code.
  2. *Zero-Friction Google IAP Bypass*: The mock SaaS portals are protected by Google Cloud Identity-Aware Proxy (IAP) for interactive browser users. FastMCP endpoints authenticate directly via the `X-MCP-Token` header, providing reliable programmatic RPC access across different GCP tenants (e.g. `@google.com`, `@altostrat.com`, Argolis).
  3. *Future-Proof Interoperability*: Prepares the enterprise for universal tool sharing across any MCP-compatible agent host.
* **How (Implementation)**:
  Implemented in `tools/workweek_tools.py` and `tools/serviceimmediately_tools.py`. Calls send structured JSON-RPC 2.0 payloads with `X-MCP-Token` and `Accept: application/json, text/event-stream` headers, with automatic fallback resolution for employee IDs.

---

### 2.5. Decision 5: Dynamic Policy Indexing & Continuous Ingestion Lifecycle
* **Selected Approach**: Dynamic Hot-Reloading Knowledge Engine (`tools/policy_tool.py`) with filesystem modification monitoring, automated cache invalidation, and version metadata tracking.
* **Why (Rationale)**:
  * *Prevents Outdated Guidelines*: Static indexes risk serving obsolete policies when HR rules (e.g., maternity leave laws, statutory medical caps) change, leading to incorrect bookings and employee grievances.
  * *Zero-Downtime Hot Reloading*: Updates made to markdown policy files in the cloud storage bucket or local knowledge repository take effect immediately without restarting agent servers.
  * *Temporal & Version Awareness*: Frontmatter metadata (`version`, `effective_date`, `status`) ensures the agent applies the legally correct policy for the employee's requested time frame.
* **How (Implementation)**:
  1. `tools/policy_tool.py` computes directory-wide modification timestamps (`_get_dir_mtime()`). On every policy query, if files have changed, the in-memory cache is automatically invalidated and re-indexed.
  2. A dedicated `refresh_policy_index()` API is exposed for event-driven webhook triggers (e.g., Google Cloud Storage object finalize events via Eventarc).
  3. The `policy_specialist` extracts and outputs the policy version and effective date in every consultation citation.

---

### 2.6. Decision 6: Peak-Period Resiliency & Multi-Tier Fallback Framework (HITL)
* **Selected Approach**: Multi-Tier Graceful Degradation with Automated Tier-2 Human Escalation Ticket Dispatch (`escalate_to_human_hr`).
* **Why (Rationale)**:
  * *High-Traffic Availability*: During peak periods (open enrollment, year-end leave rushes), backend APIs or LLM rate limits may experience transient timeouts or transaction validation conflicts.
  * *Zero User Abandonment*: Instead of failing silently or outputting error stack traces, the system preserves transaction intent and immediately routes the case to human HR specialists.
* **How (Implementation)**:
  * **Tier 1 (Intelligent Retry & Backoff)**: Client tools execute automated retries with exponential backoff and 15s timeout limits.
  * **Tier 2 (Automated Tier-2 HR Ticket Creation)**: If a transaction fails (e.g., leave booking error, policy edge-case), the agent invokes `escalate_to_human_hr()`, automatically opening a Priority "2 - High" support ticket in ServiceImmediately assigned to the "HR Support" group, attaching the user's intent and error details.
  * **Tier 3 (Warm Human Hand-Off)**: The employee receives the live ticket ID (e.g., `INC0002595`) with an explicit confirmation that an HR specialist has received the full conversational context and will follow up directly.

---

### 2.7. Decision 7: Multi-Tenant Identity Resolution & Dynamic Tenancy
* **Selected Approach**: Multi-tier dynamic token resolution with automated employee identity mapping.
* **Why (Rationale)**:
  When deployed across different developer, evaluator, or enterprise Argolis environments, multiple users must be able to test their individual accounts without code modifications.
* **How (Implementation)**:
  1. The tools dynamically resolve `MCP_TOKEN` from session context, request headers, or `.env`.
  2. The agent calls `get_current_employee_id()`, which queries the FastMCP server to resolve the token's bound identity (e.g. `EMP-380`), dynamically tailoring balances and ticket operations to that employee.

---

### 2.8. Decision 8: 3-Column Modern Web UI Workspace (Google Aura Design)
* **Selected Approach**: Custom high-performance Web UI featuring a 3-column workspace layout with Google 4-color neon aura styling, dancing dots, and dynamic container morphing.
* **Why (Rationale)**:
  1. *Progressive Disclosure*: Starts with a clean Google-style search bar, which smoothly morphs into an interactive multi-turn conversation canvas upon the first query.
  2. *Real-Time Telemetry & Ambient Awareness*: The persistent Right Panel ("My Hub") gives users real-time visibility into their live PTO balance meters and recent tickets without needing to prompt the AI.
  3. *Session Continuity*: The Left Panel maintains full multi-session chat history saved locally in `localStorage`, allowing users to resume past consultations instantly.
  4. *Actionable Deep-Linking*: AI responses render SaaS deep links as styled interactive badges opening in new browser tabs with zero context loss.
* **How (Implementation)**:
  Single-page application (`ui/index.html`) driven by a lightweight FastAPI backend (`ui/server.py`). Styled using modern CSS variables, CSS grid/flexbox, Glassmorphism, Google font typography (Outfit & Inter), and Marked.js with custom new-tab link renderers.

---

## 3. Target Architecture & Layered Breakdown

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
│  [ APPLICATION & API LAYER ]               ▼                                            │
│  ┌───────────────────────────────────────────────────────────────────────────────────┐  │
│  │ FastAPI Server Runtime (ui/server.py — Port 8080 / 8090)                          │  │
│  │ • Async Event Loop Orchestrator Bridge (run_query_traced_async)                   │  │
│  │ • Live Hub Data Aggregator & Employee Identity Context Resolver                   │  │
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
│           ▼                        ▼                        ▼                           │
│  ┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐                  │
│  │ OKF Policy Docs │      │ WorkWeek FastMCP│      │ ServiceImmed.   │                  │
│  │ (38 Categories) │      │ (/work-week/mcp)│      │ (/service...mcp)│                  │
│  │ Version-Indexed │      │                 │      │ + Tier-2 Escalat│                  │
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

## 4. Sub-Agent Responsibilities & Flow Walkthroughs

### 4.1. Sub-Agent Roles & Capabilities

| Agent Name | Role Description | Toolset Attached | Key Responsibilities |
| :--- | :--- | :--- | :--- |
| **`hr_orchestrator`** | Central Router & Synthesizer | Sub-agent delegation | • Analyzes user intent & breaks down compound requests.<br>• Coordinates sequential and parallel sub-agent execution.<br>• Synthesizes clear, itemized answers with SaaS deep-links.<br>• Coordinates fallback escalation to human HR upon failure. |
| **`policy_specialist`** | Grounded Policy Analyst | `list_concepts`, `read_concept`, `refresh_policy_index` | • Dynamically explores statutory rules across 38 OKF categories.<br>• Extracts exact eligibility, notice periods, and document rules.<br>• Quotes exact markdown section citations with version/effective date. |
| **`hcm_specialist`** | Core HR & Leave Operator | `get_balances`, `request_time_off`, `get_personal_info`, `update_personal_info`, `get_leave_requests`, `cancel_leave` | • Checks real-time leave balances before booking.<br>• Validates leave requests against available accruals.<br>• Submits approved leave and updates contact records. |
| **`itsm_specialist`** | IT & Support Ticket Operator | `list_tickets`, `get_ticket_details`, `create_ticket`, `add_ticket_comment`, `update_ticket_status`, `escalate_to_human_hr` | • Queries open incident tickets.<br>• Creates new support tickets for hardware, access, and out-of-office routing.<br>• Updates ticket work notes and lifecycle states.<br>• Dispatches Tier-2 HR escalation tickets when transactions fail. |

---

### 4.2. Peak-Period Resilient Fallback & Human Escalation Sequence Flow

The following sequence illustrates the multi-tier fallback when a live transaction encounters an unexpected exception or peak timeout:

```mermaid
sequenceDiagram
    autonumber
    actor Employee as Employee (EMP-380)
    participant UI as Google Aura Web UI
    participant Orch as hr_orchestrator
    participant HCM as hcm_specialist
    participant ITSM as itsm_specialist
    participant SaaS as Mock SaaS FastMCP Backend
    actor HRAdmin as Human HR Specialist (Tier 2)

    Employee->>UI: "Book 3 days vacation starting tomorrow"
    UI->>Orch: POST /api/chat (prompt, mode="auto")
    
    rect rgb(255, 240, 240)
        Note over Orch,HCM: Phase 1: Transaction Execution & Timeout Detection
        Orch->>HCM: "Check balance and book 3 days Vacation leave"
        HCM->>SaaS: tools/call: request_time_off(EMP-380, ...)
        SaaS--xHCM: HTTP 504 Gateway Timeout (Peak Traffic Spike)
        HCM->>HCM: Automated Retry (Exponential Backoff, 2 attempts)
        HCM--xHCM: Retry limit reached
        HCM-->>Orch: Error: "WorkWeek HCM service timeout during peak period."
    end

    rect rgb(255, 250, 230)
        Note over Orch,ITSM: Phase 2: Automated Tier-2 Human Escalation Dispatch
        Orch->>ITSM: "Escalate to Human HR: Leave booking timed out for EMP-380"
        ITSM->>SaaS: tools/call: escalate_to_human_hr(requested_by="EMP-380", reason="WorkWeek booking timeout during peak period", conversation_summary="User requested 3 days vacation starting 2026-08-19")
        SaaS-->>ITSM: {"ticket_id": "INC0002595", "priority": "2 - High", "assignment_group": "HR Support", "status": "New"}
        ITSM-->>Orch: "Tier-2 HR Escalation Ticket INC0002595 created."
    end

    rect rgb(240, 255, 240)
        Note over Orch,UI: Phase 3: Transparent User Confirmation & Hand-off
        Orch->>UI: "I encountered a delay booking your leave directly. To ensure you don't experience delays, I have opened Priority Ticket **INC0002595** with our HR Support team. A human HR specialist has your full request and will confirm your leave shortly."
        UI->>Employee: Display structured escalation card with direct ticket link [INC0002595]
        SaaS->>HRAdmin: Push incident to HR Support dashboard queue with conversation transcript
    end
```

---

## 5. Security, Governance & Identity Guardrails

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              Zero-Trust Security Architecture                           │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│  1. Inbound Request Sanitization                                                        │
│     • Prompt injection pattern matching & delimiter isolation                           │
│     • Sensitive PII/SPII redaction (national IDs, credit card numbers, passwords)       │
│                                                                                         │
│  2. Identity & Token Binding                                                            │
│     • Runtime session bound to authenticated employee ID (EMP-380)                      │
│     • FastMCP requests transmit verified `X-MCP-Token` header                           │
│     • Google Cloud Application Default Credentials (ADC) for IAM authorization          │
│                                                                                         │
│  3. Backend Access Control & Tenant Segregation                                         │
│     • Mock SaaS backend validates that token owner matches target employee record       │
│     • Unauthorized cross-employee data modification returns JSON-RPC Access Denied      │
│                                                                                         │
│  4. Grounding & Hallucination Guardrails                                                │
│     • Temperature fixed at 0.2 for deterministic adherence to retrieved content         │
│     • Policy specialist strictly forbidden from inventing ungrounded rules              │
│     • Execution trace logged for full transparency and compliance auditing              │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Integration Specifications & FastMCP Catalog

### 6.1. WorkWeek HCM Toolset (`/work-week/mcp/`)

| Tool Name | Parameters | Return Type | Functional Description |
| :--- | :--- | :--- | :--- |
| `get_current_employee_id` | *(none)* | `{"employee_id": str}` | Resolves the employee ID associated with the current session token. |
| `get_employee_balances` | `employee_id: str` | `{"vacation_days": float, "sick_days": float}` | Fetches real-time available and used leave balances. |
| `request_time_off` | `employee_id`, `start_date`, `end_date`, `leave_type`, `days` | `{"status": str, "request_id": str, "remaining_days": float}` | Submits a time-off booking in WorkWeek. |
| `get_personal_info` | `employee_id: str` | `{"email": str, "phone": str, "address": str}` | Retrieves current profile contact information. |
| `update_personal_info` | `employee_id`, `address?`, `phone?` | `{"status": str, "updated_fields": dict}` | Updates home address and/or phone number. |
| `get_leave_requests` | `employee_id: str` | `[{"request_id": str, "start_date": str, ...}]` | Lists all historical and pending leave requests. |
| `cancel_leave_request` | `employee_id`, `request_id` | `{"status": str, "restored_days": float}` | Cancels an existing leave request and restores balance. |

---

### 6.2. ServiceImmediately ITSM Toolset (`/service-immediately/mcp/`)

| Tool Name | Parameters | Return Type | Functional Description |
| :--- | :--- | :--- | :--- |
| `list_tickets` | `employee_id: str` | `[{"ticket_id": str, "category": str, "status": str, ...}]` | Retrieves all support incident tickets requested by the employee. |
| `get_ticket_details` | `ticket_id: str` | `{"ticket_id": str, "comments": list, ...}` | Fetches complete ticket details, history, and work notes. |
| `create_ticket` | `requested_by`, `category`, `short_description`, `priority`, `assignment_group` | `{"ticket_id": str, "status": "New"}` | Creates a new support ticket in ServiceImmediately. |
| `add_ticket_comment` | `ticket_id`, `author`, `comment` | `{"status": "Comment added", "timestamp": str}` | Appends a comment or work note to an existing ticket. |
| `update_ticket_status`| `ticket_id`, `status`, `resolution_notes`, `updated_by` | `{"status": str, "ticket_id": str}` | Updates lifecycle status (`In Progress`, `Resolved`, `Closed`). |
| `escalate_to_human_hr`| `requested_by`, `reason`, `conversation_summary` | `{"ticket_id": str, "status": "New", "priority": "2 - High"}` | Automatically generates a high-priority Tier-2 HR escalation ticket when automated resolution fails. |

---

## 7. FinOps & Operational Cost Analysis

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                           FinOps Cost Comparison & ROI Analysis                         │
├──────────────────────────────────────────────────────┬──────────────────────────────────┤
│ Metric                                               │ Value                            │
├──────────────────────────────────────────────────────┼──────────────────────────────────┤
│ Average Input Tokens per Multi-Turn Interaction      │ ~1,850 tokens                    │
│ Average Output Tokens per Multi-Turn Interaction     │ ~420 tokens                      │
│ Gemini 2.5 Flash Input Cost per Million Tokens       │ $0.075                           │
│ Gemini 2.5 Flash Output Cost per Million Tokens      │ $0.300                           │
│ **Total LLM Cost per Resolved Employee Inquiry**     │ **$0.000265 (~0.026 cents)**     │
│ Cloud Run Compute Cost per Turn (2 vCPU, 2GB, 1.2s)  │ ~$0.000048                       │
│ **Total All-Inclusive Cost per Self-Service Query**  │ **<$0.00035 (~0.035 cents)**     │
│ Traditional Tier 1 Human Support Ticket Cost         │ $12.00 – $22.00                  │
│ **Net Cost Reduction per Automated Inquiry**         │ **>99.9%**                       │
│ **Projected Monthly Savings (10,000 Inquiries/Mo)**  │ **~$120,000 / Month**            │
└──────────────────────────────────────────────────────┴──────────────────────────────────┘
```

---

## 8. User Acceptance Testing (UAT) Verification Matrix

| Test ID | Test Scenario | Expected Outcome | Status |
| :--- | :--- | :--- | :--- |
| **UAT-01** | Query Singapore outpatient sick leave entitlement | Returns exactly 14 days outpatient, 60 days hospitalization with citation from `1.1-outpatient-sick...` | **PASSED** |
| **UAT-02** | Live PTO balance check | Fetches exact balances from WorkWeek FastMCP (Vacation: 15.0 days, Sick: 10.0 days) | **PASSED** |
| **UAT-03** | End-to-end sick leave submission | Books 2 days sick leave, verifies reduction to 8.0 days, confirms in WorkWeek | **PASSED** |
| **UAT-04** | Excessive leave validation guardrail | Rejects request of 25 vacation days when only 15.0 days are available | **PASSED** |
| **UAT-05** | View active incident tickets | Fetches live list of tickets for `EMP-380` from ServiceImmediately FastMCP | **PASSED** |
| **UAT-06** | Create support ticket with priority | Generates new ticket (e.g. `INC0002594`) with correct category and assignment group | **PASSED** |
| **UAT-07** | Update ticket lifecycle status | Successfully transitions ticket to `Resolved` with mandatory resolution notes | **PASSED** |
| **UAT-08** | Compound cross-system workflow | Executes policy check $\rightarrow$ leave booking $\rightarrow$ ticket routing in a single turn | **PASSED** |
| **UAT-09** | Out-of-scope query guardrail | Responds with a polite redirect explaining supported HR/IT domains | **PASSED** |
| **UAT-10** | SaaS deep link navigation | All generated links and sidebar shortcuts open in new tabs (`target="_blank"`) | **PASSED** |
| **UAT-11** | Dynamic policy hot-reload verification | Modifying a policy markdown document reflects immediately in agent answers without server restart | **PASSED** |
| **UAT-12** | Peak failure fallback escalation | Automated booking error automatically creates Tier-2 ticket `INC0002595` and provides tracking ID | **PASSED** |

---

## 9. Conclusion & Deployment Verification

The **HR Agentic Solution (MVP 1)** is fully implemented, verified, containerized, and ready for immediate deployment via:
1. **Google Cloud Run (Full-Stack Web App)**: `./deploy_full_gcp.sh` (or `./deploy.sh --gcp`)
2. **Gemini Enterprise (Raw Agent Engine)**: `./deploy_gemini_enterprise.sh` (or `./deploy.sh --ge`)
3. **Local Interactive Session**: `./deploy.sh --ui` (Web) or `./deploy.sh --cli` (Terminal)
