# 🚀 Gemini Enterprise (GE) Agent Deployment Guide — Team 12

This guide outlines how to deploy **ONLY the Multi-Agent Orchestrator and its tool associations** directly to the **Gemini Enterprise / Vertex AI Agent Engine (Reasoning Engines)** runtime using Google ADK.

---

## 🏗️ Architecture & Decoupled Design

The solution is architected in a decoupled structure:
* **Raw Agent & Sub-Agents (`agents/`)**: Pure ADK multi-agent orchestrator (`hr_orchestrator`), 3 specialist agents (`policy_specialist`, `hcm_specialist`, `itsm_specialist`), and FastMCP tool contracts (`tools/`).
* **Web UI Wrapper (`ui/`)**: Optional visualization layer (can be run locally or skipped entirely for pure GE runtime deployment).

```
                      ┌───────────────────────────────────────────────┐
                      │    Gemini Enterprise Agent Space Runtime      │
                      │                                               │
                      │    ┌─────────────────────────────────────┐    │
                      │    │   hr_orchestrator (Root Agent)      │    │
                      │    └──────────────────┬──────────────────┘    │
                      │                       │                       │
                      │        ┌──────────────┼──────────────┐        │
                      │        │              │              │        │
                      │  ┌─────▼─────┐  ┌─────▼─────┐  ┌─────▼─────┐  │
                      │  │  Policy   │  │  WorkWeek │  │  Service  │  │
                      │  │ Specialist│  │HCM Expert │  │Immediately│  │
                      │  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘  │
                      └────────┼──────────────┼──────────────┼────────┘
                               │              │              │
                    FastMCP / Knowledge       │              │
                               │        Streamable HTTP      │
                               │        (X-MCP-Token)        │
                               ▼              ▼              ▼
                       [Policy Docs]     [WorkWeek]    [ServiceDesk]
```

---

## 🔑 Authentication: LLM Keys & Google IAP Protection

### 1. LLM Model Authentication
When someone clones the repository, they can authenticate Gemini models using either:
* **Option A (API Key)**: Set `GEMINI_API_KEY` or pass `--api-key <KEY>`.
* **Option B (Google Cloud ADC / IAM)**: Authenticate with their Google Cloud project:
  ```bash
  gcloud auth application-default login
  export GOOGLE_CLOUD_PROJECT="<your-gcp-project-id>"
  ```

### 2. Mock SaaS Apps & Google Identity-Aware Proxy (IAP) Protection
The mock SaaS applications are protected by Google Cloud Identity-Aware Proxy (IAP) for interactive browser access. 

**How the Agent Handles This Seamlessly:**
1. **FastMCP Direct Streamable RPC**: The mock apps expose dedicated FastMCP JSON-RPC endpoints:
   * `/work-week/mcp/`
   * `/service-immediately/mcp/`
2. **`X-MCP-Token` Header**: Each tool call automatically transmits the user's `MCP_TOKEN` in the `X-MCP-Token` header. This token is cryptographically verified by the mock backend and mapped directly to employee ID `EMP-380`, completely bypassing interactive IAP browser login prompts!
3. **If using Cloud IAP-protected REST APIs directly**: When running on Google Cloud, the agent can also generate an OIDC ID token using the GCP metadata server / ADC:
   ```python
   import google.auth.transport.requests
   import google.oauth2.id_token

   auth_req = google.auth.transport.requests.Request()
   iap_token = google.oauth2.id_token.fetch_id_token(auth_req, audience=IAP_CLIENT_ID)
   headers["Authorization"] = f"Bearer {iap_token}"
   ```

---

## ⚡ Deployment Instructions

### Step 1: Clone Repository
```bash
git clone https://github.com/zuhaibp656/project_elevate_team_12.git
cd project_elevate_team_12
```

### Step 2: Configure Environment
Copy `.env.example` to `.env` and set your credentials:
```bash
cp .env.example .env
```
Edit `.env`:
```ini
# Gemini Configuration
GEMINI_MODEL=gemini-2.5-flash
GEMINI_API_KEY=AIzaSy...  # Or use gcloud ADC

# FastMCP Authentication Token
MCP_TOKEN=mcp_CsoiJPHj_FGICu8pf8aFJLIuPc4Kt4AXeOLWyUmwHxQ

# Google Cloud Settings
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GOOGLE_CLOUD_LOCATION=us-central1
```

### Step 3: Run Dry-Run Validation
Verify that all sub-agents, FastMCP endpoints, and dependencies are ready:
```bash
./deploy_gemini_enterprise.sh --dry-run
```

### Step 4: Deploy to Gemini Enterprise / Agent Engine
Execute the deployment script:
```bash
# Using Google Cloud Project credentials:
./deploy_gemini_enterprise.sh --project <PROJECT_ID> --region us-central1

# OR using API Key mode:
./deploy_gemini_enterprise.sh --api-key <GEMINI_API_KEY>

# OR via deploy.sh shortcut:
./deploy.sh --ge --project <PROJECT_ID>
```

---

## 🧪 Testing the Live Deployed Agent

Once deployed, the agent can be invoked via Vertex AI SDK or Gemini Enterprise Agent Space:

```python
from vertexai.preview import reasoning_engines

# Connect to the deployed Gemini Enterprise Reasoning Engine
agent = reasoning_engines.ReasoningEngine(
    "projects/<PROJECT_ID>/locations/us-central1/reasoningEngines/<ENGINE_ID>"
)

# Query the multi-agent orchestrator
response = agent.query(
    message="How many vacation days do I have remaining, and what is the policy for medical leave?"
)
print(response)
```
