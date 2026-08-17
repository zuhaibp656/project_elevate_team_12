# HR Agentic Solution (MVP 1) — Implementation Plan & Architecture

## 1. Executive Summary & Goal Description
Based on the **HR Agentic Solution (MVP 1) BRD**, this solution is an enterprise, AI-driven virtual assistant designed to provide employees with instantaneous, conversational access to HR services and cross-system orchestration.

### Core Objectives:
1. **Deflect Tier 1 HR/IT Inquiries**: Automate policy-related inquiries strictly grounded in verified policy documentation.
2. **Employee Self-Service Transactions (WorkWeek HCM)**: Real-time profile lookup, contact information updates, and leave balance checks/submissions.
3. **IT Incident Management (ServiceImmediately ITSM)**: Ticket creation, comment appending, status tracking, and transition validation.
4. **Cross-System Orchestration**: Chain multi-step actions across Policies, HCM, and ITSM (e.g. equipment procurement, medical leave coordination, employee relocation).

---

## 2. System Architecture

![System Architecture](images/system_architecture.jpg)

### Architecture Highlights:
- **Visually Aesthetic UI Wrapper**: Decoupled, responsive web chat interface with animated states and bright modern gradients.
- **Google ADK Multi-Agent Orchestration**:
  - **Main Orchestrator Agent (`hr_orchestrator`)**: Performs intent detection, multi-turn state management, safety guardrails, and cross-system delegation.
  - **HR Policy Specialist Agent (`policy_agent`)**: Dedicated RAG-powered agent grounded strictly in HR policy documents with citation metadata.
  - **WorkWeek HCM Specialist Agent (`hcm_agent`)**: Dedicated agent managing profile and leave operations with balance validation and chronological guardrails.
  - **ServiceImmediately ITSM Specialist Agent (`itsm_agent`)**: Dedicated agent handling support tickets, status lifecycles, and priority verification.
- **Model Context Protocol (MCP) Integration Layer**: Standardized tool interface bridging ADK agents with enterprise backends.
- **Enterprise Backend Systems**: WorkWeek HCM, ServiceImmediately ITSM, and HR Policy Knowledge Base.

---

## 3. End-to-End Flow Diagram (Cross-System Use Case)

![Multi-Agent AI System Flow](images/flow_diagram.jpg)

### Flow Breakdown (Medical Leave Example):
1. **Step 1 (User Request)**: Employee requests medical leave starting next Monday via the Chat UI.
2. **Step 2 (Policy Verification)**: Orchestrator delegates to `policy_agent` to quote medical leave entitlements (e.g., 10 days) and identify prerequisites (manager email delegation).
3. **Step 3 (Leave Submission)**: Orchestrator delegates to `hcm_agent` to query accrued balance and submit the leave request in WorkWeek.
4. **Step 4 (IT Ticket Creation)**: Orchestrator delegates to `itsm_agent` to open an incident ticket in ServiceImmediately for IT to route incoming emails to the manager.
5. **Step 5 (Consolidated Response)**: Orchestrator synthesizes output from all sub-agents into a single, cohesive, friendly response back to the user.

---

## 4. Key Functional & Non-Functional Guardrails

| Domain | Requirement | Guardrail Enforcement |
| :--- | :--- | :--- |
| **Policy Retrieval** | Strict Grounding & Containment | Rejects out-of-domain prompts; guarantees 0% policy hallucination with exact citations. |
| **WorkWeek HCM** | Leave & Balance Constraints | Validates requested days <= remaining balance; enforces chronological validity ($Start \le End$). |
| **ServiceImmediately** | Lifecycle Transitions | Blocks invalid transitions (e.g. directly `New` to `Closed`); mitigates duplicate submissions. |
| **Security & Privacy** | AI Safety & SPII Redaction | Detects and blocks prompt injection/jailbreak attempts; masks sensitive personal data in logs. |
