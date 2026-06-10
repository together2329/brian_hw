# Mutation Guard Workflow

Mutation guard measures whether the generated FL-vs-RTL harness can fail when
small deterministic RTL changes are injected.

It is an advisory depth signal by default, not a locked-truth editor and not a
replacement for functional coverage.  The script copies the IP to a temporary
directory, mutates copied RTL, rewrites the copied cocotb manifest, and runs the
existing `tb/cocotb/test_runner.py`.

When `<ip>/verify/ip_contract.json` exists, the guard prioritizes supported
contract-required mutation categories before generic operator/constant
mutations.  It still does not select a static IP profile.

Currently supported contract-specific categories include:

- `bit_order_flip`
- `serial_clock_edge_flip`
- `chip_select_polarity_flip`
- `uart_start_stop_polarity_flip`
- `serial_timing_flip`

Unsupported categories remain explicit follow-up obligations in the report.

Run:

```bash
python3 workflow/mutation/scripts/mutation_guard.py <ip> --root <ip-parent>
```

Useful options:

```bash
python3 workflow/mutation/scripts/mutation_guard.py <ip> --root <ip-parent> --list-only
python3 workflow/mutation/scripts/mutation_guard.py <ip> --root <ip-parent> --max-mutants 20
python3 workflow/mutation/scripts/mutation_guard.py <ip> --root <ip-parent> --enforce-threshold --threshold 0.8
```

The unmutated baseline must already be green.  If
`sim/fl_rtl_compare.json` or `sim/scoreboard_events.jsonl` shows existing
failures, the guard writes `status=blocked_baseline` and does not execute
mutants, because every mutant would inherit the original failure and produce a
misleading kill-rate.

Outputs:

```text
<ip>/mutation/mutation_report.json
<ip>/mutation/mutation_report.md
```

Interpretation:

- `killed`: an existing test or scoreboard detected the mutant.
- `survived`: the mutant still passed the current harness.
- `invalid`: the mutant did not compile or elaborate, so it is not counted in
  the kill-rate denominator.
