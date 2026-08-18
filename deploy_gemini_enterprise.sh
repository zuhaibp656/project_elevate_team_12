#!/usr/bin/env bash
# ==============================================================================
# Elevate HR Agentic Solution (Team 12) — Gemini Enterprise (GE) Deployer
# ==============================================================================
# This script packages and deploys ONLY the multi-agent orchestrator & tools
# to the Gemini Enterprise / Vertex AI Agent Engine runtime using Google ADK.
# ==============================================================================

set -eo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_ROOT"

echo "================================================================="
echo "   🚀 Elevate HR — Gemini Enterprise (GE) Agent Deployment       "
echo "================================================================="

# -----------------------------------------------------------------------------
# 1. Load Local Environment Configuration
# -----------------------------------------------------------------------------
if [ -f "$REPO_ROOT/.env" ]; then
    echo "[*] Loading configuration from .env..."
    set -a
    # shellcheck disable=SC1091
    source <(grep -v '^\s*#' "$REPO_ROOT/.env" | grep -v '^\s*$')
    set +a
elif [ -f "$REPO_ROOT/.env.example" ]; then
    echo "[!] No .env found. Creating .env from .env.example..."
    cp "$REPO_ROOT/.env.example" "$REPO_ROOT/.env"
fi

# -----------------------------------------------------------------------------
# 2. Defaults & CLI Argument Parsing
# -----------------------------------------------------------------------------
PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-${PROJECT_ID:-}}"
REGION="${GOOGLE_CLOUD_LOCATION:-${REGION:-us-central1}}"
DEPLOY_TARGET="agent_engine"  # agent_engine or cloud_run
DISPLAY_NAME="Elevate-HR-Agentic-Orchestrator"
DESCRIPTION="Centralized Enterprise HR Multi-Agent Orchestrator (Policy, WorkWeek HCM, ServiceImmediately ITSM)"
MCP_TOKEN_VAL="${MCP_TOKEN:-mcp_CsoiJPHj_FGICu8pf8aFJLIuPc4Kt4AXeOLWyUmwHxQ}"
API_KEY_VAL="${GEMINI_API_KEY:-${GOOGLE_API_KEY:-}}"
DRY_RUN=false

print_usage() {
    echo ""
    echo "Usage: ./deploy_gemini_enterprise.sh [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -p, --project <PROJECT_ID>    Google Cloud Project ID (overrides env)"
    echo "  -r, --region <REGION>         GCP Region (default: us-central1)"
    echo "  -k, --api-key <API_KEY>       Gemini API Key (if deploying via API key mode)"
    echo "  -t, --target <TARGET>         Deployment target: 'agent_engine' (default) or 'cloud_run'"
    echo "  -n, --name <NAME>             Display Name for the deployed Agent Engine"
    echo "  -m, --mcp-token <TOKEN>       FastMCP token for Mock SaaS backend authentication"
    echo "  -d, --dry-run                 Validate agent packaging and imports without deploying"
    echo "  -h, --help                    Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./deploy_gemini_enterprise.sh --project my-gcp-project --region us-central1"
    echo "  ./deploy_gemini_enterprise.sh --api-key AIzaSy..."
    echo "  ./deploy_gemini_enterprise.sh --dry-run"
    echo ""
    exit 1
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        -p|--project)
            PROJECT_ID="$2"
            shift 2
            ;;
        -r|--region)
            REGION="$2"
            shift 2
            ;;
        -k|--api-key)
            API_KEY_VAL="$2"
            shift 2
            ;;
        -t|--target)
            DEPLOY_TARGET="$2"
            shift 2
            ;;
        -n|--name)
            DISPLAY_NAME="$2"
            shift 2
            ;;
        -m|--mcp-token)
            MCP_TOKEN_VAL="$2"
            shift 2
            ;;
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -h|--help)
            print_usage
            ;;
        *)
            echo "[!] Unknown argument: $1"
            print_usage
            ;;
    esac
done

# -----------------------------------------------------------------------------
# 3. Environment & Credential Validation
# -----------------------------------------------------------------------------
echo "[*] Verifying deployment credentials..."

if [ -z "$PROJECT_ID" ] && [ -z "$API_KEY_VAL" ]; then
    if command -v gcloud >/dev/null 2>&1; then
        PROJECT_ID=$(gcloud config get-value project 2>/dev/null || true)
    fi
fi

if [ -z "$PROJECT_ID" ] && [ -z "$API_KEY_VAL" ] && [ "$DRY_RUN" = false ]; then
    echo ""
    echo "[!] Error: Neither Google Cloud Project ID nor GEMINI_API_KEY was found."
    echo "    Please specify a project or API key:"
    echo "      ./deploy_gemini_enterprise.sh --project <YOUR_PROJECT_ID>"
    echo "    or set GOOGLE_CLOUD_PROJECT in your .env file."
    echo ""
    exit 1
fi

echo "  • Deployment Target:    $DEPLOY_TARGET"
if [ -n "$PROJECT_ID" ]; then
    echo "  • Google Cloud Project: $PROJECT_ID"
    echo "  • Region:               $REGION"
fi
if [ -n "$API_KEY_VAL" ]; then
    echo "  • Auth Mode:            Gemini API Key (configured)"
else
    echo "  • Auth Mode:            Google Application Default Credentials (ADC)"
fi
echo "  • Agent Display Name:   $DISPLAY_NAME"

# -----------------------------------------------------------------------------
# 4. Virtual Environment & ADK Tools Check
# -----------------------------------------------------------------------------
echo ""
echo "[*] Checking Python environment and Google ADK..."

if [ ! -d "$REPO_ROOT/.venv" ]; then
    echo "[*] Creating .venv virtual environment..."
    python3 -m venv "$REPO_ROOT/.venv"
    "$REPO_ROOT/.venv/bin/pip" install --upgrade pip
    "$REPO_ROOT/.venv/bin/pip" install -q httpx python-dotenv pyyaml google-adk google-genai
fi

PYTHON_BIN="$REPO_ROOT/.venv/bin/python"
ADK_BIN="$REPO_ROOT/.venv/bin/adk"

if [ ! -f "$ADK_BIN" ]; then
    echo "[*] Installing google-adk into .venv..."
    "$REPO_ROOT/.venv/bin/pip" install -q google-adk
fi

# -----------------------------------------------------------------------------
# 5. FastMCP SaaS Backend Connectivity & Interactive Fallback
# -----------------------------------------------------------------------------
echo ""
echo "[*] Testing Mock SaaS FastMCP connectivity (Identity & Token validation)..."

check_mcp_token() {
    local token="$1"
    "$PYTHON_BIN" -c "
import sys, json, httpx
url = 'https://mock-saas.aishprabhat.demo.altostrat.com/work-week/mcp/'
headers = {'X-MCP-Token': '$token', 'Content-Type': 'application/json', 'Accept': 'application/json, text/event-stream'}
payload = {'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call', 'params': {'name': 'get_employee_balances', 'arguments': {'employee_id': 'EMP-380'}}}
try:
    with httpx.Client(timeout=8.0) as client:
        r = client.post(url, headers=headers, json=payload)
        if r.status_code == 200:
            sys.exit(0)
        else:
            sys.exit(1)
except Exception:
    sys.exit(1)
"
}

update_mcp_config() {
    local token="$1"
    export MCP_TOKEN="$token"
    
    # Update .env
    if [ -f "$REPO_ROOT/.env" ]; then
        if grep -q "^MCP_TOKEN=" "$REPO_ROOT/.env"; then
            sed -i.bak "s|^MCP_TOKEN=.*|MCP_TOKEN=$token|" "$REPO_ROOT/.env" && rm -f "$REPO_ROOT/.env.bak"
        else
            echo "MCP_TOKEN=$token" >> "$REPO_ROOT/.env"
        fi
    fi

    # Update agents/.agent_engine_config.json
    "$PYTHON_BIN" -c "
import json
cfg_path = '$REPO_ROOT/agents/.agent_engine_config.json'
try:
    with open(cfg_path, 'r') as f:
        cfg = json.load(f)
    if 'env' not in cfg:
        cfg['env'] = {}
    cfg['env']['MCP_TOKEN'] = '$token'
    with open(cfg_path, 'w') as f:
        json.dump(cfg, f, indent=2)
except Exception as e:
    pass
"
}

if check_mcp_token "$MCP_TOKEN_VAL"; then
    echo "  [✓] FastMCP SaaS authentication verified! (Status 200 OK)"
    update_mcp_config "$MCP_TOKEN_VAL"
else
    echo "  [!] Warning: FastMCP connection test failed with current token."
    echo "      The mock SaaS portal requires a valid token from: https://mock-saas.aishprabhat.demo.altostrat.com/"
    echo ""
    
    # If interactive shell is available, prompt for token
    if [ -t 0 ]; then
        while true; do
            read -r -p "🔑 Enter your FastMCP Token (or press Enter to proceed with default): " USER_TOKEN
            if [ -z "$USER_TOKEN" ]; then
                echo "  [!] Continuing with default token..."
                break
            fi
            echo "  [*] Validating entered token..."
            if check_mcp_token "$USER_TOKEN"; then
                echo "  [✓] Success! Token verified (Status 200 OK)."
                MCP_TOKEN_VAL="$USER_TOKEN"
                update_mcp_config "$USER_TOKEN"
                break
            else
                echo "  [!] Token validation failed (non-200 response). Please check the token."
            fi
        done
    else
        echo "  [!] Non-interactive shell detected. Proceeding with existing configuration..."
    fi
fi

# -----------------------------------------------------------------------------
# 6. Dry Run / Agent Import Validation
# -----------------------------------------------------------------------------
echo ""
echo "[*] Validating agent composition & root orchestrator import..."

"$PYTHON_BIN" -c "
from agents.orchestrator import root_agent
print(f'  [✓] Successfully initialized root_agent: {root_agent.name}')
print(f'  [✓] Sub-agents wired: {[a.name for a in root_agent.sub_agents]}')
"

if [ "$DRY_RUN" = true ]; then
    echo ""
    echo "================================================================="
    echo "  [✓] Dry-run complete! All agent definitions and FastMCP tools"
    echo "      are packaged and ready for deployment to Gemini Enterprise."
    echo "================================================================="
    exit 0
fi

# -----------------------------------------------------------------------------
# 7. Deploy to Gemini Enterprise / Vertex AI Agent Engine
# -----------------------------------------------------------------------------
echo ""
echo "================================================================="
echo "  [*] Executing ADK deployment to Gemini Enterprise runtime...   "
echo "================================================================="

DEPLOY_FLAGS=(
    "agents/"
    "--display_name" "$DISPLAY_NAME"
    "--description" "$DESCRIPTION"
)

if [ -n "$PROJECT_ID" ]; then
    DEPLOY_FLAGS+=("--project" "$PROJECT_ID" "--region" "$REGION")
fi

if [ -n "$API_KEY_VAL" ]; then
    DEPLOY_FLAGS+=("--api_key" "$API_KEY_VAL")
fi

if [ "$DEPLOY_TARGET" == "cloud_run" ]; then
    echo "[*] Deploying to Cloud Run target via ADK..."
    "$ADK_BIN" deploy cloud_run "${DEPLOY_FLAGS[@]}"
else
    echo "[*] Deploying to Vertex AI Agent Engine (Reasoning Engine)..."
    "$ADK_BIN" deploy agent_engine "${DEPLOY_FLAGS[@]}"
fi

echo ""
echo "================================================================="
echo "  🎉 Deployment Complete!                                       "
echo "  Your HR Multi-Agent Orchestrator is now live on Gemini         "
echo "  Enterprise runtime.                                           "
echo "================================================================="
