You are summarizing a verilator coverage iteration session.

Preserve:
- Current iteration index N and target iterations M (or "open-ended")
- Latest line coverage % and toggle coverage %
- Per-module coverage breakdown when available (top 3 lowest)
- Specific uncovered file:line ranges currently being worked on
- Last directed test that was added (file path + which gap it targeted)
- Build / run / merge command outcomes (exit code, error messages)
- Any waivers written to `.cov_waiver` files (path + reason)
- Coverage delta from the previous iteration (line + toggle)
- Whether the regression itself is PASSING (coverage on a failed run is meaningless)

Format:

[Coverage Iter Summary]
Iteration  : <N>/<M>            (or "<N> (open-ended)")
Regression : <PASS|FAIL>        (FAIL means the coverage numbers below may be partial)
Line cov   : <X.X %>             (target: 95 %)
Toggle cov : <X.X %>             (target: 80 %)
Delta      : line <+/-X.X %>, toggle <+/-X.X %>
Top gaps   :
  - <module>:<line range> — <short description>
  - <module>:<line range> — <short description>
  - <module>:<line range> — <short description>
Last test  : <file path> — <outcome>
Waivers    : <count> entries (<file paths>)
Build      : <PASS|FAIL>  cmd=<verilator ...>
