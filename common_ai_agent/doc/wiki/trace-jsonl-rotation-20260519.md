# trace.jsonl Growth + Rotation Audit (2026-05-19)

## Summary

`core/orchestrator_trace.py` writes an append-only `trace.jsonl` per IP under
`<ip>/orchestrator/trace.jsonl`. There is **no rotation policy** in the current
implementation. This audit measures actual growth rates and assesses risk.

## File Inventory (2026-05-19)

| File | Lines | Bytes |
|---|---|---|
| dma_scratch_orch_live_20260519b | 314 | 78,866 |
| pl330realverify | 111 | 28,452 |
| artifacts/runtime/_unknown | 103 | 23,702 |
| dma_scratch_ui_live_20260519a | 82 | 20,843 |
| simple_uart_tx | 53 | 13,305 |
| all others (33 files) | 171 | 43,544 |
| **Total (38 files)** | **834** | **208,712 (~204 KB)** |

## Growth Rate Measurement

Largest file (`dma_scratch_orch_live_20260519b`) analyzed:

- 314 events across 105 unique correlation IDs (proxy for dispatches)
- Average events per dispatch: **3.0**
- Average bytes per event: **251 bytes**
- **Actual bytes per dispatch: ~751 bytes (0.73 KB)**

## Extrapolation

| Threshold | Dispatches required |
|---|---|
| 10 MB | ~13,960 |
| 100 MB | ~139,600 |

At current observed usage (38 IPs, ~834 total events ever), the system is at
**204 KB total** — less than 0.2% of a 100 MB threshold.

Each IP file grows independently. A heavily-used IP running thousands of
dispatches would need ~14,000 dispatches to reach 10 MB in a single file.
That is not reachable in normal development usage, but is reachable in
long-running automated regression or stress-test scenarios.

## Rotation Policy Finding

**No rotation policy exists.** `record_trace()` in `core/orchestrator_trace.py`
opens the file with `open(target, "a")` on every call and appends one JSON
line. There is no `max_size`, `rotate`, `rollover`, or `backupCount` guard.

`read_trace()` reads the full file every call (with a `limit` slice at the
end), so a large file increases read latency linearly.

## Risk Assessment

**Low risk at current scale.** The trace is per-IP and each IP represents a
discrete project run. Files only grow while that IP is actively dispatching.
Completed IPs are frozen. The largest live file today is ~77 KB.

**Medium risk for stress / regression workloads.** A loop running 50,000
dispatches against a single IP would produce a ~36 MB file. `read_trace()`
would then scan the entire file on every API call that uses it.

## Recommendation

No immediate code change required. If automated stress tests or long-lived IPs
become common, add a rolling rotation policy to `record_trace()`:

```python
# Suggested addition in record_trace(), after target.parent.mkdir(...)
_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
_MAX_ROTATIONS = 3
if target.exists() and target.stat().st_size >= _MAX_BYTES:
    for i in range(_MAX_ROTATIONS - 1, 0, -1):
        old = target.with_suffix(f".{i}.jsonl")
        new = target.with_suffix(f".{i+1}.jsonl") if i < _MAX_ROTATIONS else None
        if old.exists():
            if new:
                old.rename(new)
            else:
                old.unlink()
    target.rename(target.with_suffix(".1.jsonl"))
```

This keeps 3 rotated files (10 MB each, 30 MB max per IP) and is consistent
with Python `RotatingFileHandler` semantics.

## Conclusion

- Current total: **204 KB** across 38 IPs — not a concern today.
- No rotation means unbounded growth; **~14,000 dispatches/IP reaches 10 MB**.
- Recommend adding rotation only when stress-test or CI workloads are introduced.
- `read_trace()` reads full file per call; rotation also protects read latency.
