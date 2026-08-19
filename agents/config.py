"""Configuration module for HR Agentic Multi-Agent System (Enterprise Ready, Multi-User Isolation & Secret Manager Integration)."""
import os
from contextvars import ContextVar
from dotenv import load_dotenv

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(REPO_ROOT, ".env"), override=True)

# Google Cloud & Project Settings
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", os.getenv("PROJECT_ID", ""))
GOOGLE_CLOUD_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", os.getenv("REGION", "us-central1"))
GOOGLE_GENAI_USE_ENTERPRISE = os.getenv("GOOGLE_GENAI_USE_ENTERPRISE", "false").lower() in ("true", "1", "yes")
IAP_CLIENT_ID = os.getenv("IAP_CLIENT_ID", "")


def get_secret(secret_name: str, env_fallback: str, default: str = "") -> str:
    """Retrieve secret from environment variable first, or dynamically from Google Cloud Secret Manager if on GCP."""
    val = os.getenv(env_fallback, "")
    if val and val.strip():
        return val.strip()

    # Try Google Cloud Secret Manager if project ID is available
    if GOOGLE_CLOUD_PROJECT:
        try:
            from google.cloud import secretmanager
            client = secretmanager.SecretManagerServiceClient()
            secret_path = f"projects/{GOOGLE_CLOUD_PROJECT}/secrets/{secret_name}/versions/latest"
            response = client.access_secret_version(request={"name": secret_path})
            payload = response.payload.data.decode("UTF-8").strip()
            if payload:
                return payload
        except Exception:
            pass

    return default


# Gemini Model Configuration
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# FastMCP Endpoints and Authentication
MOCK_SAAS_BASE_URL = os.getenv(
    "MOCK_SAAS_BASE_URL", 
    "https://mock-saas.aishprabhat.demo.altostrat.com"
)
MCP_TOKEN = get_secret("hr-agent-mcp-token", "MCP_TOKEN", "")

# ---------------------------------------------------------------------------
# Dynamic ContextVar for Per-Request Multi-User Token & Identity Isolation
# ---------------------------------------------------------------------------
ACTIVE_MCP_TOKEN_CV: ContextVar[str] = ContextVar("active_mcp_token", default="")
ACTIVE_USER_ID_CV: ContextVar[str] = ContextVar("active_user_id", default="")
ACTIVE_USER_EMAIL_CV: ContextVar[str] = ContextVar("active_user_email", default="")


def get_current_mcp_token() -> str:
    """Get the active MCP token for the currently executing async request or fallback to default secret."""
    token = ACTIVE_MCP_TOKEN_CV.get()
    if token and token.strip():
        return token.strip()
    return MCP_TOKEN


def get_current_user_id() -> str:
    """Get the active employee ID for the currently executing request or default to EMP-380."""
    uid = ACTIVE_USER_ID_CV.get()
    if uid and uid.strip():
        return uid.strip()
    return "EMP-380"


# Path to local HR Policy Knowledge Base (OKF Bundle)
KNOWLEDGE_DIR = os.getenv("KNOWLEDGE_DIR", os.path.join(REPO_ROOT, "knowledge"))

# App Name for ADK Runner
APP_NAME = "hr_agentic_solution"
