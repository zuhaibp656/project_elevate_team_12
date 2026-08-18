"""Configuration module for HR Agentic Multi-Agent System (Enterprise Ready)."""
import os
from dotenv import load_dotenv

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(REPO_ROOT, ".env"), override=True)

# Gemini Model Configuration
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# FastMCP Endpoints and Authentication
MOCK_SAAS_BASE_URL = os.getenv(
    "MOCK_SAAS_BASE_URL", 
    "https://mock-saas.aishprabhat.demo.altostrat.com"
)
MCP_TOKEN = os.getenv("MCP_TOKEN", "mcp_CsoiJPHj_FGICu8pf8aFJLIuPc4Kt4AXeOLWyUmwHxQ")

# Google Cloud & Gemini Enterprise Deployment Settings
GOOGLE_GENAI_USE_ENTERPRISE = os.getenv("GOOGLE_GENAI_USE_ENTERPRISE", "true").lower() in ("true", "1", "yes")
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", os.getenv("PROJECT_ID", ""))
GOOGLE_CLOUD_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", os.getenv("REGION", "us-central1"))
IAP_CLIENT_ID = os.getenv("IAP_CLIENT_ID", "")

# Path to local HR Policy Knowledge Base (OKF Bundle)
KNOWLEDGE_DIR = os.getenv("KNOWLEDGE_DIR", os.path.join(REPO_ROOT, "knowledge"))

# App Name for ADK Runner
APP_NAME = "hr_agentic_solution"
