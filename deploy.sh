#!/usr/bin/env bash
# ==============================================================================
# HR Agentic Solution (Team 12) — Deployment & Execution Script (venv-powered)
# ==============================================================================

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_ROOT"

echo "================================================================="
echo "   HR Agentic Solution (Team 12) — Multi-Agent Orchestrator   "
echo "================================================================="

# 1. Check or Setup .env
if [ ! -f "$REPO_ROOT/.env" ]; then
    if [ -f "$REPO_ROOT/.env.example" ]; then
        echo "[!] .env file not found. Creating from .env.example..."
        cp "$REPO_ROOT/.env.example" "$REPO_ROOT/.env"
        echo "[✓] Created .env. Please verify your MCP_TOKEN inside .env if needed."
    fi
fi

# 2. Virtual Environment Setup (Python 3.11)
if [ ! -d "$REPO_ROOT/.venv" ]; then
    echo "[*] Creating virtual environment (.venv) using Python 3.11..."
    if command -v uv >/dev/null 2>&1; then
        uv venv --python /opt/homebrew/opt/python@3.11/bin/python3.11 .venv 2>/dev/null || uv venv .venv
        uv sync
    else
        /opt/homebrew/opt/python@3.11/bin/python3.11 -m venv .venv || python3 -m venv .venv
        .venv/bin/pip install -q httpx python-dotenv pyyaml google-adk
    fi
    echo "[✓] Virtual environment ready."
fi

PYTHON_EXEC="$REPO_ROOT/.venv/bin/python"

# 3. Parse command arguments
MODE="${1:-}"

case "$MODE" in
    --web|-w)
        PORT="${2:-8088}"
        echo "[*] Starting Google ADK Web View UI on http://localhost:$PORT ..."
        if command -v uv >/dev/null 2>&1; then
            uv run adk web . --port "$PORT"
        elif [ -f "$REPO_ROOT/.venv/bin/adk" ]; then
            "$REPO_ROOT/.venv/bin/adk" web . --port "$PORT"
        else
            echo "[!] adk command not found in .venv. Installing google-adk..."
            "$REPO_ROOT/.venv/bin/pip" install google-adk
            "$REPO_ROOT/.venv/bin/adk" web . --port "$PORT"
        fi
        ;;
    --ui|-u)
        PORT="${2:-8090}"
        echo "[*] Starting Elevate HR Google Aura Web UI on http://localhost:$PORT ..."
        "$PYTHON_EXEC" -m uvicorn ui.server:app --host 127.0.0.1 --port "$PORT"
        ;;
    --cli|-c|--interactive|-i)
        echo "[*] Starting Interactive CLI Session..."
        "$PYTHON_EXEC" -m agents.orchestrator --interactive
        ;;
    --test|-t)
        echo "[*] Running MCP Connectivity Test..."
        "$PYTHON_EXEC" tests/test_mcp_connection.py
        ;;
    --query|-q)
        shift
        QUERY="$*"
        if [ -z "$QUERY" ]; then
            echo "Usage: ./deploy.sh --query \"Your question here\""
            exit 1
        fi
        "$PYTHON_EXEC" -m agents.orchestrator "$QUERY"
        ;;
    --ge|--gemini-enterprise)
        shift
        exec ./deploy_gemini_enterprise.sh "$@"
        ;;
    *)
        echo ""
        echo "Usage: ./deploy.sh [OPTION]"
        echo ""
        echo "Options:"
        echo "  -u, --ui            Launch the Elevate HR Google Aura Web UI (http://localhost:8090)"
        echo "  --ge, --gemini-enterprise Deploy ONLY agent to Gemini Enterprise (Agent Engine / Cloud Run)"
        echo "  -w, --web           Launch the Google ADK Web View UI (http://localhost:8088)"
        echo "  -i, --cli           Launch Interactive Terminal Chat session"
        echo "  -t, --test          Run MCP endpoints connectivity test"
        echo "  -q, --query <text>  Run a single query through the orchestrator"
        echo ""
        echo "Examples:"
        echo "  ./deploy.sh --ui"
        echo "  ./deploy.sh --ge --project <PROJECT_ID>"
        echo "  ./deploy.sh --web"
        echo "  ./deploy.sh --cli"
        echo "  ./deploy.sh --query \"How many days of sick leave do I get?\""
        echo ""
        ;;
esac
