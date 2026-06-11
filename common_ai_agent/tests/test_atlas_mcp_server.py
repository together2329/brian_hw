"""atlas MCP 서버 검증 — JSON-RPC stdio 계약 (handshake / tools/list / tools/call).

evidence for: OBL_ATLAS_MCP_SERVER
"""

from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SERVER = REPO / "scripts" / "atlas_mcp_server.py"


def _rpc(messages, env_extra=None):
    """서버를 띄워 메시지들을 보내고 id별 응답 dict 를 돌려준다."""
    env = {"PATH": "/usr/bin:/bin"}
    if env_extra:
        env.update(env_extra)
    stdin = "".join(json.dumps(m) + "\n" for m in messages)
    proc = subprocess.run(
        [sys.executable, str(SERVER)], input=stdin,
        capture_output=True, text=True, env=env, timeout=30)
    assert proc.returncode == 0, proc.stderr
    replies = {}
    for line in proc.stdout.splitlines():
        if line.strip():
            msg = json.loads(line)
            replies[msg.get("id")] = msg
    return replies


def _handshake():
    return [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize",
         "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                    "clientInfo": {"name": "pytest", "version": "0"}}},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
    ]


def test_initialize_and_tools_list():
    replies = _rpc(_handshake() + [{"jsonrpc": "2.0", "id": 2, "method": "tools/list"}])
    init = replies[1]["result"]
    assert init["serverInfo"]["name"] == "atlas-mcp"
    assert init["protocolVersion"] == "2025-06-18"
    tools = {t["name"] for t in replies[2]["result"]["tools"]}
    assert tools == {"ontology_query", "wiki_search", "rtl_db_query", "rtl_db_wiki"}
    for t in replies[2]["result"]["tools"]:
        assert t["description"] and t["inputSchema"]["type"] == "object"


def test_ontology_query_select(tmp_path):
    db = tmp_path / "ont.db"
    con = sqlite3.connect(db)
    con.execute("CREATE TABLE unit_state (unit_id TEXT, level INTEGER)")
    con.execute("INSERT INTO unit_state VALUES ('agent.memory', 2)")
    con.commit(); con.close()
    replies = _rpc(_handshake() + [
        {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
         "params": {"name": "ontology_query",
                    "arguments": {"sql": "SELECT unit_id, level FROM unit_state"}}}],
        env_extra={"ATLAS_ONTOLOGY_DB": str(db)})
    text = replies[2]["result"]["content"][0]["text"]
    assert "agent.memory | 2" in text
    assert not replies[2]["result"]["isError"]


def test_ontology_query_rejects_non_select(tmp_path):
    """KILL-PROOF: 쓰기 SQL 은 거부해야 한다."""
    db = tmp_path / "ont.db"
    sqlite3.connect(db).close()
    replies = _rpc(_handshake() + [
        {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
         "params": {"name": "ontology_query",
                    "arguments": {"sql": "DROP TABLE unit_state"}}}],
        env_extra={"ATLAS_ONTOLOGY_DB": str(db)})
    text = replies[2]["result"]["content"][0]["text"]
    assert "SELECT statements only" in text
    assert replies[2]["result"]["isError"]


def test_wiki_search_finds_known_doc():
    replies = _rpc(_handshake() + [
        {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
         "params": {"name": "wiki_search",
                    "arguments": {"query": "Platform Ontology"}}}])
    text = replies[2]["result"]["content"][0]["text"]
    assert "platform-ontology" in text  # doc/wiki/platform-ontology.md 매치


def test_wiki_search_covers_ip_wiki(tmp_path):
    ip = tmp_path / "uart_v1"
    (ip / "wiki").mkdir(parents=True)
    (ip / "wiki" / "log.md").write_text(
        "---\ntitle: t\nip: uart_v1\ncategory: ip-wiki\n---\n# log\nUNIQUE_NEEDLE_XYZ here\n",
        encoding="utf-8")
    replies = _rpc(_handshake() + [
        {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
         "params": {"name": "wiki_search",
                    "arguments": {"query": "UNIQUE_NEEDLE_XYZ", "ip_dir": str(ip)}}}])
    text = replies[2]["result"]["content"][0]["text"]
    assert "UNIQUE_NEEDLE_XYZ" in text


def test_unknown_tool_and_method_errors():
    replies = _rpc(_handshake() + [
        {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
         "params": {"name": "nope", "arguments": {}}},
        {"jsonrpc": "2.0", "id": 3, "method": "no/such/method"}])
    assert replies[2]["error"]["code"] == -32602
    assert replies[3]["error"]["code"] == -32601


def test_mcp_json_registers_server():
    doc = json.loads((REPO / ".cursor" / "mcp.json").read_text(encoding="utf-8"))
    server = doc["mcpServers"]["rtl-db"]
    script = server["args"][0]
    assert (REPO / script).is_file(), f"mcp.json references missing server: {script}"


# ---------- HTTP transport (상주 서버 모드) ----------

def test_http_mode_serves_requests(tmp_path):
    """--http 모드: 상주 서버를 띄워 /health + JSON-RPC POST 가 동작."""
    import time
    import urllib.request
    port = 8791
    proc = subprocess.Popen(
        [sys.executable, str(SERVER), "--http", "--port", str(port)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        env={"PATH": "/usr/bin:/bin"})
    try:
        # 바인딩될 때까지 폴링 (sleep 대신 재시도)
        base = f"http://127.0.0.1:{port}"
        health = None
        for _ in range(50):
            try:
                with urllib.request.urlopen(base + "/health", timeout=1) as r:
                    health = json.loads(r.read())
                    break
            except Exception:
                time.sleep(0.1)
        assert health and health["server"] == "atlas-mcp" and health["status"] == "ok"

        def post(obj):
            req = urllib.request.Request(
                base + "/mcp", data=json.dumps(obj).encode(),
                headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=5) as r:
                return json.loads(r.read())

        init = post({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                     "params": {"protocolVersion": "2025-06-18"}})
        assert init["result"]["serverInfo"]["name"] == "atlas-mcp"
        tools = post({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        assert {t["name"] for t in tools["result"]["tools"]} == \
            {"ontology_query", "wiki_search", "rtl_db_query", "rtl_db_wiki"}
        call = post({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                     "params": {"name": "wiki_search",
                                "arguments": {"query": "Platform Ontology"}}})
        assert "platform-ontology" in call["result"]["content"][0]["text"]
    finally:
        proc.terminate()
        proc.wait(timeout=5)
