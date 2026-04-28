`timescale 1ns / 1ps

module tb_ai_engine;
    localparam CLK_PERIOD = 10;

    reg clk, resetn;
    reg awvalid, wvalid, bready, arvalid, rready;
    wire awready, wready, bvalid, arready, rvalid;
    wire [1:0] bresp, rresp;
    wire [31:0] rdata;
    reg [31:0] awaddr, wdata, araddr;
    wire ai_irq;

    integer tests_passed, tests_failed;
    reg [31:0] rd_val;
    integer i;

    ai_engine dut (
        .S_AXI_ACLK(clk), .S_AXI_ARESETn(resetn),
        .S_AXI_AWVALID(awvalid), .S_AXI_AWREADY(awready), .S_AXI_AWADDR(awaddr),
        .S_AXI_AWPROT(3'd0), .S_AXI_WVALID(wvalid), .S_AXI_WREADY(wready),
        .S_AXI_WDATA(wdata), .S_AXI_WSTRB(4'd15),
        .S_AXI_BVALID(bvalid), .S_AXI_BREADY(bready), .S_AXI_BRESP(bresp),
        .S_AXI_ARVALID(arvalid), .S_AXI_ARREADY(arready), .S_AXI_ARADDR(araddr),
        .S_AXI_ARPROT(3'd0), .S_AXI_RVALID(rvalid), .S_AXI_RREADY(rready),
        .S_AXI_RDATA(rdata), .S_AXI_RRESP(rresp), .ai_irq(ai_irq)
    );

    always #((CLK_PERIOD)/2) clk = ~clk;

    task axi_write;
        input [31:0] addr;
        input [31:0] data;
        begin
            @(posedge clk);
            awaddr = addr; awvalid = 1'b1;
            wdata = data;   wvalid = 1'b1;
            @(posedge clk);
            while (!awready || !wready) @(posedge clk);
            awvalid = 1'b0; wvalid = 1'b0;
            bready = 1'b1;
            while (!bvalid) @(posedge clk);
            @(posedge clk);
            bready = 1'b0;
            @(posedge clk);
        end
    endtask

    task axi_read;
        input [31:0] addr;
        output [31:0] data;
        begin
            @(posedge clk);
            araddr = addr; arvalid = 1'b1;
            @(posedge clk);
            while (!arready) @(posedge clk);
            arvalid = 1'b0;
            rready = 1'b1;
            while (!rvalid) @(posedge clk);
            data = rdata;
            @(posedge clk);
            rready = 1'b0;
            @(posedge clk);
        end
    endtask

    task check;
        input ok;
        input [1023:0] msg;
        begin
            if (ok) begin
                $display("[PASS] %0s", msg);
                tests_passed = tests_passed + 1;
            end else begin
                $display("[FAIL] %0s", msg);
                tests_failed = tests_failed + 1;
            end
        end
    endtask

    // Helper: clear start bit (write CTRL with start=0, keep enable+irq_en)
    task clear_start;
        begin
            axi_write(32'h00, 32'h21);
        end
    endtask

    initial begin
        $dumpfile("ai_engine.vcd");
        $dumpvars(0, tb_ai_engine);
        clk = 1'b0; resetn = 1'b0;
        awvalid = 1'b0; wvalid = 1'b0; bready = 1'b0;
        arvalid = 1'b0; rready = 1'b0;
        tests_passed = 0; tests_failed = 0;

        repeat(5) @(posedge clk);
        resetn = 1'b1;
        repeat(2) @(posedge clk);

        //======================================================================
        // Test 1: Reset check
        //======================================================================
        $display("--- Test 1: Reset ---");
        axi_read(32'h00, rd_val);
        check(rd_val == 32'd0, "T1: CTRL zero after reset");
        axi_read(32'h04, rd_val);
        check(rd_val[1:0] == 2'b00, "T1: STATUS.busy=0, done=0 after reset");
        check(ai_irq == 1'b0, "T1: IRQ low after reset");

        //======================================================================
        // Test 2: Register R/W
        //======================================================================
        $display("--- Test 2: Register R/W ---");
        axi_write(32'h08, 32'd4);
        axi_write(32'h0C, 32'd0);
        axi_write(32'h10, 32'd16);
        axi_write(32'h14, 32'd80);
        axi_read(32'h08, rd_val);
        check(rd_val[7:0] == 8'd4, "T2: DIM=4");
        axi_read(32'h0C, rd_val);
        check(rd_val[7:0] == 8'd0, "T2: IADDR=0");
        axi_read(32'h10, rd_val);
        check(rd_val[7:0] == 8'd16, "T2: WADDR=16");
        axi_read(32'h14, rd_val);
        check(rd_val[7:0] == 8'd80, "T2: RADDR=80");
        axi_write(32'h00, 32'h21);
        axi_read(32'h00, rd_val);
        check(rd_val[0] == 1'b1, "T2: enable set");
        check(rd_val[5] == 1'b1, "T2: irq_en set");

        //======================================================================
        // Test 3: SRAM R/W
        //======================================================================
        $display("--- Test 3: SRAM R/W ---");
        axi_write(32'h20, 32'h04030201);
        axi_read(32'h20, rd_val);
        check(rd_val[7:0]   == 8'h01, "T3: byte0=01");
        check(rd_val[15:8]  == 8'h02, "T3: byte1=02");
        check(rd_val[23:16] == 8'h03, "T3: byte2=03");
        check(rd_val[31:24] == 8'h04, "T3: byte3=04");

        //======================================================================
        // Test 4: MATMUL 4x4 identity
        //======================================================================
        $display("--- Test 4: MATMUL identity ---");
        axi_write(32'h20, {8'd4, 8'd3, 8'd2, 8'd1});
        axi_write(32'h30, {8'd0, 8'd0, 8'd0, 8'd1});
        axi_write(32'h34, {8'd0, 8'd0, 8'd1, 8'd0});
        axi_write(32'h38, {8'd0, 8'd1, 8'd0, 8'd0});
        axi_write(32'h3C, {8'd1, 8'd0, 8'd0, 8'd0});
        axi_write(32'h08, 32'd4);
        axi_write(32'h0C, 32'd0);
        axi_write(32'h10, 32'd16);
        axi_write(32'h14, 32'd80);
        clear_start();                  // ensure reg_start=0
        axi_write(32'h00, 32'h23);     // start + enable + irq_en + OP=MATMUL
        while (!ai_irq) @(posedge clk);
        axi_read(32'h70, rd_val);
        check(rd_val == {8'd4, 8'd3, 8'd2, 8'd1}, "T4: result correct");
        axi_read(32'h04, rd_val);
        check(rd_val[1] == 1'b1, "T4: done flag set");

        //======================================================================
        // Test 5: MATMUL 2x2
        //======================================================================
        $display("--- Test 5: MATMUL 2x2 ---");
        axi_write(32'h20, {8'd0, 8'd0, 8'd3, 8'd2});
        axi_write(32'h30, {8'd0, 8'd0, 8'd5, 8'd3});
        axi_write(32'h34, {8'd0, 8'd0, 8'd2, 8'd7});
        axi_write(32'h08, 32'd2);
        axi_write(32'h0C, 32'd0);
        axi_write(32'h10, 32'd16);
        axi_write(32'h14, 32'd80);
        clear_start();
        axi_write(32'h00, 32'h23);
        while (!ai_irq) @(posedge clk);
        axi_read(32'h70, rd_val);
        check(rd_val[7:0]  == 8'd21, "T5: result[0]=21");
        check(rd_val[15:8] == 8'd20, "T5: result[1]=20");
        axi_read(32'h04, rd_val);

        //======================================================================
        // Test 6: RELU
        //======================================================================
        $display("--- Test 6: RELU ---");
        axi_write(32'h20, {8'd0, 8'd64, 8'd200, 8'd10});
        axi_write(32'h24, {8'd127, 8'd128, 8'd255, 8'd50});
        axi_write(32'h08, 32'd8);
        axi_write(32'h0C, 32'd0);
        axi_write(32'h14, 32'd80);
        clear_start();
        axi_write(32'h00, 32'h2B);  // irq_en + OP=RELU + start + enable
        while (!ai_irq) @(posedge clk);
        axi_read(32'h70, rd_val);
        check(rd_val[7:0]   == 8'd0,   "T6: RELU(10)=0");
        check(rd_val[15:8]  == 8'd200, "T6: RELU(200)=200");
        check(rd_val[23:16] == 8'd0,   "T6: RELU(64)=0");
        check(rd_val[31:24] == 8'd0,   "T6: RELU(0)=0");
        axi_read(32'h74, rd_val);
        check(rd_val[7:0]   == 8'd0,   "T6: RELU(50)=0");
        check(rd_val[15:8]  == 8'd255, "T6: RELU(255)=255");
        check(rd_val[23:16] == 8'd128, "T6: RELU(128)=128");
        check(rd_val[31:24] == 8'd0,   "T6: RELU(127)=0");
        axi_read(32'h04, rd_val);

        //======================================================================
        // Test 7: SIGMOID
        //======================================================================
        $display("--- Test 7: SIGMOID ---");
        axi_write(32'h20, {8'd255, 8'd160, 8'd128, 8'd96});
        axi_write(32'h24, 8'd64);
        axi_write(32'h08, 32'd5);
        axi_write(32'h0C, 32'd0);
        axi_write(32'h14, 32'd80);
        clear_start();
        axi_write(32'h00, 32'h33);  // irq_en + OP=SIGMOID + start + enable
        while (!ai_irq) @(posedge clk);
        axi_read(32'h70, rd_val);
        check(rd_val[7:0]   == 8'd128,  "T7: sigmoid(96)=128");
        check(rd_val[15:8]  >  8'd128,  "T7: sigmoid(128)>128");
        check(rd_val[23:16] <  8'd255,  "T7: sigmoid(160)<255");
        check(rd_val[31:24] == 8'd255,  "T7: sigmoid(255)=255");
        axi_read(32'h74, rd_val);
        check(rd_val[7:0]   == 8'd0,    "T7: sigmoid(64)=0");
        axi_read(32'h04, rd_val);

        //======================================================================
        // Test 8: ADD_VEC
        //======================================================================
        $display("--- Test 8: ADD_VEC ---");
        axi_write(32'h20, {8'd40, 8'd30, 8'd20, 8'd10});
        axi_write(32'h30, {8'd20, 8'd15, 8'd10, 8'd5});
        axi_write(32'h08, 32'd4);
        axi_write(32'h0C, 32'd0);
        axi_write(32'h10, 32'd16);
        axi_write(32'h14, 32'd80);
        clear_start();
        axi_write(32'h00, 32'h3B);  // irq_en + OP=ADD_VEC + start + enable
        while (!ai_irq) @(posedge clk);
        axi_read(32'h70, rd_val);
        check(rd_val[7:0]   == 8'd15, "T8: add[0]=15");
        check(rd_val[15:8]  == 8'd30, "T8: add[1]=30");
        check(rd_val[23:16] == 8'd45, "T8: add[2]=45");
        check(rd_val[31:24] == 8'd60, "T8: add[3]=60");
        axi_read(32'h04, rd_val);

        //======================================================================
        // Test 9: LAYERNORM
        //======================================================================
        $display("--- Test 9: LAYERNORM ---");
        axi_write(32'h20, {8'd90, 8'd120, 8'd80, 8'd100});
        axi_write(32'h08, 32'd4);
        axi_write(32'h0C, 32'd0);
        axi_write(32'h14, 32'd80);
        clear_start();
        axi_write(32'h00, 32'h43);  // irq_en + OP=LAYERNORM + start + enable
        while (!ai_irq) @(posedge clk);
        begin
            integer mn;
            mn = 0;
            for (i = 0; i < 4; i = i + 1) begin
                axi_read(32'h70 + i, rd_val);
                mn = mn + rd_val[7:0];
            end
            check(((mn/4) >= 123) && ((mn/4) <= 133), "T9: mean near 128");
        end
        axi_read(32'h04, rd_val);

        //======================================================================
        // Test 10: IRQ behavior (irq_en=0)
        //======================================================================
        $display("--- Test 10: IRQ ---");
        check(ai_irq == 1'b0, "T10: IRQ cleared");
        axi_write(32'h20, 8'd1);
        axi_write(32'h21, 8'd1);
        axi_write(32'h08, 32'd2);
        axi_write(32'h0C, 32'd0);
        axi_write(32'h14, 32'd80);
        clear_start();
        axi_write(32'h00, 32'h0B);  // OP=RELU + start + enable (NO irq_en)
        repeat(80) @(posedge clk);
        check(ai_irq == 1'b0, "T10: IRQ low when irq_en=0");
        axi_read(32'h04, rd_val);
        check(rd_val[1] == 1'b1, "T10: done set");

        //======================================================================
        // Test 11: Multi-op back-to-back
        //======================================================================
        $display("--- Test 11: Multi-op ---");
        axi_write(32'h20, {8'd0, 8'd200, 8'd5, 8'd0});
        axi_write(32'h08, 32'd2);
        axi_write(32'h0C, 32'd0);
        axi_write(32'h14, 32'd80);
        clear_start();
        axi_write(32'h00, 32'h2B);
        while (!ai_irq) @(posedge clk);
        axi_read(32'h70, rd_val);
        check(rd_val[7:0]  == 8'd0, "T11: RELU(0)=0");
        check(rd_val[15:8] == 8'd5, "T11: RELU(5)=5");
        axi_read(32'h04, rd_val);

        clear_start();
        axi_write(32'h30, {8'd0, 8'd0, 8'd30, 8'd10});
        axi_write(32'h0C, 32'd80);
        axi_write(32'h10, 32'd16);
        axi_write(32'h14, 32'd160);
        axi_write(32'h00, 32'h3B);
        while (!ai_irq) @(posedge clk);
        axi_read(32'hC0, rd_val);
        check(rd_val[7:0]  == 8'd10,  "T11: ADD(0,10)=10");
        check(rd_val[15:8] == 8'd230, "T11: ADD(200,30)=230");
        axi_read(32'h04, rd_val);

        $display("========================================");
        $display(" Tests Passed: %0d", tests_passed);
        $display(" Tests Failed: %0d", tests_failed);
        if (tests_failed == 0)
            $display(" RESULT: ALL TESTS PASSED");
        else
            $display(" RESULT: SOME TESTS FAILED");
        $display("========================================");
        $finish;
    end

endmodule
