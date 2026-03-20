`timescale 1ns/1ps

module rag_tb;

    parameter ADDR_WIDTH = 12;
    parameter DATA_WIDTH = 32;

    logic aclk;
    logic aresetn;

    // AXI-Lite Signals
    logic [ADDR_WIDTH-1:0] awaddr;
    logic awvalid;
    logic awready;
    logic [DATA_WIDTH-1:0] wdata;
    logic wvalid;
    logic wready;
    logic [1:0] bresp;
    logic bvalid;
    logic bready;
    logic [ADDR_WIDTH-1:0] araddr;
    logic arvalid;
    logic arready;
    logic [DATA_WIDTH-1:0] rdata;
    logic [1:0] rresp;
    logic rvalid;
    logic rready;

    // Clock Generation
    initial aclk = 0;
    always #5 aclk = ~aclk;

    // DUT Instantiation
    rag_axi_lite #(
        .ADDR_WIDTH(ADDR_WIDTH),
        .DATA_WIDTH(DATA_WIDTH)
    ) dut (.*);

    // AXI-Lite Write Task
    task axi_write(input [ADDR_WIDTH-1:0] addr, input [DATA_WIDTH-1:0] data);
        awaddr  = addr;
        awvalid = 1;
        wdata   = data;
        wvalid  = 1;
        bready  = 1;
        
        wait(awready && wready);
        @(posedge aclk);
        awvalid = 0;
        wvalid  = 0;
        
        wait(bvalid);
        @(posedge aclk);
        bready = 0;
    endtask

    // AXI-Lite Read Task
    task axi_read(input [ADDR_WIDTH-1:0] addr, output [DATA_WIDTH-1:0] data);
        araddr  = addr;
        arvalid = 1;
        rready  = 1;
        
        wait(arready);
        @(posedge aclk);
        arvalid = 0;
        
        wait(rvalid);
        data = rdata;
        @(posedge aclk);
        rready = 0;
    endtask

    // Main Test Sequence
    logic [31:0] test_rdata;
    initial begin
        // Reset
        aresetn = 0;
        awvalid = 0;
        wvalid  = 0;
        bready  = 0;
        arvalid = 0;
        rready  = 0;
        #50;
        aresetn = 1;
        #20;

        $display("--- Load RAG DB ---");
        // Loading key 0x1234 (addr 0x0 << 28)
        axi_write(12'h10, 32'h0000_1234); 
        #20;

        $display("--- Perform Query ---");
        // Write Query Data
        axi_write(12'h08, 32'h0000_1234);
        // Start lookup (CTRL[0])
        axi_write(12'h00, 32'h0000_0001);

        // Wait/Poll for Busy status
        do begin
            axi_read(12'h04, test_rdata);
            #10;
        end while (test_rdata[0]); // Bit 0 is busy

        if (test_rdata[1]) begin
            $display("MATCH FOUND!");
            axi_read(12'h0C, test_rdata);
            $display("Result Data: %h", test_rdata);
        end else begin
            $display("NO MATCH.");
        end

        #100;
        $display("Testbench Finished.");
        $finish;
    end

endmodule
