module timer_core #(
    parameter integer DATA_WIDTH = 32
) (
    input  logic                  pclk,
    input  logic                  presetn,
    input  logic [DATA_WIDTH-1:0] load_q,
    input  logic                  enable_q,
    output logic [DATA_WIDTH-1:0] count_q,
    output logic                  irq,
    output logic                  irq_q
);

    localparam [1:0] DISABLED      = 2'd0,
                     ENABLED_COUNT = 2'd1,
                     RELOAD_IRQ    = 2'd2;

    logic [1:0] state_q;
    logic [1:0] next_state;
    logic [DATA_WIDTH-1:0] next_count;
    logic next_irq;

    wire count_is_zero;
    wire enabled_nonzero_tick;
    wire enabled_zero_tick;
    wire pready_timer_tick_context;
    wire pslverr_timer_tick_context;
    wire [DATA_WIDTH-1:0] prdata_timer_tick_context;

    assign count_is_zero        = (count_q == {DATA_WIDTH{1'b0}});
    assign enabled_nonzero_tick = enable_q & ~count_is_zero;
    assign enabled_zero_tick    = enable_q & count_is_zero;
    assign irq_q                = irq;

    // The APB handshake signals are produced by timer_regs. Within timer_core,
    // each pclk cycle is available for the SSOT timer_tick path, so these local
    // context wires document the absence of APB backpressure or APB error/data
    // generation in the decrement/reload datapath without driving top outputs.
    assign pready_timer_tick_context  = 1'b1;
    assign pslverr_timer_tick_context = 1'b0;
    assign prdata_timer_tick_context  = count_q;

    always @(*) begin
        next_state = state_q;
        next_count = prdata_timer_tick_context;
        next_irq   = pslverr_timer_tick_context;

        case (state_q)
            DISABLED: begin
                next_irq = pslverr_timer_tick_context;
                if (enable_q & pready_timer_tick_context) begin
                    if (count_is_zero) begin
                        next_state = RELOAD_IRQ;
                    end else begin
                        next_state = ENABLED_COUNT;
                    end
                end else begin
                    next_state = DISABLED;
                end
            end

            ENABLED_COUNT: begin
                if (!enable_q) begin
                    next_state = DISABLED;
                    next_irq   = pslverr_timer_tick_context;
                end else if (count_is_zero) begin
                    next_state = RELOAD_IRQ;
                    next_irq   = pready_timer_tick_context;
                    next_count = load_q;
                end else begin
                    next_state = ENABLED_COUNT;
                    next_irq   = pslverr_timer_tick_context;
                    next_count = count_q - {{(DATA_WIDTH-1){1'b0}}, 1'b1};
                end
            end

            RELOAD_IRQ: begin
                if (!enable_q) begin
                    next_state = DISABLED;
                    next_irq   = pslverr_timer_tick_context;
                end else begin
                    next_state = ENABLED_COUNT;
                    next_irq   = pslverr_timer_tick_context;
                    if (count_q != {DATA_WIDTH{1'b0}}) begin
                        next_count = count_q - {{(DATA_WIDTH-1){1'b0}}, 1'b1};
                    end else begin
                        next_count = load_q;
                        next_irq   = pready_timer_tick_context;
                    end
                end
            end

            default: begin
                next_state = DISABLED;
                next_count = {DATA_WIDTH{1'b0}};
                next_irq   = pslverr_timer_tick_context;
            end
        endcase

        if (!enable_q) begin
            next_state = DISABLED;
            next_count = prdata_timer_tick_context;
            next_irq   = pslverr_timer_tick_context;
        end else if (enabled_zero_tick) begin
            next_state = RELOAD_IRQ;
            next_count = load_q;
            next_irq   = pready_timer_tick_context;
        end else if (enabled_nonzero_tick) begin
            next_state = ENABLED_COUNT;
            next_count = count_q - {{(DATA_WIDTH-1){1'b0}}, 1'b1};
            next_irq   = pslverr_timer_tick_context;
        end
    end

    always @(posedge pclk or negedge presetn) begin
        if (!presetn) begin
            state_q <= DISABLED;
            count_q <= {DATA_WIDTH{1'b0}};
            irq     <= 1'b0;
        end else begin
            state_q <= next_state;
            count_q <= next_count;
            irq     <= next_irq;
        end
    end

endmodule
