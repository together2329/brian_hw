import asyncio
import threading
import time

import pytest

from core.atlas_multiuser import (
    _MultiUserBridge,
    changed_paths_from_tool_result,
    reset_atlas_bridge_session_id,
    set_atlas_bridge_session_id,
)


def test_session_isolation():
    bridge = _MultiUserBridge()
    sess_a = bridge._ensure_session("user-a")
    sess_b = bridge._ensure_session("user-b")
    sess_a.emit("token", text="hello from A")
    sess_b.emit("token", text="hello from B")
    events = []
    for _ in range(2):
        msg, sid = asyncio.get_event_loop().run_until_complete(bridge.next_event(timeout=0.5))
        if msg:
            events.append((msg.get("text"), sid))
    assert len(events) == 2, f"Expected 2 events, got {len(events)}"
    texts = {e[0] for e in events}
    assert "hello from A" in texts
    assert "hello from B" in texts
    print("PASS: session isolation")


def test_client_binding():
    bridge = _MultiUserBridge()
    class MockClient:
        pass
    client = MockClient()
    sid = bridge.bind_client(client, "session-1")
    assert sid == "session-1"
    session = bridge.get_session("session-1")
    assert client in session.clients
    bridge.unbind_client(client)
    assert client not in session.clients
    print("PASS: client binding")


def test_active_session_delegation():
    bridge = _MultiUserBridge()
    bridge.activate_session("active-1")
    bridge.submit_prompt("test prompt")
    print("PASS: active session delegation")


def test_msg_id_dedup():
    bridge = _MultiUserBridge()
    bridge.activate_session("default")
    assert bridge.msg_id_seen("id-1") is False
    assert bridge.msg_id_seen("id-1") is True
    assert bridge.msg_id_seen("id-1") is True
    print("PASS: msg_id dedup")


def test_queue_prompt():
    bridge = _MultiUserBridge()
    bridge.activate_session("default")
    bridge.queue_prompt("/mode normal")
    session = bridge.get_session("default")
    msg = session.get_input()
    assert msg == "/mode normal"
    print("PASS: queue_prompt")


def test_next_event_wakes_for_late_non_default_event():
    bridge = _MultiUserBridge()
    session = bridge._ensure_session("user-a")

    def emit_later():
        time.sleep(0.05)
        session.emit("token", text="late")

    thread = threading.Thread(target=emit_later)
    thread.start()
    started = time.monotonic()
    msg, sid = asyncio.get_event_loop().run_until_complete(bridge.next_event(timeout=0.5))
    elapsed = time.monotonic() - started
    thread.join(timeout=1)
    assert sid == "user-a"
    assert msg and msg.get("text") == "late"
    assert elapsed < 0.2, f"next_event took too long: {elapsed:.3f}s"
    print("PASS: next_event late non-default event")


def test_changed_paths_from_patch_summary():
    text = (
        "Success. Updated the following files:\n"
        "M common_ai_agent/frontend/atlas/workspace.jsx\n"
        "M /tmp/demo/rtl/top.sv\n"
    )
    paths = changed_paths_from_tool_result("apply_patch", text)
    assert "common_ai_agent/frontend/atlas/workspace.jsx" in paths
    assert "/tmp/demo/rtl/top.sv" in paths
    print("PASS: changed path extraction from patch summary")


def test_changed_paths_from_write_replace_results():
    paths = changed_paths_from_tool_result(
        "write_file",
        "Successfully wrote to 'gpio/yaml/gpio.ssot.yaml'.",
    )
    assert paths == ["gpio/yaml/gpio.ssot.yaml"]

    paths = changed_paths_from_tool_result(
        "write_to_file",
        "Successfully wrote to 'gpio/yaml/gpio.ssot.yaml'.",
    )
    assert paths == ["gpio/yaml/gpio.ssot.yaml"]

    paths = changed_paths_from_tool_result(
        "replace_file_content",
        "Replaced 2 occurrence(s) in gpio/rtl/gpio.sv\n",
    )
    assert paths == ["gpio/rtl/gpio.sv"]

    paths = changed_paths_from_tool_result(
        "replace_lines",
        "Update(gpio/rtl/gpio_ctrl.sv)\n@@\n-old\n+new\n",
    )
    assert paths == ["gpio/rtl/gpio_ctrl.sv"]

    paths = changed_paths_from_tool_result(
        "multi_replace_file_content",
        "updated file: gpio/doc/gpio_mas.md\nupdated file: gpio/list/gpio.f\n",
    )
    assert paths == ["gpio/doc/gpio_mas.md", "gpio/list/gpio.f"]
    print("PASS: changed path extraction from write/replace results")


def test_patch_summary_emits_file_changed():
    bridge = _MultiUserBridge()
    session = bridge._ensure_session("user-a")
    bridge._maybe_emit_file_changed(
        session,
        {
            "type": "tool_result",
            "tool": "apply_patch",
            "text": (
                "Success. Updated the following files:\n"
                "M gpio/yaml/gpio.ssot.yaml\n"
            ),
        },
    )
    msg, sid = asyncio.get_event_loop().run_until_complete(bridge.next_event(timeout=0.5))
    assert sid == "user-a"
    assert msg and msg.get("type") == "file_changed"
    assert msg.get("path") == "gpio/yaml/gpio.ssot.yaml"
    print("PASS: patch summary emits file_changed")


def test_strict_routing_requires_session_or_context():
    bridge = _MultiUserBridge(strict_session_routing=True)

    with pytest.raises(RuntimeError):
        bridge.emit("token", text="missing session")

    token = set_atlas_bridge_session_id("user-a")
    try:
        bridge.emit("token", text="context routed")
    finally:
        reset_atlas_bridge_session_id(token)

    msg, sid = asyncio.get_event_loop().run_until_complete(bridge.next_event(timeout=0.5))
    assert sid == "user-a"
    assert msg and msg.get("text") == "context routed"


def test_private_events_cannot_be_broadcast_to_every_session():
    bridge = _MultiUserBridge()
    bridge._ensure_session("alice/ip_alpha/rtl-gen")
    bridge._ensure_session("bob/ip_beta/rtl-gen")

    bridge.broadcast_all(
        "cost",
        session_id="alice/ip_alpha/rtl-gen",
        input=7,
        output=3,
    )

    msg, sid = asyncio.get_event_loop().run_until_complete(bridge.next_event(timeout=0.5))
    assert sid == "alice/ip_alpha/rtl-gen"
    assert msg and msg.get("type") == "cost"
    assert msg.get("input") == 7

    msg, sid = asyncio.get_event_loop().run_until_complete(bridge.next_event(timeout=0.05))
    assert msg is None
    assert sid is None


def test_token_usage_cannot_be_broadcast_to_every_session():
    bridge = _MultiUserBridge()
    bridge._ensure_session("alice/ip_alpha/rtl-gen")
    bridge._ensure_session("bob/ip_beta/rtl-gen")

    bridge.broadcast_all(
        "token_usage",
        session_id="alice/ip_alpha/rtl-gen",
        input_tokens=7,
        output_tokens=3,
    )

    msg, sid = asyncio.get_event_loop().run_until_complete(bridge.next_event(timeout=0.5))
    assert sid == "alice/ip_alpha/rtl-gen"
    assert msg and msg.get("type") == "token_usage"
    assert msg.get("input_tokens") == 7

    msg, sid = asyncio.get_event_loop().run_until_complete(bridge.next_event(timeout=0.05))
    assert msg is None
    assert sid is None


def test_question_flow_uses_context_session_not_latest_active():
    bridge = _MultiUserBridge()
    bridge.activate_session("user-b")

    token = set_atlas_bridge_session_id("user-a")
    try:
        bridge.open_question("flow-1")
        assert bridge.submit_answer_for_session("user-a", "flow-1", {"answer": "ok"})
        assert bridge.wait_answer("flow-1", timeout=0.1) == {"answer": "ok"}
        bridge.close_question("flow-1")
    finally:
        reset_atlas_bridge_session_id(token)

    assert bridge.get_session("user-a").pending_ask_user_events() == []


def test_agent_io_uses_context_session_not_latest_active():
    bridge = _MultiUserBridge()
    bridge.activate_session("user-b")
    bridge.queue_prompt_for_session("user-a", "prompt-a")
    bridge.queue_prompt_for_session("user-b", "prompt-b")
    bridge.submit_interrupt_for_session("user-a", "interrupt-a")
    bridge.request_stop_for_session("user-a")

    token = set_atlas_bridge_session_id("user-a")
    try:
        assert bridge.get_input() == "prompt-a"
        assert bridge.poll_interrupt() == "interrupt-a"
        assert bridge.check_stop() is True
        assert bridge.check_stop() is False
    finally:
        reset_atlas_bridge_session_id(token)

    assert bridge.get_input() == "prompt-b"


if __name__ == "__main__":
    test_session_isolation()
    test_client_binding()
    test_active_session_delegation()
    test_msg_id_dedup()
    test_queue_prompt()
    test_next_event_wakes_for_late_non_default_event()
    test_changed_paths_from_patch_summary()
    test_changed_paths_from_write_replace_results()
    test_patch_summary_emits_file_changed()
    print("ALL INTEGRATION TESTS PASSED")
