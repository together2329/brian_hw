module arm_m0_min_mem_if #(
    parameter integer XLEN = 32
) (
    input  logic             is_ldr,
    input  logic             is_str,
    input  logic [XLEN-1:0]  base_addr,
    input  logic [XLEN-1:0]  imm_ext,
    input  logic [XLEN-1:0]  store_data,
    output logic [XLEN-1:0]  d_haddr,
    output logic [1:0]       d_htrans,
    output logic             d_hwrite,
    output logic [2:0]       d_hsize,
    output logic [2:0]       d_hburst,
    output logic [3:0]       d_hprot,
    output logic             d_hmastlock,
    output logic [XLEN-1:0]  d_hwdata
);

    localparam [1:0] HTRANS_IDLE   = 2'b00,
                     HTRANS_NONSEQ = 2'b10;

    logic mem_req;
    assign mem_req = is_ldr | is_str;

    assign d_haddr     = base_addr + imm_ext;
    assign d_htrans    = mem_req ? HTRANS_NONSEQ : HTRANS_IDLE;
    assign d_hwrite    = is_str;
    assign d_hsize     = 3'b010;
    assign d_hburst    = 3'b000;
    assign d_hprot     = 4'b0011;
    assign d_hmastlock = 1'b0;
    assign d_hwdata    = is_str ? store_data : {XLEN{1'b0}};

endmodule
