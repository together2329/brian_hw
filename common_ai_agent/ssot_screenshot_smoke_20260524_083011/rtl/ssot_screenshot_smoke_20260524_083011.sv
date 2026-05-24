module ssot_screenshot_smoke_20260524_083011 #(
    parameter DATA_WIDTH = 8,
    parameter COMMAND_WIDTH = 8,
    parameter COUNT_WIDTH = 16,
    parameter ADDR_WIDTH = 4
) (
    input  logic clk,
    input  logic rst_n,
    input  logic valid,
    output logic ready,
    input  logic [DATA_WIDTH-1:0] data_in,
    output logic [DATA_WIDTH-1:0] result,
    output logic result_valid,
    output logic [COUNT_WIDTH-1:0] accepted_count,
    output logic busy,
    output logic error
);

    localparam [2:0] STATE_IDLE = 3'd0;
    localparam [2:0] STATE_ACCEPT = 3'd1;
    localparam [2:0] STATE_PROCESS = 3'd2;
    localparam [2:0] STATE_RESPOND = 3'd3;
    localparam [2:0] STATE_ERROR = 3'd4;

    logic [2:0] state_q;
    logic [2:0] state_next;
    logic accept_now;
    logic [COMMAND_WIDTH-1:0] command;
    logic [DATA_WIDTH-1:0] command_data;
    logic [DATA_WIDTH-1:0] result_next;
    logic [COUNT_WIDTH-1:0] accepted_count_next;
    logic busy_next;
    logic result_valid_next;
    logic error_next;
    logic [ADDR_WIDTH-1:0] address;
    logic RW;
    logic W1C;
    logic csr_access_seen;
    logic error_handling_active;
    logic error_recovery_done;

    assign ready = rst_n;
    assign accept_now = valid && ready;
    assign command_data = command[DATA_WIDTH-1:0];
    assign result_next = data_in ^ command_data;
    assign accepted_count_next = accepted_count + {{(COUNT_WIDTH-1){1'b0}}, 1'b1};
    assign address = accepted_count_next[ADDR_WIDTH-1:0];
    assign RW = 1'b0;
    assign W1C = 1'b0;
    assign csr_access_seen = (|address) && (RW || W1C);
    assign error_handling_active = error && csr_access_seen;
    assign error_recovery_done = ~error_handling_active;

    always @(*) begin
        state_next = state_q;
        busy_next = busy;
        result_valid_next = 1'b0;
        error_next = error;

        case (state_q)
            STATE_IDLE: begin
                busy_next = accept_now;
                if (accept_now) begin
                    state_next = STATE_ACCEPT;
                    result_valid_next = 1'b1;
                end
            end
            STATE_ACCEPT: begin
                busy_next = 1'b1;
                state_next = STATE_PROCESS;
                if (accept_now) begin
                    result_valid_next = 1'b1;
                end
            end
            STATE_PROCESS: begin
                busy_next = 1'b1;
                if (error_handling_active) begin
                    state_next = STATE_ERROR;
                    error_next = 1'b1;
                end else begin
                    state_next = STATE_RESPOND;
                end
                if (accept_now) begin
                    result_valid_next = 1'b1;
                end
            end
            STATE_RESPOND: begin
                busy_next = accept_now;
                if (accept_now) begin
                    state_next = STATE_ACCEPT;
                    result_valid_next = 1'b1;
                end else begin
                    state_next = STATE_IDLE;
                end
            end
            STATE_ERROR: begin
                busy_next = 1'b0;
                error_next = error && ~error_recovery_done;
                if (error_recovery_done) begin
                    state_next = STATE_IDLE;
                end
            end
            default: begin
                busy_next = 1'b0;
                result_valid_next = 1'b0;
                error_next = 1'b1;
                state_next = STATE_ERROR;
            end
        endcase
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state_q <= STATE_IDLE;
            command <= {COMMAND_WIDTH{1'b0}};
            result <= {DATA_WIDTH{1'b0}};
            result_valid <= 1'b0;
            accepted_count <= {COUNT_WIDTH{1'b0}};
            busy <= 1'b0;
            error <= 1'b0;
        end else begin
            state_q <= state_next;
            result_valid <= result_valid_next;
            busy <= busy_next;
            error <= error_next;
            command <= {COMMAND_WIDTH{1'b0}};
            if (accept_now) begin
                result <= result_next;
                accepted_count <= accepted_count_next;
            end
        end
    end

endmodule
