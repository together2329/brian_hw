"""
mcp/ — Lightweight MCP (Model Context Protocol) client module.

Loads MCP servers defined in .mcp.json and registers their tools
dynamically into the agent's AVAILABLE_TOOLS and tool_schema registry.

Usage (from core/tools.py):
    import mcp
    manager = mcp.init(".mcp.json")
    AVAILABLE_TOOLS.update(manager.get_tools())

Adding a new MCP server: edit .mcp.json only — no code changes needed.
"""

from typing import Optional
from mcp.manager import MCPManager

_manager: Optional[MCPManager] = None


def get_manager() -> Optional[MCPManager]:
    """Return the active MCPManager singleton, or None if not initialized."""
    return _manager


def init(config_path: str = ".mcp.json") -> MCPManager:
    """Initialize MCP: load config, start all servers, return manager."""
    global _manager
    _manager = MCPManager(config_path)
    _manager.load()
    _manager.start_all()
    return _manager


def shutdown() -> None:
    """Stop all MCP server subprocesses."""
    global _manager
    if _manager:
        _manager.stop_all()
        _manager = None
