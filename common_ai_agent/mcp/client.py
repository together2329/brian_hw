"""
mcp/client.py — Low-level MCP stdio client.

Implements JSON-RPC 2.0 over subprocess stdin/stdout following the
Model Context Protocol spec. Zero external dependencies (stdlib only).

Protocol flow:
  → initialize
  ← result
  → notifications/initialized
  → tools/list
  ← {tools: [{name, description, inputSchema}]}
  → tools/call {name, arguments}
  ← {content: [{type:"text", text:"..."}]}
"""

import json
import subprocess
import threading
from typing import Dict, List, Optional


class MCPStdioClient:
    """MCP client that communicates with a server over stdin/stdout."""

    def __init__(self, server_name: str, command: List[str], env: Optional[Dict[str, str]] = None):
        self.server_name = server_name
        self.command = command
        self.env = env  # merged with os.environ in start()
        self._proc: Optional[subprocess.Popen] = None
        self._lock = threading.Lock()
        self._req_id = 0
        self._tools: List[dict] = []

    def start(self) -> None:
        """Spawn the server process and perform the MCP initialize handshake."""
        import os
        merged_env = {**os.environ, **(self.env or {})}
        self._proc = subprocess.Popen(
            self.command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=merged_env,
        )
        # Initialize handshake
        self._rpc("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "common_ai_agent", "version": "1.0"},
        })
        # Send initialized notification (no response expected)
        self._send({"jsonrpc": "2.0", "method": "notifications/initialized"})

    def list_tools(self) -> List[dict]:
        """Fetch the list of tools from the MCP server."""
        resp = self._rpc("tools/list", {})
        self._tools = resp.get("result", {}).get("tools", [])
        return self._tools

    def call_tool(self, tool_name: str, arguments: dict) -> str:
        """Call a tool and return its text output."""
        resp = self._rpc("tools/call", {"name": tool_name, "arguments": arguments})
        if "error" in resp:
            err = resp["error"]
            raise RuntimeError(f"MCP tool error ({err.get('code')}): {err.get('message')}")
        content = resp.get("result", {}).get("content", [])
        parts = [c.get("text", "") for c in content if c.get("type") == "text"]
        return "\n".join(parts)

    def stop(self) -> None:
        """Terminate the server subprocess."""
        if self._proc:
            try:
                self._proc.terminate()
                self._proc.wait(timeout=5)
            except Exception:
                try:
                    self._proc.kill()
                except Exception:
                    pass
            self._proc = None

    def is_alive(self) -> bool:
        return self._proc is not None and self._proc.poll() is None

    # ── Private ──────────────────────────────────────────────────────────────

    def _next_id(self) -> int:
        self._req_id += 1
        return self._req_id

    def _send(self, msg: dict) -> None:
        data = (json.dumps(msg) + "\n").encode()
        self._proc.stdin.write(data)
        self._proc.stdin.flush()

    def _recv(self) -> dict:
        while True:
            line = self._proc.stdout.readline()
            if not line:
                raise EOFError(f"[{self.server_name}] Server process ended unexpectedly")
            line = line.strip()
            if line:
                return json.loads(line.decode())

    def _rpc(self, method: str, params: dict) -> dict:
        """Send a JSON-RPC request and return the matching response."""
        with self._lock:
            req_id = self._next_id()
            self._send({"jsonrpc": "2.0", "id": req_id, "method": method, "params": params})
            # Drain responses until we get ours (ignore out-of-band notifications)
            while True:
                resp = self._recv()
                if resp.get("id") == req_id:
                    return resp
