import sys
import importlib
from pathlib import Path
from types import SimpleNamespace


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))


def test_read_image_uses_current_llm_input_image_blocks(tmp_path, monkeypatch):
    image_path = tmp_path / "clip.png"
    image_path.write_bytes(b"\x89PNG\r\n")
    cfg = SimpleNamespace(
        ENABLE_IMAGE_READ=True,
        IMAGE_READ_MAX_SIZE=8,
        MODEL_NAME="gpt-5.5-codex",
    )
    calls = []

    def fake_call_llm_raw(**kwargs):
        calls.append(kwargs)
        return "The screenshot contains a small PNG header."

    monkeypatch.delenv("IMAGE_READ_MODEL", raising=False)
    monkeypatch.setitem(sys.modules, "config", cfg)
    monkeypatch.setitem(
        sys.modules,
        "llm_client",
        SimpleNamespace(call_llm_raw=fake_call_llm_raw),
    )

    tools = importlib.import_module("core.tools")

    result = tools.read_image(
        path=str(image_path),
        prompt="What is in this image?",
    )

    assert result.startswith("[Image: clip.png | image/png")
    assert result.endswith("The screenshot contains a small PNG header.")
    assert len(calls) == 1
    assert calls[0]["model"] == "gpt-5.5-codex"
    assert calls[0]["caller_tag"] == "read_image"
    assert calls[0]["messages"] == [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "What is in this image?"},
                {
                    "type": "input_image",
                    "image_url": "data:image/png;base64,iVBORw0K",
                    "detail": "high",
                },
            ],
        }
    ]
