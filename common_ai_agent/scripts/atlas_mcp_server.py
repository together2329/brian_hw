#!/usr/bin/env python3
"""atlas_mcp_server.py — Cursor/Claude 가 ATLAS 지식을 query 하는 stdio MCP 서버.

newline-delimited JSON-RPC 2.0 (MCP stdio transport). 의존성 없음 (stdlib only).

Tools:
  ontology_query    — ontology/platform.db 에 SELECT (read-only; 단위/spine/스냅샷 이력)
  wiki_search       — doc/wiki + <ip>/wiki 전체에서 본문 검색 (file:line 매치)
  external_db_query — core.tools.external_db_query 위임 (ATLAS_EXTERNAL_DB_* env 계약)

등록: .cursor/mcp.json (Cursor) / claude mcp add (Claude Code)
검증: tests/test_atlas_mcp_server.py (handshake + tools/list + tools/call 계약)
"""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PROTOCOL_VERSION = "2025-06-18"
MAX_ROWS = 50
MAX_MATCHES = 40

TOOLS = [
    {
        "name": "ontology_query",
        "description": (
            "Run a read-only SELECT against the platform ontology SQLite DB "
            "(tables: snapshots, unit_state, unit_files, unit_tests, orphans, spine_state). "
            "Use to ask about DevUnit maturity, obligations, evidence, history."),
        "inputSchema": {
            "type": "object",
            "properties": {"sql": {"type": "string", "description": "SELECT statement"}},
            "required": ["sql"],
        },
    },
    {
        "name": "wiki_search",
        "description": (
            "Search the project wikis (doc/wiki/*.md and every <ip>/wiki/*.md) for a "
            "case-insensitive substring. Returns file:line matches."),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "ip_dir": {"type": "string", "description": "optional IP dir to also search"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "rtl_db_query",
        "description": (
            "PRIMARY: query the external RTL design knowledge DB (prior projects' RTL, "
            "modules, interfaces) configured via ATLAS_RTL_DB_QUERY / ATLAS_EXTERNAL_DB_QUERY "
            "— graph walk by topic."),
        "inputSchema": {
            "type": "object",
            "properties": {
                "topic": {"type": "string"},
                "depth": {"type": "integer", "default": 3},
                "max_nodes": {"type": "integer", "default": 12},
            },
            "required": ["topic"],
        },
    },
    {
        "name": "rtl_db_wiki",
        "description": (
            "Walk the external RTL DB wiki corpus (ATLAS_RTL_DB_WIKI / ATLAS_EXTERNAL_DB_WIKI) "
            "for design knowledge about an IP or topic from prior projects."),
        "inputSchema": {
            "type": "object",
            "properties": {
                "ip": {"type": "string", "default": ""},
                "topic": {"type": "string", "default": ""},
                "depth": {"type": "integer", "default": 2},
                "max_nodes": {"type": "integer", "default": 12},
            },
        },
    },
]


def _ontology_db() -> Path:
    override = os.environ.get("ATLAS_ONTOLOGY_DB")
    return Path(override) if override else REPO / "ontology" / "platform.db"


def tool_ontology_query(args: dict) -> str:
    sql = str(args.get("sql", "")).strip().rstrip(";")
    if not sql.lower().startswith("select"):
        return "[ontology_query] ERROR: SELECT statements only."
    db = _ontology_db()
    if not db.is_file():
        return f"[ontology_query] ERROR: DB not found at {db} (run scripts/platform_ontology.py scan)."
    try:
        uri = f"file:{db}?mode=ro"
        con = sqlite3.connect(uri, uri=True, timeout=5)
        cur = con.execute(sql)
        cols = [d[0] for d in cur.description or []]
        rows = cur.fetchmany(MAX_ROWS)
        con.close()
    except sqlite3.Error as exc:
        return f"[ontology_query] ERROR: {exc}"
    lines = [" | ".join(cols)] if cols else []
    lines += [" | ".join(str(v) for v in row) for row in rows]
    if len(rows) == MAX_ROWS:
        lines.append(f"... (truncated at {MAX_ROWS} rows)")
    return "\n".join(lines) if lines else "(no rows)"


def _wiki_files(ip_dir: str = ""):
    roots = [REPO / "doc" / "wiki"]
    if ip_dir:
        roots.append(Path(ip_dir) / "wiki")
    else:
        # repo 바로 아래 IP 폴더들의 wiki (깊이 제한 — 전체 rglob 은 과도)
        roots.extend(sorted(REPO.glob("*/wiki")))
        roots.extend(sorted(REPO.glob("*/*/wiki")))
    for root in roots:
        if root.is_dir():
            yield from sorted(root.glob("*.md"))


def tool_wiki_search(args: dict) -> str:
    query = str(args.get("query", "")).strip()
    if not query:
        return "[wiki_search] ERROR: empty query."
    needle = query.lower()
    matches = []
    for path in _wiki_files(str(args.get("ip_dir", "") or "")):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            if needle in line.lower():
                try:
                    rel = path.relative_to(REPO)
                except ValueError:
                    rel = path
                matches.append(f"{rel}:{lineno}: {line.strip()[:160]}")
                if len(matches) >= MAX_MATCHES:
                    return "\n".join(matches + [f"... (truncated at {MAX_MATCHES})"])
    return "\n".join(matches) if matches else f"(no matches for {query!r})"


def _delegate_core(call_expr: str, label: str) -> str:
    """core.tools 함수를 격리 subprocess 로 위임 (무거운 import 를 서버 밖으로)."""
    try:
        proc = subprocess.run(
            [sys.executable, "-c", f"from core.tools import wiki_query, external_db_query;print({call_expr})"],
            cwd=str(REPO), capture_output=True, text=True, timeout=90)
    except subprocess.TimeoutExpired:
        return f"[{label}] ERROR: timed out."
    if proc.returncode != 0:
        return f"[{label}] ERROR: {proc.stderr.strip()[-400:]}"
    return proc.stdout.strip() or "(empty result)"


def tool_rtl_db_query(args: dict) -> str:
    topic = str(args.get("topic", "")).strip()
    if not topic:
        return "[rtl_db_query] ERROR: empty topic."
    return _delegate_core(
        f"external_db_query(topic={topic!r}, depth={int(args.get('depth', 3))}, "
        f"max_nodes={int(args.get('max_nodes', 12))})", "rtl_db_query")


def tool_rtl_db_wiki(args: dict) -> str:
    ip = str(args.get("ip", "")).strip()
    topic = str(args.get("topic", "")).strip()
    if not ip and not topic:
        return "[rtl_db_wiki] ERROR: give ip and/or topic."
    return _delegate_core(
        f"wiki_query(ip={ip!r}, topic={topic!r}, depth={int(args.get('depth', 2))}, "
        f"max_nodes={int(args.get('max_nodes', 12))})", "rtl_db_wiki")


TOOL_FNS = {
    "ontology_query": tool_ontology_query,
    "wiki_search": tool_wiki_search,
    "rtl_db_query": tool_rtl_db_query,
    "rtl_db_wiki": tool_rtl_db_wiki,
}


def _reply(msg_id, result=None, error=None) -> None:
    payload = {"jsonrpc": "2.0", "id": msg_id}
    if error is not None:
        payload["error"] = error
    else:
        payload["result"] = result
    sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def handle(msg: dict) -> None:
    method = msg.get("method", "")
    msg_id = msg.get("id")
    if method.startswith("notifications/"):
        return  # no response to notifications
    if method == "initialize":
        client = msg.get("params", {}).get("protocolVersion") or PROTOCOL_VERSION
        _reply(msg_id, {
            "protocolVersion": client,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "atlas-mcp", "version": "1.0.0"},
        })
        return
    if method == "ping":
        _reply(msg_id, {})
        return
    if method == "tools/list":
        _reply(msg_id, {"tools": TOOLS})
        return
    if method == "tools/call":
        params = msg.get("params", {})
        name = params.get("name", "")
        fn = TOOL_FNS.get(name)
        if fn is None:
            _reply(msg_id, error={"code": -32602, "message": f"unknown tool: {name}"})
            return
        try:
            text = fn(params.get("arguments") or {})
        except Exception as exc:  # noqa: BLE001 — 서버는 죽지 않는다
            text = f"[{name}] ERROR: {exc}"
        _reply(msg_id, {
            "content": [{"type": "text", "text": text}],
            "isError": text.startswith("[") and "ERROR" in text.split("\n", 1)[0],
        })
        return
    if msg_id is not None:
        _reply(msg_id, error={"code": -32601, "message": f"method not found: {method}"})


def main() -> int:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        handle(msg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
