# HR Agentic Solution (MVP 1) — Streamlined 2-Day Implementation Plan & Architecture

---

## 1. Executive Summary & Chosen Technical Strategy

### Delivery Timeline: **2 Days (Target: Complete by Day After Tomorrow)**

To meet this accelerated timeline without sacrificing robustness, we select the **FastMCP Streamable HTTP Integration via Google ADK `McpToolset`** using a generated Personal Access Token (`X-MCP-Token`). 

### Why FastMCP over Direct REST APIs?
- **Zero Boilerplate**: The mounted FastMCP endpoints (`/work-week/mcp/` and `/service-immediately/mcp/`) expose all required tools (`request_time_off`, `get_employee_balances`, `create_ticket`, `update_ticket_status`) with built-in parameter validation and schemas automatically.
- **Fastest Time-to-Delivery**: Eliminates the need to manually write and maintain 10+ individual REST wrapper functions.
- **Seamless ADK Native Support**: Google ADK natively connects to Streamable HTTP MCP servers in under 10 lines of code.

---

## 2. System Architecture & Flow

![System Architecture](images/system_architecture.jpg)

### Core Components:
1. **Visually Aesthetic UI Wrapper**: Lightweight web chat interface (Vanilla JS/CSS) with real-time status animations.
2. **ADK Multi-Agent Core**:
   - **`hr_orchestrator` (Main Agent)**: Routes intents and coordinates multi-step workflows.
   - **`hcm_agent`**: Binds directly to the WorkWeek FastMCP server.
   - **`itsm_agent`**: Binds directly to the ServiceImmediately FastMCP server.
   - **`policy_agent`**: RAG-powered agent answering from ingested policy documents with citations.
3. **Live Mock Platform**: `https://mock-saas.aishprabhat.demo.altostrat.com`

---

## 3. End-to-End Cross-System Flow

![Multi-Agent AI Flow](images/flow_diagram.jpg)

### Cross-System Execution (e.g. Medical Leave Request):
1. **User asks**: *"I need medical leave starting Monday. Can you set it up?"*
2. **Step 1 (`policy_agent`)**: Quotes medical leave entitlement (10 days) and identifies manager email delegation requirement.
3. **Step 2 (`hcm_agent`)**: Calls MCP tool `get_employee_balances` $\rightarrow$ calls `request_time_off`.
4. **Step 3 (`itsm_agent`)**: Calls MCP tool `create_ticket` to route incoming emails to manager.
5. **Step 4 (Synthesis)**: Orchestrator presents combined confirmation and ticket reference to user.

---

## 4. Live MCP Integration & Code Setup

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Mint Token in Mock App UI or via cURL:                   │
│    POST https://mock-saas.../api/mcp-tokens                 │
│    Body: {"token_name": "team12-agent"}                     │
│    Response: {"token": "mcp_abc123..."}                     │
│                                                             │
│ 2. Pass Token in ADK Connection Headers:                    │
│    headers = {"X-MCP-Token": "mcp_abc123..."}               │
│                                                             │
│ 3. FastMCP Auto-Discovers All Tools:                        │
│    • WorkWeek: get_employee_balances, request_time_off, ... │
│    • ServiceImmediately: list_tickets, create_ticket, ...   │
└─────────────────────────────────────────────────────────────┘
```

### Complete ADK Multi-Agent Implementation (`src/agent/agent.py`):

```python
import os
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams

BASE_URL = "https://mock-saas.aishprabhat.demo.altostrat.com"
MCP_TOKEN = os.getenv("MCP_TOKEN", "mcp_your_token_here")
AUTH_HEADERS = {"X-MCP-Token": MCP_TOKEN}

# 1. Connect WorkWeek FastMCP
workweek_mcp = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url=f"{BASE_URL}/work-week/mcp/",
        headers=AUTH_HEADERS
    )
)

# 2. Connect ServiceImmediately FastMCP
serviceimmediately_mcp = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url=f"{BASE_URL}/service-immediately/mcp/",
        headers=AUTH_HEADERS
    )
)

# 3. Sub-Agents
hcm_agent = LlmAgent(
    name="hcm_specialist",
    model="gemini-2.5-pro",
    description="WorkWeek HCM specialist for employee profiles, leave balances, and time off requests.",
    instruction="Always check leave balances before submitting requests. Enforce YYYY-MM-DD date format and chronological ordering.",
    tools=[workweek_mcp],
)

itsm_agent = LlmAgent(
    name="itsm_specialist",
    model="gemini-2.5-pro",
    description="ServiceImmediately ITSM specialist for IT support and incident tickets.",
    instruction="Manage tickets, status transitions, and comments. Enforce valid state transitions (New -> In Progress -> Resolved -> Closed).",
    tools=[serviceimmediately_mcp],
)

policy_agent = LlmAgent(
    name="policy_specialist",
    model="gemini-2.5-pro",
    description="HR Policy specialist answering questions based on company policy documents.",
    instruction="Answer strictly using verified policy chunks. Include document title and deep-link citations. Never hallucinate.",
    tools=[], # Policy retrieval tool
)

# 4. Central Orchestrator
root_agent = LlmAgent(
    name="hr_orchestrator",
    model="gemini-2.5-pro",
    description="Central HR Orchestrator managing self-service inquiries and cross-system workflows.",
    instruction="Analyze user intent. Delegate to hcm_specialist, itsm_specialist, or policy_specialist. Coordinate multi-step tasks across specialists and synthesize a unified response.",
    tools=[hcm_agent, itsm_agent, policy_agent],
)
```

---

## 5. UI Wrapper Design & Features

- **Bright & Modern Look**: Indigo-to-Blue header gradient (`#6B46C1` $\rightarrow$ `#3182CE`), clean chat bubbles, soft shadows.
- **Animated Feedback**: Pulsing agent readiness badge, 3-dot thinking bounce during backend tool execution.
- **Decoupled Architecture**: Communicates via standard REST endpoint (`/api/chat`), making frontend and agent updates completely independent.
- **Dual Deployment**: Runs standalone or embeds directly into Gemini Enterprise.

---

## 6. Actionable 2-Day Delivery Roadmap

```
Day 1: Core Connectivity & Multi-Agent Logic
├── 1. Generate MCP Personal Access Token from /api/mcp-tokens
├── 2. Configure ADK McpToolset connections (WorkWeek & ServiceImmediately)
├── 3. Implement Policy Knowledge Base RAG tool with citations
└── 4. Wire root_agent Orchestrator with sub-agents

Day 2: UI Polish, E2E Testing & Final Verification
├── 1. Connect aesthetic Web UI wrapper to Agent runtime (/api/chat)
├── 2. Validate Single-Domain Use Cases (Policy Q&A, Leave balance check, Ticket status)
├── 3. Validate Cross-System Use Cases (Medical Leave, Equipment Procurement, Relocation)
└── 4. Benchmark Grounding (>=95% accuracy, 0% hallucinations) & finalize repo
```
