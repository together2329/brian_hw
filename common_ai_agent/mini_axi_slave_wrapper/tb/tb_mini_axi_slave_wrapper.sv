`timescale 1ns/1ps

module tb_mini_axi_slave_wrapper;
    localparam integer ADDR_WIDTH = 8;
    localparam integer DATA_WIDTH = 32;
    localparam integer ID_WIDTH   = 4;

    logic ACLK;
    logic ARESETn;

    logic [ID_WIDTH-1:0]   S_AXI_AWID;
    logic [ADDR_WIDTH-1:0] S_AXI_AWADDR;
    logic [7:0]            S_AXI_AWLEN;
    logic [2:0]            S_AXI_AWSIZE;
    logic [1:0]            S_AXI_AWBURST;
    logic                  S_AXI_AWVALID;
    logic                  S_AXI_AWREADY;

    logic [DATA_WIDTH-1:0] S_AXI_WDATA;
    logic [3:0]            S_AXI_WSTRB;
    logic                  S_AXI_WLAST;
    logic                  S_AXI_WVALID;
    logic                  S_AXI_WREADY;

    logic [ID_WIDTH-1:0]   S_AXI_BID;
    logic [1:0]            S_AXI_BRESP;
    logic                  S_AXI_BVALID;
    logic                  S_AXI_BREADY;

    logic [ID_WIDTH-1:0]   S_AXI_ARID;
    logic [ADDR_WIDTH-1:0] S_AXI_ARADDR;
    logic [7:0]            S_AXI_ARLEN;
    logic [2:0]            S_AXI_ARSIZE;
    logic [1:0]            S_AXI_ARBURST;
    logic                  S_AXI_ARVALID;
    logic                  S_AXI_ARREADY;

    logic [ID_WIDTH-1:0]   S_AXI_RID;
    logic [DATA_WIDTH-1:0] S_AXI_RDATA;
    logic [1:0]            S_AXI_RRESP;
    logic                  S_AXI_RLAST;
    logic                  S_AXI_RVALID;
    logic                  S_AXI_RREADY;

    logic [2:0]            write_outstanding_o;
    logic [2:0]            read_outstanding_o;

    mini_axi_slave_wrapper #(
        .ADDR_WIDTH (ADDR_WIDTH),
        .DATA_WIDTH (DATA_WIDTH),
        .ID_WIDTH   (ID_WIDTH),
        .OUTSTANDING(4),
        .MEM_WORDS  (16)
    ) dut (
        .ACLK,
        .ARESETn,
        .S_AXI_AWID,
        .S_AXI_AWADDR,
        .S_AXI_AWLEN,
        .S_AXI_AWSIZE,
        .S_AXI_AWBURST,
        .S_AXI_AWVALID,
        .S_AXI_AWREADY,
        .S_AXI_WDATA,
        .S_AXI_WSTRB,
        .S_AXI_WLAST,
        .S_AXI_WVALID,
        .S_AXI_WREADY,
        .S_AXI_BID,
        .S_AXI_BRESP,
        .S_AXI_BVALID,
        .S_AXI_BREADY,
        .S_AXI_ARID,
        .S_AXI_ARADDR,
        .S_AXI_ARLEN,
        .S_AXI_ARSIZE,
        .S_AXI_ARBURST,
        .S_AXI_ARVALID,
        .S_AXI_ARREADY,
        .S_AXI_RID,
        .S_AXI_RDATA,
        .S_AXI_RRESP,
        .S_AXI_RLAST,
        .S_AXI_RVALID,
        .S_AXI_RREADY,
        .write_outstanding_o,
        .read_outstanding_o
    );

    initial ACLK = 1'b0;
    always #5 ACLK = ~ACLK;

    task automatic fail(input string msg);
        begin
            $display("FAIL: %s at t=%0t", msg, $time);
            $fatal(1);
        end
    endtask

    task automatic check_true(input bit cond, input string msg);
        begin
            if (!cond) fail(msg);
        end
    endtask

    task automatic issue_aw(input [ID_WIDTH-1:0] id, input [ADDR_WIDTH-1:0] addr);
        begin
            @(negedge ACLK);
            S_AXI_AWID    = id;
            S_AXI_AWADDR  = addr;
            S_AXI_AWLEN   = 8'd0;
            S_AXI_AWSIZE  = 3'd2;
            S_AXI_AWBURST = 2'b01;
            S_AXI_AWVALID = 1'b1;
            #1 check_true(S_AXI_AWREADY, "AWREADY should accept one of four outstanding writes");
            @(posedge ACLK);
            @(negedge ACLK);
            S_AXI_AWVALID = 1'b0;
        end
    endtask

    task automatic issue_w(input [DATA_WIDTH-1:0] data);
        begin
            @(negedge ACLK);
            S_AXI_WDATA  = data;
            S_AXI_WSTRB  = 4'hf;
            S_AXI_WLAST  = 1'b1;
            S_AXI_WVALID = 1'b1;
            #1 check_true(S_AXI_WREADY, "WREADY should accept data for queued AW");
            @(posedge ACLK);
            @(negedge ACLK);
            S_AXI_WVALID = 1'b0;
        end
    endtask

    task automatic drain_b(input [ID_WIDTH-1:0] expected_id);
        begin
            @(negedge ACLK);
            S_AXI_BREADY = 1'b1;
            #1;
            check_true(S_AXI_BVALID, "BVALID should be queued");
            check_true(S_AXI_BID == expected_id, "BID must preserve AWID order");
            check_true(S_AXI_BRESP == 2'b00, "BRESP should be OKAY");
            @(posedge ACLK);
            @(negedge ACLK);
            S_AXI_BREADY = 1'b0;
        end
    endtask

    task automatic issue_ar(input [ID_WIDTH-1:0] id, input [ADDR_WIDTH-1:0] addr);
        begin
            @(negedge ACLK);
            S_AXI_ARID    = id;
            S_AXI_ARADDR  = addr;
            S_AXI_ARLEN   = 8'd0;
            S_AXI_ARSIZE  = 3'd2;
            S_AXI_ARBURST = 2'b01;
            S_AXI_ARVALID = 1'b1;
            #1 check_true(S_AXI_ARREADY, "ARREADY should accept one of four outstanding reads");
            @(posedge ACLK);
            @(negedge ACLK);
            S_AXI_ARVALID = 1'b0;
        end
    endtask

    task automatic drain_r(
        input [ID_WIDTH-1:0] expected_id,
        input [DATA_WIDTH-1:0] expected_data
    );
        begin
            @(negedge ACLK);
            S_AXI_RREADY = 1'b1;
            #1;
            check_true(S_AXI_RVALID, "RVALID should be queued");
            check_true(S_AXI_RID == expected_id, "RID must preserve ARID order");
            check_true(S_AXI_RDATA == expected_data, "RDATA mismatch");
            check_true(S_AXI_RRESP == 2'b00, "RRESP should be OKAY");
            check_true(S_AXI_RLAST, "single-beat read must assert RLAST");
            @(posedge ACLK);
            @(negedge ACLK);
            S_AXI_RREADY = 1'b0;
        end
    endtask

    initial begin
        ARESETn       = 1'b0;
        S_AXI_AWID    = '0;
        S_AXI_AWADDR  = '0;
        S_AXI_AWLEN   = '0;
        S_AXI_AWSIZE  = 3'd2;
        S_AXI_AWBURST = 2'b01;
        S_AXI_AWVALID = 1'b0;
        S_AXI_WDATA   = '0;
        S_AXI_WSTRB   = '0;
        S_AXI_WLAST   = 1'b0;
        S_AXI_WVALID  = 1'b0;
        S_AXI_BREADY  = 1'b0;
        S_AXI_ARID    = '0;
        S_AXI_ARADDR  = '0;
        S_AXI_ARLEN   = '0;
        S_AXI_ARSIZE  = 3'd2;
        S_AXI_ARBURST = 2'b01;
        S_AXI_ARVALID = 1'b0;
        S_AXI_RREADY  = 1'b0;

        repeat (4) @(posedge ACLK);
        ARESETn = 1'b1;
        repeat (2) @(posedge ACLK);

        issue_aw(4'h0, 8'h00);
        issue_aw(4'h1, 8'h04);
        issue_aw(4'h2, 8'h08);
        issue_aw(4'h3, 8'h0c);
        @(negedge ACLK);
        #1 check_true(write_outstanding_o == 3'd4, "four AW transactions should be outstanding");
        S_AXI_AWID    = 4'h4;
        S_AXI_AWADDR  = 8'h10;
        S_AXI_AWVALID = 1'b1;
        #1 check_true(!S_AXI_AWREADY, "fifth AW must backpressure at depth four");
        S_AXI_AWVALID = 1'b0;

        issue_w(32'h1111_0000);
        issue_w(32'h2222_0001);
        issue_w(32'h3333_0002);
        issue_w(32'h4444_0003);
        @(negedge ACLK);
        #1 check_true(write_outstanding_o == 3'd4, "four B responses should remain outstanding");

        drain_b(4'h0);
        drain_b(4'h1);
        drain_b(4'h2);
        drain_b(4'h3);
        @(negedge ACLK);
        #1 check_true(write_outstanding_o == 3'd0, "write outstanding count should drain to zero");

        issue_ar(4'ha, 8'h00);
        issue_ar(4'hb, 8'h04);
        issue_ar(4'hc, 8'h08);
        issue_ar(4'hd, 8'h0c);
        @(negedge ACLK);
        #1 check_true(read_outstanding_o == 3'd4, "four reads should be outstanding");
        S_AXI_ARID    = 4'he;
        S_AXI_ARADDR  = 8'h10;
        S_AXI_ARVALID = 1'b1;
        #1 check_true(!S_AXI_ARREADY, "fifth AR must backpressure at depth four");
        S_AXI_ARVALID = 1'b0;

        drain_r(4'ha, 32'h1111_0000);
        drain_r(4'hb, 32'h2222_0001);
        drain_r(4'hc, 32'h3333_0002);
        drain_r(4'hd, 32'h4444_0003);
        @(negedge ACLK);
        #1 check_true(read_outstanding_o == 3'd0, "read outstanding count should drain to zero");

        // Unsupported burst lengths are still consumed and reported as SLVERR.
        @(negedge ACLK);
        S_AXI_ARID    = 4'hf;
        S_AXI_ARADDR  = 8'h00;
        S_AXI_ARLEN   = 8'd1;
        S_AXI_ARVALID = 1'b1;
        #1 check_true(S_AXI_ARREADY, "unsupported burst should be consumed");
        @(posedge ACLK);
        @(negedge ACLK);
        S_AXI_ARVALID = 1'b0;
        S_AXI_ARLEN   = 8'd0;
        S_AXI_RREADY  = 1'b1;
        #1;
        check_true(S_AXI_RVALID, "SLVERR read response should be queued");
        check_true(S_AXI_RID == 4'hf, "SLVERR read should preserve ID");
        check_true(S_AXI_RRESP == 2'b10, "unsupported burst should return SLVERR");
        @(posedge ACLK);
        @(negedge ACLK);
        S_AXI_RREADY = 1'b0;

        $display("PASS: mini_axi_slave_wrapper supports four outstanding reads and writes");
        $finish;
    end
endmodule
