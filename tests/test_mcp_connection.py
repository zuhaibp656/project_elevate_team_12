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

print(f"Testing connectivity to {BASE_URL} with token {MCP_TOKEN[:10]}...")

async def check_endpoints():
    headers = {
        "X-MCP-Token": MCP_TOKEN,
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json"
    }
    async with httpx.AsyncClient(headers=headers, timeout=15.0) as client:
        # 1. Test WorkWeek MCP initialize & tools/list
        try:
            r = await client.post(f"{BASE_URL}/work-week/mcp/", json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list",
                "params": {}
            })
            print(f"\n[✓] WorkWeek MCP (status {r.status_code}):")
            print(r.text[:500])
        except Exception as e:
            print(f"WorkWeek MCP error: {e}")

        # 2. Test ServiceImmediately MCP tools/list
        try:
            r = await client.post(f"{BASE_URL}/service-immediately/mcp/", json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {}
            })
            print(f"\n[✓] ServiceImmediately MCP (status {r.status_code}):")
            print(r.text[:500])
        except Exception as e:
            print(f"ServiceImmediately MCP error: {e}")

if __name__ == "__main__":
    asyncio.run(check_endpoints())
