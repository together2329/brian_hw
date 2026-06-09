import base64
from io import BytesIO
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))


def _write_png(path: Path, size: tuple[int, int] = (8, 6)) -> bytes:
    from PIL import Image

    image = Image.new("RGB", size, (24, 80, 160))
    output = BytesIO()
    image.save(output, format="PNG")
    data = output.getvalue()
    path.write_bytes(data)
    return data


def _decode_data_url(data_url: str) -> tuple[str, bytes]:
    header, encoded = data_url.split(",", 1)
    return header, base64.b64decode(encoded)


def test_session_worker_preserves_prompt_images_for_llm_content(tmp_path):
    from core.prompt_input import prompt_content_for_llm, prompt_has_content
    from core.session_worker import SessionWorker

    worker = SessionWorker("alice/demo/rtl-gen", str(tmp_path / "atlas.db"))
    try:
        worker.db.enqueue_message(
            "alice/demo/rtl-gen",
            "in",
            "prompt",
            {
                "text": "What is wrong in this screenshot?",
                "images": [
                    {
                        "image_url": "data:image/png;base64,aGVsbG8=",
                        "detail": "high",
                        "name": "clipboard.png",
                    }
                ],
            },
        )
        prompt = worker.input("> ")
    finally:
        worker.close()

    assert prompt == "What is wrong in this screenshot?"
    assert prompt_has_content(prompt) is True
    assert prompt_content_for_llm(prompt) == [
        {"type": "text", "text": "What is wrong in this screenshot?"},
        {
            "type": "input_image",
            "image_url": "data:image/png;base64,aGVsbG8=",
            "detail": "high",
        },
    ]


def test_image_only_prompt_is_not_treated_as_empty(tmp_path):
    from core.prompt_input import prompt_content_for_llm, prompt_has_content
    from core.session_worker import SessionWorker

    worker = SessionWorker("alice/demo/rtl-gen", str(tmp_path / "atlas.db"))
    try:
        worker.db.enqueue_message(
            "alice/demo/rtl-gen",
            "in",
            "prompt",
            {
                "text": "",
                "images": [{"image_url": "data:image/png;base64,aGVsbG8="}],
            },
        )
        prompt = worker.input("> ")
    finally:
        worker.close()

    assert prompt == ""
    assert prompt_has_content(prompt) is True
    assert prompt_content_for_llm(prompt) == [
        {
            "type": "input_image",
            "image_url": "data:image/png;base64,aGVsbG8=",
            "detail": "auto",
        },
    ]


def test_path_backed_prompt_image_is_loaded_only_for_llm_content(tmp_path):
    from core.prompt_input import prompt_content_for_llm, prompt_input_from_payload

    image_path = tmp_path / "clipboard.png"
    expected = _write_png(image_path)
    prompt = prompt_input_from_payload(
        "inspect this",
        {
            "images": [
                {
                    "path": str(image_path),
                    "detail": "high",
                    "mime_type": "image/png",
                    "name": "clipboard.png",
                }
            ]
        },
    )

    assert prompt == "inspect this"
    assert prompt.images[0].path == str(image_path)
    assert prompt.images[0].image_url is None

    content = prompt_content_for_llm(prompt)
    assert content[0] == {"type": "text", "text": "inspect this"}
    assert content[1]["type"] == "input_image"
    assert content[1]["detail"] == "high"
    header, payload = _decode_data_url(content[1]["image_url"])
    assert header == "data:image/png;base64"
    assert payload == expected


def test_path_backed_large_prompt_image_is_resized_for_llm_content(tmp_path):
    from PIL import Image

    from core.prompt_input import PromptImage, PromptInput, prompt_content_for_llm

    image_path = tmp_path / "large.png"
    Image.new("RGB", (4096, 1024), (40, 90, 140)).save(image_path, format="PNG")
    prompt = PromptInput("", (PromptImage(path=str(image_path), detail="high"),))

    content = prompt_content_for_llm(prompt)
    header, payload = _decode_data_url(content[0]["image_url"])

    assert header == "data:image/png;base64"
    with Image.open(BytesIO(payload)) as image:
        assert image.size == (2048, 512)


def test_spools_browser_data_urls_to_path_payload(tmp_path):
    from core.prompt_image_store import spool_prompt_images_for_session

    image_path = tmp_path / "clipboard.png"
    data = _write_png(image_path)
    data_url = f"data:image/png;base64,{base64.b64encode(data).decode('ascii')}"

    [spooled] = spool_prompt_images_for_session(
        [{"image_url": data_url, "detail": "high", "name": "clipboard.png"}],
        session_id="alice/demo/rtl-gen",
        store_root=tmp_path / "store",
    )

    assert "image_url" not in spooled
    assert spooled["detail"] == "high"
    assert spooled["mime_type"] == "image/png"
    assert spooled["name"] == "clipboard.png"
    assert Path(spooled["path"]).read_bytes() == data


# --- Mid-run human-in-the-loop / interrupt path -------------------------------
# These cover poll_interrupt(), which deep-interview and other long-lived loops
# use to inject the user's reply *between* turns. It previously degraded to the
# text field only, so an image attached mid-conversation was silently dropped
# (image-only message -> empty text -> skipped entirely, no response).


def test_poll_interrupt_preserves_text_and_images(tmp_path):
    from core.prompt_input import prompt_content_for_llm, prompt_has_content
    from core.session_worker import SessionWorker

    worker = SessionWorker("alice/demo/rtl-gen", str(tmp_path / "atlas.db"))
    try:
        worker.db.enqueue_message(
            "alice/demo/rtl-gen",
            "in",
            "interrupt",
            {
                "text": "use this register map",
                "images": [
                    {"image_url": "data:image/png;base64,aGVsbG8=", "detail": "high"}
                ],
            },
        )
        human = worker.poll_interrupt()
    finally:
        worker.close()

    assert human is not None
    assert str(human) == "use this register map"
    assert prompt_has_content(human) is True
    assert prompt_content_for_llm(human) == [
        {"type": "text", "text": "use this register map"},
        {
            "type": "input_image",
            "image_url": "data:image/png;base64,aGVsbG8=",
            "detail": "high",
        },
    ]


def test_poll_interrupt_image_only_is_not_dropped(tmp_path):
    from core.prompt_input import prompt_content_for_llm, prompt_has_content
    from core.session_worker import SessionWorker

    worker = SessionWorker("alice/demo/rtl-gen", str(tmp_path / "atlas.db"))
    try:
        worker.db.enqueue_message(
            "alice/demo/rtl-gen",
            "in",
            "interrupt",
            {
                "text": "",
                "images": [{"image_url": "data:image/png;base64,aGVsbG8="}],
            },
        )
        human = worker.poll_interrupt()
    finally:
        worker.close()

    # Image-only mid-run message: bare-str truthiness is False, but it must NOT
    # be treated as empty -- this is exactly the case that produced no response.
    assert human is not None
    assert str(human) == ""
    assert bool(human) is False
    assert prompt_has_content(human) is True
    assert prompt_content_for_llm(human) == [
        {
            "type": "input_image",
            "image_url": "data:image/png;base64,aGVsbG8=",
            "detail": "auto",
        },
    ]


def test_poll_interrupt_text_only_returns_plain_text(tmp_path):
    from core.prompt_input import prompt_content_for_llm
    from core.session_worker import SessionWorker

    worker = SessionWorker("alice/demo/rtl-gen", str(tmp_path / "atlas.db"))
    try:
        worker.db.enqueue_message(
            "alice/demo/rtl-gen", "in", "interrupt", {"text": "keep going"}
        )
        human = worker.poll_interrupt()
    finally:
        worker.close()

    assert human == "keep going"
    # No images -> plain string content, unchanged provider behavior.
    assert prompt_content_for_llm(human) == "keep going"


def test_poll_interrupt_returns_none_when_no_message(tmp_path):
    from core.session_worker import SessionWorker

    worker = SessionWorker("alice/demo/rtl-gen", str(tmp_path / "atlas.db"))
    try:
        assert worker.poll_interrupt() is None
    finally:
        worker.close()


def test_react_loop_human_input_gating_matches_fix(tmp_path):
    """Guards the react_loop injection predicate against regressions.

    react_loop injects mid-run human input as
    ``if _human_msg is not None and prompt_has_content(_human_msg)`` with
    ``content=prompt_content_for_llm(_human_msg)``. Verify each branch the loop
    relies on, including the None-guard (prompt_has_content(None) is truthy via
    str(None)=="None", so the None check must come first).
    """
    from core.prompt_input import (
        PromptImage,
        PromptInput,
        prompt_content_for_llm,
        prompt_has_content,
    )

    def _should_inject(msg):
        return msg is not None and prompt_has_content(msg)

    # No queued message -> skipped.
    assert _should_inject(None) is False
    # Empty plain text -> skipped (no regression for text-only callers).
    assert _should_inject("") is False
    # Image-only PromptInput (empty text) -> injected as image blocks.
    img = PromptInput("", (PromptImage("data:image/png;base64,aGVsbG8=", "auto"),))
    assert _should_inject(img) is True
    assert prompt_content_for_llm(img) == [
        {
            "type": "input_image",
            "image_url": "data:image/png;base64,aGVsbG8=",
            "detail": "auto",
        },
    ]


def test_message_content_text_extracts_text_from_multimodal_blocks():
    from core.prompt_input import message_content_text

    content = [
        {"type": "text", "text": "look at this"},
        {"type": "input_image", "image_url": "data:image/png;base64,aGVsbG8="},
        {"type": "text", "text": "and use task agent"},
    ]

    assert message_content_text(content) == "look at this\nand use task agent"


def test_strategy_injection_handles_multimodal_user_content():
    import main

    messages = [
        {"role": "system", "content": "sys"},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "please use task agent"},
                {"type": "input_image", "image_url": "data:image/png;base64,aGVsbG8="},
            ],
        },
    ]

    assert main._maybe_inject_exploration_strategy(messages, "please use task agent")
    assert "DELEGATION STRATEGY" in messages[-1]["content"]


def test_strategy_injection_ignores_image_only_content_without_crashing():
    import main

    messages = [
        {"role": "system", "content": "sys"},
        {
            "role": "user",
            "content": [
                {"type": "input_image", "image_url": "data:image/png;base64,aGVsbG8="}
            ],
        },
    ]

    assert main._maybe_inject_exploration_strategy(messages, "") is False
