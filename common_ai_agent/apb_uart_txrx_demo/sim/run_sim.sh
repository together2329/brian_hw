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
from pathlib import Path

sim = Path('sim')
results_path = sim / 'sim_results.json'
scoreboard_path = sim / 'scoreboard_events.csv'
vcd_path = sim / 'waves' / 'apb_uart_txrx_demo.vcd'
coverage_path = sim / 'coverage_results.json'
waveform_manifest_path = sim / 'waveform_manifest.json'

sim_results = json.loads(results_path.read_text())
if not sim_results.get('passed', False) or sim_results.get('scoreboard_fail') != 0:
    print(f"ERROR: scoreboard failure in {results_path}: {sim_results}", file=sys.stderr)
    sys.exit(6)

rows = list(csv.DictReader(scoreboard_path.open()))
fail_rows = [r for r in rows if r.get('result') == 'FAIL']
if fail_rows:
    print(f"ERROR: scoreboard CSV contains FAIL rows: {fail_rows[:3]}", file=sys.stderr)
    sys.exit(7)

expected_scenarios = [
    'SC_APB_RESET', 'SC_APB_RW', 'SC_APB_INVALID', 'SC_TX_ONE_BYTE',
    'SC_TX_BACK_TO_BACK', 'SC_TX_IRQ', 'SC_RX_ONE_BYTE',
    'SC_RX_BACK_TO_BACK', 'SC_RX_FRAMING_ERROR', 'SC_RX_OVERRUN',
    'SC_RX_IRQ', 'SC_BAUD_VARIANTS',
]
scenarios = {r['scenario'] for r in rows if r.get('check') == 'SCENARIO_START'}

def hit(scenario=None, check=None):
    return any(
        (scenario is None or r.get('scenario') == scenario) and
        (check is None or r.get('check') == check) and
        r.get('result') == 'PASS'
        for r in rows
    )

def cov_bin(name, condition, evidence):
    return {
        'name': name,
        'required': True,
        'hit': bool(condition),
        'waived': False,
        'evidence': evidence,
    }

coverage_bins = [
    cov_bin('directed_scenarios_all_12', len(scenarios) == 12 and set(expected_scenarios) == scenarios, '12 SCENARIO_START rows in scoreboard_events.csv'),
    cov_bin('apb_ctrl_reset', hit('SC_APB_RESET', 'CTRL_RESET'), 'CTRL_RESET scoreboard row'),
    cov_bin('apb_status_reset', hit('SC_APB_RESET', 'STATUS_RESET'), 'STATUS_RESET scoreboard row'),
    cov_bin('apb_baud_reset', hit('SC_APB_RESET', 'BAUD_RESET'), 'BAUD_RESET scoreboard row'),
    cov_bin('apb_ctrl_reserved_mask', hit('SC_APB_RW', 'CTRL_MASK'), 'CTRL_MASK scoreboard row'),
    cov_bin('apb_baud_zero_coerce_min', hit('SC_APB_RW', 'BAUD_ZERO_COERCE'), 'BAUD_ZERO_COERCE scoreboard row'),
    cov_bin('apb_invalid_write_error', hit('SC_APB_INVALID', 'INVALID_WRITE_ERR'), 'INVALID_WRITE_ERR scoreboard row'),
    cov_bin('apb_invalid_read_error', hit('SC_APB_INVALID', 'INVALID_READ_ERR'), 'INVALID_READ_ERR scoreboard row'),
    cov_bin('tx_one_byte_a5_decode', hit('SC_TX_ONE_BYTE', 'TX_DECODE_A5'), 'TX_DECODE_A5 scoreboard row'),
    cov_bin('tx_back_to_back_zero', hit('SC_TX_BACK_TO_BACK', 'TX_B2B_FIRST'), 'TX_B2B_FIRST scoreboard row'),
    cov_bin('tx_back_to_back_ff', hit('SC_TX_BACK_TO_BACK', 'TX_B2B_SECOND'), 'TX_B2B_SECOND scoreboard row'),
    cov_bin('tx_irq_assert', hit('SC_TX_IRQ', 'TX_IRQ_ASSERT'), 'TX_IRQ_ASSERT scoreboard row'),
    cov_bin('tx_irq_clear', hit('SC_TX_IRQ', 'TX_IRQ_CLEAR'), 'TX_IRQ_CLEAR scoreboard row'),
    cov_bin('rx_one_byte_valid_set', hit('SC_RX_ONE_BYTE', 'RX_VALID_SET'), 'RX_VALID_SET scoreboard row'),
    cov_bin('rx_one_byte_data_3c', hit('SC_RX_ONE_BYTE', 'RX_DATA_3C'), 'RX_DATA_3C scoreboard row'),
    cov_bin('rx_valid_clear_on_read', hit('SC_RX_ONE_BYTE', 'RX_VALID_CLEAR'), 'RX_VALID_CLEAR scoreboard row'),
    cov_bin('rx_back_to_back_zero', hit('SC_RX_BACK_TO_BACK', 'RX_B2B_FIRST'), 'RX_B2B_FIRST scoreboard row'),
    cov_bin('rx_back_to_back_ff', hit('SC_RX_BACK_TO_BACK', 'RX_B2B_SECOND'), 'RX_B2B_SECOND scoreboard row'),
    cov_bin('rx_framing_error_status', hit('SC_RX_FRAMING_ERROR', 'FRAME_ERR_STATUS'), 'FRAME_ERR_STATUS scoreboard row'),
    cov_bin('rx_error_irq_frame', hit('SC_RX_FRAMING_ERROR', 'ERR_IRQ_FRAME'), 'ERR_IRQ_FRAME scoreboard row'),
    cov_bin('rx_overrun_status', hit('SC_RX_OVERRUN', 'OVERRUN_STATUS'), 'OVERRUN_STATUS scoreboard row'),
    cov_bin('rx_overrun_preserve_old_data', hit('SC_RX_OVERRUN', 'OVERRUN_PRESERVE'), 'OVERRUN_PRESERVE scoreboard row'),
    cov_bin('rx_irq_assert_clear', hit('SC_RX_IRQ', 'RX_IRQ_ASSERT') and hit('SC_RX_IRQ', 'RX_IRQ_CLEAR'), 'RX_IRQ_ASSERT and RX_IRQ_CLEAR scoreboard rows'),
    cov_bin('baud_alt8_tx_rx', hit('SC_BAUD_VARIANTS', 'TX_BAUD8') and hit('SC_BAUD_VARIANTS', 'RX_BAUD8'), 'TX_BAUD8 and RX_BAUD8 scoreboard rows'),
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
    'schema_version': 'directed_coverage.v3',
    'ip': 'apb_uart_txrx_demo',
    'generated_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
    'source_artifacts': ['sim/sim.log', 'sim/sim_results.json', 'sim/scoreboard_events.csv', 'sim/waves/apb_uart_txrx_demo.vcd'],
    'directed_scenarios': {'required': expected_scenarios, 'hit': sorted(scenarios)},
    'scoreboard': sim_results,
    'coverage_bins': coverage_bins,
    'summary': summary,
}
coverage_path.write_text(json.dumps(coverage, indent=2, sort_keys=True) + '\n')
if summary['signoff_status'] != 'pass':
    print(f"ERROR: coverage failed: {summary}", file=sys.stderr)
    sys.exit(8)

vcd_head = vcd_path.read_text(errors='replace')[:50000]
required_signals = ['pclk', 'preset_n', 'psel', 'penable', 'pwrite', 'paddr', 'pwdata', 'prdata', 'pready', 'pslverr', 'uart_tx', 'uart_rx', 'irq']
observed = {sig: (sig in vcd_head) for sig in required_signals}
waveform = {
    'schema_version': 'waveform_manifest.v2',
    'ip': 'apb_uart_txrx_demo',
    'generated_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
    'status': 'pass' if vcd_path.exists() and vcd_path.stat().st_size > 0 and all(observed.values()) else 'fail',
    'waveform': {'path': 'sim/waves/apb_uart_txrx_demo.vcd', 'exists': vcd_path.exists(), 'size_bytes': vcd_path.stat().st_size if vcd_path.exists() else 0},
    'generation_command': 'cd apb_uart_txrx_demo && ./sim/run_sim.sh',
    'testbench_only': True,
    'dut_source_modified_for_waveforms': False,
    'dump_source': {'file': 'sim/tb_apb_uart_txrx_demo.sv', 'dumpfile_line': 324, 'dumpvars_line': 325},
    'required_top_signals': observed,
    'source_artifacts': ['sim/sim.log', 'sim/sim_results.json', 'sim/scoreboard_events.csv'],
}
waveform_manifest_path.write_text(json.dumps(waveform, indent=2, sort_keys=True) + '\n')
if waveform['status'] != 'pass':
    print(f"ERROR: waveform manifest failed: {waveform}", file=sys.stderr)
    sys.exit(9)

print(f"Directed simulation passed: {sim_results}")
print(f"Coverage manifest generated: {summary}")
print(f"Waveform manifest generated: status={waveform['status']} size_bytes={waveform['waveform']['size_bytes']}")
PY
