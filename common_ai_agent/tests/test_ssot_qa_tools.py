import os
import sys


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def test_record_ssot_qa_normalizes_deferred_question_metadata():
    from core import tools

    calls = []
    prior_cb = getattr(tools, "_record_ssot_qa_callback", None)
    try:
        tools.set_record_ssot_qa_callback(lambda **kwargs: calls.append(kwargs) or "recorded")

        result = tools.record_ssot_qa(
            ip="dma330",
            session="u-test/dma330/ssot-gen",
            questions=[
                {
                    "id": "burst_policy",
                    "section_id": "03_interface",
                    "section_title": "03. Interface",
                    "decision_key": "burst_policy",
                    "decision_label": "DMA burst policy",
                    "question": "Which burst policy should DMA330 use?",
                    "kind": "single",
                    "options": [{"id": "fixed", "label": "Fixed"}],
                    "criteria": ["RTL burst generator follows the approved policy"],
                    "source_refs": ["spec/dma.md#burst"],
                }
            ],
        )

        assert result == "recorded"
        assert len(calls) == 1
        assert calls[0]["ip"] == "dma330"
        assert calls[0]["session"] == "u-test/dma330/ssot-gen"
        assert calls[0]["status"] == "pending"
        q = calls[0]["questions"][0]
        assert q["decision_key"] == "burst_policy"
        assert q["section_id"] == "03_interface"
        assert q["kind"] == "single"
        assert q["options"] == [{"id": "fixed", "label": "Fixed", "detail": None}]
        assert q["criteria"] == ["RTL burst generator follows the approved policy"]
        assert q["source_refs"] == ["spec/dma.md#burst"]
    finally:
        tools.set_record_ssot_qa_callback(prior_cb)


def test_record_ssot_qa_single_mode_does_not_require_fixed_options():
    from core import tools

    calls = []
    prior_cb = getattr(tools, "_record_ssot_qa_callback", None)
    try:
        tools.set_record_ssot_qa_callback(lambda **kwargs: calls.append(kwargs) or "recorded")

        result = tools.record_ssot_qa(
            question="Confirm performance target.",
            kind="single",
            decision_key="perf_target",
            section_id="18_verification",
        )

        assert result == "recorded"
        q = calls[0]["questions"][0]
        assert q["question"] == "Confirm performance target."
        assert q["kind"] == "input"
        assert q["options"] == []
        assert q["decision_key"] == "perf_target"
        assert q["section_id"] == "18_verification"
    finally:
        tools.set_record_ssot_qa_callback(prior_cb)
