from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil

import pytest


def _load_script(rel: str, name: str):
    root = Path(__file__).resolve().parents[1]
    path = root / rel
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_starter_llm_authored_tiny_rtl_runs_to_sim(tmp_path: Path):
    if not shutil.which("iverilog") or not shutil.which("vvp"):
        pytest.skip("iverilog and vvp are required for Starter preview simulation")
    rtl_gen = _load_script("workflow/rtl-gen/scripts/ssot_to_rtl.py", "starter_rtl_gen_under_test")
    sim = _load_script("workflow/sim/scripts/starter_preview_sim.py", "starter_preview_sim_under_test")
    ip = "tiny_starter_and"
    ip_dir = tmp_path / ip
    (ip_dir / "yaml").mkdir(parents=True)
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        """
top_module:
  name: tiny_starter_and
io_list:
  interfaces:
    - name: pins
      type: raw
      ports:
        - {name: a_i, direction: input, width: 1}
        - {name: b_i, direction: input, width: 1}
        - {name: y_o, direction: output, width: 1}
function_model:
  description: y_o is asserted when both inputs are asserted.
  output_rules:
    - {name: y_o, expr: a_i and b_i}
""".strip()
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(SystemExit) as exc:
        rtl_gen.generate(ip, tmp_path, mode="starter")
    assert exc.value.code == 2
    assert not (ip_dir / "rtl" / f"{ip}.sv").exists()
    contract_doc = json.loads((ip_dir / "rtl" / "rtl_contract.json").read_text(encoding="utf-8"))
    assert contract_doc["type"] == "starter_llm_rtl_authoring_contract"

    (ip_dir / "rtl" / f"{ip}.sv").write_text(
        """
module tiny_starter_and (
    input logic a_i,
    input logic b_i,
    output logic y_o
);
    assign y_o = a_i & b_i;
endmodule
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (ip_dir / "list").mkdir(exist_ok=True)
    (ip_dir / "list" / f"{ip}.f").write_text(f"rtl/{ip}.sv\n", encoding="utf-8")
    (ip_dir / "rtl" / "rtl_authoring_provenance.json").write_text(
        json.dumps({
            "schema_version": 1,
            "type": "rtl_authoring_provenance",
            "agent": "test_llm",
            "generator": "none",
            "authoring_method": "llm_authored_from_starter_handoff",
            "rtl_files": [f"rtl/{ip}.sv"],
        }, indent=2) + "\n",
        encoding="utf-8",
    )

    payload = sim.run(ip, tmp_path)

    report = json.loads((ip_dir / "sim" / "starter_preview_sim.json").read_text(encoding="utf-8"))
    assert payload["status"] == "PASS"
    assert report["tests"] == 4
    assert report["pass"] == 4
    assert report["fail"] == 0
    assert (ip_dir / "tb" / f"tb_{ip}.sv").is_file()
    assert (ip_dir / "sim" / f"{ip}.out").is_file()
    assert (ip_dir / "sim" / "results.xml").is_file()
    assert "TESTS=4 PASS=4 FAIL=0" in (ip_dir / "sim" / "sim_report.txt").read_text(encoding="utf-8")


def test_starter_apb_timer_requires_llm_authored_rtl_then_simulates(tmp_path: Path):
    if not shutil.which("iverilog") or not shutil.which("vvp"):
        pytest.skip("iverilog and vvp are required for Starter preview simulation")
    rtl_gen = _load_script("workflow/rtl-gen/scripts/ssot_to_rtl.py", "starter_apb_timer_rtl_gen_under_test")
    sim = _load_script("workflow/sim/scripts/starter_preview_sim.py", "starter_apb_timer_sim_under_test")
    ip = "starter_apb_timer"
    ip_dir = tmp_path / ip
    (ip_dir / "yaml").mkdir(parents=True)
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        """
top_module:
  name: starter_apb_timer
io_list:
  clock_domains:
    - ports:
        - {name: clk, direction: input, width: 1}
  resets:
    - ports:
        - {name: rst_n, direction: input, width: 1}
  interfaces:
    - name: apb
      type: apb
      ports:
        - {name: paddr, direction: input, width: 8}
        - {name: psel, direction: input, width: 1}
        - {name: penable, direction: input, width: 1}
        - {name: pwrite, direction: input, width: 1}
        - {name: pwdata, direction: input, width: 32}
        - {name: prdata, direction: output, width: 32}
        - {name: pready, direction: output, width: 1}
        - {name: pslverr, direction: output, width: 1}
        - {name: irq, direction: output, width: 1}
rtl_contract:
  clock: clk
  reset: rst_n
  reset_active: low
  sample_condition: "1"
function_model:
  description: APB timer starter contract for LLM-authored RTL.
  state_variables:
    - {name: enable, width: 1, reset: 0}
    - {name: compare, width: 8, reset: 3}
    - {name: count, width: 8, reset: 0}
    - {name: irq_state, width: 1, reset: 0}
  transactions:
    - id: FM_RULES
      state_updates:
        - name: enable
          width: 1
          expr: "pwdata[0] if (psel and penable and pwrite and paddr == 0) else enable"
        - name: compare
          width: 8
          expr: "pwdata[0:8] if (psel and penable and pwrite and paddr == 4) else compare"
        - name: count
          width: 8
          expr: "0 if (psel and penable and pwrite and paddr == 8) else ((0 if count == compare else count + 1) if enable else count)"
        - name: irq_state
          width: 1
          expr: "0 if (psel and penable and pwrite and paddr == 12) else (1 if (enable and count == compare) else irq_state)"
      output_rules:
        - {name: pready, port: pready, width: 1, expr: "psel and penable"}
        - {name: pslverr, port: pslverr, width: 1, expr: "0"}
        - {name: irq, port: irq, width: 1, expr: "irq_state"}
        - name: prdata
          port: prdata
          width: 32
          expr: "enable if paddr == 0 else (compare if paddr == 4 else (count if paddr == 8 else irq_state))"
""".strip()
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(SystemExit) as exc:
        rtl_gen.generate(ip, tmp_path, mode="starter")
    assert exc.value.code == 2
    assert not (ip_dir / "rtl" / f"{ip}.sv").exists()
    contract_doc = json.loads((ip_dir / "rtl" / "rtl_contract.json").read_text(encoding="utf-8"))
    assert contract_doc["type"] == "starter_llm_rtl_authoring_contract"
    assert (ip_dir / "rtl" / "starter_llm_rtl_handoff.json").is_file()

    (ip_dir / "rtl" / f"{ip}.sv").write_text(
        """
module starter_apb_timer (
    input logic clk,
    input logic rst_n,
    input logic [7:0] paddr,
    input logic psel,
    input logic penable,
    input logic pwrite,
    input logic [31:0] pwdata,
    output logic [31:0] prdata,
    output logic pready,
    output logic pslverr,
    output logic irq
);

    logic enable;
    logic [7:0] compare;
    logic [7:0] count;
    logic irq_state;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            enable <= 1'b0;
            compare <= 8'd3;
            count <= 8'd0;
            irq_state <= 1'b0;
        end else begin
            if (psel && penable && pwrite && paddr == 8'd0) begin
                enable <= pwdata[0];
            end
            if (psel && penable && pwrite && paddr == 8'd4) begin
                compare <= pwdata[7:0];
            end
            if (psel && penable && pwrite && paddr == 8'd8) begin
                count <= 8'd0;
            end else if (enable) begin
                count <= (count == compare) ? 8'd0 : count + 8'd1;
            end
            if (psel && penable && pwrite && paddr == 8'd12) begin
                irq_state <= 1'b0;
            end else if (enable && count == compare) begin
                irq_state <= 1'b1;
            end
        end
    end

    assign pready = psel && penable;
    assign pslverr = 1'b0;
    assign irq = irq_state;
    assign prdata = (paddr == 8'd0) ? {31'd0, enable}
                  : (paddr == 8'd4) ? {24'd0, compare}
                  : (paddr == 8'd8) ? {24'd0, count}
                  : {31'd0, irq_state};
endmodule
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (ip_dir / "list").mkdir(exist_ok=True)
    (ip_dir / "list" / f"{ip}.f").write_text(f"rtl/{ip}.sv\n", encoding="utf-8")

    payload = sim.run(ip, tmp_path)

    rtl = (ip_dir / "rtl" / f"{ip}.sv").read_text(encoding="utf-8")
    report = json.loads((ip_dir / "sim" / "starter_preview_sim.json").read_text(encoding="utf-8"))
    assert "always @(posedge clk or negedge rst_n)" in rtl
    assert "logic [7:0] count;" in rtl
    assert payload["status"] == "PASS"
    assert report["tests"] > 0
    assert report["fail"] == 0
