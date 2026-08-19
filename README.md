# 🤖 HR Agentic Solution (Team 12) — Enterprise Virtual Assistant

An enterprise-grade, multi-agent virtual assistant designed to provide employees with instantaneous, conversational self-service. Built on **Google ADK (Agent Development Kit)** with Gemini models following the **[BMAD Method (Breakthrough Method for Agile AI-Driven Development)](BMAD_METHODOLOGY.md)**, this solution orchestrates workflows across **WorkWeek (HCM)**, **ServiceImmediately (ITSM)**, and company **HR Policy Knowledge Bases** using the **Model Context Protocol (FastMCP)**.

[![BMAD Method](https://img.shields.io/badge/Methodology-BMAD_Method-blueviolet)](https://github.com/bmad-code-org/BMAD-METHOD)
[![ADK Powered](https://img.shields.io/badge/Framework-Google_ADK-4285F4)](https://github.com/google/adk)
[![Model](https://img.shields.io/badge/Model-Gemini_2.5_Flash-FF6F00)](https://ai.google.dev/)
[![Cloud Run](https://img.shields.io/badge/Deploy-Google_Cloud_Run-34A853)](https://cloud.google.com/run)
[![Evaluation Suite](https://img.shields.io/badge/Evals-100%25_Pass_(33%2F33)-1A73E8)](tests/eval/evaluation_report.md)

---

## 🏛️ System Architecture

![System Architecture](images/system_architecture.jpg)

### Architecture Highlights:
- **Centralized Orchestrator (`hr_orchestrator`)**: Performs intent detection, contextual synthesis, multi-turn state management, safety guardrails, and cross-system task delegation.
- **HR Policy Specialist (`policy_specialist`)**: RAG-powered agent strictly grounded in company policy documents with deep-link source citations (`policy://...`).
- **WorkWeek HCM Specialist (`hcm_specialist`)**: Manages employee profiles, contact updates, leave balance inquiries, and direct time-off bookings.
- **ServiceImmediately ITSM Specialist (`itsm_specialist`)**: Manages support tickets, activity comment logs, and lifecycle state machines (`New` $\rightarrow$ `In Progress` $\rightarrow$ `Resolved` $\rightarrow$ `Closed`).
- **FastMCP Integration & Resilient Fallback Layer**: Connects statelessly over Streamable HTTP using custom `X-MCP-Token` headers for Google Frontend (GFE) compliance with zero-lockout local state fallback on sandbox token rotations.

---

## 🔄 End-to-End Cross-System Flow

![Multi-Agent AI Flow](images/flow_diagram.jpg)

### Contextual Decision Flow (Notice & Policy Enforcement):
1. **User Prompt**: *"I want 7 days leave from tomorrow"*
2. **Step 1 (Policy Verification)**: `hr_orchestrator` consults `policy_specialist` to inspect statutory rules and notice requirements.
3. **Step 2 (Constraint Identification)**: Flags that Paid Vacation Leave (Section 1.2) strictly requires **15 days advance notice** with manager approval, and 7 consecutive sick days require a Medical Certificate (MC) and hospitalization certification (Section 1.1).
4. **Step 3 (Direct & Intelligent Guidance)**: States the 15-day notice constraint directly up-front in the first sentence without regurgitating irrelevant policy tiers, and offers actionable alternatives (e.g. valid planned dates 15 days out or urgent medical leave options).
5. **Step 4 (Execution)**: When compliant, coordinates balance verification and booking directly via `hcm_specialist` and opens IT tickets via `itsm_specialist`.

---

## 📊 Interactive Evaluation Suite (33 Test Cases)

The application includes an empirical benchmark suite covering 4 stratified tiers, multi-turn trajectories, and adversarial security guardrails aligned with the `agent-eval-guide`:

- **🟢 Tier 1: Happy Path (10 Cases)**: Statutory sick/maternity leaves, vacation accruals, WorkWeek balance checks, ticket creation.
- **🟡 Tier 2: MAS Multi-Hop & Gotchas (6 Cases)**: Cross-agent medical delegation, equipment procurement, unpaid leave preconditions, ethics overrides.
- **🔴 Tier 3: Hallucination Baits (3 Cases)**: Zero-hallucination abstention against fictitious perks (pet helicopters, crypto meals, yacht charters).
- **🟣 Tier 4: Boundary & Safety Probes (3 Cases)**: Out-of-scope domain refusals (code generation, elections, stock tips).
- **💬 Multi-Turn Trajectories (3 Flows)**: Context retention across multi-turn sequences and missing date clarification loops.
- **🛡️ Adversarial & Guardrails (8 Cases)**: Singapore NRIC masking, credit card sanitization, Model Armor prompt injection defense, and SaaS 500 error escalation.

### Dynamic Scoring Formula:
$$S_{overall} = 0.30 \cdot S_{rel} + 0.35 \cdot S_{rigor} + 0.15 \cdot S_{cost} + 0.20 \cdot S_{guard}$$

> **Empirical Results**: **100% Pass Rate (33/33 cases)** | **Composite Score: 99.34%** (Threshold: 90.0%).

---

## 🚀 Quick Start & 1-Click Deployment

### Option A: 1-Click Google Cloud Run Deployment (Recommended)
From **Google Cloud Shell** or your authenticated terminal:
```bash
git clone https://github.com/zuhaibp656/project_elevate_team_12.git
cd project_elevate_team_12
./deploy_full_gcp.sh
```
> The script automatically detects existing secrets in Google Cloud Secret Manager, provisions the Cloud Run container with Vertex AI permissions, and provides the live URL.

### Option B: Local Interactive Web UI
```bash
# 1. Install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Run the Full-Stack Workspace
uvicorn ui.server:app --host 127.0.0.1 --port 8080 --reload
```
> Open `http://localhost:8080` in your browser.

---

## 🧪 Running Automated Tests & Evaluations

```bash
# 1. Run the core system test suite (14/14 assertion tests)
python tests/run_tests.py

# 2. Run the full 33-case golden evaluation suite
python tests/eval/run_eval.py
```

---

## 🛡️ Enterprise Security & Compliance

- **Model Armor & Prompt Injection Defense**: Sanitizes adversarial override attempts, jailbreaks, and unauthorized privilege escalation.
- **In-Flight DLP PII Sanitization**: Masks Singapore NRIC numbers (`S****123A`) and 16-digit credit card numbers prior to model inference.
- **0% Policy Hallucination (FR-5.2)**: Answers are strictly constrained to retrieved policy context; out-of-scope queries are gracefully declined.
- **Mandatory Source Citations (FR-5.4)**: Every policy answer includes clickable citations to the exact document and section used.
- **GDPR / Right to be Forgotten**: Instant session purge endpoints for compliance auditing.
- **Resilient SaaS Fallback**: Zero-lockout high-fidelity state fallback ensures continuous operation during external sandbox token rotations.
