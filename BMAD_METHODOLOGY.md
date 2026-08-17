# 🚀 BMAD Method: Agile AI-Driven Development Framework

This project follows the **BMAD Method (Breakthrough Method for Agile AI-Driven Development)** ([bmad-code-org/BMAD-METHOD](https://github.com/bmad-code-org/BMAD-METHOD)) to deliver a robust, enterprise-grade multi-agent solution within an accelerated 2-day delivery cycle.

---

## 🏛️ The 5 Pillars of BMAD in Team 12's Solution

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          BMAD Multi-Agent Lifecycle                         │
│                                                                             │
│  [1. Domain Decomposition] ──► Sub-Agents: Policy, HCM, ITSM                │
│             │                                                               │
│             ▼                                                               │
│  [2. Tool Binding & Schemas] ─► FastMCP, X-MCP-Token, Strict Guardrails     │
│             │                                                               │
│             ▼                                                               │
│  [3. Orchestration & State] ──► Intent Routing & Cross-System Chaining      │
│             │                                                               │
│             ▼                                                               │
│  [4. Verification & Evals] ──► 0% Hallucinations & Transaction Correctness  │
│             │                                                               │
│             ▼                                                               │
│  [5. Deployment & Delivery] ──► ADK Web View, CLI Mode & deploy.sh          │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### Pillar 1: Domain Decomposition & Specialist Personas
Rather than relying on a brittle monolithic prompt, the system separates concerns into discrete, bounded agents using Google ADK:
- **`policy_specialist`**: Isolated to company policies; strictly evaluates markdown knowledge concepts.
- **`hcm_specialist`**: Isolated to WorkWeek HCM actions; manages profiles and leave balances.
- **`itsm_specialist`**: Isolated to ServiceImmediately ITSM actions; manages tickets and lifecycle transitions.
- **`hr_orchestrator`**: Central planner that classifies user intent and orchestrates multi-agent sequences.

---

### Pillar 2: Standardized Tool Contracts (MCP Integration)
To enable zero-code boilerplate and dynamic tool discovery:
- **FastMCP Protocol**: Connects statelessly over Streamable HTTP (`/work-week/mcp/` and `/service-immediately/mcp/`).
- **Security Context**: Authenticates via custom `X-MCP-Token` headers to ensure Google Frontend (GFE) compatibility.
- **Deterministic Guardrails**: Validates input syntax, date formats (`YYYY-MM-DD`), chronological ordering ($Start \le End$), and balance constraints before backend execution.

---

### Pillar 3: Cross-System Orchestration & State Chaining
BMAD emphasizes seamless multi-agent collaboration for complex real-world workflows:
- **Medical Leave (UC-2.2)**: `policy_specialist` $\rightarrow$ `hcm_specialist` $\rightarrow$ `itsm_specialist`.
- **Equipment Order (UC-2.1)**: `policy_specialist` $\rightarrow$ `hcm_specialist` $\rightarrow$ `itsm_specialist`.
- **Office Relocation (UC-2.3)**: `policy_specialist` $\rightarrow$ `hcm_specialist` $\rightarrow$ `itsm_specialist`.

---

### Pillar 4: Continuous Verification & Grounding
To maintain enterprise compliance and zero-trust execution:
- **0% Hallucination Target**: Policy answers must cite source document titles and deep-link URLs.
- **Graceful Error Handling**: Network failures or invalid inputs degrade gracefully without exposing technical stack traces.
- **Automated Testing**: `tests/test_mcp_connection.py` verifies tool discovery and live endpoint responses.

---

### Pillar 5: Agile Deployment & Testing Surfaces
- **Automated Scripting**: `deploy.sh` provisions the virtual environment and manages dependencies.
- **ADK Web View UI**: Real-time browser testing on `http://localhost:8000`.
- **Interactive CLI**: Fast terminal-based validation and debugging.
