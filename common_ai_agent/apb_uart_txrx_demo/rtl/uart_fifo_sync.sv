`timescale 1ns/1ps
// uart_fifo_sync.sv — small single-clock FIFO for APB UART TX/RX buffering.
//
// Semantics:
// - push is accepted when FIFO is not full, or when full and a valid pop occurs
//   in the same cycle.
// - pop is accepted only when FIFO is not empty.
// - push+pop on an empty FIFO records underflow_pulse for the invalid pop and
//   still accepts the push; the newly pushed byte is visible on later cycles.
// - push+pop on a full FIFO preserves full level, returns the oldest byte, and
//   enqueues the new byte at the tail.
module uart_fifo_sync #(
  parameter integer DATA_WIDTH  = 8,
  parameter integer DEPTH       = 4,
  parameter integer PTR_WIDTH   = (DEPTH <= 1) ? 1 : $clog2(DEPTH),
  parameter integer LEVEL_WIDTH = (DEPTH <= 1) ? 1 : $clog2(DEPTH + 1)
) (
  input  logic                    clk,
  input  logic                    reset_n,
  input  logic                    clear,

  input  logic                    push,
  input  logic [DATA_WIDTH-1:0]   push_data,
  input  logic                    pop,

  output logic [DATA_WIDTH-1:0]   pop_data,
  output logic                    full,
  output logic                    empty,
  output logic [LEVEL_WIDTH-1:0]  level,
  output logic                    overflow_pulse,
  output logic                    underflow_pulse
);
  logic [DATA_WIDTH-1:0] mem [0:DEPTH-1];
  logic [PTR_WIDTH-1:0] rd_ptr;
  logic [PTR_WIDTH-1:0] wr_ptr;
  logic [LEVEL_WIDTH-1:0] count;

  wire pop_accept  = pop && (count != {LEVEL_WIDTH{1'b0}});
  wire push_accept = push && ((count != DEPTH[LEVEL_WIDTH-1:0]) || pop_accept);

  assign empty = (count == {LEVEL_WIDTH{1'b0}});
  assign full  = (count == DEPTH[LEVEL_WIDTH-1:0]);
  assign level = count;
  assign pop_data = empty ? {DATA_WIDTH{1'b0}} : mem[rd_ptr];

  function automatic [PTR_WIDTH-1:0] ptr_next(input [PTR_WIDTH-1:0] ptr);
    begin
      if (ptr == (DEPTH-1)[PTR_WIDTH-1:0]) begin
        ptr_next = {PTR_WIDTH{1'b0}};
      end else begin
        ptr_next = ptr + {{(PTR_WIDTH-1){1'b0}}, 1'b1};
      end
    end
  endfunction

  always_ff @(posedge clk or negedge reset_n) begin
    if (!reset_n) begin
      rd_ptr <= {PTR_WIDTH{1'b0}};
      wr_ptr <= {PTR_WIDTH{1'b0}};
      count  <= {LEVEL_WIDTH{1'b0}};
      overflow_pulse  <= 1'b0;
      underflow_pulse <= 1'b0;
    end else begin
      overflow_pulse  <= 1'b0;
      underflow_pulse <= 1'b0;

      if (clear) begin
        rd_ptr <= {PTR_WIDTH{1'b0}};
        wr_ptr <= {PTR_WIDTH{1'b0}};
        count  <= {LEVEL_WIDTH{1'b0}};
      end else begin
        overflow_pulse  <= push && full && !pop_accept;
        underflow_pulse <= pop && empty;

        if (push_accept) begin
          mem[wr_ptr] <= push_data;
          wr_ptr <= ptr_next(wr_ptr);
        end
        if (pop_accept) begin
          rd_ptr <= ptr_next(rd_ptr);
        end

        case ({push_accept, pop_accept})
          2'b10: count <= count + {{(LEVEL_WIDTH-1){1'b0}}, 1'b1};
          2'b01: count <= count - {{(LEVEL_WIDTH-1){1'b0}}, 1'b1};
          default: count <= count;
        endcase
      end
    end
  end
endmodule
