"""
MCP Knowledge Server — exposes policy search via MCP protocol.
"""
import asyncio
import json
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from app.tools.policy_tools import search_policy

app = Server("knowledge-server")


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="search_policy",
            description=(
                "Search the company knowledge base for policy information. "
                "Use this to find information about refunds, shipping, returns, "
                "cancellations, escalation procedures, and customer support guidelines."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The policy topic or question to search for",
                    },
                    "n_results": {
                        "type": "integer",
                        "description": "Number of results to return (default: 3)",
                        "default": 3,
                    },
                },
                "required": ["query"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name == "search_policy":
        result = search_policy(
            query=arguments["query"],
            n_results=arguments.get("n_results", 3),
        )
    else:
        result = {"success": False, "error": f"Unknown tool: {name}"}

    return [types.TextContent(type="text", text=json.dumps(result, indent=2))]


async def run_server():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(run_server())
