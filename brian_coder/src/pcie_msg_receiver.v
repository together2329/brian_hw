// PCIe Message Receiver: extracts TLP header and writes to SRAM
module pcie_msg_receiver (
    input  wire                   clk,
    input  wire                   rst_n,
    
    // AXI Write Address Channel
    input  wire                   axi_awvalid,
    input  wire [63:0]            axi_awaddr,
    input  wire [11:0]            axi_awlen,
    input  wire [2:0]             axi_awsize,
    input  wire [1:0]             axi_awburst,
    input  wire [3:0]             axi_awcache,
    input  wire [2:0]             axi_awprot,
    
    // AXI Write Data Channel
    input  wire                   axi_wvalid,
    input  wire [255:0]           axi_wdata,
    input  wire [31:0]            axi_wstrb,
    input  wire                   axi_wlast,
    
    // AXI Write Response Channel
    output wire                   axi_bready,
    input  wire                   axi_bvalid,
    input  wire [1:0]             axi_bresp,
    
    // PCIe Transaction Layer Packet Input
    input  wire [255:0]           rx_tlp_data,
    input  wire                   rx_tlp_valid,
    output wire                   rx_tlp_ready,
    
    // SRAM Interface
    output wire [11:0]            sram_addr,
    output wire [255:0]           sram_wdata,
    output wire [31:0]            sram_wstrb,
    output wire                   sram_we
);

    // TLP Header Signal (128 bits = 4 DW)
    reg [127:0] tlp_header;
    
    // TLP Header Fields (based on PCIe Specification)
    reg [1:0]   header_version;     // TLP Format Version
    reg [6:0]   header_type;        // TLP Type (6 bits)
    reg [10:0]  header_length;      // TLP Length in DW (LSB of Fmt/Type field)
    reg [15:0]  requester_id;       // Source ID
    reg [7:0]   tag;                // Request Tag
    reg [3:0]   last_dw_be;         // Last DW Byte Enable
    reg [31:0]  address;            // Address (for Memory Request)
    reg [7:0]   attributes;         // TLP Attributes
    reg [1:0]   order;              // Ordering
    reg [1:0]   priority;           // Priority
    
    // State Machine
    reg [3:0] state;
    
    // Temporary storage for TLP processing
    reg [255:0] tlp_data_buffer;
    reg [5:0]   tlp_beat_counter;
    reg [11:0]  sram_current_addr;
    reg         tlp_header_received;
    
    // FSM States
    localparam IDLE           = 4'h0;
    localparam WAIT_HEADER    = 4'h1;
    localparam WAIT_DATA      = 4'h2;
    localparam WRITE_SRAM     = 4'h3;
    
    // Control Logic for TLP Header Extraction
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            tlp_header <= 128'b0;
            header_version <= 2'b0;
            header_type <= 7'b0;
            header_length <= 11'b0;
            requester_id <= 16'b0;
            tag <= 8'b0;
            last_dw_be <= 4'b0;
            address <= 32'b0;
            attributes <= 8'b0;
            order <= 2'b0;
            priority <= 2'b0;
            tlp_header_received <= 1'b0;
            state <= IDLE;
            tlp_beat_counter <= 6'b0;
            sram_current_addr <= 12'b0;
        end else begin
            case (state)
                IDLE: begin
                    if (rx_tlp_valid) begin
                        tlp_header <= rx_tlp_data[127:0];
                        header_version <= tlp_header[127:126];
                        header_type <= tlp_header[125:119];
                        header_length <= tlp_header[118:108];
                        requester_id <= tlp_header[107:92];
                        tag <= tlp_header[91:84];
                        last_dw_be <= tlp_header[83:80];
                        address <= tlp_header[79:48];
                        attributes <= tlp_header[47:40];
                        order <= tlp_header[39:38];
                        priority <= tlp_header[37:36];
                        tlp_header_received <= 1'b1;
                        tlp_beat_counter <= 6'b0;
                        state <= WAIT_DATA;
                    end
                end
                
                WAIT_DATA: begin
                    if (rx_tlp_valid && tlp_header_received) begin
                        tlp_data_buffer <= rx_tlp_data;
                        tlp_beat_counter <= tlp_beat_counter + 1;
                        if (tlp_beat_counter == header_length - 1) begin
                            state <= WRITE_SRAM;
                        end
                    end
                end
                
                WRITE_SRAM: begin
                    sram_current_addr <= sram_current_addr + 1;
                    if (tlp_beat_counter == header_length) begin
                        sram_addr <= sram_current_addr;
                        sram_wdata <= tlp_data_buffer;
                        sram_wstrb <= 32'hFFFFFFFF;
                        sram_we <= 1'b1;
                        if (tlp_beat_counter == header_length) begin
                            state <= IDLE;
                        end
                    end
                end
                
                default: state <= IDLE;
            endcase
        end
    end
    
    // Output Signals
    assign axi_bready = 1'b1;
    assign rx_tlp_ready = (state == IDLE || state == WAIT_DATA);
    assign sram_addr = sram_current_addr;
    assign sram_wdata = tlp_data_buffer;
    assign sram_wstrb = (state == WRITE_SRAM) ? 32'hFFFFFFFF : 32'h0;
    assign sram_we = (state == WRITE_SRAM) ? 1'b1 : 1'b0;

endmodule
