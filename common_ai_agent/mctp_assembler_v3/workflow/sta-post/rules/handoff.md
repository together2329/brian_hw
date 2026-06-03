# Post-Route STA Handoff Contract

`sta-post` is the sign-off step. It consumes the routed netlist + extracted parasitics
from `/pnr-route` and produces silicon-accurate timing.

## Required upstream artifacts

```
<ip>/pnr/out/routed.v        # post-route netlist (with CTS buffers, post-route opt)
<ip>/pnr/out/routed.spef     # parasitic R/C; non-empty required
<ip>/sta/out/<ip>.sdc        # same SDC /sta used (or scan-mode override)
$SKY130_LIB                  # same corner as /syn /sta /pnr
```

## What's different from /sta

| | /sta (pre-route) | /sta-post (sign-off) |
|---|---|---|
| Netlist | `synth.v` | `routed.v` (has CTS buffers) |
| Net delay | 0 (ideal) | from SPEF (real RC) |
| Clock skew | trivial / single point | post-CTS, real distribution |
| Setup WNS | optimistic | the truth |
| Hold WNS | optimistic | catches CTS-induced fast paths |
| When to run | every iteration after /syn | only after /pnr-route |
| Run time | seconds | seconds (still small for sky130 IPs) |

The user's expectation is: pre-route setup WNS will _degrade_ post-route. If it
doesn't, something silently failed (SDC not loaded, SPEF empty, wrong corner).
The report flags this as suspicious.

## Why the staleness gates are strict

Three independent files must be mutually consistent:

```
routed.v   ≥ mtime  cts.v        # post-route opt happened
routed.spef ≥ mtime routed.def   # extraction happened after final routing
```

Any inversion = the SPEF describes a different layout than routed.v. Sign-off
based on that is meaningless. Better to refuse and re-run /pnr-route.

## Comparing pre vs post

When `<ip>/sta/out/wns.json` (pre-route) AND `<ip>/sta-post/out/wns.json` (this run)
both exist, the report shows a delta column:

```
| clock | pre setup_wns | post setup_wns | Δ      |
|---|---|---|---|
| clk   | -2.640        | -3.120         | -0.480 |
```

A positive Δ (less negative) is suspicious — usually wrong-corner or non-loaded SPEF.

## What sign-off STA does NOT cover

- **Multi-corner** — only one corner per run; SS, FF, TT each need a separate sta-post pass
- **Statistical timing (SSTA)** — not in OpenSTA
- **Aging / NBTI / EM** — out of scope
- **Crosstalk / SI** — OpenSTA reads SI-aware SPEF only if `extract_parasitics`
  was run with `-coupling`, which the current /pnr-route does not enable. Add it
  later for SI-aware sign-off.
