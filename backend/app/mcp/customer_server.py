"""
MCP Customer Server — exposes customer lookup capabilities via MCP protocol.
This server runs in-process and is used by the LangGraph agent.
"""
import asyncio
import json
import logging
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from app.tools.customer_tools import get_customer, search_customer_by_email

logger = logging.getLogger(__name__)

app = Server("customer-server")


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_customer",
            description="Retrieve customer information by their unique customer ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "string",
                        "description": "The unique customer identifier (e.g., CUST-001)",
                    }
                },
                "required": ["customer_id"],
            },
        ),
        types.Tool(
            name="search_customer_by_email",
            description="Find a customer by their email address",
            inputSchema={
                "type": "object",
                "properties": {
                    "email": {
                        "type": "string",
                        "description": "Customer email address or partial email",
                    }
                },
                "required": ["email"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name == "get_customer":
        result = get_customer(arguments["customer_id"])
    elif name == "search_customer_by_email":
        result = search_customer_by_email(arguments["email"])
    else:
        result = {"success": False, "error": f"Unknown tool: {name}"}

    return [types.TextContent(type="text", text=json.dumps(result, indent=2))]


async def run_server():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(run_server())
