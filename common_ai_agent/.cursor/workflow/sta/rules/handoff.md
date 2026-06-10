# STA Handoff Contract

The `sta` workflow consumes the gate-level netlist produced by `syn` workflow.
This is a strict, fail-fast handoff — the STA agent never reads RTL directly.

## Required upstream artifact

`<ip>/syn/out/synth.v` — must exist and be **fresh**:

```
mtime(synth.v) >= max(mtime(<ip>/rtl/*.{sv,v}))
```

If stale, the netlist no longer reflects the current RTL, and timing numbers
are nonsense. STA refuses to run.

## Why no RTL fallback

Timing analysis must run on cells with real propagation delays from the Liberty
file. Reading RTL would force STA to invent delays — it cannot, and silently
producing zero-delay reports is worse than refusing to run.

## SSOT fields consumed

```yaml
top_module: gpio_pad
clocks:
  - { name: clk,  period_ns: 10.0, source_port: clk }
  - { name: clk2, period_ns: 25.0, source_port: clk2 }
resets:
  - { name: presetn, polarity: active_low, sync_async: async_assert_sync_deassert,
      source_port: presetn }
false_paths:
  - { from: "cfg_q[*]", to: "out_q[*]" }   # quote `[*]` — YAML reads bare * as an alias
multicycle_paths:
  - { cycles: 2, from: slow_in, to: slow_out, kind: setup }
io_delay:           # optional; conservative defaults if absent
  input_pct:  0.20
  output_pct: 0.20
```

## Same corner contract

`/syn` and `/sta` MUST use the same `$SKY130_LIB` path. Mismatched corners
silently produce wrong WNS — there is no diagnostic. The handoff gate checks
this is set; the human owns the corner choice.

## What STA does NOT fix

STA reports timing. Fixing setup violations belongs to:
- `/syn` (longer clock period via SSOT, or different abc cost function)
- RTL refactor (pipeline a long combinational path)
- (later) `/pnr` for net delays

Hold violations almost always mean the netlist saw async-CDC paths that should
be waived in SDC — go back to SSOT and add `false_paths` rather than ignoring.
