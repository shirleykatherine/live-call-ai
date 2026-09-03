"""
MCP Support Server — exposes ticket creation via MCP protocol.
"""
import asyncio
import json
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from app.tools.ticket_tools import create_support_ticket

app = Server("support-server")


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="create_support_ticket",
            description="Create a support ticket to track a customer issue that requires follow-up",
            inputSchema={
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "string",
                        "description": "Customer identifier",
                    },
                    "issue_type": {
                        "type": "string",
                        "description": (
                            "Type of issue: late_delivery, refund_request, defective_product, "
                            "wrong_item, cancellation, billing_issue, account_issue, escalation, other"
                        ),
                    },
                    "description": {
                        "type": "string",
                        "description": "Detailed description of the issue",
                    },
                    "order_id": {
                        "type": "string",
                        "description": "Related order ID (optional)",
                    },
                    "priority": {
                        "type": "string",
                        "description": "Ticket priority: low, medium, high, urgent",
                        "default": "medium",
                    },
                    "call_id": {
                        "type": "string",
                        "description": "ID of the current support call (optional)",
                    },
                },
                "required": ["customer_id", "issue_type", "description"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name == "create_support_ticket":
        result = create_support_ticket(**arguments)
    else:
        result = {"success": False, "error": f"Unknown tool: {name}"}

    return [types.TextContent(type="text", text=json.dumps(result, indent=2))]


async def run_server():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(run_server())
