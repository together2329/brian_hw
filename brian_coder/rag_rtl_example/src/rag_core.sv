module rag_core #(
    parameter ADDR_WIDTH = 4,
    parameter DATA_WIDTH = 32
)(
    input  logic                   clk,
    input  logic                   rst_n,
    
    // Control/Status
    input  logic                   start,
    input  logic                   clear,
    output logic                   busy,
    output logic                   match_found,
    
    // Query/Result
    input  logic [DATA_WIDTH-1:0]  query_key,
    output logic [DATA_WIDTH-1:0]  result_data,
    
    // External Memory Load Interface
    input  logic                   mem_wen,
    input  logic [ADDR_WIDTH-1:0]  mem_addr,
    input  logic [DATA_WIDTH-1:0]  mem_wdata
);

    // Simple BRAM-based storage (Key and Value)
    logic [DATA_WIDTH-1:0] keys [2**ADDR_WIDTH];
    logic [DATA_WIDTH-1:0] values [2**ADDR_WIDTH];
    
    logic [ADDR_WIDTH:0]  search_ptr;
    
    typedef enum logic [1:0] {
        IDLE    = 2'b00,
        SEARCH  = 2'b01,
        FOUND   = 2'b10,
        CLEANUP = 2'b11
    } state_t;
    
    state_t state;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= IDLE;
            busy <= 1'b0;
            match_found <= 1'b0;
            result_data <= '0;
            search_ptr <= '0;
            // Note: In real RTL we wouldn't loop to clear keys/values 
            // without a multi-cycle process, but for this simulation...
        end else begin
            if (clear) begin
                state <= IDLE;
                busy <= 1'b0;
                match_found <= 1'b0;
            end else if (mem_wen) begin
                keys[mem_addr] <= mem_wdata; // For simplicity, load keys and values alternatively or via offset
                values[mem_addr] <= mem_wdata ^ 32'hAAAA_AAAA; // Pseudo-answer
            end else begin
                case (state)
                    IDLE: begin
                        if (start) begin
                            state <= SEARCH;
                            busy <= 1'b1;
                            match_found <= 1'b0;
                            search_ptr <= '0;
                        end
                    end
                    
                    SEARCH: begin
                        if (keys[search_ptr[ADDR_WIDTH-1:0]] == query_key) begin
                            state <= FOUND;
                            match_found <= 1'b1;
                            result_data <= values[search_ptr[ADDR_WIDTH-1:0]];
                        end else if (search_ptr == (2**ADDR_WIDTH)-1) begin
                            state <= IDLE;
                            busy <= 1'b0;
                            match_found <= 1'b0;
                        end else begin
                            search_ptr <= search_ptr + 1;
                        end
                    end
                    
                    FOUND: begin
                        state <= IDLE;
                        busy <= 1'b0;
                    end
                endcase
            end
        end
    end

endmodule
