"""
MCP Order Server — exposes order management capabilities via MCP protocol.
"""
import asyncio
import json
import logging
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from app.tools.order_tools import get_order_status, get_customer_orders, get_available_resolution_options

logger = logging.getLogger(__name__)

app = Server("order-server")


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_order_status",
            description="Get detailed status and tracking information for a specific order",
            inputSchema={
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "The unique order identifier (e.g., ORD-10001)",
                    }
                },
                "required": ["order_id"],
            },
        ),
        types.Tool(
            name="get_customer_orders",
            description="Get all orders for a specific customer",
            inputSchema={
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "string",
                        "description": "The customer's unique identifier",
                    }
                },
                "required": ["customer_id"],
            },
        ),
        types.Tool(
            name="get_available_resolution_options",
            description="Get available resolution options for a specific order based on its current status",
            inputSchema={
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "The order ID to get resolution options for",
                    }
                },
                "required": ["order_id"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name == "get_order_status":
        result = get_order_status(arguments["order_id"])
    elif name == "get_customer_orders":
        result = get_customer_orders(arguments["customer_id"])
    elif name == "get_available_resolution_options":
        result = get_available_resolution_options(arguments["order_id"])
    else:
        result = {"success": False, "error": f"Unknown tool: {name}"}

    return [types.TextContent(type="text", text=json.dumps(result, indent=2))]


async def run_server():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(run_server())
