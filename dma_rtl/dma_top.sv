// DMA Controller Top Module
// AXI4 Master Interface
// Supports memory-to-memory and peripheral-to-memory transfers

module dma_top #(
    parameter DATA_WIDTH = 32,
    parameter ADDR_WIDTH = 32,
    parameter STRB_WIDTH = DATA_WIDTH/8,
    parameter ID_WIDTH = 4
) (
    input  logic                    clk,
    input  logic                    rst_n,
    
    // Control Interface
    input  logic                    start,
    output logic                    busy,
    output logic                    done,
    output logic [1:0]              error,  // 00: no error, 01: bus error, 10: timeout
    
    // Configuration
    input  logic [ADDR_WIDTH-1:0]   src_addr,
    input  logic [ADDR_WIDTH-1:0]   dst_addr,
    input  logic [31:0]             length,  // Transfer length in bytes
    
    // AXI4 Master Write Channel (AW, W, B)
    output logic [ID_WIDTH-1:0]     m_axi_awid,
    output logic [ADDR_WIDTH-1:0]   m_axi_awaddr,
    output logic [7:0]              m_axi_awlen,
    output logic [2:0]              m_axi_awsize,
    output logic [1:0]              m_axi_awburst,
    output logic                    m_axi_awvalid,
    input  logic                    m_axi_awready,
    
    output logic [DATA_WIDTH-1:0]   m_axi_wdata,
    output logic [STRB_WIDTH-1:0]   m_axi_wstrb,
    output logic                    m_axi_wlast,
    output logic                    m_axi_wvalid,
    input  logic                    m_axi_wready,
    
    input  logic [ID_WIDTH-1:0]     m_axi_bid,
    input  logic [1:0]              m_axi_bresp,
    input  logic                    m_axi_bvalid,
    output logic                    m_axi_bready,
    
    // AXI4 Master Read Channel (AR, R)
    output logic [ID_WIDTH-1:0]     m_axi_arid,
    output logic [ADDR_WIDTH-1:0]   m_axi_araddr,
    output logic [7:0]              m_axi_arlen,
    output logic [2:0]              m_axi_arsize,
    output logic [1:0]              m_axi_arburst,
    output logic                    m_axi_arvalid,
    input  logic                    m_axi_arready,
    
    input  logic [ID_WIDTH-1:0]     m_axi_rid,
    input  logic [DATA_WIDTH-1:0]   m_axi_rdata,
    input  logic [1:0]              m_axi_rresp,
    input  logic                    m_axi_rlast,
    input  logic                    m_axi_rvalid,
    output logic                    m_axi_rready
);

    // Internal signals
    logic [DATA_WIDTH-1:0]  read_data;
    logic                   read_data_valid;
    logic                   read_data_last;
    logic                   read_error;
    
    logic                   write_req;
    logic [ADDR_WIDTH-1:0]  write_addr;
    logic [DATA_WIDTH-1:0]  write_data;
    logic                   write_last;
    logic                   write_done;
    logic                   write_error;
    
    logic                   read_req;
    logic [ADDR_WIDTH-1:0]  read_addr;
    logic                   read_done;
    
    // FSM States
    typedef enum logic [2:0] {
        IDLE,
        READ_START,
        READ_WAIT,
        WRITE_START,
        WRITE_WAIT,
        DONE,
        ERROR
    } state_t;
    
    state_t state, next_state;
    
    // Transfer counter
    logic [31:0] byte_count;
    logic [31:0] beat_count;
    logic [31:0] total_beats;
    
    // Address alignment
    logic [1:0]  addr_offset;
    logic [7:0]  burst_len;
    
    // Calculate transfer beats based on length and data width
    always_comb begin
        if (length == 0) begin
            total_beats = 0;
        end else begin
            total_beats = (length + DATA_WIDTH/8 - 1) / (DATA_WIDTH/8);
        end
    end
    
    // Address offset handling
    always_comb begin
        addr_offset = src_addr[1:0];
    end
    
    // State Machine
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= IDLE;
            byte_count <= 0;
            beat_count <= 0;
            error <= 2'b00;
        end else begin
            state <= next_state;
            case (state)
                IDLE: begin
                    byte_count <= 0;
                    beat_count <= 0;
                    error <= 2'b00;
                end
                READ_WAIT: begin
                    if (read_data_valid) begin
                        beat_count <= beat_count + 1;
                        byte_count <= byte_count + DATA_WIDTH/8;
                    end
                end
                default: begin
                    // Maintain current values
                end
            endcase
        end
    end
    
    // Next State Logic
    always_comb begin
        next_state = state;
        read_req = 1'b0;
        write_req = 1'b0;
        busy = 1'b0;
        done = 1'b0;
        
        case (state)
            IDLE: begin
                if (start && length > 0) begin
                    next_state = READ_START;
                end
            end
            
            READ_START: begin
                read_req = 1'b1;
                next_state = READ_WAIT;
            end
            
            READ_WAIT: begin
                busy = 1'b1;
                if (read_data_valid) begin
                    write_req = 1'b1;
                    if (read_data_last || read_error) begin
                        next_state = WRITE_WAIT;
                    end
                end
                if (read_error) begin
                    next_state = ERROR;
                end
            end
            
            WRITE_WAIT: begin
                busy = 1'b1;
                if (write_done) begin
                    next_state = DONE;
                end
                if (write_error) begin
                    next_state = ERROR;
                end
            end
            
            DONE: begin
                done = 1'b1;
                next_state = IDLE;
            end
            
            ERROR: begin
                busy = 1'b0;
                done = 1'b1;
                next_state = IDLE;
            end
            
            default: begin
                next_state = IDLE;
            end
        endcase
    end
    
    // Calculate addresses
    always_comb begin
        read_addr = src_addr + beat_count * (DATA_WIDTH/8);
        write_addr = dst_addr + beat_count * (DATA_WIDTH/8);
    end
    
    // AXI4 Read Adapter Instance
    dma_axi_read #(
        .DATA_WIDTH(DATA_WIDTH),
        .ADDR_WIDTH(ADDR_WIDTH),
        .ID_WIDTH(ID_WIDTH)
    ) dma_axi_read_inst (
        .clk(clk),
        .rst_n(rst_n),
        .req(read_req),
        .addr(read_addr),
        .len(total_beats - 1),
        .data_valid(read_data_valid),
        .data(read_data),
        .last(read_data_last),
        .error(read_error),
        .ready(1'b1),  // Always ready to accept data
        
        .m_axi_arid(m_axi_arid),
        .m_axi_araddr(m_axi_araddr),
        .m_axi_arlen(m_axi_arlen),
        .m_axi_arsize(m_axi_arsize),
        .m_axi_arburst(m_axi_arburst),
        .m_axi_arvalid(m_axi_arvalid),
        .m_axi_arready(m_axi_arready),
        .m_axi_rid(m_axi_rid),
        .m_axi_rdata(m_axi_rdata),
        .m_axi_rresp(m_axi_rresp),
        .m_axi_rlast(m_axi_rlast),
        .m_axi_rvalid(m_axi_rvalid),
        .m_axi_rready(m_axi_rready)
    );
    
    // AXI4 Write Adapter Instance
    dma_axi_write #(
        .DATA_WIDTH(DATA_WIDTH),
        .ADDR_WIDTH(ADDR_WIDTH),
        .ID_WIDTH(ID_WIDTH)
    ) dma_axi_write_inst (
        .clk(clk),
        .rst_n(rst_n),
        .req(write_req),
        .addr(write_addr),
        .data(write_data),
        .last(write_last),
        .done(write_done),
        .error(write_error),
        
        .m_axi_awid(m_axi_awid),
        .m_axi_awaddr(m_axi_awaddr),
        .m_axi_awlen(m_axi_awlen),
        .m_axi_awsize(m_axi_awsize),
        .m_axi_awburst(m_axi_awburst),
        .m_axi_awvalid(m_axi_awvalid),
        .m_axi_awready(m_axi_awready),
        .m_axi_wdata(m_axi_wdata),
        .m_axi_wstrb(m_axi_wstrb),
        .m_axi_wlast(m_axi_wlast),
        .m_axi_wvalid(m_axi_wvalid),
        .m_axi_wready(m_axi_wready),
        .m_axi_bid(m_axi_bid),
        .m_axi_bresp(m_axi_bresp),
        .m_axi_bvalid(m_axi_bvalid),
        .m_axi_bready(m_axi_bready)
    );
    
    // Data path from read to write
    always_ff @(posedge clk) begin
        if (read_data_valid) begin
            write_data <= read_data;
        end
    end
    
    // Generate last signal
    always_ff @(posedge clk) begin
        if (read_data_valid) begin
            write_last <= read_data_last;
        end
    end
    
    // Error handling
    always_ff @(posedge clk) begin
        if (read_error) begin
            error <= 2'b01;
        end else if (write_error) begin
            error <= 2'b10;
        end
    end

endmodule
