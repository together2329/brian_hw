"""
mcp/registry.py — Tool name prefixing, schema conversion, wrapper creation.

Handles the mapping between MCP tool definitions and the agent's
AVAILABLE_TOOLS / tool_schema formats.
"""

from typing import Callable, Dict, List, TYPE_CHECKING

if TYPE_CHECKING:
    from mcp.client import MCPStdioClient


def prefix_tool_name(server_name: str, tool_name: str) -> str:
    """Build a collision-safe tool name: 'z_ai_image__analyze_image'."""
    return f"{server_name}__{tool_name}"


def make_tool_wrapper(client: "MCPStdioClient", tool_name: str) -> Callable:
    """Return a Python callable that forwards **kwargs to client.call_tool()."""
    def wrapper(**kwargs) -> str:
        return client.call_tool(tool_name, kwargs)
    wrapper.__name__ = tool_name
    wrapper.__doc__ = f"MCP tool: {client.server_name}/{tool_name}"
    return wrapper


def to_openai_schema(server_name: str, mcp_tool: dict) -> dict:
    """Convert an MCP tool definition to OpenAI function-calling schema format.

    The tool name is prefixed to avoid collisions across servers.
    """
    prefixed_name = prefix_tool_name(server_name, mcp_tool["name"])
    input_schema = mcp_tool.get("inputSchema", {"type": "object", "properties": {}})
    # Strip $schema field if present — OpenAI API rejects it
    input_schema = {k: v for k, v in input_schema.items() if k != "$schema"}
    return {
        "type": "function",
        "function": {
            "name": prefixed_name,
            "description": mcp_tool.get("description", ""),
            "parameters": input_schema,
        },
    }


def build_tools_from_server(
    client: "MCPStdioClient",
    mcp_tools: List[dict],
) -> tuple[Dict[str, Callable], List[dict]]:
    """
    Given a connected client and its tool list, return:
      - available_tools: {prefixed_name: callable}
      - schemas: [openai_schema, ...]
    """
    available: Dict[str, Callable] = {}
    schemas: List[dict] = []

    for mcp_tool in mcp_tools:
        prefixed = prefix_tool_name(client.server_name, mcp_tool["name"])
        available[prefixed] = make_tool_wrapper(client, mcp_tool["name"])
        schemas.append(to_openai_schema(client.server_name, mcp_tool))

    return available, schemas
