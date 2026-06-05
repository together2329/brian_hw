import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def test_mcp_call_tool_preserves_structured_content(monkeypatch):
    from common_ai_agent.mcp.client import MCPStdioClient

    client = MCPStdioClient("codex", ["codex", "mcp-server"])

    def fake_rpc(method, params):
        assert method == "tools/call"
        assert params == {"name": "codex", "arguments": {"prompt": "hi"}}
        return {
            "result": {
                "content": [{"type": "text", "text": "OK"}],
                "structuredContent": {"threadId": "thread-123", "content": "OK"},
            }
        }

    monkeypatch.setattr(client, "_rpc", fake_rpc)

    result = client.call_tool_result("codex", {"prompt": "hi"})

    assert result.text == "OK"
    assert result.structured_content == {"threadId": "thread-123", "content": "OK"}
    observation = json.loads(result.to_observation())
    assert observation["content"] == "OK"
    assert observation["structuredContent"]["threadId"] == "thread-123"


def test_mcp_call_tool_returns_plain_text_without_structured_content(monkeypatch):
    from common_ai_agent.mcp.client import MCPStdioClient

    client = MCPStdioClient("filesystem", ["fake"])

    monkeypatch.setattr(
        client,
        "_rpc",
        lambda _method, _params: {"result": {"content": [{"type": "text", "text": "plain"}]}},
    )

    assert client.call_tool("read_file", {"path": "a.txt"}) == "plain"
