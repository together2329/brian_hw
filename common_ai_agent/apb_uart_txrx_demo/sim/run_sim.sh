#!/usr/bin/env bash
set -euo pipefail

# Run from the IP root: apb_uart_txrx_demo/
if [[ ! -f rtl/apb_uart_txrx_demo.sv || ! -f sim/tb_apb_uart_txrx_demo.sv ]]; then
  echo "ERROR: run from apb_uart_txrx_demo/ IP root" >&2
  exit 2
fi

mkdir -p sim/waves
rm -f sim/tb_apb_uart_txrx_demo.vvp \
      sim/sim.log \
      sim/sim_results.json \
      sim/scoreboard_events.csv \
      sim/coverage_results.json \
      sim/waveform_manifest.json \
      sim/waves/apb_uart_txrx_demo.vcd

iverilog -g2012 -Wall -o sim/tb_apb_uart_txrx_demo.vvp \
  -c list/apb_uart_txrx_demo.f \
  sim/tb_apb_uart_txrx_demo.sv

set +e
vvp sim/tb_apb_uart_txrx_demo.vvp | tee sim/sim.log
sim_status=${PIPESTATUS[0]}
set -e
if [[ ${sim_status} -ne 0 ]]; then
  echo "ERROR: vvp failed with status ${sim_status}" >&2
  exit ${sim_status}
fi

if [[ ! -f sim/sim_results.json ]]; then
  echo "ERROR: missing sim/sim_results.json" >&2
  exit 3
fi
if [[ ! -f sim/scoreboard_events.csv ]]; then
  echo "ERROR: missing sim/scoreboard_events.csv" >&2
  exit 4
fi
if [[ ! -s sim/waves/apb_uart_txrx_demo.vcd ]]; then
  echo "ERROR: missing or empty VCD" >&2
  exit 5
fi

python3 - <<'PY'
import csv
import json
import sys
import time
from collections import Counter
from pathlib import Path

sim = Path('sim')
results_path = sim / 'sim_results.json'
scoreboard_path = sim / 'scoreboard_events.csv'
vcd_path = sim / 'waves' / 'apb_uart_txrx_demo.vcd'
coverage_path = sim / 'coverage_results.json'
waveform_manifest_path = sim / 'waveform_manifest.json'
tb_path = sim / 'tb_apb_uart_txrx_demo.sv'

required_paths = [results_path, scoreboard_path, vcd_path, tb_path]
missing = [str(p) for p in required_paths if not p.exists() or (p == vcd_path and p.stat().st_size == 0)]
if missing:
    print(f"ERROR: missing required directed evidence: {missing}", file=sys.stderr)
    sys.exit(5)

try:
    sim_results = json.loads(results_path.read_text())
except Exception as exc:
    print(f"ERROR: cannot parse {results_path}: {exc}", file=sys.stderr)
    sys.exit(6)

if not sim_results.get('passed', False) or sim_results.get('scoreboard_fail') != 0:
    print(f"ERROR: scoreboard failure in {results_path}: {sim_results}", file=sys.stderr)
    sys.exit(6)

rows = list(csv.DictReader(scoreboard_path.open()))
if not rows:
    print(f"ERROR: scoreboard CSV is empty: {scoreboard_path}", file=sys.stderr)
    sys.exit(7)
fail_rows = [r for r in rows if r.get('result') == 'FAIL']
if fail_rows:
    print(f"ERROR: scoreboard CSV contains FAIL rows: {fail_rows[:3]}", file=sys.stderr)
    sys.exit(7)

legacy_scenarios = [
    'SC_APB_RESET', 'SC_APB_RW', 'SC_APB_INVALID', 'SC_TX_ONE_BYTE',
    'SC_TX_BACK_TO_BACK', 'SC_TX_IRQ', 'SC_RX_ONE_BYTE',
    'SC_RX_BACK_TO_BACK', 'SC_RX_FRAMING_ERROR', 'SC_RX_OVERRUN',
    'SC_RX_IRQ', 'SC_BAUD_VARIANTS', 'SC_RX_MAJORITY_NOISE',
    'SC_RX_FALSE_START',
]
v2_scenarios = [
    'SC_FRAME_CFG', 'SC_TX_DATA_WIDTHS', 'SC_RX_DATA_WIDTHS',
    'SC_TX_PARITY_EVEN_ODD', 'SC_RX_PARITY_GOOD', 'SC_RX_PARITY_ERROR',
    'SC_TX_STOP2', 'SC_RX_STOP2', 'SC_TX_FIFO_BURST', 'SC_RX_FIFO_ORDER',
    'SC_TX_FIFO_FULL', 'SC_FIFO_CLEAR', 'SC_FIFO_THRESHOLD_IRQ',
    'SC_RX_TIMEOUT_IRQ', 'SC_LOOPBACK', 'SC_BREAK', 'SC_SCRATCH',
]
expected_scenarios = legacy_scenarios + v2_scenarios
scenario_rows = [r['scenario'] for r in rows if r.get('check') == 'SCENARIO_START']
scenario_counter = Counter(scenario_rows)
duplicate_scenarios = sorted([s for s, count in scenario_counter.items() if count != 1])
missing_scenarios = [s for s in expected_scenarios if s not in scenario_counter]
unexpected_scenarios = [s for s in scenario_rows if s not in expected_scenarios]
scenario_order_exact = scenario_rows == expected_scenarios

if missing_scenarios or unexpected_scenarios or duplicate_scenarios or not scenario_order_exact:
    print(
        "ERROR: directed scenario manifest mismatch: "
        f"missing={missing_scenarios} unexpected={unexpected_scenarios} "
        f"duplicates={duplicate_scenarios} observed={scenario_rows}",
        file=sys.stderr,
    )
    sys.exit(8)

if sim_results.get('scenario_count') != len(expected_scenarios):
    print(
        f"ERROR: sim_results scenario_count={sim_results.get('scenario_count')} "
        f"does not match expected {len(expected_scenarios)}",
        file=sys.stderr,
    )
    sys.exit(8)

def hit(scenario=None, check=None):
    return any(
        (scenario is None or r.get('scenario') == scenario) and
        (check is None or r.get('check') == check) and
        r.get('result') == 'PASS'
        for r in rows
    )

def all_hits(*pairs):
    return all(hit(s, c) for s, c in pairs)

def cov_bin(name, condition, evidence, required=True, details=None):
    b = {
        'name': name,
        'required': bool(required),
        'hit': bool(condition),
        'waived': False,
        'evidence': evidence,
    }
    if details is not None:
        b['details'] = details
    return b

coverage_flags = sim_results.get('coverage_flags', {})
required_flags = [
    'legacy_apb', 'legacy_tx_rx_irq_error', 'frame_cfg', 'data_widths',
    'parity', 'stop2', 'fifo', 'threshold_irq', 'timeout_irq', 'loopback',
    'break_error', 'scratch',
]

# Capture VCD header once for both coverage and waveform manifests.
vcd_text = vcd_path.read_text(errors='replace')
end_idx = vcd_text.find('$enddefinitions')
vcd_header = vcd_text if end_idx < 0 else vcd_text[:end_idx]
required_signals = [
    'pclk', 'preset_n', 'psel', 'penable', 'pwrite', 'paddr', 'pwdata',
    'prdata', 'pready', 'pslverr', 'uart_tx', 'uart_rx', 'irq',
]
observed_signals = {sig: (sig in vcd_header) for sig in required_signals}
waveform_ok = vcd_path.exists() and vcd_path.stat().st_size > 0 and all(observed_signals.values())

coverage_bins = [
    cov_bin(
        'directed_scenarios_all_31_exact_order',
        scenario_order_exact and len(scenario_rows) == len(expected_scenarios),
        '31 expected SCENARIO_START rows in exact legacy+v2 order',
        details={'observed': scenario_rows, 'expected': expected_scenarios},
    ),
    cov_bin('scoreboard_json_pass', sim_results.get('passed') is True and sim_results.get('scoreboard_fail') == 0, 'sim_results.json passed=true and scoreboard_fail=0'),
    cov_bin('scoreboard_csv_no_fail_rows', len(fail_rows) == 0, 'scoreboard_events.csv contains no FAIL rows'),
    cov_bin('waveform_vcd_present', waveform_ok, 'non-empty VCD contains required top-level APB/UART/IRQ signals', details=observed_signals),

    # Legacy compatibility bins retained from the original directed suite.
    cov_bin('legacy_apb_reset_readback', all_hits(('SC_APB_RESET', 'CTRL_RESET'), ('SC_APB_RESET', 'STATUS_RESET'), ('SC_APB_RESET', 'BAUD_RESET'), ('SC_APB_RESET', 'UART_TX_IDLE')), 'reset CTRL/STATUS/BAUD and UART idle rows'),
    cov_bin('legacy_apb_rw_and_invalid', all_hits(('SC_APB_RW', 'CTRL_MASK'), ('SC_APB_RW', 'BAUD_ZERO_COERCE'), ('SC_APB_INVALID', 'INVALID_WRITE_ERR'), ('SC_APB_INVALID', 'INVALID_READ_ERR'), ('SC_APB_INVALID', 'INVALID_PRESERVE')), 'APB RW/coerce/invalid rows'),
    cov_bin('legacy_tx_default_8n1', all_hits(('SC_TX_ONE_BYTE', 'TX_DECODE_A5'), ('SC_TX_BACK_TO_BACK', 'TX_B2B_FIRST'), ('SC_TX_BACK_TO_BACK', 'TX_B2B_SECOND')), 'default 8N1 TX decode and back-to-back rows'),
    cov_bin('legacy_tx_irq', all_hits(('SC_TX_IRQ', 'TX_IRQ_ASSERT'), ('SC_TX_IRQ', 'TX_IRQ_STATUS'), ('SC_TX_IRQ', 'TX_IRQ_CLEAR')), 'TX IRQ assert/status/clear rows'),
    cov_bin('legacy_rx_default_8n1', all_hits(('SC_RX_ONE_BYTE', 'RX_VALID_SET'), ('SC_RX_ONE_BYTE', 'RX_DATA_3C'), ('SC_RX_ONE_BYTE', 'RX_VALID_CLEAR'), ('SC_RX_BACK_TO_BACK', 'RX_B2B_FIRST'), ('SC_RX_BACK_TO_BACK', 'RX_B2B_SECOND')), 'default RX valid/data/clear and back-to-back rows'),
    cov_bin('legacy_rx_error_overrun_irq', all_hits(('SC_RX_FRAMING_ERROR', 'FRAME_ERR_STATUS'), ('SC_RX_FRAMING_ERROR', 'ERR_IRQ_FRAME'), ('SC_RX_OVERRUN', 'OVERRUN_STATUS'), ('SC_RX_OVERRUN', 'OVERRUN_PRESERVE'), ('SC_RX_IRQ', 'RX_IRQ_ASSERT'), ('SC_RX_IRQ', 'RX_IRQ_CLEAR')), 'frame error, overrun, and RX IRQ rows'),
    cov_bin('legacy_baud_majority_false_start', all_hits(('SC_BAUD_VARIANTS', 'TX_BAUD8'), ('SC_BAUD_VARIANTS', 'RX_BAUD8'), ('SC_RX_MAJORITY_NOISE', 'RX_MAJORITY_VALID'), ('SC_RX_MAJORITY_NOISE', 'RX_MAJORITY_NO_ERRORS'), ('SC_RX_MAJORITY_NOISE', 'RX_MAJORITY_DATA_C3'), ('SC_RX_FALSE_START', 'FALSE_START_NO_STATUS'), ('SC_RX_FALSE_START', 'FALSE_START_RECOVERY_DATA')), 'baud variant, majority vote, and false-start rows'),

    # Enhanced v2+ bins.
    cov_bin('frame_config_reset_readback', all_hits(('SC_FRAME_CFG', 'FRAME_CFG_RESET_8N1'), ('SC_FRAME_CFG', 'FRAME_CFG_WRITE_ERR'), ('SC_FRAME_CFG', 'FRAME_CFG_READBACK_5O2')), 'FRAME_CFG reset/write/readback rows'),
    cov_bin('tx_data_width_7_and_5', all_hits(('SC_TX_DATA_WIDTHS', 'TX_7BIT_MASK'), ('SC_TX_DATA_WIDTHS', 'TX_7BIT_STOP_AFTER_DATA'), ('SC_TX_DATA_WIDTHS', 'TX_5BIT_MASK'), ('SC_TX_DATA_WIDTHS', 'TX_5BIT_STOP_AFTER_DATA')), 'TX 7-bit and 5-bit masking rows'),
    cov_bin('rx_data_width_7_and_5', all_hits(('SC_RX_DATA_WIDTHS', 'RX_7BIT_MASK'), ('SC_RX_DATA_WIDTHS', 'RX_5BIT_MASK')), 'RX 7-bit and 5-bit masking rows'),
    cov_bin('tx_parity_even_odd', all_hits(('SC_TX_PARITY_EVEN_ODD', 'TX_PARITY_EVEN_DATA'), ('SC_TX_PARITY_EVEN_ODD', 'TX_PARITY_EVEN_BIT'), ('SC_TX_PARITY_EVEN_ODD', 'TX_PARITY_ODD_DATA'), ('SC_TX_PARITY_EVEN_ODD', 'TX_PARITY_ODD_BIT')), 'TX even and odd parity rows'),
    cov_bin('rx_parity_good_even_odd', all_hits(('SC_RX_PARITY_GOOD', 'RX_PARITY_EVEN_NOERR'), ('SC_RX_PARITY_GOOD', 'RX_PARITY_EVEN_DATA'), ('SC_RX_PARITY_GOOD', 'RX_PARITY_ODD_NOERR'), ('SC_RX_PARITY_GOOD', 'RX_PARITY_ODD_DATA')), 'RX good even and odd parity rows'),
    cov_bin('rx_parity_error_irq_and_data', all_hits(('SC_RX_PARITY_ERROR', 'RX_PARITY_ERR_STATUS'), ('SC_RX_PARITY_ERROR', 'RX_PARITY_ERR_IRQ'), ('SC_RX_PARITY_ERROR', 'RX_PARITY_ERR_IRQ_STATUS'), ('SC_RX_PARITY_ERROR', 'RX_PARITY_ERR_DATA_PRESERVED')), 'RX bad parity status/IRQ/data-preserved rows'),
    cov_bin('tx_stop2', all_hits(('SC_TX_STOP2', 'TX_STOP2_DATA'), ('SC_TX_STOP2', 'TX_STOP2_STOP1'), ('SC_TX_STOP2', 'TX_STOP2_STOP2')), 'TX two-stop-bit rows'),
    cov_bin('rx_stop2_good_and_bad', all_hits(('SC_RX_STOP2', 'RX_STOP2_GOOD_DATA'), ('SC_RX_STOP2', 'RX_STOP2_BAD_FRAME_ERR')), 'RX two-stop-bit good and bad-stop rows'),
    cov_bin('tx_fifo_burst_order', all_hits(('SC_TX_FIFO_BURST', 'TX_FIFO_BURST_WR0'), ('SC_TX_FIFO_BURST', 'TX_FIFO_BURST_WR1'), ('SC_TX_FIFO_BURST', 'TX_FIFO_BURST_WR2'), ('SC_TX_FIFO_BURST', 'TX_FIFO_BURST_WR3'), ('SC_TX_FIFO_BURST', 'TX_FIFO_BURST_D0'), ('SC_TX_FIFO_BURST', 'TX_FIFO_BURST_D1'), ('SC_TX_FIFO_BURST', 'TX_FIFO_BURST_D2'), ('SC_TX_FIFO_BURST', 'TX_FIFO_BURST_D3')), 'TX FIFO burst write and decode-order rows'),
    cov_bin('rx_fifo_level_and_order', all_hits(('SC_RX_FIFO_ORDER', 'RX_FIFO_LEVEL4'), ('SC_RX_FIFO_ORDER', 'RX_FIFO_ORDER0'), ('SC_RX_FIFO_ORDER', 'RX_FIFO_ORDER1'), ('SC_RX_FIFO_ORDER', 'RX_FIFO_ORDER2'), ('SC_RX_FIFO_ORDER', 'RX_FIFO_ORDER3')), 'RX FIFO level and read-order rows'),
    cov_bin('tx_fifo_full_write_error', all_hits(('SC_TX_FIFO_FULL', 'TX_FIFO_FILL0'), ('SC_TX_FIFO_FULL', 'TX_FIFO_FILL1'), ('SC_TX_FIFO_FULL', 'TX_FIFO_FILL2'), ('SC_TX_FIFO_FULL', 'TX_FIFO_FILL3'), ('SC_TX_FIFO_FULL', 'TX_FIFO_FULL_LEVEL'), ('SC_TX_FIFO_FULL', 'TX_FIFO_FULL_STATUS'), ('SC_TX_FIFO_FULL', 'TX_FIFO_FULL_WRITE_ERR')), 'TX FIFO full and rejected write rows'),
    cov_bin('fifo_clear', all_hits(('SC_FIFO_CLEAR', 'FIFO_CLEAR_PRE_LEVELS'), ('SC_FIFO_CLEAR', 'FIFO_CLEAR_WRITE_ERR'), ('SC_FIFO_CLEAR', 'FIFO_CLEAR_TX_EMPTY'), ('SC_FIFO_CLEAR', 'FIFO_CLEAR_RX_EMPTY'), ('SC_FIFO_CLEAR', 'FIFO_CLEAR_RX_VALID_CLEAR')), 'TX/RX FIFO clear rows'),
    cov_bin('fifo_threshold_irq', all_hits(('SC_FIFO_THRESHOLD_IRQ', 'FIFO_THRESH_IRQ_IDLE'), ('SC_FIFO_THRESHOLD_IRQ', 'FIFO_THRESH_IRQ_BELOW_RX'), ('SC_FIFO_THRESHOLD_IRQ', 'FIFO_THRESH_IRQ_ASSERT'), ('SC_FIFO_THRESHOLD_IRQ', 'FIFO_THRESH_STATUS_RX'), ('SC_FIFO_THRESHOLD_IRQ', 'FIFO_THRESH_IRQ_STATUS_RX')), 'FIFO threshold status/IRQ rows'),
    cov_bin('rx_timeout_irq', all_hits(('SC_RX_TIMEOUT_IRQ', 'RX_TIMEOUT_STATUS'), ('SC_RX_TIMEOUT_IRQ', 'RX_TIMEOUT_IRQ_ASSERT'), ('SC_RX_TIMEOUT_IRQ', 'RX_TIMEOUT_IRQ_STATUS'), ('SC_RX_TIMEOUT_IRQ', 'RX_TIMEOUT_DATA_BEFORE_CLEAR'), ('SC_RX_TIMEOUT_IRQ', 'RX_TIMEOUT_IRQ_CLEAR')), 'RX timeout sticky status/IRQ/clear rows'),
    cov_bin('loopback_self_test', all_hits(('SC_LOOPBACK', 'LOOPBACK_TX_WRITE_ERR'), ('SC_LOOPBACK', 'LOOPBACK_RX_VALID'), ('SC_LOOPBACK', 'LOOPBACK_RX_DATA')), 'internal loopback TX-to-RX rows'),
    cov_bin('break_error', all_hits(('SC_BREAK', 'TX_BREAK_LINE_LOW'), ('SC_BREAK', 'TX_BREAK_RELEASE_HIGH'), ('SC_BREAK', 'RX_BREAK_STATUS'), ('SC_BREAK', 'RX_BREAK_IRQ')), 'TX break and RX break/error rows'),
    cov_bin('scratch_no_side_effect', all_hits(('SC_SCRATCH', 'SCRATCH_WRITE_ERR'), ('SC_SCRATCH', 'SCRATCH_READBACK'), ('SC_SCRATCH', 'SCRATCH_NO_RX_VALID')), 'SCRATCH read/write and no RX side-effect rows'),
    cov_bin('sim_results_v2_coverage_flags', all(bool(coverage_flags.get(k)) for k in required_flags), 'sim_results.json coverage_flags are all true', details={k: bool(coverage_flags.get(k)) for k in required_flags}),
]

summary = {
    'total_bins': len(coverage_bins),
    'hit_bins': sum(1 for b in coverage_bins if b['hit']),
    'waived_bins': sum(1 for b in coverage_bins if b['waived']),
    'missed_bins': sum(1 for b in coverage_bins if not b['hit'] and not b['waived']),
}
summary['effective_coverage_pct'] = round(100.0 * (summary['hit_bins'] + summary['waived_bins']) / summary['total_bins'], 1)
summary['signoff_status'] = 'pass' if summary['missed_bins'] == 0 else 'fail'
coverage = {
    'schema_version': 'directed_coverage.v4-enhanced-v2plus',
    'ip': 'apb_uart_txrx_demo',
    'generated_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
    'source_artifacts': ['sim/sim.log', 'sim/sim_results.json', 'sim/scoreboard_events.csv', 'sim/waves/apb_uart_txrx_demo.vcd'],
    'directed_scenarios': {
        'required': expected_scenarios,
        'hit': scenario_rows,
        'missing': missing_scenarios,
        'unexpected': unexpected_scenarios,
        'duplicates': duplicate_scenarios,
    },
    'scoreboard': sim_results,
    'coverage_bins': coverage_bins,
    'summary': summary,
}
coverage_path.write_text(json.dumps(coverage, indent=2, sort_keys=True) + '\n')

# Determine dump-source line numbers from the current testbench instead of
# hardcoding stale locations.
dumpfile_line = None
dumpvars_line = None
for line_no, text in enumerate(tb_path.read_text().splitlines(), start=1):
    if '$dumpfile' in text and dumpfile_line is None:
        dumpfile_line = line_no
    if '$dumpvars' in text and dumpvars_line is None:
        dumpvars_line = line_no

waveform = {
    'schema_version': 'waveform_manifest.v3-enhanced-v2plus',
    'ip': 'apb_uart_txrx_demo',
    'generated_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
    'status': 'pass' if waveform_ok else 'fail',
    'waveform': {'path': 'sim/waves/apb_uart_txrx_demo.vcd', 'exists': vcd_path.exists(), 'size_bytes': vcd_path.stat().st_size if vcd_path.exists() else 0},
    'generation_command': 'cd apb_uart_txrx_demo && ./sim/run_sim.sh',
    'testbench_only': True,
    'dut_source_modified_for_waveforms': False,
    'dump_source': {'file': 'sim/tb_apb_uart_txrx_demo.sv', 'dumpfile_line': dumpfile_line, 'dumpvars_line': dumpvars_line},
    'required_top_signals': observed_signals,
    'source_artifacts': ['sim/sim.log', 'sim/sim_results.json', 'sim/scoreboard_events.csv'],
}
waveform_manifest_path.write_text(json.dumps(waveform, indent=2, sort_keys=True) + '\n')

if summary['signoff_status'] != 'pass':
    missed = [b['name'] for b in coverage_bins if not b['hit'] and not b['waived']]
    print(f"ERROR: coverage failed: {summary} missed={missed}", file=sys.stderr)
    sys.exit(8)
if waveform['status'] != 'pass':
    print(f"ERROR: waveform manifest failed: {waveform}", file=sys.stderr)
    sys.exit(9)

print(f"Directed simulation passed: {sim_results}")
print(f"Coverage manifest generated: {summary}")
print(f"Waveform manifest generated: status={waveform['status']} size_bytes={waveform['waveform']['size_bytes']}")
PY
