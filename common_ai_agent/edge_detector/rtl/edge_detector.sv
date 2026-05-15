// edge_detector.sv -- top-level synchronizer and edge-detect datapath from edge_detector SSOT
module edge_detector #(
    // Number of PCLK synchronizer stages used for asynchronous signal_i.
    parameter integer SYNC_STAGES = 2,
    // Reset/default mode encoding from CONTROL.edge_mode; 0=rising, 1=falling, 2=both, 3=reserved no detect.
    parameter integer EDGE_MODE = 2,
    // Width of the external signal_i vector and edge_o pulse vector.
    parameter integer WIDTH = 1,
    // Informational target frequency parameter retained from SSOT configuration.
    parameter integer CLOCK_FREQ_MHZ = 50
) (
    input  logic              PCLK,
    input  logic              PRESETn,
    input  logic [WIDTH-1:0]  signal_i,
    output logic [WIDTH-1:0]  edge_o,
    output logic              irq_o,
    input  logic [11:0]       PADDR,
    input  logic              PSEL,
    input  logic              PENABLE,
    input  logic              PWRITE,
    input  logic [31:0]       PWDATA,
    input  logic [3:0]        PSTRB,
    output logic [31:0]       PRDATA,
    output logic              PREADY,
    output logic              PSLVERR
);
    localparam integer SYNC_W = WIDTH * SYNC_STAGES;
    localparam integer TARGET_FREQ_MHZ = CLOCK_FREQ_MHZ;

    logic [SYNC_W-1:0] sync_chain;
    logic [WIDTH-1:0]  prev_sync;
    logic [WIDTH-1:0]  curr_sync;
    logic [WIDTH-1:0]  rising_edge;
    logic [WIDTH-1:0]  falling_edge;
    logic [WIDTH-1:0]  mode_mask;
    logic [WIDTH-1:0]  edge_decode;
    logic [SYNC_W-1:0] sync_chain_next;
    logic [1:0]        edge_mode_cfg;
    logic              enable_cfg;
    logic              irq_enable_cfg;
    logic              irq_level;
    logic              target_freq_nonzero;

    assign target_freq_nonzero = (TARGET_FREQ_MHZ != 0);
    assign curr_sync = sync_chain[SYNC_W-1:SYNC_W-WIDTH];
    assign rising_edge = curr_sync & ~prev_sync;
    assign falling_edge = ~curr_sync & prev_sync;
    assign sync_chain_next = {sync_chain[SYNC_W-WIDTH-1:0], signal_i};

    // EDGE_MODE decode follows the SSOT CONTROL.edge_mode field, with 3 reserved as no detection.
    always @(*) begin
        mode_mask = {WIDTH{1'b0}};
        case (edge_mode_cfg)
            2'd0: mode_mask = rising_edge;
            2'd1: mode_mask = falling_edge;
            2'd2: mode_mask = rising_edge | falling_edge;
            default: mode_mask = {WIDTH{1'b0}};
        endcase
    end

    assign edge_decode = mode_mask & {WIDTH{enable_cfg}};

    // S0_SYNC shifts signal_i each PCLK; prev_sync captures the prior synchronized sample.
    always @(posedge PCLK or negedge PRESETn) begin
        if (!PRESETn) begin
            sync_chain <= {SYNC_W{1'b0}};
            prev_sync <= {WIDTH{1'b0}};
            edge_o <= {WIDTH{1'b0}};
        end else begin
            sync_chain <= sync_chain_next;
            prev_sync <= curr_sync;
            edge_o <= edge_decode;
        end
    end

    logic [7:0] status_sticky;
    assign status_sticky = u_regs.status_edge_sticky;

    edge_detector_regs #(
        .WIDTH(WIDTH),
        .EDGE_MODE_RESET(EDGE_MODE)
    ) u_regs (
        .PCLK(PCLK),
        .PRESETn(PRESETn),
        .PADDR(PADDR),
        .PSEL(PSEL),
        .PENABLE(PENABLE),
        .PWRITE(PWRITE),
        .PWDATA(PWDATA),
        .PSTRB(PSTRB),
        .edge_pulse_i(edge_decode),
        .edge_mode_o(edge_mode_cfg),
        .enable_o(enable_cfg),
        .irq_enable_o(irq_enable_cfg),
        .PRDATA(PRDATA),
        .PREADY(PREADY),
        .PSLVERR(PSLVERR),
        .irq_o(irq_level)
    );

    // irq_o is level-sensitive and asserted by the CSR block from sticky/raw edge status.
    always @(*) begin
        irq_o = irq_level & irq_enable_cfg & target_freq_nonzero & ((|status_sticky) | (|edge_o));
    end
endmodule
