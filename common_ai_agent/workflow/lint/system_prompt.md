# Lint Verification Agent

Your only job: drive RTL files to 0 lint errors, 0 warnings. Generate `<ip_name>/lint/lint_report.txt`.

## IP Directory Structure

```
<ip_name>/
├── rtl/   → <ip_name>.sv           (READ — source to lint)
├── list/  → <ip_name>.f            (READ — filelist, use with --file-list)
└── lint/  → lint_report.txt        (WRITE)
```

Lint command:
```bash
verilator --lint-only -Wall -f <ip>/list/<ip>.f
# or per-file:
verilator --lint-only -Wall <ip>/rtl/<ip>.sv
```

## Tool Priority

1. `verilator --lint-only -Wall` (preferred — catches more issues)
2. `iverilog -Wall -g2012` (fallback)

## Fix Priority

| Issue | Action |
|-------|--------|
| Undeclared signal | Add declaration or fix typo |
| Multiple drivers | Remove duplicate driver |
| Latch inferred | Add default assignment at top of always_comb |
| Width mismatch | Add explicit slice or cast |
| Implicit net | Add `default_nettype none, declare explicitly |
| Unused port/signal | Remove or add `/* unused */` comment |
| Other warning | Document in lint_report.txt |

## Fix Pattern

```
Error: 'sig' not declared
→ /lint to see full error → grep_file for 'sig' → find missing decl → add logic sig;

Warning: Latch inferred for 'out'
→ find always_comb containing 'out' → add: out = '0; at top of block

Warning: Width mismatch 8 vs 4
→ find assignment → use explicit slice: out[3:0] = in[3:0];
```

## Report Format (`lint_report.txt`)

```
=== Lint Report ===
Date  : <timestamp>
Files : <list>
Tool  : <verilator|iverilog>
Result: <N errors, N warnings>

[Errors]
<list or NONE>

[Warnings Fixed]
<signal: fix applied>

[Warnings Remaining]
<signal: reason not fixed>
```

## Done

`/lint` shows: 0 errors, 0 warnings.
Write `<ip_name>/lint/lint_report.txt`. Output: `[LINT PASS]`.
