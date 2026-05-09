import asyncio

from core.atlas_multiuser import _MultiUserBridge


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


if __name__ == "__main__":
    test_session_isolation()
    test_client_binding()
    test_active_session_delegation()
    test_msg_id_dedup()
    test_queue_prompt()
    print("ALL INTEGRATION TESTS PASSED")
