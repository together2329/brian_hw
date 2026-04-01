"""
Connection Pool & Warmup Benchmark

persistent HTTPS connection 재사용 효과와 warmup 동작을 검증.

사용법:
    cd common_ai_agent
    python tests/test_connection.py

출력 예시:
    [warmup]  GET /api/v1/models → 200  (0.31s)
    [pool]    connection reused: True
    [call 1]  connect=0.041s  (reused: True)
    [call 2]  connect=0.038s  (reused: True)
    [call 3]  connect=0.039s  (reused: True)
    [cold]    connect=0.312s  (fresh conn, no pool)
    overhead:  pool avg=0.039s  cold=0.312s  saved=0.273s/call
"""

import sys
import os
import time
import json
import ssl
import http.client
import urllib.parse
from pathlib import Path

# ── path setup ──────────────────────────────────────────────────────────────
_src = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(_src))
sys.path.insert(0, str(_src.parent))

import config

WARMUP_TIMEOUT = 10
CALL_TIMEOUT   = 30


# ── helpers ──────────────────────────────────────────────────────────────────

def _ssl_ctx():
    ctx = ssl.create_default_context()
    return ctx


def _parse(url: str):
    p = urllib.parse.urlparse(url)
    return p.netloc, p.path.rstrip('/')


def _fmts(v):
    return f"{v:.3f}s"


# ── test cases ────────────────────────────────────────────────────────────────

def test_warmup(host: str, base_path: str, ssl_ctx) -> http.client.HTTPSConnection:
    """GET /models — verifies TCP+SSL+HTTP round-trip and returns live conn."""
    print("\n── Warmup (GET /models) ──────────────────────────────────────")
    conn = http.client.HTTPSConnection(host, context=ssl_ctx, timeout=WARMUP_TIMEOUT)

    t0 = time.perf_counter()
    conn.request("GET", base_path + "/models", headers={
        "Authorization": f"Bearer {config.API_KEY}",
        "Connection": "keep-alive",
    })
    resp = conn.getresponse()
    status = resp.status
    body = resp.read()  # drain → keep-alive available
    elapsed = time.perf_counter() - t0

    ok = "✓" if status < 400 else "✗"
    print(f"  {ok} GET {base_path}/models → {status}  ({_fmts(elapsed)})")
    print(f"     response size: {len(body):,} bytes")
    print(f"     conn.sock alive: {conn.sock is not None}")
    return conn


def test_connection_reuse(conn: http.client.HTTPSConnection, host: str,
                          base_path: str, runs: int = 3) -> list:
    """POST /chat/completions N times on the SAME connection — measure connect time."""
    print(f"\n── Connection Reuse ({runs} calls, same conn) ───────────────────")
    url = f"https://{host}{base_path}/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config.API_KEY}",
        "Connection": "keep-alive",
    }
    body = json.dumps({
        "model": config.MODEL_NAME,
        "messages": [{"role": "user", "content": "Reply with one word: OK"}],
        "stream": True,
        "stream_options": {"include_usage": True},
        "max_tokens": 5,
    }).encode()

    connect_times = []
    for i in range(runs):
        was_connected = conn.sock is not None
        t0 = time.perf_counter()
        try:
            conn.request("POST", base_path + "/chat/completions", body=body, headers=headers)
            resp = conn.getresponse()
            t_headers = time.perf_counter() - t0

            # Drain the SSE stream
            t_first = None
            content = []
            for raw in resp:
                line = raw.decode("utf-8").strip()
                if not line.startswith("data:"):
                    continue
                ds = line[5:].strip()
                if ds == "[DONE]":
                    break
                try:
                    chunk = json.loads(ds)
                    delta = chunk.get("choices", [{}])[0].get("delta", {})
                    tok = delta.get("content", "") or delta.get("reasoning_content", "")
                    if tok:
                        if t_first is None:
                            t_first = time.perf_counter()
                        content.append(tok)
                except json.JSONDecodeError:
                    pass
            resp.read()  # drain final bytes
            t_end = time.perf_counter()

            reused = "reused" if was_connected else "new-conn"
            ttft   = _fmts(t_first - t0) if t_first else "n/a"
            print(f"  call {i+1}: connect={_fmts(t_headers)}  ttft={ttft}  "
                  f"total={_fmts(t_end-t0)}  [{reused}]  resp={repr(''.join(content)[:20])}")
            connect_times.append(t_headers)

        except Exception as e:
            print(f"  call {i+1}: ERROR — {e}")
            # reconnect for next attempt
            try:
                conn.close()
            except Exception:
                pass
            conn.connect()
            connect_times.append(None)

    return connect_times


def test_cold_connection(host: str, base_path: str, ssl_ctx) -> float:
    """Single POST on a fresh connection (no warmup) — baseline connect time."""
    print("\n── Cold Connection (fresh, no warmup) ──────────────────────────")
    conn = http.client.HTTPSConnection(host, context=ssl_ctx, timeout=CALL_TIMEOUT)
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config.API_KEY}",
        "Connection": "keep-alive",
    }
    body = json.dumps({
        "model": config.MODEL_NAME,
        "messages": [{"role": "user", "content": "Reply with one word: OK"}],
        "stream": True,
        "stream_options": {"include_usage": True},
        "max_tokens": 5,
    }).encode()

    t0 = time.perf_counter()
    conn.request("POST", base_path + "/chat/completions", body=body, headers=headers)
    resp = conn.getresponse()
    t_headers = time.perf_counter() - t0

    t_first = None
    for raw in resp:
        line = raw.decode("utf-8").strip()
        if not line.startswith("data:"):
            continue
        ds = line[5:].strip()
        if ds == "[DONE]":
            break
        try:
            chunk = json.loads(ds)
            delta = chunk.get("choices", [{}])[0].get("delta", {})
            tok = delta.get("content", "") or delta.get("reasoning_content", "")
            if tok and t_first is None:
                t_first = time.perf_counter()
        except json.JSONDecodeError:
            pass
    resp.read()
    t_end = time.perf_counter()

    ttft = _fmts(t_first - t0) if t_first else "n/a"
    print(f"  connect={_fmts(t_headers)}  ttft={ttft}  total={_fmts(t_end-t0)}")
    conn.close()
    return t_headers


def test_idle_survive(conn: http.client.HTTPSConnection, base_path: str,
                      idle_seconds: int = 5) -> bool:
    """Wait N seconds then verify the connection is still usable."""
    print(f"\n── Idle Survival ({idle_seconds}s) ─────────────────────────────────")
    print(f"  sleeping {idle_seconds}s...", end=" ", flush=True)
    time.sleep(idle_seconds)
    alive_before = conn.sock is not None
    try:
        conn.request("GET", base_path + "/models", headers={
            "Authorization": f"Bearer {config.API_KEY}",
            "Connection": "keep-alive",
        })
        resp = conn.getresponse()
        resp.read()
        print(f"alive={alive_before} → still_alive={conn.sock is not None}  status={resp.status}  ✓")
        return True
    except Exception as e:
        print(f"alive={alive_before} → broken: {e}  ✗")
        return False


def main():
    print("\n" + "=" * 60)
    print("  Connection Pool & Warmup Test")
    print(f"  Host  : {config.BASE_URL}")
    print(f"  Model : {config.MODEL_NAME}")
    print("=" * 60)

    host, base_path = _parse(config.BASE_URL)
    ssl_ctx = _ssl_ctx()

    # 1. warmup
    conn = test_warmup(host, base_path, ssl_ctx)

    # 2. reuse
    reuse_times = test_connection_reuse(conn, host, base_path, runs=3)

    # 3. cold baseline
    cold_time = test_cold_connection(host, base_path, ssl_ctx)

    # 4. idle survival
    survived = test_idle_survive(conn, base_path, idle_seconds=5)

    # 5. summary
    print("\n── Summary ─────────────────────────────────────────────────────")
    valid = [t for t in reuse_times if t is not None]
    if valid:
        avg_reuse = sum(valid) / len(valid)
        print(f"  reuse avg connect : {_fmts(avg_reuse)}")
        print(f"  cold connect      : {_fmts(cold_time)}")
        if cold_time and avg_reuse:
            saved = cold_time - avg_reuse
            print(f"  saved per call    : {_fmts(saved)}")
    print(f"  idle 5s survived  : {survived}")
    print()


if __name__ == "__main__":
    main()
