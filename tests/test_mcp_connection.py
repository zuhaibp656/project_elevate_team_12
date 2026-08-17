"""Test script to verify MCP connection and tool discovery on Mock SaaS."""
import os
import sys
import asyncio
import httpx
from dotenv import load_dotenv

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(REPO_ROOT, ".env"), override=True)

BASE_URL = os.getenv("MOCK_SAAS_BASE_URL", "https://mock-saas.aishprabhat.demo.altostrat.com")
MCP_TOKEN = os.getenv("MCP_TOKEN", "")

print(f"Testing connectivity to {BASE_URL} with token {MCP_TOKEN[:8]}...")

async def check_endpoints():
    headers = {"X-MCP-Token": MCP_TOKEN}
    async with httpx.AsyncClient(headers=headers, timeout=10.0) as client:
        # 1. Health check
        try:
            r = await client.get(f"{BASE_URL}/healthz")
            print(f"GET /healthz status: {r.status_code}")
        except Exception as e:
            print(f"Healthz error: {e}")

        # 2. List MCP tokens
        try:
            r = await client.get(f"{BASE_URL}/api/mcp-tokens")
            print(f"GET /api/mcp-tokens status: {r.status_code} - body: {r.text[:200]}")
        except Exception as e:
            print(f"MCP tokens list error: {e}")

        # 3. Test WorkWeek MCP endpoint
        try:
            r = await client.post(f"{BASE_URL}/work-week/mcp/", json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list",
                "params": {}
            })
            print(f"POST /work-week/mcp/ status: {r.status_code} - body: {r.text[:300]}")
        except Exception as e:
            print(f"WorkWeek MCP error: {e}")

        # 4. Test ServiceImmediately MCP endpoint
        try:
            r = await client.post(f"{BASE_URL}/service-immediately/mcp/", json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list",
                "params": {}
            })
            print(f"POST /service-immediately/mcp/ status: {r.status_code} - body: {r.text[:300]}")
        except Exception as e:
            print(f"ServiceImmediately MCP error: {e}")

if __name__ == "__main__":
    asyncio.run(check_endpoints())
