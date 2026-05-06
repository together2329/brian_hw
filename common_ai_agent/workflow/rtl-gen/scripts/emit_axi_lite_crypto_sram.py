#!/usr/bin/env python3
"""Emit SSOT-driven AXI4-Lite encrypted SRAM RTL and gate evidence.

This is a workflow recovery emitter for memory-like AXI4-Lite SRAM IPs. It
does not replace rtl-gen's LLM path; it gives ATLAS a deterministic fallback
when the SSOT clearly describes the supported archetype and the agent loop
stalls before producing lintable DUT RTL.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml


def _load_ssot(ip_dir: Path, ip: str) -> dict[str, Any]:
    path = ip_dir / "yaml" / f"{ip}.ssot.yaml"
    if not path.is_file():
        raise SystemExit(f"missing SSOT YAML: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise SystemExit(f"invalid SSOT YAML root: {path}")
    return data


def _param_default(params: list[dict[str, Any]], name: str, fallback: str) -> str:
    for item in params:
        if isinstance(item, dict) and item.get("name") == name and item.get("default") is not None:
            return str(item["default"])
    return fallback


def _rtl_sources(ip: str, data_width: str, addr_width: str, strb_width: str, key: str) -> dict[str, str]:
    pkg = f"""package {ip}_pkg;
  typedef logic [1:0] axi_resp_t;
  localparam axi_resp_t AXI_RESP_OKAY = 2'b00;
  localparam axi_resp_t AXI_RESP_SLVERR = 2'b10;
  typedef enum logic [2:0] {{
    AXI_IDLE,
    AXI_WRITE_ACCEPT,
    AXI_WRITE_RESP,
    AXI_READ_ACCEPT,
    AXI_READ_RESP
  }} axi_lite_state_e;
  function automatic logic axi_resp_ok(input axi_resp_t resp);
    axi_resp_ok = (resp == AXI_RESP_OKAY);
  endfunction
endpackage
"""

    axi_slv = f"""module {ip}_axi_slv (
  input  logic awvalid,
  input  logic wvalid,
  input  logic bvalid,
  input  logic arvalid,
  input  logic rvalid,
  output logic awready,
  output logic wready,
  output logic arready,
  output logic wr_fire,
  output logic rd_fire
);
  assign wr_fire = awvalid & wvalid & ~bvalid;
  assign rd_fire = arvalid & ~rvalid;
  assign awready = wr_fire;
  assign wready = wr_fire;
  assign arready = rd_fire;
endmodule
"""

    crypto = f"""module {ip}_crypto #(
  parameter int DATA_WIDTH = {data_width},
  parameter bit CRYPTO_ENABLE = 1'b1,
  parameter logic [DATA_WIDTH-1:0] CRYPTO_KEY = {key}
) (
  input  logic [DATA_WIDTH-1:0] data_i,
  output logic [DATA_WIDTH-1:0] data_o
);
  assign data_o = CRYPTO_ENABLE ? (data_i ^ CRYPTO_KEY) : data_i;
endmodule
"""

    mem = f"""module {ip}_mem #(
  parameter int DATA_WIDTH = {data_width},
  parameter int ADDR_WIDTH = {addr_width},
  parameter bit RESET_MEMORY = 1'b0
) (
  input  logic                  aclk,
  input  logic                  aresetn,
  input  logic                  we,
  input  logic [ADDR_WIDTH-1:0] waddr,
  input  logic [DATA_WIDTH-1:0] wdata,
  input  logic [ADDR_WIDTH-1:0] raddr,
  output logic [DATA_WIDTH-1:0] rdata
);
  localparam int DEPTH = 1 << ADDR_WIDTH;

  logic [DATA_WIDTH-1:0] storage [0:DEPTH-1];
  integer idx;

  always_ff @(posedge aclk or negedge aresetn) begin
    if (!aresetn) begin
      if (RESET_MEMORY) begin
        for (idx = 0; idx < DEPTH; idx = idx + 1) begin
          storage[idx] <= '0;
        end
      end
    end else if (we) begin
      storage[waddr] <= wdata;
    end
  end

  assign rdata = storage[raddr];
endmodule
"""

    core = f"""module {ip}_core #(
  parameter int DATA_WIDTH = {data_width},
  parameter int ADDR_WIDTH = {addr_width},
  parameter int STRB_WIDTH = {strb_width},
  parameter bit CRYPTO_ENABLE = 1'b1,
  parameter logic [DATA_WIDTH-1:0] CRYPTO_KEY = {key},
  parameter bit DEBUG_ENABLE = 1'b1,
  parameter bit RESET_MEMORY = 1'b0
) (
  input  logic                    aclk,
  input  logic                    aresetn,
  input  logic [ADDR_WIDTH+1:0]   s_axi_awaddr,
  input  logic                    s_axi_awvalid,
  output logic                    s_axi_awready,
  input  logic [DATA_WIDTH-1:0]   s_axi_wdata,
  input  logic [STRB_WIDTH-1:0]   s_axi_wstrb,
  input  logic                    s_axi_wvalid,
  output logic                    s_axi_wready,
  output logic [1:0]              s_axi_bresp,
  output logic                    s_axi_bvalid,
  input  logic                    s_axi_bready,
  input  logic [ADDR_WIDTH+1:0]   s_axi_araddr,
  input  logic                    s_axi_arvalid,
  output logic                    s_axi_arready,
  output logic [DATA_WIDTH-1:0]   s_axi_rdata,
  output logic [1:0]              s_axi_rresp,
  output logic                    s_axi_rvalid,
  input  logic                    s_axi_rready,
  output logic                    dbg_crypto_active,
  output logic [DATA_WIDTH-1:0]   dbg_raw_word
);
  import {ip}_pkg::*;

  logic wr_fire;
  logic rd_fire;
  logic [ADDR_WIDTH-1:0] wr_index;
  logic [ADDR_WIDTH-1:0] rd_index;
  logic [ADDR_WIDTH-1:0] mem_raddr;
  logic [DATA_WIDTH-1:0] raw_old_word;
  logic [DATA_WIDTH-1:0] old_plain_word;
  logic [DATA_WIDTH-1:0] merged_plain_word;
  logic [DATA_WIDTH-1:0] encrypted_write_word;
  logic [DATA_WIDTH-1:0] read_plain_word;
  logic [1:0] write_response;
  logic [1:0] read_response;

  assign wr_index = s_axi_awaddr[ADDR_WIDTH+1:2];
  assign rd_index = s_axi_araddr[ADDR_WIDTH+1:2];
  assign mem_raddr = wr_fire ? wr_index : rd_index;
  assign write_response = (s_axi_awaddr[1:0] == 2'b00) ? AXI_RESP_OKAY : AXI_RESP_SLVERR;
  assign read_response = (s_axi_araddr[1:0] == 2'b00) ? AXI_RESP_OKAY : AXI_RESP_SLVERR;
  assign dbg_crypto_active = CRYPTO_ENABLE;
  assign dbg_raw_word = DEBUG_ENABLE ? raw_old_word : '0;

  {ip}_axi_slv u_axi_slv (
    .awvalid(s_axi_awvalid),
    .wvalid(s_axi_wvalid),
    .bvalid(s_axi_bvalid),
    .arvalid(s_axi_arvalid),
    .rvalid(s_axi_rvalid),
    .awready(s_axi_awready),
    .wready(s_axi_wready),
    .arready(s_axi_arready),
    .wr_fire(wr_fire),
    .rd_fire(rd_fire)
  );

  {ip}_crypto #(
    .DATA_WIDTH(DATA_WIDTH),
    .CRYPTO_ENABLE(CRYPTO_ENABLE),
    .CRYPTO_KEY(CRYPTO_KEY)
  ) u_decrypt_old (
    .data_i(raw_old_word),
    .data_o(old_plain_word)
  );

  {ip}_crypto #(
    .DATA_WIDTH(DATA_WIDTH),
    .CRYPTO_ENABLE(CRYPTO_ENABLE),
    .CRYPTO_KEY(CRYPTO_KEY)
  ) u_encrypt_write (
    .data_i(merged_plain_word),
    .data_o(encrypted_write_word)
  );

  {ip}_crypto #(
    .DATA_WIDTH(DATA_WIDTH),
    .CRYPTO_ENABLE(CRYPTO_ENABLE),
    .CRYPTO_KEY(CRYPTO_KEY)
  ) u_decrypt_read (
    .data_i(raw_old_word),
    .data_o(read_plain_word)
  );

  {ip}_mem #(
    .DATA_WIDTH(DATA_WIDTH),
    .ADDR_WIDTH(ADDR_WIDTH),
    .RESET_MEMORY(RESET_MEMORY)
  ) u_mem (
    .aclk(aclk),
    .aresetn(aresetn),
    .we(wr_fire),
    .waddr(wr_index),
    .wdata(encrypted_write_word),
    .raddr(mem_raddr),
    .rdata(raw_old_word)
  );

  always_comb begin
    merged_plain_word = old_plain_word;
    for (int byte_idx = 0; byte_idx < STRB_WIDTH; byte_idx = byte_idx + 1) begin
      if (s_axi_wstrb[byte_idx]) begin
        merged_plain_word[byte_idx*8 +: 8] = s_axi_wdata[byte_idx*8 +: 8];
      end
    end
  end

  always_ff @(posedge aclk or negedge aresetn) begin
    if (!aresetn) begin
      s_axi_bvalid <= 1'b0;
      s_axi_bresp <= AXI_RESP_OKAY;
      s_axi_rvalid <= 1'b0;
      s_axi_rdata <= '0;
      s_axi_rresp <= AXI_RESP_OKAY;
    end else begin
      if (wr_fire) begin
        s_axi_bvalid <= 1'b1;
        s_axi_bresp <= write_response;
      end else if (s_axi_bvalid && s_axi_bready) begin
        s_axi_bvalid <= 1'b0;
      end

      if (rd_fire) begin
        s_axi_rvalid <= 1'b1;
        s_axi_rdata <= read_plain_word;
        s_axi_rresp <= read_response;
      end else if (s_axi_rvalid && s_axi_rready) begin
        s_axi_rvalid <= 1'b0;
      end
    end
  end
endmodule
"""

    top = f"""module {ip} #(
  parameter int DATA_WIDTH = {data_width},
  parameter int ADDR_WIDTH = {addr_width},
  parameter int STRB_WIDTH = {strb_width},
  parameter bit CRYPTO_ENABLE = 1'b1,
  parameter logic [DATA_WIDTH-1:0] CRYPTO_KEY = {key},
  parameter bit DEBUG_ENABLE = 1'b1,
  parameter bit RESET_MEMORY = 1'b0
) (
  input  logic                    aclk,
  input  logic                    aresetn,
  input  logic [ADDR_WIDTH+1:0]   s_axi_awaddr,
  input  logic                    s_axi_awvalid,
  output logic                    s_axi_awready,
  input  logic [DATA_WIDTH-1:0]   s_axi_wdata,
  input  logic [STRB_WIDTH-1:0]   s_axi_wstrb,
  input  logic                    s_axi_wvalid,
  output logic                    s_axi_wready,
  output logic [1:0]              s_axi_bresp,
  output logic                    s_axi_bvalid,
  input  logic                    s_axi_bready,
  input  logic [ADDR_WIDTH+1:0]   s_axi_araddr,
  input  logic                    s_axi_arvalid,
  output logic                    s_axi_arready,
  output logic [DATA_WIDTH-1:0]   s_axi_rdata,
  output logic [1:0]              s_axi_rresp,
  output logic                    s_axi_rvalid,
  input  logic                    s_axi_rready,
  output logic                    dbg_crypto_active,
  output logic [DATA_WIDTH-1:0]   dbg_raw_word
);
  {ip}_core #(
    .DATA_WIDTH(DATA_WIDTH),
    .ADDR_WIDTH(ADDR_WIDTH),
    .STRB_WIDTH(STRB_WIDTH),
    .CRYPTO_ENABLE(CRYPTO_ENABLE),
    .CRYPTO_KEY(CRYPTO_KEY),
    .DEBUG_ENABLE(DEBUG_ENABLE),
    .RESET_MEMORY(RESET_MEMORY)
  ) u_core (
    .aclk(aclk),
    .aresetn(aresetn),
    .s_axi_awaddr(s_axi_awaddr),
    .s_axi_awvalid(s_axi_awvalid),
    .s_axi_awready(s_axi_awready),
    .s_axi_wdata(s_axi_wdata),
    .s_axi_wstrb(s_axi_wstrb),
    .s_axi_wvalid(s_axi_wvalid),
    .s_axi_wready(s_axi_wready),
    .s_axi_bresp(s_axi_bresp),
    .s_axi_bvalid(s_axi_bvalid),
    .s_axi_bready(s_axi_bready),
    .s_axi_araddr(s_axi_araddr),
    .s_axi_arvalid(s_axi_arvalid),
    .s_axi_arready(s_axi_arready),
    .s_axi_rdata(s_axi_rdata),
    .s_axi_rresp(s_axi_rresp),
    .s_axi_rvalid(s_axi_rvalid),
    .s_axi_rready(s_axi_rready),
    .dbg_crypto_active(dbg_crypto_active),
    .dbg_raw_word(dbg_raw_word)
  );
endmodule
"""

    return {
        f"{ip}_pkg.sv": pkg,
        f"{ip}_axi_slv.sv": axi_slv,
        f"{ip}_crypto.sv": crypto,
        f"{ip}_mem.sv": mem,
        f"{ip}_core.sv": core,
        f"{ip}.sv": top,
    }


def _run(command: list[str], cwd: Path) -> int:
    proc = subprocess.run(command, cwd=cwd, text=True)
    return proc.returncode


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("ip")
    parser.add_argument("--root", default=".")
    parser.add_argument("--no-gates", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    ip_dir = root / args.ip
    ssot = _load_ssot(ip_dir, args.ip)
    top = ssot.get("top_module") if isinstance(ssot.get("top_module"), dict) else {}
    features = ssot.get("features") if isinstance(ssot.get("features"), (dict, list)) else {}
    io_list = ssot.get("io_list") if isinstance(ssot.get("io_list"), dict) else {}
    ssot_text = f"{top} {features} {io_list} {ssot.get('memory')}"
    supported = "axi" in ssot_text.lower() and "memory" in str(top.get("type", "")).lower()
    if not supported:
        raise SystemExit("SSOT is not the supported AXI4-Lite memory archetype")

    params = ssot.get("parameters") if isinstance(ssot.get("parameters"), list) else []
    data_width = _param_default(params, "DATA_WIDTH", "32")
    addr_width = _param_default(params, "ADDR_WIDTH", "8")
    strb_width = _param_default(params, "STRB_WIDTH", "DATA_WIDTH/8")
    key = _param_default(params, "CRYPTO_KEY", "32'hA5A5_5A5A")

    rtl_dir = ip_dir / "rtl"
    list_dir = ip_dir / "list"
    rtl_dir.mkdir(parents=True, exist_ok=True)
    list_dir.mkdir(parents=True, exist_ok=True)

    sources = _rtl_sources(args.ip, data_width, addr_width, strb_width, key)
    for filename, text in sources.items():
        (rtl_dir / filename).write_text(text, encoding="utf-8")

    ordered = [
        f"rtl/{args.ip}_pkg.sv",
        f"rtl/{args.ip}_axi_slv.sv",
        f"rtl/{args.ip}_crypto.sv",
        f"rtl/{args.ip}_mem.sv",
        f"rtl/{args.ip}_core.sv",
        f"rtl/{args.ip}.sv",
    ]
    (list_dir / f"{args.ip}.f").write_text("\n".join(ordered) + "\n", encoding="utf-8")
    print(f"[emit_axi_lite_crypto_sram] emitted {len(ordered)} RTL files for {args.ip}")

    if args.no_gates:
        return 0
    compile_script = Path(__file__).with_name("rtl_compile_report.py")
    lint_script = Path(__file__).parents[2] / "lint" / "scripts" / "dut_lint_report.py"
    rc_compile = _run([sys.executable, str(compile_script), args.ip, "--top", args.ip, "--project-root", str(root)], root)
    rc_lint = _run([sys.executable, str(lint_script), args.ip, "--top", args.ip], root)
    return 0 if rc_compile == 0 and rc_lint == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
