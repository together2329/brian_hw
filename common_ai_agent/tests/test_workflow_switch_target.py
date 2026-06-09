"""workflow_switch_target — in-worker /wf switch must keep the v2 namespace.

The old inline parse assumed 3-seg <owner>/<ip>/<workflow>, so a 4-seg v2 key
(<owner>/<workspace_session>/<ip>/<workflow>) had its workspace_session treated
as the IP and the REAL IP silently dropped — the switched workflow landed in
the wrong session directory and the canonical key never carried the new
workflow (the "/wf says default after /to-ssot" symptom).
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.session_setup import workflow_switch_target


def test_v2_four_segment_preserves_workspace_session_and_ip():
    target, prev = workflow_switch_target(
        "brian_user_3/default/mctp_assembler_v2/default", "ssot-gen"
    )
    assert target == "brian_user_3/default/mctp_assembler_v2/ssot-gen"
    assert prev == "default"


def test_v2_named_workspace_session():
    target, prev = workflow_switch_target("alice/s1/uart/rtl-gen", "tb-gen")
    assert target == "alice/s1/uart/tb-gen"
    assert prev == "rtl-gen"


def test_legacy_three_segment_swaps_workflow():
    target, prev = workflow_switch_target("alice/uart/rtl-gen", "tb-gen")
    assert target == "alice/uart/tb-gen"
    assert prev == "rtl-gen"


def test_short_namespaces_pad_default():
    assert workflow_switch_target("", "ssot-gen") == ("default/default/ssot-gen", "")
    assert workflow_switch_target("alice", "tb-gen") == ("alice/default/tb-gen", "")
    assert workflow_switch_target("alice/uart", "tb-gen") == ("alice/uart/tb-gen", "")


def test_empty_workflow_name_pads_default():
    target, _ = workflow_switch_target("a/s/ip/wf", "")
    assert target == "a/s/ip/default"
