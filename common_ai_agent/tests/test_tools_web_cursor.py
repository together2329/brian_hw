from __future__ import annotations

import subprocess
from types import SimpleNamespace

from core import tool_schema
from core import tools_web


def _cursor_stdout(text: str) -> str:
    return (
        '{"type":"assistant","timestamp_ms":1,'
        '"message":{"content":[{"type":"text","text":'
        + repr(text).replace("'", '"')
        + '}]}}\n'
    )


def test_web_search_forces_cursor_cli_even_when_engine_requests_firecrawl(monkeypatch):
    calls = []

    monkeypatch.setattr(tools_web.shutil, "which", lambda name: "/usr/bin/cursor-agent")

    def fake_run(cmd, **kwargs):
        calls.append((cmd, kwargs))
        return SimpleNamespace(returncode=0, stdout=_cursor_stdout("engine: cursor-cli\n- result"), stderr="")

    monkeypatch.setattr(tools_web.subprocess, "run", fake_run)

    out = tools_web.web_search("latest PCIe spec", limit=3, engine="firecrawl")

    assert "engine: cursor-cli" in out
    cmd, kwargs = calls[0]
    assert cmd[0] == "/usr/bin/cursor-agent"
    assert "--yolo" in cmd
    assert "firecrawl" not in " ".join(cmd).lower()
    assert kwargs["timeout"] == 120


def test_websearch_alias_uses_web_search(monkeypatch):
    seen = {}

    def fake_web_search(**kwargs):
        seen.update(kwargs)
        return "ok"

    monkeypatch.setattr(tools_web, "web_search", fake_web_search)

    assert tools_web.websearch(query="openai docs", limit=2) == "ok"
    assert seen["query"] == "openai docs"
    assert seen["limit"] == 2


def test_web_search_reports_missing_cursor_agent(monkeypatch):
    monkeypatch.setattr(tools_web.shutil, "which", lambda name: None)

    out = tools_web.web_search("anything")

    assert "cursor-agent not found" in out


def test_web_tool_registry_and_schema_include_websearch_alias():
    assert tools_web.WEB_TOOLS["websearch"] is tools_web.websearch
    names = {
        schema["function"]["name"]
        for schema in tool_schema.get_tool_schemas(["web_search", "websearch"])
    }
    assert names == {"web_search", "websearch"}


def test_web_search_timeout_message(monkeypatch):
    monkeypatch.setattr(tools_web.shutil, "which", lambda name: "/usr/bin/cursor-agent")

    def fake_run(cmd, **kwargs):
        raise subprocess.TimeoutExpired(cmd=cmd, timeout=kwargs["timeout"])

    monkeypatch.setattr(tools_web.subprocess, "run", fake_run)

    assert "timed out" in tools_web.web_search("slow query")
