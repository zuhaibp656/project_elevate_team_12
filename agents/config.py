"""Configuration module for HR Agentic Multi-Agent System."""
import os
from dotenv import load_dotenv

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(REPO_ROOT, ".env"), override=True)

# Gemini Model configuration (Supports 2.5/3.5 Flash or Pro)
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# FastMCP Endpoints and Authentication
MOCK_SAAS_BASE_URL = os.getenv(
    "MOCK_SAAS_BASE_URL", 
    "https://mock-saas.aishprabhat.demo.altostrat.com"
)
MCP_TOKEN = os.getenv("MCP_TOKEN", "")

# Path to local HR Policy Knowledge Base (OKF Bundle)
KNOWLEDGE_DIR = os.getenv("KNOWLEDGE_DIR", os.path.join(REPO_ROOT, "knowledge"))

# App Name for ADK Runner
APP_NAME = "hr_agentic_solution"
