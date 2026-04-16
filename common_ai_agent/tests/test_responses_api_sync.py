"""
test_responses_api_sync.py — Regression tests for the Responses API flow.

Covers the Chat ↔ Responses sync-up fixes:
  - G1: no fc_ id prefix remnants
  - G2: orphan tool_call_id downgrade in _convert_messages_to_responses_input
  - G4: finish_reason emission from _execute_streaming_request_responses
  - G5: _parse_openai_error classification
  - G6: list-of-blocks content flattening via _blocks_for_responses
  - tool_call accumulation regression (dfc17eb / 9e80356)

Pure unit tests — no live API calls. Run:
    pytest tests/test_responses_api_sync.py -v
"""
from __future__ import annotations

import json
import os
import sys
from typing import List
from unittest.mock import patch

import pytest

_here = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(_here)
for _p in (os.path.join(_root, "src"), _root):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import llm_client as lc


def _input_items(msgs):
    """Helper: call _convert_messages_to_responses_input and return only input items."""
    items, _instructions = lc._convert_messages_to_responses_input(msgs)
    return items


# ──────────────────────────────────────────────────────────────────────────────
# G2 / G6: _convert_messages_to_responses_input (canonical converter)
# ──────────────────────────────────────────────────────────────────────────────
class TestMessagesToResponsesInput:
    def test_orphan_tool_message_is_downgraded_to_user(self):
        # tool message without a preceding assistant.tool_calls entry
        msgs = [
            {"role": "user", "content": "hi"},
            {"role": "tool", "tool_call_id": "call_missing", "content": "result"},
        ]
        out = _input_items(msgs)
        # The orphan must NOT become a function_call_output
        assert all(x.get("type") != "function_call_output" for x in out)
        # It must be preserved as a user message with the marker
        orphan_msgs = [x for x in out if x.get("role") == "user"
                       and isinstance(x.get("content"), list)
                       and any("Orphaned tool result" in b.get("text", "") for b in x["content"])]
        assert len(orphan_msgs) == 1

    def test_matched_tool_message_becomes_function_call_output(self):
        msgs = [
            {"role": "user", "content": "please call foo"},
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [{"id": "call_xyz", "type": "function",
                                "function": {"name": "foo", "arguments": "{}"}}],
            },
            {"role": "tool", "tool_call_id": "call_xyz", "content": "42"},
        ]
        out = _input_items(msgs)
        fc_outputs = [x for x in out if x.get("type") == "function_call_output"]
        assert len(fc_outputs) == 1
        assert fc_outputs[0]["call_id"] == "call_xyz"
        assert fc_outputs[0]["output"] == "42"

    def test_function_call_id_is_not_prefixed(self):
        # G1: call_id must be passed through — no fc_ prefix conversion
        msgs = [
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [{"id": "call_abc123", "type": "function",
                                "function": {"name": "x", "arguments": "{}"}}],
            },
        ]
        out = _input_items(msgs)
        fc_items = [x for x in out if x.get("type") == "function_call"]
        assert len(fc_items) == 1
        assert fc_items[0]["call_id"] == "call_abc123"
        assert not fc_items[0]["call_id"].startswith("fc_")

    def test_list_content_is_flattened_to_blocks(self):
        # G6: list-of-blocks content must survive, not be str()-ified
        msgs = [
            {"role": "user", "content": [
                {"type": "text", "text": "hello"},
                {"type": "text", "text": "world"},
            ]},
        ]
        out = _input_items(msgs)
        assert len(out) == 1
        blocks = out[0]["content"]
        assert isinstance(blocks, list) and len(blocks) == 2
        assert blocks[0]["type"] == "input_text" and blocks[0]["text"] == "hello"
        assert blocks[1]["type"] == "input_text" and blocks[1]["text"] == "world"

    def test_string_content_becomes_single_block(self):
        msgs = [{"role": "user", "content": "plain string"}]
        out = _input_items(msgs)
        assert out[0]["content"] == [{"type": "input_text", "text": "plain string"}]

    def test_assistant_with_tool_calls_and_list_content(self):
        # G6 on the assistant+tool_calls branch
        msgs = [{
            "role": "assistant",
            "content": [{"type": "text", "text": "calling now"}],
            "tool_calls": [{"id": "call_1", "type": "function",
                            "function": {"name": "n", "arguments": "{}"}}],
        }]
        out = _input_items(msgs)
        # assistant message with output_text blocks should also be present
        msg_items = [x for x in out if x.get("role") == "assistant"]
        assert len(msg_items) == 1
        assert msg_items[0]["content"][0]["type"] == "output_text"
        assert msg_items[0]["content"][0]["text"] == "calling now"

    def test_system_message_becomes_instructions(self):
        msgs = [
            {"role": "system", "content": "be helpful"},
            {"role": "user", "content": "hi"},
        ]
        items, instructions = lc._convert_messages_to_responses_input(msgs)
        assert instructions == "be helpful"
        # system must not appear in input_items
        assert all(x.get("role") != "system" for x in items)


# ──────────────────────────────────────────────────────────────────────────────
# G5: _parse_openai_error
# ──────────────────────────────────────────────────────────────────────────────
class TestParseOpenAIError:
    def test_rate_limit_by_type(self):
        body = json.dumps({"error": {"message": "rate limit",
                                     "type": "rate_limit_exceeded"}})
        r = lc._parse_openai_error(body)
        assert r["is_rate_limit"] and r["is_retryable"]

    def test_rate_limit_by_http_429(self):
        r = lc._parse_openai_error("", http_status=429)
        assert r["is_rate_limit"] and r["is_retryable"]

    def test_context_length_exceeded(self):
        body = json.dumps({"error": {"code": "context_length_exceeded",
                                     "message": "maximum context length"}})
        r = lc._parse_openai_error(body)
        assert r["is_prompt_too_long"] and r["is_retryable"]

    def test_azure_deployment_missing(self):
        body = json.dumps({"error": {"code": "DeploymentNotFound",
                                     "message": "The API deployment not found."}})
        r = lc._parse_openai_error(body, http_status=404)
        assert r["is_deployment_missing"]

    def test_insufficient_quota(self):
        body = json.dumps({"error": {"code": "insufficient_quota",
                                     "message": "You exceeded your quota"}})
        r = lc._parse_openai_error(body)
        assert r["is_balance_exhausted"]

    def test_content_filter(self):
        body = json.dumps({"error": {"type": "content_filter",
                                     "message": "blocked"}})
        r = lc._parse_openai_error(body)
        assert r["is_content_filter"]

    def test_server_5xx_is_retryable(self):
        r = lc._parse_openai_error("", http_status=503)
        assert r["is_retryable"]

    def test_unknown_body_is_safe(self):
        r = lc._parse_openai_error("not json")
        assert r["code"] == "" and r["message"] == ""

    def test_empty_body_with_status(self):
        # Verify empty body + non-retryable status
        r = lc._parse_openai_error("", http_status=400)
        assert not r["is_retryable"]


# ──────────────────────────────────────────────────────────────────────────────
# G4 + tool_call accumulation: _execute_streaming_request_responses via mocked SSE
# ──────────────────────────────────────────────────────────────────────────────
class _FakeSSEResponse:
    """Minimal stand-in for http.client.HTTPResponse. Iteration yields bytes lines."""

    def __init__(self, events: List[dict]):
        # Encode SSE frames: each event is a dict {"type": "...", ...}
        self._lines: List[bytes] = []
        for ev in events:
            self._lines.append(f"data: {json.dumps(ev)}".encode("utf-8"))
            self._lines.append(b"")  # blank separator
        self._lines.append(b"data: [DONE]")

    def __iter__(self):
        return iter(self._lines)

    def read(self):
        return b""

    def close(self):
        pass


def _collect(gen):
    """Drain a generator, grouping yields by type."""
    plain, tuples = [], []
    for item in gen:
        if isinstance(item, tuple):
            tuples.append(item)
        else:
            plain.append(item)
    return plain, tuples


class TestExecuteResponsesStream:
    def test_tool_call_accumulation(self, monkeypatch):
        # Mimic Responses API SSE for: output_item.added (function_call) + arg deltas + completed
        events = [
            {"type": "response.output_item.added",
             "item": {"type": "function_call", "call_id": "call_abc",
                      "id": "call_abc", "name": "my_tool"}},
            {"type": "response.function_call_arguments.delta",
             "call_id": "call_abc", "delta": '{"k":'},
            {"type": "response.function_call_arguments.delta",
             "call_id": "call_abc", "delta": '"v"}'},
            {"type": "response.completed",
             "response": {"status": "completed",
                          "usage": {"input_tokens": 10, "output_tokens": 5}}},
        ]
        fake = _FakeSSEResponse(events)
        monkeypatch.setattr(lc, "_persistent_post", lambda *a, **kw: fake)

        plain, tuples = _collect(
            lc._execute_streaming_request_responses("u", {}, {}, [], native_mode=True)
        )
        # Exactly one ("native_tool_calls", [...]) with accumulated args
        native = [t for t in tuples if t[0] == "native_tool_calls"]
        assert len(native) == 1
        calls = native[0][1]
        assert len(calls) == 1
        assert calls[0]["id"] == "call_abc"
        assert calls[0]["name"] == "my_tool"
        assert json.loads(calls[0]["arguments"]) == {"k": "v"}

    def test_finish_reason_length_emitted(self, monkeypatch):
        # G4: status == "incomplete" must yield ("finish_reason", "length")
        events = [
            {"type": "response.output_text.delta", "delta": "partial"},
            {"type": "response.completed",
             "response": {"status": "incomplete",
                          "incomplete_details": {"reason": "max_output_tokens"},
                          "usage": {"input_tokens": 10, "output_tokens": 500}}},
        ]
        fake = _FakeSSEResponse(events)
        monkeypatch.setattr(lc, "_persistent_post", lambda *a, **kw: fake)

        _, tuples = _collect(
            lc._execute_streaming_request_responses("u", {}, {}, [], native_mode=True)
        )
        finish = [t for t in tuples if t[0] == "finish_reason"]
        assert finish == [("finish_reason", "length")]

    def test_finish_reason_content_filter_emitted(self, monkeypatch):
        events = [
            {"type": "response.output_text.delta", "delta": "x"},
            {"type": "response.completed",
             "response": {"status": "incomplete",
                          "incomplete_details": {"reason": "content_filter"},
                          "usage": {}}},
        ]
        fake = _FakeSSEResponse(events)
        monkeypatch.setattr(lc, "_persistent_post", lambda *a, **kw: fake)

        _, tuples = _collect(
            lc._execute_streaming_request_responses("u", {}, {}, [], native_mode=True)
        )
        assert ("finish_reason", "content_filter") in tuples

    def test_completed_stop_does_not_emit_finish_reason(self, monkeypatch):
        # Normal completion — no finish_reason tuple (parity with Chat path)
        events = [
            {"type": "response.output_text.delta", "delta": "hello"},
            {"type": "response.completed",
             "response": {"status": "completed", "usage": {}}},
        ]
        fake = _FakeSSEResponse(events)
        monkeypatch.setattr(lc, "_persistent_post", lambda *a, **kw: fake)

        plain, tuples = _collect(
            lc._execute_streaming_request_responses("u", {}, {}, [], native_mode=True)
        )
        assert "hello" in plain
        assert not any(t[0] == "finish_reason" for t in tuples)


# ──────────────────────────────────────────────────────────────────────────────
# G1: grep-style assertion — no fc_ prefix variable or conversion remains
# ──────────────────────────────────────────────────────────────────────────────
class TestNoFcPrefixConversion:
    def test_no_to_fc_id_helper(self):
        # The old _to_fc_id() helper (pre-dfc17eb) must not be present
        assert not hasattr(lc, "_to_fc_id")

    def test_set_a_converter_is_removed(self):
        # Dedup: the Set A converter _messages_to_responses_input must be gone
        assert not hasattr(lc, "_messages_to_responses_input")

    def test_set_a_stream_executor_is_removed(self):
        # Dedup: the Set A executor _execute_responses_stream must be gone
        assert not hasattr(lc, "_execute_responses_stream")

    def test_call_ids_are_passed_through(self):
        # End-to-end: assistant tool_calls.id → function_call.call_id unchanged
        msgs = [{
            "role": "assistant",
            "content": "",
            "tool_calls": [{"id": "call_passthrough_123", "type": "function",
                            "function": {"name": "n", "arguments": "{}"}}],
        }]
        out = _input_items(msgs)
        fc = [x for x in out if x.get("type") == "function_call"][0]
        assert fc["call_id"] == "call_passthrough_123"
