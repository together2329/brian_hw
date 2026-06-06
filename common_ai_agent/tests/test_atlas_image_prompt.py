import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))


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
