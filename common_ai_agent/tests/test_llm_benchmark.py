"""
LLM Overhead Benchmark

순수 LLM 호출 vs 시스템 경유 호출의 오버헤드를 측정.

사용법:
    cd common_ai_agent
    python tests/test_llm_benchmark.py

출력 예시:
    ┌────────────────────────┬──────────┬──────────┬──────────┐
    │ Phase                  │  Run 1   │  Run 2   │  Run 3   │
    ├────────────────────────┼──────────┼──────────┼──────────┤
    │ [PURE] connect         │  0.312s  │  0.287s  │  0.301s  │
    │ [PURE] ttft            │  3.821s  │  3.102s  │  3.541s  │
    │ [PURE] decode          │  1.234s  │  1.198s  │  1.211s  │
    │ [PURE] total           │  5.367s  │  4.587s  │  5.053s  │
    ├────────────────────────┼──────────┼──────────┼──────────┤
    │ [SYS] build_prompt     │  0.002s  │  0.001s  │  0.002s  │
    │ [SYS] compress         │  0.000s  │  0.000s  │  0.000s  │
    │ [SYS] json_encode      │  0.021s  │  0.020s  │  0.019s  │
    │ [SYS] ssl_ctx          │  0.008s  │  0.003s  │  0.004s  │
    │ [SYS] connect          │  0.345s  │  0.301s  │  0.312s  │
    │ [SYS] ttft             │  3.912s  │  3.201s  │  3.612s  │
    │ [SYS] decode           │  1.301s  │  1.212s  │  1.289s  │
    │ [SYS] total            │  5.589s  │  4.738s  │  5.238s  │
    ├────────────────────────┼──────────┼──────────┼──────────┤
    │ overhead               │  0.222s  │  0.151s  │  0.185s  │
    └────────────────────────┴──────────┴──────────┴──────────┘
"""

import sys
import os
import time
import json
import ssl
import urllib.request
from pathlib import Path
from typing import Dict, List, Any

# ── path setup ──────────────────────────────────────────────────────────────
_src = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(_src))
sys.path.insert(0, str(_src.parent))

import config

RUNS = 3
TEST_MESSAGE = "Reply with exactly one word: Hello"
SYSTEM_MSG = "You are a helpful assistant. Be extremely brief."


# ── helpers ──────────────────────────────────────────────────────────────────

def _fmts(v):
    if v is None:
        return "  n/a   "
    return f" {v:6.3f}s "


def _avg(lst):
    valid = [x for x in lst if x is not None]
    return sum(valid) / len(valid) if valid else None


def _make_messages(extra_turns: int = 0) -> List[Dict[str, Any]]:
    """Build a minimal but realistic message list."""
    msgs = [{"role": "system", "content": SYSTEM_MSG}]
    for i in range(extra_turns):
        msgs.append({"role": "user", "content": f"Turn {i}"})
        msgs.append({"role": "assistant", "content": f"Reply {i}"})
    msgs.append({"role": "user", "content": TEST_MESSAGE})
    return msgs


def _stream_call(messages) -> Dict[str, float]:
    """
    Direct streaming call — measures connect / ttft / decode separately.
    Returns dict of timing values.
    """
    url = f"{config.BASE_URL}/chat/completions"
    api_key = config.API_KEY
    resolved_model = config.MODEL_NAME

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "User-Agent": "BenchmarkTest/1.0",
    }
    data = {
        "model": resolved_model,
        "messages": messages,
        "stream": True,
        "stream_options": {"include_usage": True},
    }
    if config.MAX_OUTPUT_TOKENS > 0:
        data["max_tokens"] = min(config.MAX_OUTPUT_TOKENS, 100)  # cap for benchmark

    t_start = time.perf_counter()

    # json encode
    t0 = time.perf_counter()
    payload = json.dumps(data).encode("utf-8")
    t_json = time.perf_counter() - t0

    # ssl ctx
    t0 = time.perf_counter()
    ssl_ctx = ssl.create_default_context()
    t_ssl = time.perf_counter() - t0

    req = urllib.request.Request(url, data=payload, headers=headers)

    t_connect_start = time.perf_counter()
    t_first_token = None
    t_done = None
    chunks = 0
    content_buf = []

    try:
        with urllib.request.urlopen(req, timeout=60, context=ssl_ctx) as resp:
            t_connect = time.perf_counter() - t_connect_start

            for line in resp:
                line = line.decode("utf-8").strip()
                if not line.startswith("data: "):
                    continue
                data_str = line[6:]
                if data_str == "[DONE]":
                    t_done = time.perf_counter()
                    break
                try:
                    chunk = json.loads(data_str)
                    choices = chunk.get("choices", [])
                    if choices:
                        delta = choices[0].get("delta", {})
                        content = delta.get("content", "")
                        reasoning = delta.get("reasoning") or delta.get("reasoning_content", "")
                        if content or reasoning:
                            if t_first_token is None:
                                t_first_token = time.perf_counter()
                            chunks += 1
                            content_buf.append(content)
                except json.JSONDecodeError:
                    pass

    except Exception as e:
        return {"error": str(e)}

    t_end = t_done or time.perf_counter()
    ttft = (t_first_token - t_connect_start) if t_first_token else None
    decode = (t_end - t_first_token) if t_first_token else None

    return {
        "json_encode": t_json,
        "ssl_ctx": t_ssl,
        "connect": t_connect,
        "ttft": ttft,
        "decode": decode,
        "chunks": chunks,
        "total": t_end - t_start,
        "response": "".join(content_buf).strip(),
    }


def run_pure(runs: int, messages: List[Dict]) -> List[Dict]:
    """순수 LLM 호출 — 시스템 오버헤드 없음."""
    results = []
    for i in range(runs):
        print(f"  [PURE] run {i+1}/{runs}...", end=" ", flush=True)
        r = _stream_call(messages)
        if "error" in r:
            print(f"ERROR: {r['error']}")
        else:
            print(f"total={r['total']:.3f}s  resp={r['response'][:40]!r}")
        results.append(r)
    return results


def run_system(runs: int, messages: List[Dict]) -> List[Dict]:
    """시스템 경유 호출 — build_prompt / compress / hook 포함."""
    results = []

    # Import system components
    try:
        from core.prompt_builder import build_system_prompt, PromptContext
        from core.compressor import compress_history
    except ImportError as e:
        print(f"  [SYS] import error: {e}")
        return []

    for i in range(runs):
        print(f"  [SYS]  run {i+1}/{runs}...", end=" ", flush=True)
        r = {}

        # ── build_prompt ──────────────────────────────
        t0 = time.perf_counter()
        try:
            ctx = PromptContext()
            _ = build_system_prompt(
                messages=messages,
                context=ctx,
                cfg=config,
                build_base_fn=config.build_base_system_prompt,
                load_skills_fn=None,  # skip skill loading (tested separately)
            )
        except Exception as e:
            r["build_prompt_error"] = str(e)
        r["build_prompt"] = time.perf_counter() - t0

        # ── compress (check only, no actual compression for short history) ──
        t0 = time.perf_counter()
        try:
            limit_chars = getattr(config, "MAX_CONTEXT_CHARS", 262144)
            threshold = getattr(config, "COMPRESSION_THRESHOLD", 0.8)
            total_chars = sum(len(str(m.get("content", ""))) for m in messages)
            # just measure the check, not actual compression
            _ = total_chars > limit_chars * threshold
        except Exception:
            pass
        r["compress_check"] = time.perf_counter() - t0

        # ── actual LLM call (with json_encode + ssl) ──────────────────────
        call_r = _stream_call(messages)
        r.update({
            "json_encode": call_r.get("json_encode"),
            "ssl_ctx": call_r.get("ssl_ctx"),
            "connect": call_r.get("connect"),
            "ttft": call_r.get("ttft"),
            "decode": call_r.get("decode"),
            "chunks": call_r.get("chunks"),
            "response": call_r.get("response", ""),
            "error": call_r.get("error"),
        })

        sys_overhead = r["build_prompt"] + r["compress_check"]
        llm_total = call_r.get("total", 0)
        r["total"] = sys_overhead + llm_total

        if "error" in call_r:
            print(f"ERROR: {call_r['error']}")
        else:
            print(f"total={r['total']:.3f}s  (overhead={sys_overhead*1000:.1f}ms)")
        results.append(r)
    return results


def run_skill_routing_benchmark():
    """skill routing LLM 호출 단독 측정."""
    print("\n  Measuring skill routing overhead...")
    try:
        from llm_client import call_llm_raw
        from core.skill_system import get_skill_registry
    except ImportError as e:
        print(f"  skip: {e}")
        return None

    registry = get_skill_registry()
    all_skills = registry.get_all_skills()
    routable = [s for s in all_skills if s.activation.auto_detect]
    if not routable:
        print("  no routable skills found")
        return None

    menu = "\n".join(f"- {s.name}: {s.description.strip()}" for s in routable)
    routing_prompt = (
        f"Available skills:\n{menu}\n\n"
        f"User message: \"hi\"\n\n"
        "Reply with ONLY the skill name, or \"none\"."
    )

    t0 = time.perf_counter()
    try:
        response = call_llm_raw(routing_prompt, temperature=0.0)
        elapsed = time.perf_counter() - t0
        print(f"  skill routing: {elapsed:.3f}s  response={response!r:.40}")
        return elapsed
    except Exception as e:
        elapsed = time.perf_counter() - t0
        print(f"  skill routing error ({elapsed:.3f}s): {e}")
        return elapsed


def print_table(pure_results, sys_results):
    """비교 테이블 출력."""
    phases_pure = ["json_encode", "ssl_ctx", "connect", "ttft", "decode", "total"]
    phases_sys  = ["build_prompt", "compress_check", "json_encode", "ssl_ctx", "connect", "ttft", "decode", "total"]

    col_w = 10
    label_w = 26

    def header(label):
        cols = "".join(f"{'Run '+str(i+1):^{col_w}}" for i in range(RUNS))
        avg_col = f"{'avg':^{col_w}}"
        print(f"\n  {'─'*(label_w + col_w*RUNS + col_w)}")
        print(f"  {label:<{label_w}}" + "".join(f"{'Run '+str(i+1):^{col_w}}" for i in range(RUNS)) + f"{'avg':^{col_w}}")
        print(f"  {'─'*(label_w + col_w*RUNS + col_w)}")

    def row(label, values):
        avg = _avg(values)
        cells = "".join(f"{_fmts(v):^{col_w}}" for v in values)
        avg_cell = f"{_fmts(avg):^{col_w}}"
        print(f"  {label:<{label_w}}{cells}{avg_cell}")

    header("PURE LLM (direct call)")
    for p in phases_pure:
        vals = [r.get(p) for r in pure_results]
        row(f"[pure] {p}", vals)

    header("SYSTEM (with overhead)")
    for p in phases_sys:
        vals = [r.get(p) for r in sys_results]
        row(f"[sys]  {p}", vals)

    # overhead diff
    print(f"\n  {'─'*(label_w + col_w*RUNS + col_w)}")
    print(f"  {'OVERHEAD DIFF':^{label_w + col_w*RUNS + col_w}}")
    print(f"  {'─'*(label_w + col_w*RUNS + col_w)}")
    overhead_vals = []
    for i in range(min(len(pure_results), len(sys_results))):
        pt = pure_results[i].get("total")
        st = sys_results[i].get("total")
        if pt and st:
            overhead_vals.append(st - pt)
        else:
            overhead_vals.append(None)
    row("sys_total - pure_total", overhead_vals)

    overhead_components = []
    for i in range(min(len(sys_results), RUNS)):
        bp = sys_results[i].get("build_prompt", 0) or 0
        cc = sys_results[i].get("compress_check", 0) or 0
        overhead_components.append(bp + cc)
    row("python overhead only", overhead_components)

    print(f"\n  {'─'*(label_w + col_w*RUNS + col_w)}\n")


def main():
    print("\n" + "=" * 60)
    print("  LLM Overhead Benchmark")
    print(f"  Model : {config.MODEL_NAME}")
    print(f"  URL   : {config.BASE_URL}")
    print(f"  Runs  : {RUNS}")
    print("=" * 60)

    messages = _make_messages(extra_turns=2)
    print(f"\n  Messages: {len(messages)} (system + {len(messages)-2} history + 1 user)")
    print(f"  Payload chars: {sum(len(str(m.get('content',''))) for m in messages):,}\n")

    # ── Skill routing (단독) ──────────────────────────────────────────────
    skill_routing_time = run_skill_routing_benchmark()

    # ── Pure LLM ──────────────────────────────────────────────────────────
    print(f"\n{'─'*60}")
    print("  [1/2] Pure LLM calls")
    print(f"{'─'*60}")
    pure_results = run_pure(RUNS, messages)

    # ── System ───────────────────────────────────────────────────────────
    print(f"\n{'─'*60}")
    print("  [2/2] System calls (with pipeline overhead)")
    print(f"{'─'*60}")
    sys_results = run_system(RUNS, messages)

    # ── Table ─────────────────────────────────────────────────────────────
    if pure_results and sys_results:
        print_table(pure_results, sys_results)

    # ── Summary ───────────────────────────────────────────────────────────
    print("  Optimization targets:")
    print(f"  ├─ skill routing (1st message/session): {skill_routing_time:.3f}s" if skill_routing_time else "  ├─ skill routing: n/a")

    pure_connects = [r.get("connect") for r in pure_results if r.get("connect")]
    if pure_connects:
        avg_connect = sum(pure_connects) / len(pure_connects)
        print(f"  ├─ connect latency (network): avg {avg_connect:.3f}s")

    pure_ttfts = [r.get("ttft") for r in pure_results if r.get("ttft")]
    if pure_ttfts:
        avg_ttft = sum(pure_ttfts) / len(pure_ttfts)
        print(f"  ├─ ttft / prefill: avg {avg_ttft:.3f}s")

    sys_bp = [r.get("build_prompt") for r in sys_results if r.get("build_prompt") is not None]
    if sys_bp:
        avg_bp = sum(sys_bp) / len(sys_bp)
        print(f"  └─ build_prompt python overhead: avg {avg_bp*1000:.1f}ms")

    print()


if __name__ == "__main__":
    main()
