//============================================================================
// Module : sram_slave
// Description : Behavioral SRAM slave with bus interface
//               32-bit wide, parameterized depth, single-port
//               1-cycle read latency, synchronous write
//               Byte/half/word write support via byte-lane masking
//============================================================================

module sram_slave #(
    parameter ADDR_WIDTH = 14,  // 14 bits → 16384 words = 64KB
    parameter DATA_WIDTH = 32   // 32-bit data bus
)(
    input  logic                  clk,
    input  logic                  rst_n,

    // Bus slave interface
    input  logic [31:0]           addr,
    input  logic [DATA_WIDTH-1:0] wdata,
    output logic [DATA_WIDTH-1:0] rdata,
    input  logic                  we,
    input  logic                  cs,
    output logic                  ack,
    input  logic [1:0]            size      // 00=byte, 01=halfword, 10=word
);

    // ===============================================================
    // Memory array
    // ===============================================================
    logic [DATA_WIDTH-1:0] mem [0:(1 << ADDR_WIDTH) - 1];

    // ===============================================================
    // Internal address (word-aligned index from byte address)
    // ===============================================================
    logic [ADDR_WIDTH-1:0] word_addr;

    assign word_addr = addr[ADDR_WIDTH+1:2];  // Convert byte addr to word index

    // ===============================================================
    // Byte-lane write masking
    // ===============================================================
    logic [3:0] byte_en;

    always @(*) begin
        case (size)
            2'b00: begin  // Byte access
                case (addr[1:0])
                    2'b00: byte_en = 4'b0001;
                    2'b01: byte_en = 4'b0010;
                    2'b10: byte_en = 4'b0100;
                    2'b11: byte_en = 4'b1000;
                endcase
            end
            2'b01: begin  // Halfword access
                case (addr[1])
                    1'b0: byte_en = 4'b0011;
                    1'b1: byte_en = 4'b1100;
                endcase
            end
            default: byte_en = 4'b1111;  // Word access
        endcase
    end

    // ===============================================================
    // Write logic with byte-lane masking
    // ===============================================================
    integer i;

    always @(posedge clk) begin
        if (cs && we) begin
            for (i = 0; i < 4; i = i + 1) begin
                if (byte_en[i]) begin
                    mem[word_addr][i*8 +: 8] <= wdata[i*8 +: 8];
                end
            end
        end
    end

    // ===============================================================
    // Read logic — 1-cycle latency (read registered)
    // ===============================================================
    always @(posedge clk) begin
        if (!rst_n) begin
            rdata <= {DATA_WIDTH{1'b0}};
        end else if (cs && !we) begin
            rdata <= mem[word_addr];
        end
    end

    // ===============================================================
    // Ack generation — 1 cycle after cs assertion
    // ===============================================================
    always @(posedge clk) begin
        if (!rst_n) begin
            ack <= 1'b0;
        end else begin
            ack <= cs;  // Ack follows cs with 1-cycle delay
        end
    end

endmodule
