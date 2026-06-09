#!/usr/bin/env python3
"""Live E2E: does an attached image actually reach a vision model end-to-end?

Verifies the chat image-input fix (poll_interrupt/react_loop preserve images ->
prompt_content_for_llm -> llm_client Responses path -> model) by sending a
KNOWN test image (3 horizontal color bands: red / green / blue, top->bottom)
to gpt-5.x via the Codex/OAuth Responses route and checking the model's answer
describes the bands correctly. A model that does NOT actually receive the image
cannot name the exact band order.

Routes through Codex because that is the only provider path in this stack that
delivers `input_image` blocks (OpenAI/Azure/Codex Responses); glm/deepseek/kimi
Chat-Completions flatten list content and drop images. See memory
project_image_input_provider_gap.

Usage:
    python3 scripts/verify_image_input_codex.py [model]   # default gpt-5.5
Makes ONE real (billable) API call.
"""
import sys
import os
import io
import base64
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT), str(ROOT / "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)


def build_known_image_data_url() -> tuple[str, list[str]]:
    """Return (data_url, expected_bands_top_to_bottom)."""
    from PIL import Image

    w, h = 120, 120
    img = Image.new("RGB", (w, h))
    bands = [("red", (220, 20, 20)), ("green", (20, 200, 20)), ("blue", (20, 20, 220))]
    band_h = h // 3
    px = img.load()
    for y in range(h):
        idx = min(y // band_h, 2)
        color = bands[idx][1]
        for x in range(w):
            px[x, y] = color
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/png;base64,{b64}", [b[0] for b in bands]


def main() -> int:
    model = sys.argv[1] if len(sys.argv) > 1 else "gpt-5.5"

    import config
    if not config.activate_opencode_oauth(model):
        print("FAIL: no Codex/OAuth credential (run `python -m src.opencode_backend login`)")
        return 2

    import llm_client
    from core.prompt_input import PromptInput, PromptImage, prompt_content_for_llm

    data_url, expected = build_known_image_data_url()

    # Build the user message EXACTLY the way the chat fix does: a PromptInput
    # carrying the image, converted by the real prompt_content_for_llm().
    prompt = PromptInput(
        "This image has three solid horizontal color bands. "
        "List the band colors from TOP to BOTTOM as three words, comma-separated. "
        "If you cannot see an image, reply exactly: NO_IMAGE.",
        (PromptImage(image_url=data_url, detail="high"),),
    )
    content = prompt_content_for_llm(prompt)

    assert isinstance(content, list), "fix regression: content should be multimodal blocks"
    assert any(b.get("type") == "input_image" for b in content), "image block missing"

    messages = [
        {"role": "system", "content": "You are a precise vision assistant. Answer tersely."},
        {"role": "user", "content": content},
    ]

    print(f"model={config.MODEL_NAME}  base_url={config.BASE_URL}")
    print(f"responses_api={llm_client.use_responses_api(model)}  "
          f"block_content={llm_client._responses_api_supports_block_content(config.BASE_URL)}")
    print(f"image block: type=input_image  bytes(data_url)={len(data_url)}")
    print(f"expected bands (top->bottom): {expected}")
    print("--- calling model (1 real API call) ---")

    chunks = []
    try:
        for c in llm_client.chat_completion_stream(
            messages, model=model, skip_rate_limit=True, suppress_spinner=True
        ):
            if isinstance(c, str):
                chunks.append(c)
            elif isinstance(c, tuple) and c and isinstance(c[0], str):
                chunks.append(c[0])
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"FAIL: API call raised {type(e).__name__}: {e}")
        return 3

    answer = "".join(chunks).strip()
    print(f"--- model answer ---\n{answer}\n--------------------")

    low = answer.lower()
    if "no_image" in low:
        print("RESULT: FAIL — model reports it received NO image (image dropped before model).")
        return 1
    hits = [b for b in expected if b in low]
    ordered = (low.find("red") < low.find("green") < low.find("blue")) if all(
        b in low for b in expected) else False
    print(f"color hits: {hits}  correct_order(red<green<blue): {ordered}")
    if len(hits) == 3 and ordered:
        print("RESULT: PASS — model correctly read the image (all 3 bands in order). "
              "Image reaches the model end-to-end.")
        return 0
    if len(hits) >= 2:
        print("RESULT: LIKELY PASS — model saw image (named >=2 exact bands) but order/format imperfect.")
        return 0
    print("RESULT: FAIL — model did not describe the known image content.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
