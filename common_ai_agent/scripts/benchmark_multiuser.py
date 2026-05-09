#!/usr/bin/env python3
"""
scripts/benchmark_multiuser.py

Performance benchmark for multi-user WebSocket sessions.

Usage:
    python scripts/benchmark_multiuser.py --sessions 10 --prompts 5 --host 127.0.0.1:8765
"""

import argparse
import asyncio
import json
import random
import sys
import time
import urllib.request
from dataclasses import dataclass, field
from typing import List

try:
    import psutil
except ImportError:
    psutil = None  # type: ignore

try:
    import websockets
except ImportError as exc:
    print("ERROR: 'websockets' package is required. Run: python -m pip install websockets")
    raise SystemExit(1) from exc


@dataclass
class PromptResult:
    prompt_index: int
    text: str
    ack_latency_ms: float = 0.0
    first_msg_latency_ms: float = 0.0
    error: str = ""


@dataclass
class SessionResult:
    session_id: str
    connect_latency_ms: float = 0.0
    prompts: List[PromptResult] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


async def create_session(host: str, title: str, project_id: str = "benchmark") -> str:
    url = f"http://{host}/api/sessions"
    body = json.dumps({"title": title, "project_id": project_id}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(None, urllib.request.urlopen, req)
    data = json.loads(response.read().decode("utf-8"))
    session_id = data.get("session_id")
    if not session_id:
        raise RuntimeError(f"No session_id in response: {data}")
    return session_id


async def run_session(host: str, session_index: int, num_prompts: int) -> SessionResult:
    result = SessionResult(session_id="")
    base_uri = f"ws://{host}/ws/agent"
    session_id = ""

    try:
        session_id = await create_session(host, f"bench-session-{session_index}")
        result.session_id = session_id

        uri_with_sid = f"{base_uri}?session_id={session_id}"
        t_connect = time.perf_counter()
        async with websockets.connect(uri_with_sid) as ws:
            hello = await asyncio.wait_for(ws.recv(), timeout=5.0)
            hello_data = json.loads(hello)
            if hello_data.get("type") != "hello":
                raise RuntimeError(f"Expected hello, got: {hello_data}")
            result.connect_latency_ms = (time.perf_counter() - t_connect) * 1000.0

            for i in range(num_prompts):
                prompt_text = f"Benchmark prompt {i+1} from session {session_index}"
                msg_id = f"s{session_index}-p{i+1}"
                payload = {
                    "type": "prompt",
                    "text": prompt_text,
                    "msg_id": msg_id,
                    "session": session_id,
                }

                pr = PromptResult(prompt_index=i + 1, text=prompt_text)
                t_send = time.perf_counter()
                await ws.send(json.dumps(payload))

                ack_seen = False
                first_non_hello_seen = False
                deadline = time.perf_counter() + 10.0

                while time.perf_counter() < deadline:
                    try:
                        raw = await asyncio.wait_for(ws.recv(), timeout=2.0)
                    except asyncio.TimeoutError:
                        break

                    try:
                        msg = json.loads(raw)
                    except Exception:
                        continue

                    msg_type = msg.get("type", "")

                    if msg_type == "agent_received" and not ack_seen:
                        ack_seen = True
                        pr.ack_latency_ms = (time.perf_counter() - t_send) * 1000.0

                    if msg_type not in ("hello",) and not first_non_hello_seen:
                        first_non_hello_seen = True
                        pr.first_msg_latency_ms = (time.perf_counter() - t_send) * 1000.0
                        break

                if not ack_seen:
                    pr.error = "agent_received ack not received within timeout"
                result.prompts.append(pr)

                await asyncio.sleep(random.uniform(0.05, 0.2))

    except Exception as exc:
        err_text = f"{type(exc).__name__}: {exc}"
        result.errors.append(err_text)
        if "sqlite3.OperationalError" in err_text or "database is locked" in err_text:
            result.errors.append("SQLITE_CONTENTION_DETECTED")

    return result


def measure_memory(host: str) -> float:
    if psutil is None:
        return 0.0
    try:
        for proc in psutil.process_iter(["pid", "name", "cmdline", "memory_info"]):
            cmdline = " ".join(proc.info["cmdline"] or [])
            if "uvicorn" in cmdline or "atlas_ui" in cmdline or "textual_main" in cmdline:
                return proc.info["memory_info"].rss / (1024 * 1024)
        return psutil.Process().memory_info().rss / (1024 * 1024)
    except Exception:
        return 0.0


def print_report(results: List[SessionResult], total_time_s: float, memory_mb: float) -> bool:
    print("\n" + "=" * 60)
    print("MULTI-USER BENCHMARK REPORT")
    print("=" * 60)

    all_acks: List[float] = []
    all_firsts: List[float] = []
    sqlite_errors = 0
    session_errors = 0

    for r in results:
        if r.errors:
            session_errors += 1
        for e in r.errors:
            if "SQLITE_CONTENTION_DETECTED" in e or "sqlite3" in e.lower():
                sqlite_errors += 1
        for p in r.prompts:
            if p.ack_latency_ms > 0:
                all_acks.append(p.ack_latency_ms)
            if p.first_msg_latency_ms > 0:
                all_firsts.append(p.first_msg_latency_ms)

    print(f"Sessions created    : {len([r for r in results if r.session_id])}")
    print(f"Sessions with errors: {session_errors}")
    print(f"Total prompts sent  : {sum(len(r.prompts) for r in results)}")
    print(f"Total time          : {total_time_s:.2f}s")

    if all_acks:
        avg_ack = sum(all_acks) / len(all_acks)
        max_ack = max(all_acks)
        print(f"\nAck Latency (prompt -> agent_received)")
        print(f"  Count : {len(all_acks)}")
        print(f"  Avg   : {avg_ack:.1f} ms")
        print(f"  Max   : {max_ack:.1f} ms")
    else:
        avg_ack = max_ack = 0.0
        print("\nAck Latency: no successful measurements")

    if all_firsts:
        avg_first = sum(all_firsts) / len(all_firsts)
        max_first = max(all_firsts)
        print(f"\nFirst-Message Latency (prompt -> first non-hello msg)")
        print(f"  Count : {len(all_firsts)}")
        print(f"  Avg   : {avg_first:.1f} ms")
        print(f"  Max   : {max_first:.1f} ms")
    else:
        avg_first = max_first = 0.0
        print("\nFirst-Message Latency: no successful measurements")

    if memory_mb > 0:
        print(f"\nMemory (RSS)        : {memory_mb:.1f} MB")
    else:
        print("\nMemory (RSS)        : N/A (install psutil for memory measurement)")

    if sqlite_errors:
        print(f"\nSQLite errors       : {sqlite_errors} ⚠️")
    else:
        print(f"\nSQLite errors       : 0 ✅")

    target_latency_ms = 2000.0
    target_memory_mb = 500.0
    print("\n--- Targets ---")
    latency_ok = max_ack <= target_latency_ms if max_ack else False
    mem_ok = memory_mb <= target_memory_mb if memory_mb else True
    sqlite_ok = sqlite_errors == 0

    print(f"Latency < {target_latency_ms}ms   : {'PASS ✅' if latency_ok else 'FAIL ❌'} (max={max_ack:.1f}ms)")
    print(f"Memory < {target_memory_mb}MB     : {'PASS ✅' if mem_ok else 'FAIL ❌'} (rss={memory_mb:.1f}MB)")
    print(f"No SQLite errors    : {'PASS ✅' if sqlite_ok else 'FAIL ❌'}")

    overall = latency_ok and mem_ok and sqlite_ok
    print(f"\nOVERALL             : {'PASS ✅' if overall else 'FAIL ❌'}")
    print("=" * 60)
    return overall


async def main() -> int:
    parser = argparse.ArgumentParser(description="Multi-user WebSocket benchmark")
    parser.add_argument("--sessions", type=int, default=10, help="Number of concurrent sessions (default: 10)")
    parser.add_argument("--prompts", type=int, default=5, help="Prompts per session (default: 5)")
    parser.add_argument("--host", type=str, default="127.0.0.1:8765", help="Server host:port (default: 127.0.0.1:8765)")
    args = parser.parse_args()

    print(f"Benchmark starting: {args.sessions} sessions, {args.prompts} prompts each, host={args.host}")
    print("Ensure the server is running before starting this benchmark.\n")

    mem_before = measure_memory(args.host)

    t_start = time.perf_counter()
    tasks = [
        run_session(args.host, i, args.prompts)
        for i in range(args.sessions)
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    t_end = time.perf_counter()

    processed: List[SessionResult] = []
    for r in results:
        if isinstance(r, Exception):
            sr = SessionResult(session_id="", errors=[f"Task exception: {type(r).__name__}: {r}"])
            processed.append(sr)
        else:
            processed.append(r)

    total_time = t_end - t_start
    mem_after = measure_memory(args.host)
    memory_used = max(mem_after, mem_before)

    ok = print_report(processed, total_time, memory_used)
    return 0 if ok else 1


if __name__ == "__main__":
    try:
        sys.exit(asyncio.run(main()))
    except KeyboardInterrupt:
        print("\nBenchmark interrupted by user.")
        sys.exit(130)
