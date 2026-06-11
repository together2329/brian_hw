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

_here = Path(__file__).resolve().parent          # scripts/
# 정본(repo/scripts/)이면 repo 루트, vendored(.cursor/scripts/)면 .cursor 의 부모(수신자 프로젝트 루트)
REPO = _here.parent.parent if _here.parent.name == ".cursor" else _here.parent
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


def dispatch(msg: dict):
    """JSON-RPC 메시지 → 응답 payload dict (notification이면 None).

    transport(stdio/HTTP) 무관하게 동일 로직. 호출측이 응답을 어떻게 보낼지 결정.
    """
    method = msg.get("method", "")
    msg_id = msg.get("id")

    def ok(result):
        return {"jsonrpc": "2.0", "id": msg_id, "result": result}

    def err(code, message):
        return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": message}}

    if method.startswith("notifications/"):
        return None
    if method == "initialize":
        client = msg.get("params", {}).get("protocolVersion") or PROTOCOL_VERSION
        return ok({
            "protocolVersion": client,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "atlas-mcp", "version": "1.0.0"},
        })
    if method == "ping":
        return ok({})
    if method == "tools/list":
        return ok({"tools": TOOLS})
    if method == "tools/call":
        params = msg.get("params", {})
        name = params.get("name", "")
        fn = TOOL_FNS.get(name)
        if fn is None:
            return err(-32602, f"unknown tool: {name}")
        try:
            text = fn(params.get("arguments") or {})
        except Exception as exc:  # noqa: BLE001 — 서버는 죽지 않는다
            text = f"[{name}] ERROR: {exc}"
        return ok({
            "content": [{"type": "text", "text": text}],
            "isError": text.startswith("[") and "ERROR" in text.split("\n", 1)[0],
        })
    if msg_id is not None:
        return err(-32601, f"method not found: {method}")
    return None


def run_stdio() -> int:
    """기본 transport: Cursor가 이 프로세스를 spawn해 stdin/stdout으로 대화."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        resp = dispatch(msg)
        if resp is not None:
            sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
            sys.stdout.flush()
    return 0


def run_http(host: str, port: int) -> int:
    """상주 transport: 직접 실행해두면 Cursor가 URL로 접속 (Streamable HTTP).

    POST <path> 로 JSON-RPC 1건을 받아 application/json 1건으로 응답.
    notification(id 없음)은 202. GET /health 로 살아있는지 확인.
    """
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *a):  # 조용히
            pass

        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(
                {"server": "atlas-mcp", "status": "ok", "tools": [t["name"] for t in TOOLS]}
            ).encode())

        def do_POST(self):
            length = int(self.headers.get("Content-Length", 0) or 0)
            body = self.rfile.read(length) if length else b""
            try:
                msg = json.loads(body or b"{}")
            except json.JSONDecodeError:
                self.send_response(400); self.end_headers(); return
            resp = dispatch(msg)
            if resp is None:
                self.send_response(202); self.end_headers(); return
            payload = json.dumps(resp, ensure_ascii=False).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

    server = ThreadingHTTPServer((host, port), Handler)
    sys.stderr.write(f"[atlas-mcp] HTTP listening on http://{host}:{port}  "
                     f"(Cursor mcp.json: {{\"url\": \"http://{host}:{port}/mcp\"}})\n")
    sys.stderr.flush()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if "--http" in argv:
        host = "127.0.0.1"
        port = 8765
        for i, a in enumerate(argv):
            if a == "--port" and i + 1 < len(argv):
                port = int(argv[i + 1])
            elif a == "--host" and i + 1 < len(argv):
                host = argv[i + 1]
        return run_http(host, port)
    return run_stdio()


if __name__ == "__main__":
    sys.exit(main())
