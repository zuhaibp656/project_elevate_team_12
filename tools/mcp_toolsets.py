"""MCP Toolsets configuration for WorkWeek and ServiceImmediately FastMCP servers."""
from agents import config

try:
    from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
    from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams
    HAS_ADK_MCP = True
except Exception:
    HAS_ADK_MCP = False
    McpToolset = None
    StreamableHTTPConnectionParams = None


def get_auth_headers() -> dict:
    """Generate headers including X-MCP-Token and Accept headers for FastMCP."""
    headers = {
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json",
    }
    if config.MCP_TOKEN:
        headers["X-MCP-Token"] = config.MCP_TOKEN
    return headers


def create_workweek_mcp_toolset():
    """Create McpToolset instance for WorkWeek HCM if available."""
    if not HAS_ADK_MCP:
        return None
    url = f"{config.MOCK_SAAS_BASE_URL.rstrip('/')}/work-week/mcp/"
    return McpToolset(
        connection_params=StreamableHTTPConnectionParams(
            url=url,
            headers=get_auth_headers()
        )
    )


def create_serviceimmediately_mcp_toolset():
    """Create McpToolset instance for ServiceImmediately ITSM if available."""
    if not HAS_ADK_MCP:
        return None
    url = f"{config.MOCK_SAAS_BASE_URL.rstrip('/')}/service-immediately/mcp/"
    return McpToolset(
        connection_params=StreamableHTTPConnectionParams(
            url=url,
            headers=get_auth_headers()
        )
    )
