from __future__ import annotations

import json
import subprocess
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "workflow" / "ip-contract" / "scripts" / "derive_ip_contract.py"


def test_derive_ip_contract_uses_capabilities_not_static_profiles(tmp_path: Path) -> None:
    ip = "generic_stream_ip"
    ip_dir = tmp_path / ip
    (ip_dir / "yaml").mkdir(parents=True)
    (ip_dir / "verify").mkdir(parents=True)
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        """
top_module:
  name: generic_stream_ip
io_list:
  clock_domains:
    - name: clk
      ports:
        - {name: clk, width: 1, direction: input}
  resets:
    - name: rst_n
      ports:
        - {name: rst_n, width: 1, direction: input}
  interfaces:
    - name: ingress
      type: custom_stream
      role: sink
      ports:
        - {name: in_valid, width: 1, direction: input}
        - {name: in_ready, width: 1, direction: output}
        - {name: in_data, width: 32, direction: input}
        - {name: in_last, width: 1, direction: input}
    - name: egress
      type: custom_stream
      role: source
      ports:
        - {name: out_valid, width: 1, direction: output}
        - {name: out_ready, width: 1, direction: input}
        - {name: out_data, width: 32, direction: output}
        - {name: out_last, width: 1, direction: output}
function_model:
  transactions:
    - id: FM_PACKET
      output_rules:
        - {name: out_valid, port: out_valid, expr: 1, width: 1}
        - {name: out_data, port: out_data, expr: in_data, width: 32}
cycle_model:
  pipeline:
    - {stage: accept, cycle: 0}
    - {stage: emit, cycle: 2}
  latency:
    packet:
      min_cycles: 1
      max_cycles: 3
  backpressure:
    - out_ready may deassert and stall egress.
memory:
  instances:
    - {name: payload_ram, depth: 16, width: 32}
interrupts:
  sources:
    - {name: packet_done}
debug_observability:
  signals:
    - {name: state_q}
""",
        encoding="utf-8",
    )
    (ip_dir / "verify" / "equivalence_goals.json").write_text(
        json.dumps(
            {
                "goals": [
                    {
                        "goal_id": "EQ_PACKET",
                        "expected_contract": {"observables": ["out_valid", "out_data", "packet emitted"]},
                    }
                ]
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        ["python3", str(SCRIPT), ip, "--root", str(tmp_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    assert result.returncode == 0, result.stdout
    contract = json.loads((ip_dir / "verify" / "ip_contract.json").read_text(encoding="utf-8"))
    assert contract["generation"] == "derived_from_ip_artifacts_not_static_profile"
    assert contract["policy"]["no_static_profile_selection"] is True

    capabilities = {item["id"] for item in contract["capabilities"]}
    assert "ready_valid_handshake" in capabilities
    assert "packet_boundary" in capabilities
    assert "multi_cycle_timing" in capabilities
    assert "backpressure" in capabilities
    assert "memory_state" in capabilities
    assert "interrupt_behavior" in capabilities

    monitors = {item["id"] for item in contract["required_monitors"]}
    assert "ready_valid_monitor" in monitors
    assert "packet_boundary_monitor" in monitors
    assert "backpressure_monitor" in monitors
    assert "interrupt_monitor" in monitors

    mutations = {item["id"] for item in contract["required_mutations"]}
    assert "handshake_hold_drop" in mutations
    assert "boundary_flag_flip" in mutations
    assert "state_update_drop" in mutations

    observables = set(contract["observability"]["required_rtl_observed"])
    assert {"out_valid", "out_data", "out_last", "in_ready"} <= observables


def test_derive_ip_contract_detects_spi_serial_obligations(tmp_path: Path) -> None:
    ip = "spi_contract_ip"
    ip_dir = tmp_path / ip
    (ip_dir / "yaml").mkdir(parents=True)
    (ip_dir / "verify").mkdir(parents=True)
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        """
top_module:
  name: spi_contract_ip
io_list:
  clock_domains:
    - name: clk
      ports:
        - {name: clk, width: 1, direction: input}
  resets:
    - name: rst_n
      ports:
        - {name: rst_n, width: 1, direction: input}
  interfaces:
    - name: spi_master
      type: SPI
      role: master
      ports:
        - {name: sclk_o, width: 1, direction: output}
        - {name: mosi_o, width: 1, direction: output}
        - {name: cs_n_o, width: 1, direction: output}
function_model:
  transactions:
    - id: FM_TRANSFER
      output_rules:
        - {name: sclk_o, port: sclk_o, expr: 0, width: 1}
        - {name: mosi_o, port: mosi_o, expr: 1, width: 1}
        - {name: cs_n_o, port: cs_n_o, expr: 0, width: 1}
cycle_model:
  pipeline:
    - {stage: load, cycle: 0}
    - {stage: shift, cycle: 16}
""",
        encoding="utf-8",
    )
    (ip_dir / "verify" / "equivalence_goals.json").write_text('{"goals": []}\n', encoding="utf-8")

    result = subprocess.run(
        ["python3", str(SCRIPT), ip, "--root", str(tmp_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    assert result.returncode == 0, result.stdout
    contract = json.loads((ip_dir / "verify" / "ip_contract.json").read_text(encoding="utf-8"))
    capabilities = {item["id"] for item in contract["capabilities"]}
    assert "serial_shift_protocol" in capabilities
    assert "chip_select_protocol" in capabilities
    monitors = {item["id"] for item in contract["required_monitors"]}
    assert "serial_frame_monitor" in monitors
    assert "chip_select_monitor" in monitors
    mutations = {item["id"] for item in contract["required_mutations"]}
    assert "bit_order_flip" in mutations
    assert "serial_clock_edge_flip" in mutations
    assert "chip_select_polarity_flip" in mutations


def test_derive_ip_contract_detects_uart_frame_obligations(tmp_path: Path) -> None:
    ip = "uart_contract_ip"
    ip_dir = tmp_path / ip
    (ip_dir / "yaml").mkdir(parents=True)
    (ip_dir / "verify").mkdir(parents=True)
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        """
top_module:
  name: uart_contract_ip
io_list:
  clock_domains:
    - name: clk
      ports:
        - {name: clk, width: 1, direction: input}
  resets:
    - name: rst_n
      ports:
        - {name: rst_n, width: 1, direction: input}
  interfaces:
    - name: uart_tx
      type: UART
      role: source
      ports:
        - {name: tx_o, width: 1, direction: output}
        - {name: busy_o, width: 1, direction: output}
        - {name: done_o, width: 1, direction: output}
function_model:
  transactions:
    - id: FM_TX
      output_rules:
        - {name: tx_o, port: tx_o, expr: 1, width: 1}
        - {name: busy_o, port: busy_o, expr: 0, width: 1}
        - {name: done_o, port: done_o, expr: 1, width: 1}
cycle_model:
  pipeline:
    - {stage: start, cycle: 0}
    - {stage: bits, cycle: 10}
  latency:
    frame:
      min_cycles: 10
      max_cycles: 160
""",
        encoding="utf-8",
    )
    (ip_dir / "verify" / "equivalence_goals.json").write_text(
        json.dumps(
            {
                "goals": [
                    {
                        "goal_id": "EQ_UART_TX",
                        "expected_contract": {"observables": ["tx_o", "data_bits", "stop_bits", "done_cycle"]},
                    }
                ]
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        ["python3", str(SCRIPT), ip, "--root", str(tmp_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    assert result.returncode == 0, result.stdout
    contract = json.loads((ip_dir / "verify" / "ip_contract.json").read_text(encoding="utf-8"))
    capabilities = {item["id"] for item in contract["capabilities"]}
    assert "serial_shift_protocol" in capabilities
    assert "uart_frame_protocol" in capabilities
    monitors = {item["id"] for item in contract["required_monitors"]}
    assert "uart_frame_monitor" in monitors
    mutations = {item["id"] for item in contract["required_mutations"]}
    assert "uart_start_stop_polarity_flip" in mutations
    assert "serial_timing_flip" in mutations


def test_derive_ip_contract_backpressure_text_allows_local_negation(tmp_path: Path) -> None:
    ip = "backpressure_contract_ip"
    ip_dir = tmp_path / ip
    (ip_dir / "yaml").mkdir(parents=True)
    (ip_dir / "verify").mkdir(parents=True)
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        """
top_module:
  name: backpressure_contract_ip
io_list:
  clock_domains:
    - name: clk
      ports:
        - {name: clk, width: 1, direction: input}
  resets:
    - name: rst_n
      ports:
        - {name: rst_n, width: 1, direction: input}
  interfaces:
    - name: sink
      type: ready_valid_stream
      role: sink
      ports:
        - {name: s_valid_i, width: 1, direction: input}
        - {name: s_ready_o, width: 1, direction: output}
cycle_model:
  backpressure:
    - s_ready_o deasserts when full and no same-cycle dequeue happens.
""",
        encoding="utf-8",
    )
    (ip_dir / "verify" / "equivalence_goals.json").write_text('{"goals": []}\n', encoding="utf-8")

    result = subprocess.run(
        ["python3", str(SCRIPT), ip, "--root", str(tmp_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    assert result.returncode == 0, result.stdout
    contract = json.loads((ip_dir / "verify" / "ip_contract.json").read_text(encoding="utf-8"))
    capabilities = {item["id"] for item in contract["capabilities"]}
    assert "backpressure" in capabilities
    monitors = {item["id"] for item in contract["required_monitors"]}
    assert "backpressure_monitor" in monitors
