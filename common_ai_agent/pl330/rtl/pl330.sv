`timescale 1ns/1ps
module pl330 #(
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
      8'h00: prdata = {{(DATA_WIDTH-MEM_AW){1'b0}}, src_addr};
      8'h04: prdata = {{(DATA_WIDTH-MEM_AW){1'b0}}, dst_addr};
      8'h08: prdata = {{(DATA_WIDTH-8){1'b0}}, len_reg};
      8'h0c: prdata = {{(DATA_WIDTH-2){1'b0}}, irq_en, busy};
      8'h10: prdata = {{(DATA_WIDTH-2){1'b0}}, done, busy};
      8'h14: prdata = {{(DATA_WIDTH-1){1'b0}}, irq};
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
        src_cur      <= src_cur + {{(MEM_AW-1){1'b0}}, 1'b1};
        dst_cur      <= dst_cur + {{(MEM_AW-1){1'b0}}, 1'b1};
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
