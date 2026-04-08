"""
mcp/manager.py — Multi-server MCP lifecycle manager.

Reads .mcp.json, spawns all configured servers in parallel,
and exposes their tools as AVAILABLE_TOOLS-compatible dicts.

.mcp.json format:
{
  "mcpServers": {
    "z_ai_image": {
      "command": "npx",
      "args": ["-y", "@z_ai/mcp-server"],
      "env": {
        "Z_AI_API_KEY": "${MCP_Z_AI_API_KEY}",
        "Z_AI_MODE": "ZAI"
      }
    }
  }
}

${VAR} in env values is expanded from os.environ.
"""

import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, List, Optional

from mcp.client import MCPStdioClient
from mcp.registry import build_tools_from_server


def _expand_env(value: str) -> str:
    """Replace ${VAR_NAME} with os.environ.get('VAR_NAME', '')."""
    return re.sub(r"\$\{(\w+)\}", lambda m: os.environ.get(m.group(1), ""), value)


class MCPManager:
    """Manages multiple MCP server connections from a .mcp.json config."""

    def __init__(self, config_path: str = ".mcp.json"):
        self.config_path = config_path
        self._clients: Dict[str, MCPStdioClient] = {}
        self._tools: Dict[str, Callable] = {}
        self._schemas: List[dict] = []
        self._errors: Dict[str, str] = {}

    def load(self) -> None:
        """Parse .mcp.json and create MCPStdioClient instances (not started yet)."""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"MCP config not found: {self.config_path}")

        with open(self.config_path) as f:
            cfg = json.load(f)

        for name, server_cfg in cfg.get("mcpServers", {}).items():
            command = [server_cfg["command"]] + server_cfg.get("args", [])
            env = {
                k: _expand_env(v)
                for k, v in server_cfg.get("env", {}).items()
            }
            self._clients[name] = MCPStdioClient(name, command, env)

    def start_all(self) -> None:
        """Start all servers in parallel and discover their tools."""
        if not self._clients:
            return

        def _start_one(name: str, client: MCPStdioClient):
            client.start()
            tools_list = client.list_tools()
            return name, client, tools_list

        with ThreadPoolExecutor(max_workers=len(self._clients)) as pool:
            futures = {
                pool.submit(_start_one, name, client): name
                for name, client in self._clients.items()
            }
            for future in as_completed(futures):
                name = futures[future]
                try:
                    _, client, tools_list = future.result()
                    avail, schemas = build_tools_from_server(client, tools_list)
                    self._tools.update(avail)
                    self._schemas.extend(schemas)
                    print(
                        f"[MCP] {name}: {len(tools_list)} tools loaded"
                        f" ({', '.join(t['name'] for t in tools_list)})",
                        file=sys.stderr,
                    )
                except Exception as e:
                    self._errors[name] = str(e)
                    print(f"[MCP] {name}: failed — {e}", file=sys.stderr)

    def get_tools(self) -> Dict[str, Callable]:
        """Return prefixed tool callables for AVAILABLE_TOOLS."""
        return dict(self._tools)

    def get_schemas(self) -> List[dict]:
        """Return OpenAI-format schemas for tool_schema registry."""
        return list(self._schemas)

    def stop_all(self) -> None:
        """Terminate all server subprocesses."""
        for client in self._clients.values():
            try:
                client.stop()
            except Exception:
                pass
        self._clients.clear()

    def status(self) -> Dict[str, str]:
        """Return health status per server: {'name': 'ok'} or {'name': 'error: ...'}."""
        result = {}
        for name, client in self._clients.items():
            if name in self._errors:
                result[name] = f"error: {self._errors[name]}"
            elif client.is_alive():
                result[name] = "ok"
            else:
                result[name] = "stopped"
        return result
