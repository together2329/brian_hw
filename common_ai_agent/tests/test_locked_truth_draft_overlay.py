"""The atlas_ui locked-truth-draft interview overlay must be OPT-IN and default
OFF, so the web default agent is a plain chat agent that does not keep pushing
/draft-req on every message. Toggled by ATLAS_LOCKED_TRUTH_DRAFT_MODE.

Finding it fixes: with prompt-injection OFF, the default agent still wrapped
each non-slash chat message in `[ATLAS LOCKED TRUTH DRAFT MODE]` (recommending
/draft-req). That overlay is independent of the prompt-injection toggle and was
suppressed only in codex mode — so non-codex normal mode always injected it.
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

import src.atlas_ui as atlas_ui


def test_overlay_default_off(monkeypatch, tmp_path):
    """No env set -> overlay disabled; even a resolvable unlocked IP gets no
    overlay, so the user's message passes through verbatim."""
    monkeypatch.delenv("ATLAS_LOCKED_TRUTH_DRAFT_MODE", raising=False)
    monkeypatch.delenv("ENABLE_LOCKED_TRUTH_DRAFT_MODE", raising=False)
    assert atlas_ui._locked_truth_draft_overlay_enabled() is False

    text, applied = atlas_ui._apply_locked_truth_draft_overlay(
        tmp_path, "brian/myip/default", {"ip": "myip"}, "make an interrupt")
    assert applied is False
    assert text == "make an interrupt"
    assert atlas_ui._LOCKED_TRUTH_DRAFT_SENTINEL not in text


def test_overlay_opt_in_restores_interview(monkeypatch, tmp_path):
    """ATLAS_LOCKED_TRUTH_DRAFT_MODE=true restores the interview overlay (the
    /draft-req push) for an unlocked IP."""
    monkeypatch.setenv("ATLAS_LOCKED_TRUTH_DRAFT_MODE", "true")
    assert atlas_ui._locked_truth_draft_overlay_enabled() is True

    text, applied = atlas_ui._apply_locked_truth_draft_overlay(
        tmp_path, "brian/myip/default", {"ip": "myip"}, "make an interrupt")
    assert applied is True
    assert atlas_ui._LOCKED_TRUTH_DRAFT_SENTINEL in text
    assert "/draft-req" in text  # the overlay is exactly what pushes draft-req
