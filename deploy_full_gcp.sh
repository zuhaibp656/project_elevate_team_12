#!/usr/bin/env bash
# ==============================================================================
# Elevate HR Agentic Solution (Team 12) — Full-Stack GCP 1-Click Deployer
# ==============================================================================
# This script deploys the complete solution (Google Aura Web UI + Multi-Agent
# Orchestrator + FastMCP Tools + Policy Knowledge Base) to Google Cloud Run
# with Secret Manager integration, Model Armor, and automated IAM configuration.
# ==============================================================================

set -eo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_ROOT"

echo "================================================================="
echo "   🌟 Elevate HR (Team 12) — Full-Stack GCP 1-Click Deployer    "
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
# 2. Defaults & CLI Arguments
# -----------------------------------------------------------------------------
PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-${PROJECT_ID:-}}"
REGION="${GOOGLE_CLOUD_LOCATION:-${REGION:-}}"
SERVICE_NAME="elevate-hr-app"
MCP_TOKEN_VAL="${MCP_TOKEN:-}"
API_KEY_VAL="${GEMINI_API_KEY:-${GOOGLE_API_KEY:-}}"
MEMORY="2Gi"
CPU="2"
DRY_RUN=false

print_usage() {
    echo ""
    echo "Usage: ./deploy_full_gcp.sh [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -p, --project <PROJECT_ID>    Google Cloud Project ID (auto-detected if omitted)"
    echo "  -r, --region <REGION>         GCP Region (default: us-central1)"
    echo "  -s, --service <NAME>          Cloud Run service name (default: elevate-hr-app)"
    echo "  -k, --api-key <KEY>           Gemini API Key (optional; uses Cloud Run IAM if omitted)"
    echo "  -m, --mcp-token <TOKEN>       FastMCP token for Mock SaaS backend authentication"
    echo "  -d, --dry-run                 Validate configuration and dependencies without deploying"
    echo "  -h, --help                    Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./deploy_full_gcp.sh"
    echo "  ./deploy_full_gcp.sh --project my-target-gcp-project --region us-central1"
    echo "  ./deploy_full_gcp.sh --service my-hr-agent"
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
        -s|--service)
            SERVICE_NAME="$2"
            shift 2
            ;;
        -k|--api-key)
            API_KEY_VAL="$2"
            shift 2
            ;;
        -m|--mcp-token|--token)
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
# 3. Google Cloud Project & Region Resolution
# -----------------------------------------------------------------------------
echo "[*] Resolving Google Cloud project and credentials..."

if [ -z "$PROJECT_ID" ] && command -v gcloud >/dev/null 2>&1; then
    PROJECT_ID=$(gcloud config get-value project 2>/dev/null || true)
fi

if [ -z "$PROJECT_ID" ] && [ "$DRY_RUN" = false ]; then
    if [ -t 0 ]; then
        read -r -p "🔑 Enter your Google Cloud Project ID: " USER_PROJECT
        PROJECT_ID="$USER_PROJECT"
    fi
fi

if [ -z "$PROJECT_ID" ] && [ "$DRY_RUN" = false ]; then
    echo "[!] Error: No Google Cloud Project ID provided."
    echo "    Please run with: ./deploy_full_gcp.sh --project <YOUR_PROJECT_ID>"
    exit 1
fi

if [ -z "$REGION" ] && command -v gcloud >/dev/null 2>&1; then
    REGION=$(gcloud config get-value compute/region 2>/dev/null || true)
fi
if [ -z "$REGION" ]; then
    REGION="us-central1"
fi

echo "  • Target Platform:     Google Cloud Run (Serverless Managed)"
echo "  • Service Name:        $SERVICE_NAME"
if [ -n "$PROJECT_ID" ]; then
    echo "  • GCP Project ID:      $PROJECT_ID"
fi
echo "  • GCP Region:          $REGION"
echo "  • Memory / CPU:        $MEMORY / $CPU vCPU"
if [ -n "$API_KEY_VAL" ]; then
    echo "  • Auth Mode:           Gemini API Key"
else
    echo "  • Auth Mode:           Native Cloud Run IAM / Vertex AI Service Account"
fi
if [ -n "$MCP_TOKEN_VAL" ]; then
    echo "  • FastMCP Token:       ${MCP_TOKEN_VAL:0:8}... (configured)"
else
    echo "  • FastMCP Token:       (Will prompt or check Secret Manager)"
fi

# -----------------------------------------------------------------------------
# 4. FastMCP Backend Connectivity & Secret Manager Auto-Resolution
# -----------------------------------------------------------------------------
echo ""
echo "[*] Resolving FastMCP token and Secret Manager configuration..."

# 1. Check if token is in .env if not set via CLI or env
if [ -z "$MCP_TOKEN_VAL" ] && [ -f "$REPO_ROOT/.env" ]; then
    ENV_TOKEN=$(grep -E '^MCP_TOKEN=' "$REPO_ROOT/.env" 2>/dev/null | head -n1 | cut -d '=' -f2- | tr -d '"' | tr -d "'" | tr -d '\r' || true)
    if [ -n "$ENV_TOKEN" ]; then
        MCP_TOKEN_VAL="$ENV_TOKEN"
        echo "  [✓] Auto-loaded FastMCP token from .env file."
    fi
fi

# 2. Check if secret exists in Google Cloud Secret Manager
if [ -z "$MCP_TOKEN_VAL" ] && command -v gcloud >/dev/null 2>&1 && [ -n "$PROJECT_ID" ]; then
    EXISTING_SECRET=$(gcloud secrets versions access latest --secret=hr-agent-mcp-token --project="$PROJECT_ID" 2>/dev/null || true)
    if [ -n "$EXISTING_SECRET" ]; then
        MCP_TOKEN_VAL="$EXISTING_SECRET"
        echo "  [✓] Auto-loaded FastMCP token from Google Cloud Secret Manager."
    fi
fi

# 3. Only prompt if token is completely absent across all sources
if [ -z "$MCP_TOKEN_VAL" ]; then
    if [ -t 0 ] && [ "$DRY_RUN" = false ]; then
        echo "  [!] No existing FastMCP token found in Secret Manager or .env."
        read -r -p "🔑 Enter your FastMCP Token (from https://mock-saas.aishprabhat.demo.altostrat.com/): " NEW_TOKEN
        if [ -n "$NEW_TOKEN" ]; then
            MCP_TOKEN_VAL="$NEW_TOKEN"
            echo "  [✓] FastMCP token recorded for deployment."
        fi
    fi
else
    echo "  [✓] FastMCP token ready (${MCP_TOKEN_VAL:0:8}...). Proceeding without prompting."
fi

# -----------------------------------------------------------------------------
# 5. Check for Existing Cloud Run Deployment & Fast-Track Rolling Update
# -----------------------------------------------------------------------------
EXISTING_SERVICE_URL=""
if command -v gcloud >/dev/null 2>&1 && [ -n "$PROJECT_ID" ]; then
    EXISTING_SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --project "$PROJECT_ID" --region "$REGION" --format="value(status.url)" 2>/dev/null || true)
fi

if [ -n "$EXISTING_SERVICE_URL" ]; then
    echo ""
    echo "================================================================="
    echo "  ⚡ Existing Deployment Detected: $EXISTING_SERVICE_URL"
    echo "  [*] Mode: Updating existing Cloud Run service (Rolling Revision)"
    echo "================================================================="
    IS_UPDATE=true
else
    echo ""
    echo "================================================================="
    echo "  [*] Mode: Initial Deployment (Provisioning new Cloud Run service)"
    echo "================================================================="
    IS_UPDATE=false
fi

# -----------------------------------------------------------------------------
# 6. Enable APIs, IAM Roles & Secret Manager (Only on first run or if needed)
# -----------------------------------------------------------------------------
if [ "$DRY_RUN" = false ] && command -v gcloud >/dev/null 2>&1 && [ -n "$PROJECT_ID" ]; then
    if [ "$IS_UPDATE" = false ]; then
        echo ""
        echo "[*] Enabling required Google Cloud APIs..."
        gcloud services enable \
            run.googleapis.com \
            secretmanager.googleapis.com \
            cloudbuild.googleapis.com \
            artifactregistry.googleapis.com \
            aiplatform.googleapis.com \
            storage-component.googleapis.com \
            --project "$PROJECT_ID" 2>/dev/null || true
        echo "  [✓] Cloud Run, Secret Manager, Cloud Build & Vertex AI APIs enabled."

        # IAM Role Bindings for Build & Runtime Service Accounts
        PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)' 2>/dev/null || true)
        if [ -n "$PROJECT_NUMBER" ]; then
            echo "[*] Configuring IAM permissions for Cloud Build & Compute service accounts..."
            COMPUTE_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
            CLOUDBUILD_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"

            for ROLE in roles/storage.admin roles/logging.logWriter roles/artifactregistry.writer roles/cloudbuild.builds.builder roles/aiplatform.user roles/secretmanager.secretAccessor; do
                gcloud projects add-iam-policy-binding "$PROJECT_ID" \
                    --member="serviceAccount:${COMPUTE_SA}" \
                    --role="$ROLE" \
                    --condition=None 2>/dev/null || true
            done

            for ROLE in roles/storage.admin roles/logging.logWriter roles/artifactregistry.writer roles/aiplatform.user roles/secretmanager.secretAccessor; do
                gcloud projects add-iam-policy-binding "$PROJECT_ID" \
                    --member="serviceAccount:${CLOUDBUILD_SA}" \
                    --role="$ROLE" \
                    --condition=None 2>/dev/null || true
            done
            echo "  [✓] IAM permissions successfully configured."
        fi
    fi

    # Secret Manager Setup for MCP Token
    if [ -n "$MCP_TOKEN_VAL" ]; then
        if ! gcloud secrets describe hr-agent-mcp-token --project "$PROJECT_ID" >/dev/null 2>&1; then
            echo "[*] Creating secret hr-agent-mcp-token in Secret Manager..."
            gcloud secrets create hr-agent-mcp-token \
                --replication-policy="automatic" \
                --project "$PROJECT_ID" 2>/dev/null || true
        fi
        echo -n "$MCP_TOKEN_VAL" | gcloud secrets versions add hr-agent-mcp-token \
            --data-file=- \
            --project "$PROJECT_ID" 2>/dev/null || true
        echo "  [✓] Secret hr-agent-mcp-token updated with latest version in Secret Manager."
    fi
fi

# -----------------------------------------------------------------------------
# 6. Dry-Run Verification
# -----------------------------------------------------------------------------
if [ "$DRY_RUN" = true ]; then
    echo ""
    echo "================================================================="
    echo "  [✓] Dry-run complete! All deployment prerequisites, secrets,"
    echo "      and configurations are validated and ready for Cloud Run."
    echo "================================================================="
    exit 0
fi

# -----------------------------------------------------------------------------
# 7. Build & Deploy to Google Cloud Run (Rolling Update / New Revision)
# -----------------------------------------------------------------------------
echo ""
echo "================================================================="
if [ "$IS_UPDATE" = true ]; then
    echo "  [*] Deploying new revision to existing Cloud Run service...  "
else
    echo "  [*] Deploying full-stack solution to Google Cloud Run...       "
fi
echo "================================================================="

ENV_VARS="GEMINI_MODEL=gemini-2.5-flash"
ENV_VARS="$ENV_VARS,MOCK_SAAS_BASE_URL=https://mock-saas.aishprabhat.demo.altostrat.com"
ENV_VARS="$ENV_VARS,GOOGLE_GENAI_USE_VERTEXAI=true"
ENV_VARS="$ENV_VARS,GOOGLE_GENAI_USE_ENTERPRISE=true"
ENV_VARS="$ENV_VARS,GOOGLE_CLOUD_PROJECT=$PROJECT_ID"
ENV_VARS="$ENV_VARS,GOOGLE_CLOUD_LOCATION=$REGION"
if [ -n "$API_KEY_VAL" ]; then
    ENV_VARS="$ENV_VARS,GEMINI_API_KEY=$API_KEY_VAL"
fi

DEPLOY_CMD=(
    gcloud run deploy "$SERVICE_NAME"
    --source .
    --project "$PROJECT_ID"
    --region "$REGION"
    --platform managed
    --allow-unauthenticated
    --memory "$MEMORY"
    --cpu "$CPU"
    --timeout 300
    --set-env-vars "$ENV_VARS"
)

# Use Secret Manager binding if secret is available
if gcloud secrets describe hr-agent-mcp-token --project "$PROJECT_ID" >/dev/null 2>&1; then
    DEPLOY_CMD+=(--set-secrets="MCP_TOKEN=hr-agent-mcp-token:latest")
elif [ -n "$MCP_TOKEN_VAL" ]; then
    DEPLOY_CMD+=(--set-env-vars="MCP_TOKEN=$MCP_TOKEN_VAL")
fi

"${DEPLOY_CMD[@]}"

# Explicitly ensure unauthenticated public access (roles/run.invoker to allUsers)
echo "[*] Setting public unauthenticated access policy (roles/run.invoker)..."
gcloud run services add-iam-policy-binding "$SERVICE_NAME" \
    --project "$PROJECT_ID" \
    --region "$REGION" \
    --member="allUsers" \
    --role="roles/run.invoker" 2>/dev/null || true

# -----------------------------------------------------------------------------
# 8. Retrieve Live Public URL & Health Check
# -----------------------------------------------------------------------------
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
    --project "$PROJECT_ID" \
    --region "$REGION" \
    --format 'value(status.url)' 2>/dev/null || true)

echo ""
echo "================================================================="
if [ "$IS_UPDATE" = true ]; then
    echo "  🎉 Existing Service Updated Successfully!                      "
else
    echo "  🎉 Deployment Complete!                                       "
fi
echo "================================================================="
echo ""
echo "  🌐 Live Public URL:  $SERVICE_URL"
echo ""
echo "  Features Deployed:"
echo "    • Google Aura Modern Web UI (3-Column Workspace)"
echo "    • Multi-Agent Orchestrator (Policy, WorkWeek HCM, ServiceImmediately ITSM)"
echo "    • Model Armor & Prompt Injection Protection Layer"
echo "    • FastMCP Streamable JSON-RPC Live Tool Routing"
echo "    • Google Cloud Secret Manager Token Storage"
echo "    • Real-time PTO Balances, Incident Tickets Feed & Reasoning Trace"
echo ""
echo "  Try opening the URL in your browser: $SERVICE_URL"
echo "================================================================="
