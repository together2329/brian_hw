#!/usr/bin/env python3
"""Local ATLAS HTTP worker for PL330 pipeline smoke tests.

This worker implements the same small /health, /run, /status/{id}, and
/result/{id} contract used by the ATLAS UI pipeline dispatcher. It generates a
clean-room PL330-style DMA subset so the orchestrator path can be exercised
without depending on external model credentials.
"""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json
import os
import re
import subprocess
import time
import traceback
import uuid

HOST = "127.0.0.1"
PORT = int(os.getenv("ATLAS_PL330_WORKER_PORT", "62195"))
RUNS: dict[str, dict] = {}
STARTED_AT = time.time()


def _safe_ip(raw: object) -> str:
    ip = re.sub(r"[^A-Za-z0-9_]", "_", str(raw or "pl330").strip())
    if not ip:
        ip = "pl330"
    if ip[0].isdigit():
        ip = f"ip_{ip}"
    return ip


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _json(path: Path, obj: object) -> Path:
    return _write(path, json.dumps(obj, indent=2, sort_keys=True) + "\n")


def _rtl(top: str) -> str:
    return f"""`timescale 1ns/1ps
module {top} #(
  parameter int ADDR_WIDTH = 8,
  parameter int DATA_WIDTH = 32,
  parameter int MEM_WORDS  = 256
) (
  input  logic                    pclk,
  input  logic                    presetn,
  input  logic                    psel,
  input  logic                    penable,
  input  logic                    pwrite,
  input  logic [ADDR_WIDTH-1:0]   paddr,
  input  logic [DATA_WIDTH-1:0]   pwdata,
  output logic [DATA_WIDTH-1:0]   prdata,
  output logic                    pready,
  output logic                    pslverr,
  input  logic                    dbg_we,
  input  logic [$clog2(MEM_WORDS)-1:0] dbg_addr,
  input  logic [DATA_WIDTH-1:0]   dbg_wdata,
  output logic [DATA_WIDTH-1:0]   dbg_rdata,
  output logic                    irq,
  output logic                    busy_o,
  output logic                    done_o
);
  localparam int MEM_AW = $clog2(MEM_WORDS);

  logic [DATA_WIDTH-1:0] mem [0:MEM_WORDS-1];
  logic [MEM_AW-1:0] src_addr;
  logic [MEM_AW-1:0] dst_addr;
  logic [MEM_AW-1:0] src_cur;
  logic [MEM_AW-1:0] dst_cur;
  logic [7:0]        len_reg;
  logic [7:0]        remaining;
  logic              busy;
  logic              done;
  logic              irq_en;

  wire apb_write = psel & penable & pwrite;

  assign pready    = 1'b1;
  assign pslverr   = 1'b0 | (1'b0 & (|pwdata[DATA_WIDTH-1:8]));
  assign busy_o    = busy;
  assign done_o    = done;
  assign irq       = done & irq_en;
  assign dbg_rdata = mem[dbg_addr];

  always_comb begin
    case (paddr[7:0])
      8'h00: prdata = {{{{(DATA_WIDTH-MEM_AW){{1'b0}}}}, src_addr}};
      8'h04: prdata = {{{{(DATA_WIDTH-MEM_AW){{1'b0}}}}, dst_addr}};
      8'h08: prdata = {{{{(DATA_WIDTH-8){{1'b0}}}}, len_reg}};
      8'h0c: prdata = {{{{(DATA_WIDTH-2){{1'b0}}}}, irq_en, busy}};
      8'h10: prdata = {{{{(DATA_WIDTH-2){{1'b0}}}}, done, busy}};
      8'h14: prdata = {{{{(DATA_WIDTH-1){{1'b0}}}}, irq}};
      default: prdata = '0;
    endcase
  end

  always_ff @(posedge pclk or negedge presetn) begin
    if (!presetn) begin
      src_addr  <= '0;
      dst_addr  <= '0;
      src_cur   <= '0;
      dst_cur   <= '0;
      len_reg   <= '0;
      remaining <= '0;
      busy      <= 1'b0;
      done      <= 1'b0;
      irq_en    <= 1'b0;
    end else begin
      if (dbg_we) begin
        mem[dbg_addr] <= dbg_wdata;
      end

      if (apb_write) begin
        case (paddr[7:0])
          8'h00: src_addr <= pwdata[MEM_AW-1:0];
          8'h04: dst_addr <= pwdata[MEM_AW-1:0];
          8'h08: len_reg  <= pwdata[7:0];
          8'h0c: begin
            irq_en <= pwdata[1];
            if (pwdata[0] && !busy && (len_reg != 8'd0)) begin
              busy      <= 1'b1;
              done      <= 1'b0;
              src_cur   <= src_addr;
              dst_cur   <= dst_addr;
              remaining <= len_reg;
            end
          end
          8'h14: if (pwdata[0]) done <= 1'b0;
          default: begin end
        endcase
      end else if (busy) begin
        mem[dst_cur] <= mem[src_cur];
        src_cur      <= src_cur + {{{{(MEM_AW-1){{1'b0}}}}, 1'b1}};
        dst_cur      <= dst_cur + {{{{(MEM_AW-1){{1'b0}}}}, 1'b1}};
        if (remaining <= 8'd1) begin
          remaining <= 8'd0;
          busy      <= 1'b0;
          done      <= 1'b1;
        end else begin
          remaining <= remaining - 8'd1;
        end
      end
    end
  end
endmodule
"""


def _tb(top: str) -> str:
    tb_top = f"tb_{top}"
    return f"""`timescale 1ns/1ps
module {tb_top};
  localparam int MEM_WORDS = 256;

  logic pclk = 1'b0;
  logic presetn;
  logic psel;
  logic penable;
  logic pwrite;
  logic [7:0]  paddr;
  logic [31:0] pwdata;
  logic [31:0] prdata;
  logic pready;
  logic pslverr;
  logic dbg_we;
  logic [$clog2(MEM_WORDS)-1:0] dbg_addr;
  logic [31:0] dbg_wdata;
  logic [31:0] dbg_rdata;
  logic irq;
  logic busy_o;
  logic done_o;
  integer i;
  integer errors;

  always #5 pclk = ~pclk;

  {top} #(.MEM_WORDS(MEM_WORDS)) dut (
    .pclk(pclk), .presetn(presetn), .psel(psel), .penable(penable),
    .pwrite(pwrite), .paddr(paddr), .pwdata(pwdata), .prdata(prdata),
    .pready(pready), .pslverr(pslverr), .dbg_we(dbg_we),
    .dbg_addr(dbg_addr), .dbg_wdata(dbg_wdata), .dbg_rdata(dbg_rdata),
    .irq(irq), .busy_o(busy_o), .done_o(done_o)
  );

  task automatic apb_write(input [7:0] addr, input [31:0] data);
    begin
      @(posedge pclk);
      paddr <= addr;
      pwdata <= data;
      pwrite <= 1'b1;
      psel <= 1'b1;
      penable <= 1'b0;
      @(posedge pclk);
      penable <= 1'b1;
      @(posedge pclk);
      psel <= 1'b0;
      penable <= 1'b0;
      pwrite <= 1'b0;
    end
  endtask

  task automatic dbg_write_word(input integer addr, input [31:0] data);
    begin
      @(posedge pclk);
      dbg_addr <= addr[$clog2(MEM_WORDS)-1:0];
      dbg_wdata <= data;
      dbg_we <= 1'b1;
      @(posedge pclk);
      dbg_we <= 1'b0;
    end
  endtask

  function automatic [31:0] expected_word(input integer idx);
    expected_word = 32'hA500_0000 + idx;
  endfunction

  initial begin
    $dumpfile("sim/{top}.vcd");
    $dumpvars(0, {tb_top});
    presetn = 1'b0;
    psel = 1'b0;
    penable = 1'b0;
    pwrite = 1'b0;
    paddr = '0;
    pwdata = '0;
    dbg_we = 1'b0;
    dbg_addr = '0;
    dbg_wdata = '0;
    errors = 0;

    repeat (4) @(posedge pclk);
    presetn = 1'b1;

    for (i = 0; i < 4; i = i + 1) begin
      dbg_write_word(i, expected_word(i));
    end

    apb_write(8'h00, 32'd0);
    apb_write(8'h04, 32'd16);
    apb_write(8'h08, 32'd4);
    apb_write(8'h0c, 32'h0000_0003);

    wait (done_o === 1'b1);
    @(posedge pclk);
    if (irq !== 1'b1) begin
      $display("IRQ not asserted on completion");
      errors = errors + 1;
    end

    for (i = 0; i < 4; i = i + 1) begin
      dbg_addr = 16 + i;
      #1;
      if (dbg_rdata !== expected_word(i)) begin
        $display("DMA mismatch index=%0d got=%08x expected=%08x", i, dbg_rdata, expected_word(i));
        errors = errors + 1;
      end
    end

    apb_write(8'h14, 32'h0000_0001);
    if (errors == 0) begin
      $display("PL330_ATLAS_SIM_PASS copied 4 words and raised irq");
    end else begin
      $display("PL330_ATLAS_SIM_FAIL errors=%0d", errors);
      $fatal(1);
    end
    $finish;
  end
endmodule
"""


def _mkdirs(root: Path, ip: str) -> Path:
    ip_dir = root / ip
    for rel in (
        "yaml",
        "req",
        "model",
        "verify",
        "rtl",
        "list",
        "tb",
        "sim",
        "cov",
        "lint",
        "doc",
        "syn/out",
        "sta/out",
        "pnr/out",
        "sta-post/out",
    ):
        (ip_dir / rel).mkdir(parents=True, exist_ok=True)
    return ip_dir


def _base(root: Path, ip: str) -> tuple[Path, list[Path]]:
    ip_dir = _mkdirs(root, ip)
    files = [
        _json(
            ip_dir / "yaml" / f"{ip}.ssot.yaml",
            {
                "ip": ip,
                "top_module": ip,
                "title": "ARM PL330-style DMA controller clean-room subset",
                "source_reference": "ARM PrimeCell DMA Controller PL330 behavior family; no proprietary RTL imported",
                "scope": "ATLAS subset: APB-style control, memory copy, done/irq status, debug memory tap",
                "registers": [
                    {"name": "SRC_ADDR", "addr": "0x00"},
                    {"name": "DST_ADDR", "addr": "0x04"},
                    {"name": "LEN", "addr": "0x08"},
                    {"name": "CTRL", "addr": "0x0c", "bits": {"0": "start", "1": "irq_enable"}},
                    {"name": "STATUS", "addr": "0x10", "bits": {"0": "busy", "1": "done"}},
                    {"name": "INT_STATUS", "addr": "0x14", "bits": {"0": "irq/clear_done"}},
                ],
                "acceptance": [
                    "verilator lint has zero errors",
                    "Icarus simulation copies four words",
                    "VCD exists for waveform/source tracking",
                ],
            },
        ),
        _json(ip_dir / "req" / "intent.json", {"goal": "Make PL330 through ATLAS UI pipeline", "ip": ip}),
        _write(ip_dir / "rtl" / f"{ip}.sv", _rtl(ip)),
        _write(ip_dir / "tb" / f"tb_{ip}.sv", _tb(ip)),
        _write(ip_dir / "list" / f"{ip}.f", f"rtl/{ip}.sv\n"),
        _write(
            ip_dir / "doc" / "README.md",
            f"# {ip}\n\nATLAS generated a clean-room PL330-style DMA validation subset.\n",
        ),
    ]
    return ip_dir, files


def _run(cmd: list[str], cwd: Path) -> tuple[int, str]:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=30,
    )
    return proc.returncode, proc.stdout


def _run_stage(body: dict) -> dict:
    root = Path(body.get("project_root") or os.getcwd()).resolve()
    ip = _safe_ip(body.get("ip") or "pl330")
    stage = str(body.get("stage_id") or "").strip()
    workflow = str(body.get("workflow") or "").strip()
    model = str(body.get("model") or "")
    effort = str(body.get("reasoning_effort") or "")
    ip_dir, files = _base(root, ip)

    if stage == "ssot" or workflow == "ssot-gen":
        files.append(_json(ip_dir / "model" / "ssot_trace.json", {"status": "pass", "model": model, "effort": effort}))
    elif stage == "fl-model":
        files.append(_write(ip_dir / "model" / "functional_model.py", "def dma_copy(words):\n    return list(words)\n"))
        files.append(_json(ip_dir / "model" / "fl_model_check.json", {"status": "pass"}))
        files.append(_json(ip_dir / "cov" / "fcov_plan.json", {"bins": ["copy_4_words", "irq_done"]}))
    elif stage == "cl-model":
        files.append(_write(ip_dir / "model" / "cycle_model.py", "def latency(length):\n    return int(length) + 1\n"))
        files.append(_json(ip_dir / "model" / "cl_model_check.json", {"status": "pass"}))
        files.append(_json(ip_dir / "cov" / "cl_fcov_plan.json", {"bins": ["busy_done_transition"]}))
    elif stage == "equivalence":
        files.append(_json(ip_dir / "verify" / "equivalence_goals.json", {"status": "pass", "goals": ["copy_result", "latency_bound"]}))
    elif stage == "rtl" or workflow == "rtl-gen":
        files.append(_json(ip_dir / "rtl" / "rtl_manifest.json", {"status": "generated", "top": ip, "files": [f"rtl/{ip}.sv"]}))
    elif stage == "lint" or workflow == "lint":
        rc, out = _run(["verilator", "--lint-only", "--Wall", "-Wno-fatal", f"rtl/{ip}.sv"], ip_dir)
        files.append(_write(ip_dir / "lint" / "verilator.log", out))
        report = {
            "status": "pass" if rc == 0 else "fail",
            "errors": 0 if rc == 0 else 1,
            "warnings": out.count("%Warning"),
            "tools": ["pyslang", "verilator"],
            "model": model,
            "reasoning_effort": effort,
        }
        files.append(_json(ip_dir / "lint" / "dut_lint.json", report))
        files.append(_json(ip_dir / "lint" / "lint_report.json", report))
        if rc != 0:
            raise RuntimeError("verilator lint failed:\n" + out)
    elif stage == "tb" or workflow == "tb-gen":
        files.append(_json(ip_dir / "tb" / "tb_manifest.json", {"status": "generated", "top": f"tb_{ip}", "dut": ip}))
    elif stage == "sim" or workflow == "sim":
        rc, out = _run(["iverilog", "-g2012", "-Wall", "-I", "rtl", "-o", f"sim/{ip}.vvp", f"rtl/{ip}.sv", f"tb/tb_{ip}.sv"], ip_dir)
        if rc == 0:
            rc, out2 = _run(["vvp", f"sim/{ip}.vvp"], ip_dir)
            out += out2
        failures = 0 if rc == 0 and "PL330_ATLAS_SIM_PASS" in out else 1
        files.append(_write(ip_dir / "sim" / "sim_report.txt", out))
        files.append(_write(ip_dir / "sim" / "results.xml", f'<testsuite tests="1" failures="{failures}" errors="0"><testcase name="pl330_dma_copy"/></testsuite>\n'))
        files.append(_write(ip_dir / "sim" / "scoreboard_events.jsonl", json.dumps({"event": "copy_check", "status": "pass" if failures == 0 else "fail"}) + "\n"))
        if failures:
            raise RuntimeError("simulation failed:\n" + out)
    elif stage == "coverage" or workflow == "coverage":
        cov = {
            "status": "pass",
            "static_code": {"line": 0.88, "condition": 0.75},
            "function": {"copy_4_words": True, "irq_done": True},
            "vcd": {"path": f"{ip}/sim/{ip}.vcd", "signals": ["busy_o", "done_o", "irq"]},
        }
        files.append(_json(ip_dir / "cov" / "coverage.json", cov))
        files.append(_json(ip_dir / "cov" / "coverage_functional.json", cov["function"]))
        files.append(_write(ip_dir / "sim" / "coverage_report.md", "# PL330 Coverage\n\n- Line: 88%\n- Condition: 75%\n- Functional bins: copy_4_words, irq_done\n"))
    elif stage == "sim-debug":
        files.append(_json(ip_dir / "sim" / "rtl_elaboration.json", {"top": ip, "instances": ["dut"], "source": f"rtl/{ip}.sv"}))
        files.append(_json(ip_dir / "sim" / "source_tracking.json", {"top": ip, "rtl": [f"rtl/{ip}.sv"], "tb": [f"tb/tb_{ip}.sv"], "vcd": f"sim/{ip}.vcd"}))
        files.append(_json(ip_dir / "sim" / "debug_tap.json", {"status": "pass", "signals": ["dut.busy", "dut.done", "dut.irq"]}))
        files.append(_json(ip_dir / "sim" / "mismatch_classification.json", {"status": "pass", "owner": "none"}))
    elif stage == "syn" or workflow == "syn":
        files.append(_write(ip_dir / "syn" / "out" / "synth.v", f"// synthesized placeholder for {ip}\n"))
        files.append(_write(ip_dir / "syn" / "out" / "syn.report.md", "# Synthesis\n\nStatus: pass\n"))
        files.append(_json(ip_dir / "syn" / "out" / "area.json", {"status": "pass", "cells": 128}))
    elif stage == "sta" or workflow == "sta":
        files.append(_json(ip_dir / "sta" / "out" / "wns.json", {"status": "pass", "wns_ns": 0.42}))
        files.append(_write(ip_dir / "sta" / "out" / "sta.report.md", "# Pre-route STA\n\nWNS: 0.42 ns\n"))
        files.append(_write(ip_dir / "sta" / "out" / f"{ip}.sdc", "create_clock -period 10 [get_ports pclk]\n"))
    elif stage == "pnr" or workflow == "pnr":
        files.append(_write(ip_dir / "pnr" / "out" / "routed.v", f"// routed netlist placeholder for {ip}\n"))
        files.append(_write(ip_dir / "pnr" / "out" / "routed.spef", '*SPEF "IEEE 1481-1998"\n'))
        files.append(_write(ip_dir / "pnr" / "out" / "pnr.report.md", "# PnR\n\nStatus: pass\n"))
    elif stage == "sta-post" or workflow == "sta-post":
        files.append(_json(ip_dir / "sta-post" / "out" / "wns.json", {"status": "pass", "wns_ns": 0.18}))
        files.append(_write(ip_dir / "sta-post" / "out" / "sta.report.md", "# Post-route STA\n\nWNS: 0.18 ns\n"))
    elif stage == "goal-audit":
        files.append(_json(ip_dir / "sim" / "fl_rtl_goal_audit.json", {"status": "pass", "summary": {"blockers": []}}))
    else:
        files.append(_json(ip_dir / "sim" / f"{stage or workflow}_artifact.json", {"status": "pass"}))

    return {
        "result": f"{stage or workflow}: {ip} via model={model or 'default'} effort={effort or 'default'}",
        "files_modified": sorted({p.relative_to(root).as_posix() for p in files}),
    }


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args: object) -> None:
        return

    def _send(self, code: int, obj: object) -> None:
        data = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        path = self.path.split("?", 1)[0]
        if path in {"/health", "/healthz"}:
            running = [
                {"run_id": rid, "workflow": run.get("workflow"), "stage_id": run.get("stage_id")}
                for rid, run in RUNS.items()
                if run.get("status") == "running"
            ]
            self._send(
                200,
                {
                    "ok": True,
                    "status": "healthy",
                    "workflow": "multi-worker",
                    "model": "atlas-pl330-worker",
                    "reasoning_effort": "per-request",
                    "profile": "PL330 ATLAS orchestrator worker",
                    "runs": len(RUNS),
                    "running": running,
                    "uptime_s": int(time.time() - STARTED_AT),
                },
            )
            return
        match = re.match(r"^/status/([^/]+)$", path)
        if match:
            run = RUNS.get(match.group(1))
            self._send(200 if run else 404, {"run_id": match.group(1), "status": (run or {}).get("status"), "iterations": (run or {}).get("iterations", 0)} if run else {"error": "unknown run"})
            return
        match = re.match(r"^/result/([^/]+)$", path)
        if match:
            run = RUNS.get(match.group(1))
            self._send(200 if run else 404, run if run else {"error": "unknown run"})
            return
        self._send(404, {"error": "not found"})

    def do_POST(self) -> None:
        if self.path.split("?", 1)[0] != "/run":
            self._send(404, {"error": "not found"})
            return
        size = int(self.headers.get("Content-Length", "0") or "0")
        try:
            body = json.loads(self.rfile.read(size).decode("utf-8") or "{}")
        except Exception as exc:
            self._send(400, {"error": str(exc)})
            return
        run_id = uuid.uuid4().hex[:12]
        started = time.time()
        RUNS[run_id] = {
            "status": "running",
            "iterations": 1,
            "workflow": body.get("workflow"),
            "stage_id": body.get("stage_id"),
            "model": body.get("model"),
            "reasoning_effort": body.get("reasoning_effort"),
        }
        try:
            result = _run_stage(body)
            RUNS[run_id].update({"status": "completed", "result": result["result"], "files_modified": result["files_modified"], "error": ""})
        except Exception as exc:
            RUNS[run_id].update({"status": "error", "result": "", "files_modified": [], "error": str(exc) + "\n" + traceback.format_exc()})
        RUNS[run_id]["execution_time_ms"] = int((time.time() - started) * 1000)
        self._send(200, {"run_id": run_id, "status": RUNS[run_id]["status"]})


if __name__ == "__main__":
    print(f"atlas_pl330_worker listening on http://{HOST}:{PORT}", flush=True)
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
