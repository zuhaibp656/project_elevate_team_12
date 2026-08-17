## Goal Description
Based on the HR Agentic Solution (MVP 1) BRD, the goal is to build a secure, AI-driven centralized solution that provides employees with immediate, conversational access to HR services. The solution will:
1. **Deflect Tier 1 HR/IT inquiries** by answering policy questions strictly derived from ingested HR policy documents.
2. **Execute Employee Self-Service Transactions** via integration with **WorkWeek (HCM)** to read/write employee profiles and submit leave requests.
3. **Manage Support Desk Tickets** via integration with **ServiceImmediately (ITSM)** to query, create, and update incident tickets.

To align with your development practices:
- We will build an **ADK-based multi-agent system** capable of running independently, through a dedicated UI, or deployed on Gemini Enterprise.
- The system will consist of a **Main Agent (Orchestrator)** and specialized **Sub-Agents**.
- We will leverage **Model Context Protocol (MCP)** or direct tool access for interacting with backend systems (WorkWeek, ServiceImmediately, Policy Repo).
- We will build a **visually aesthetic, animated, and self-explanatory UI wrapper** that remains fully decoupled from the core agent layer to allow independent modifications.

## User Review Required
> [!IMPORTANT]
> **Sub-Agent Structure**: Do you prefer defining the sub-agents as distinct ADK classes/files (e.g. `policy_agent.py`, `hcm_agent.py`, `itsm_agent.py`) or defining them dynamically within the main `agent.py` file?
>
> **UI Tech Stack**: Given the requirement for a "bright, simple, and animated" UI, we can use a modern frontend framework like React (with Framer Motion for animations) or a lightweight Vanilla JS/HTML/CSS approach using View Transitions. Do you have a preference?

## Open Questions
> [!CAUTION]
> **Authentication & Authorization**: The BRD specifies using functional test credentials for MVP 1 rather than enterprise SSO. Will you be providing access to mock WorkWeek and ServiceImmediately endpoints, or should we build lightweight mock API servers to act as these backends?

## Proposed Architecture

```mermaid
flowchart TD
    subgraph UI ["Visually Aesthetic UI Wrapper"]
        ChatInterface[Conversational Interface\n(Bright, Animated, Simple)]
    end

    subgraph ADK ["Google ADK Agent Layer"]
        MainAgent{Main Agent\n(Orchestrator)}
        
        SubPolicy[Policy Sub-Agent\n(RAG / Q&A)]
        SubHCM[WorkWeek HCM\nSub-Agent]
        SubITSM[ServiceImmediately\nITSM Sub-Agent]
        
        MainAgent -->|Routes Intent| SubPolicy
        MainAgent -->|Routes Intent| SubHCM
        MainAgent -->|Routes Intent| SubITSM
        
        MainAgent <-->|Cross-System Orchestration\n(e.g., Leave + Ticket)| SubHCM & SubITSM & SubPolicy
    end
    
    subgraph MCP ["MCP Servers / Integration Tools"]
        PolicyTools[Policy Retrieval Tools\n(Chunking & Vector Search)]
        HCMTools[WorkWeek MCP Server\n(Profiles, Leaves)]
        ITSMTools[ServiceImmediately MCP Server\n(Tickets, Status, Comments)]
    end
    
    subgraph Backend ["Enterprise Systems (MVP 1 Test Envs)"]
        PolicyRepo[(HR Policy Documents)]
        WorkWeek[(WorkWeek HCM)]
        ServiceImmediately[(ServiceImmediately ITSM)]
    end

    %% Connections
    ChatInterface <-->|API / WebSockets| MainAgent
    SubPolicy <--> PolicyTools
    SubHCM <--> HCMTools
    SubITSM <--> ITSMTools
    
    PolicyTools <--> PolicyRepo
    HCMTools <--> WorkWeek
    ITSMTools <--> ServiceImmediately
```

## Proposed Changes

---

### UI Wrapper
We will create a decoupled static frontend that communicates with the ADK agent runtime.
- A modern chat interface prioritizing ease-of-use.
- Animated state transitions (loading indicators for backend fetches, success checkmarks for ticket creation).
- Configurable theming to support bright and accessible colors.
#### [NEW] `project_elevate/ui/static/index.html`
#### [NEW] `project_elevate/ui/static/app.js`
#### [NEW] `project_elevate/ui/static/styles.css`

---

### ADK Core Agent Layer
We will extend the existing `agent.py` to act as an orchestrator and define sub-agents.
#### [MODIFY] `project_elevate/agent/agent.py`
```python
# Introduce sub-agents and router logic
policy_agent = LlmAgent(prompt=POLICY_PROMPT, tools=[retrieve_policy])
hcm_agent = LlmAgent(prompt=HCM_PROMPT, tools=[get_profile, submit_leave])
itsm_agent = LlmAgent(prompt=ITSM_PROMPT, tools=[query_ticket, create_incident])

# Main agent prompt will instruct it to delegate tasks to sub-agents
root_agent = LlmAgent(prompt=ROOT_PROMPT, tools=[policy_agent, hcm_agent, itsm_agent])
```

#### [NEW] `project_elevate/agent/subagents.py`
Contains the specific prompts and instructions for the WorkWeek, ServiceImmediately, and Policy sub-agents, including validation constraints from the BRD (e.g., chronological validation of leave dates, preventing direct New -> Closed ticket transitions).

---

### MCP / Integration Tools
We will create integration scripts that abstract the WorkWeek and ServiceImmediately systems.
#### [NEW] `project_elevate/agent/tools/mcp_workweek.py`
Exposes core actions: `Retrieve Employee Profile`, `Update Contact Information`, `Query Time-Off Balances`, and `Submit Leave Request`.
#### [NEW] `project_elevate/agent/tools/mcp_service_immediately.py`
Exposes core actions: `Query Ticket Details`, `Create Incident Ticket`, `Post Ticket Comment`, and `Update Ticket Status`.

## Verification Plan

### Automated Tests
1. **Safety & Guardrail Efficacy**: We will run tests simulating prompt injections and out-of-bounds queries to ensure the Main Agent rejects them and maintains 100% domain containment.
2. **Transaction Integrity**: We will execute functional unit tests on the MCP mock tools to ensure business logic constraints (e.g., negative balance checks) hold true.

### Manual Verification
1. **Cross-System Orchestration Check**: The user will issue a complex request (e.g., "I need medical leave, please set it up and ensure my manager has email access.")
2. **UI Review**: The user will load the UI wrapper locally (`adk web` or custom static server) to verify animations, color palette, and component decoupling.
