"""MCP Toolsets configuration for WorkWeek and ServiceImmediately FastMCP servers."""
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams
from agents import config


def get_auth_headers() -> dict:
    """Generate headers including X-MCP-Token if configured."""
    headers = {}
    if config.MCP_TOKEN:
        headers["X-MCP-Token"] = config.MCP_TOKEN
    return headers


def create_workweek_mcp_toolset() -> McpToolset:
    """Create McpToolset instance for WorkWeek HCM."""
    url = f"{config.MOCK_SAAS_BASE_URL.rstrip('/')}/work-week/mcp/"
    return McpToolset(
        connection_params=StreamableHTTPConnectionParams(
            url=url,
            headers=get_auth_headers()
        )
    )


def create_serviceimmediately_mcp_toolset() -> McpToolset:
    """Create McpToolset instance for ServiceImmediately ITSM."""
    url = f"{config.MOCK_SAAS_BASE_URL.rstrip('/')}/service-immediately/mcp/"
    return McpToolset(
        connection_params=StreamableHTTPConnectionParams(
            url=url,
            headers=get_auth_headers()
        )
    )
