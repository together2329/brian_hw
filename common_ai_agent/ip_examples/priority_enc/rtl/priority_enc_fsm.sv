// priority_enc_fsm.sv — enable-state FSM for priority_enc
module priority_enc_fsm (
    input  logic PCLK,
    input  logic PRESETn,
    input  logic ctrl_enable_i,
    output logic active_o
);
    localparam [0:0] IDLE   = 1'b0,
                     ACTIVE = 1'b1;

    logic state;
    logic next_state;

    assign active_o = state;

    always @(*) begin
        next_state = state;
        case (state)
            IDLE: begin
                if (ctrl_enable_i) begin
                    next_state = ACTIVE;
                end
            end
            ACTIVE: begin
                if (!ctrl_enable_i) begin
                    next_state = IDLE;
                end
            end
            default: begin
                next_state = IDLE;
            end
        endcase
    end

    always @(posedge PCLK or negedge PRESETn) begin
        if (!PRESETn) begin
            state <= IDLE;
        end else begin
            state <= next_state;
        end
    end
endmodule
