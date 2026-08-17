#!/usr/bin/env bash
# ==============================================================================
# HR Agentic Solution (Team 12) — Deployment & Execution Script
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
    else
        echo "[!] Warning: No .env or .env.example found."
    fi
fi

# 2. Dependency Management
install_deps() {
    echo "[*] Checking Python dependencies..."
    if command -v uv >/dev/null 2>&1; then
        echo "[✓] Using uv for fast environment management."
        uv pip install -q httpx python-dotenv pyyaml google-genai 2>/dev/null || true
    else
        echo "[*] Using pip..."
        pip3 install -q httpx python-dotenv pyyaml google-genai 2>/dev/null || true
    fi
}

# 3. Parse command arguments
MODE="${1:-}"

case "$MODE" in
    --web|-w)
        echo "[*] Starting Google ADK Web View UI..."
        if command -v uv >/dev/null 2>&1; then
            uv run adk web .
        elif command -v adk >/dev/null 2>&1; then
            adk web .
        else
            echo "[!] 'adk' command not found. Please install google-adk or run with uv."
            exit 1
        fi
        ;;
    --cli|-c|--interactive|-i)
        echo "[*] Starting Interactive CLI Session..."
        python3 -m agents.orchestrator --interactive
        ;;
    --test|-t)
        echo "[*] Running MCP Connectivity Test..."
        python3 tests/test_mcp_connection.py
        ;;
    --query|-q)
        shift
        QUERY="$*"
        if [ -z "$QUERY" ]; then
            echo "Usage: ./deploy.sh --query \"Your question here\""
            exit 1
        fi
        python3 -m agents.orchestrator "$QUERY"
        ;;
    *)
        echo ""
        echo "Usage: ./deploy.sh [OPTION]"
        echo ""
        echo "Options:"
        echo "  -w, --web           Launch the ADK Web View UI (browser interface)"
        echo "  -i, --cli           Launch Interactive Terminal Chat session"
        echo "  -t, --test          Run MCP endpoints connectivity test"
        echo "  -q, --query <text>  Run a single query through the orchestrator"
        echo ""
        echo "Examples:"
        echo "  ./deploy.sh --web"
        echo "  ./deploy.sh --cli"
        echo "  ./deploy.sh --query \"How many days of sick leave do I get?\""
        echo ""
        ;;
esac
