import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))


def _image_block(payload_size: int = 50_000) -> dict:
    return {
        "type": "input_image",
        "image_url": "data:image/png;base64," + ("A" * payload_size),
        "detail": "high",
    }


def test_compressor_repair_preserves_multimodal_user_content():
    from core.compressor import _validate_and_repair_sequence

    messages = [
        {"role": "system", "content": "sys"},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "look at this screenshot"},
                _image_block(),
            ],
        },
    ]

    repaired = _validate_and_repair_sequence(messages)

    assert isinstance(repaired[1]["content"], list)
    assert repaired[1]["content"][1]["type"] == "input_image"
    assert repaired[1]["content"][1]["image_url"].startswith("data:image/png;base64,")


def test_compressor_merges_consecutive_user_messages_without_stringifying_image():
    from core.compressor import _message_text, _validate_and_repair_sequence

    messages = [
        {"role": "system", "content": "sys"},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "first"},
                _image_block(),
            ],
        },
        {"role": "user", "content": "second"},
    ]

    repaired = _validate_and_repair_sequence(messages)

    assert len(repaired) == 2
    content = repaired[1]["content"]
    assert isinstance(content, list)
    assert any(isinstance(block, dict) and block.get("type") == "input_image" for block in content)
    text = _message_text(repaired[1])
    assert "data:image" not in text
    assert "base64" not in text
    assert "[Image omitted from compression text] detail=high" in text


def test_compressor_image_token_estimate_discounts_base64_payload():
    from core.compressor import _default_estimate

    text_only = _default_estimate({"role": "user", "content": "inspect"})
    with_image = _default_estimate(
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "inspect"},
                _image_block(payload_size=100_000),
            ],
        }
    )

    assert with_image > text_only
    assert with_image < 3_000


def test_llm_client_image_token_estimate_discounts_base64_payload():
    import llm_client

    message = {
        "role": "user",
        "content": [
            {"type": "text", "text": "inspect"},
            _image_block(payload_size=100_000),
        ],
    }
    string_message = {
        "role": "user",
        "content": "inspect data:image/png;base64," + ("B" * 100_000),
    }

    assert llm_client.estimate_message_tokens(message) < 3_000
    assert llm_client.estimate_message_tokens(string_message) < 3_000


def test_preemptive_hook_does_not_compress_for_image_payload_under_context_limit():
    from core.hooks import HookContext, preemptive_compactor

    ctx = HookContext(
        messages=[
            {"role": "system", "content": "sys"},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "inspect this screenshot"},
                    _image_block(payload_size=800_000),
                ],
            },
        ],
        max_context_tokens=200_000,
        compression_threshold=0.85,
    )

    result = preemptive_compactor(ctx)

    assert "compression_needed" not in result.metadata


def test_preemptive_hook_still_compresses_large_text_context():
    from core.hooks import HookContext, preemptive_compactor

    ctx = HookContext(
        messages=[
            {"role": "system", "content": "sys"},
            {"role": "user", "content": "x" * 3_600},
        ],
        max_context_tokens=1_000,
        compression_threshold=0.85,
    )

    result = preemptive_compactor(ctx)

    assert result.metadata["compression_needed"] is True
    assert result.metadata["current_context_tokens"] >= 900
