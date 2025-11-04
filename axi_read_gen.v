module axi_read_gen
(
// Clock
input i_clk,
// Reset
input i_reset_n,
// AXI I/F
// Read Address Channel
output reg [6:0] arid,
output reg [31:0] araddr,
output reg [7:0] arlen,
output reg [2:0] arsize,
output reg [1:0] arburst,
output reg       arvalid,
input            arready,

// Read Data/Response Channel
input [6:0] rid,
input [255:0] rdata,
input [1:0] rresp,
input       rlast,
input       rvalid,
output reg  rready
);

    // Internal storage for read data verification
    reg [255:0] read_data_mem [0:15];

    // Queue initial addresses for all 15 queues
    reg [31:0] Q_ADDR_0;
    reg [31:0] Q_ADDR_1;
    reg [31:0] Q_ADDR_2;
    reg [31:0] Q_ADDR_3;
    reg [31:0] Q_ADDR_4;
    reg [31:0] Q_ADDR_5;
    reg [31:0] Q_ADDR_6;
    reg [31:0] Q_ADDR_7;
    reg [31:0] Q_ADDR_8;
    reg [31:0] Q_ADDR_9;
    reg [31:0] Q_ADDR_10;
    reg [31:0] Q_ADDR_11;
    reg [31:0] Q_ADDR_12;
    reg [31:0] Q_ADDR_13;
    reg [31:0] Q_ADDR_14;

    // Fragment type definitions (must match write gen)
    localparam S_PKT  = 2'b10;
    localparam M_PKT  = 2'b00;
    localparam L_PKT  = 2'b01;
    localparam SG_PKT = 2'b11;

    localparam MSG_T0 = 4'b1000;
    localparam MSG_T1 = 4'b1001;
    localparam MSG_T2 = 4'b1010;
    localparam MSG_T3 = 4'b1011;

    reg [127:0] expected_header;
    reg [119:0] tlp_base;

    // Interrupt monitor variables
    integer intr_count;
    reg [3:0] completed_queue;
    reg [31:0] queue_base_addr;
    reg [15:0] wptr_bytes;
    reg [7:0] arlen_val;

    // ========================================
    // Interrupt Monitor (Parallel Thread)
    // ========================================
    initial begin
        intr_count = 0;

        // Wait for reset
        wait(i_reset_n);
        #100;

`ifdef DEBUG
        $display("\n[READ_GEN] Interrupt monitor started");
`endif

        forever begin
            // Poll for any interrupt by checking INTR_STATUS register
            @(posedge i_clk);
            #1; // Small delay to let signals settle

            // Check for error interrupt (priority: handle errors first) - Check all queues
            if (tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_0[3]) begin
                $display("\n========================================");
                $display("[%0t] [READ_GEN] *** ERROR INTERRUPT DETECTED (Queue 0) ***", $time);
                $display("[%0t] [READ_GEN] Q0 INTR_STATUS = 0x%h",
                         $time, tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_0);
                $display("========================================\n");
                force tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_0[3] = 1'b1;
                @(posedge i_clk); #1;
                release tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_0;
                @(posedge i_clk);
            end else if (tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_1[3]) begin
                $display("\n========================================");
                $display("[%0t] [READ_GEN] *** ERROR INTERRUPT DETECTED (Queue 1) ***", $time);
                $display("[%0t] [READ_GEN] Q1 INTR_STATUS = 0x%h",
                         $time, tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_1);
                $display("========================================\n");
                force tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_1[3] = 1'b1;
                @(posedge i_clk); #1;
                release tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_1;
                @(posedge i_clk);
            end else if (tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_2[3]) begin
                $display("\n========================================");
                $display("[%0t] [READ_GEN] *** ERROR INTERRUPT DETECTED (Queue 2) ***", $time);
                $display("[%0t] [READ_GEN] Q2 INTR_STATUS = 0x%h",
                         $time, tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_2);
                $display("========================================\n");
                force tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_2[3] = 1'b1;
                @(posedge i_clk); #1;
                release tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_2;
                @(posedge i_clk);
            end else if (tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_3[3]) begin
                $display("\n========================================");
                $display("[%0t] [READ_GEN] *** ERROR INTERRUPT DETECTED (Queue 3) ***", $time);
                $display("[%0t] [READ_GEN] Q3 INTR_STATUS = 0x%h",
                         $time, tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_3);
                $display("========================================\n");
                force tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_3[3] = 1'b1;
                @(posedge i_clk); #1;
                release tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_3;
                @(posedge i_clk);
            end else if (tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_4[3]) begin
                $display("\n========================================");
                $display("[%0t] [READ_GEN] *** ERROR INTERRUPT DETECTED (Queue 4) ***", $time);
                $display("[%0t] [READ_GEN] Q4 INTR_STATUS = 0x%h",
                         $time, tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_4);
                $display("========================================\n");
                force tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_4[3] = 1'b1;
                @(posedge i_clk); #1;
                release tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_4;
                @(posedge i_clk);
            end else if (tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_5[3]) begin
                $display("\n========================================");
                $display("[%0t] [READ_GEN] *** ERROR INTERRUPT DETECTED (Queue 5) ***", $time);
                $display("[%0t] [READ_GEN] Q5 INTR_STATUS = 0x%h",
                         $time, tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_5);
                $display("========================================\n");
                force tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_5[3] = 1'b1;
                @(posedge i_clk); #1;
                release tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_5;
                @(posedge i_clk);
            end else if (tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_6[3]) begin
                $display("\n========================================");
                $display("[%0t] [READ_GEN] *** ERROR INTERRUPT DETECTED (Queue 6) ***", $time);
                $display("[%0t] [READ_GEN] Q6 INTR_STATUS = 0x%h",
                         $time, tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_6);
                $display("========================================\n");
                force tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_6[3] = 1'b1;
                @(posedge i_clk); #1;
                release tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_6;
                @(posedge i_clk);
            end else if (tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_7[3]) begin
                $display("\n========================================");
                $display("[%0t] [READ_GEN] *** ERROR INTERRUPT DETECTED (Queue 7) ***", $time);
                $display("[%0t] [READ_GEN] Q7 INTR_STATUS = 0x%h",
                         $time, tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_7);
                $display("========================================\n");
                force tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_7[3] = 1'b1;
                @(posedge i_clk); #1;
                release tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_7;
                @(posedge i_clk);
            end else if (tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_8[3]) begin
                $display("\n========================================");
                $display("[%0t] [READ_GEN] *** ERROR INTERRUPT DETECTED (Queue 8) ***", $time);
                $display("[%0t] [READ_GEN] Q8 INTR_STATUS = 0x%h",
                         $time, tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_8);
                $display("========================================\n");
                force tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_8[3] = 1'b1;
                @(posedge i_clk); #1;
                release tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_8;
                @(posedge i_clk);
            end else if (tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_9[3]) begin
                $display("\n========================================");
                $display("[%0t] [READ_GEN] *** ERROR INTERRUPT DETECTED (Queue 9) ***", $time);
                $display("[%0t] [READ_GEN] Q9 INTR_STATUS = 0x%h",
                         $time, tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_9);
                $display("========================================\n");
                force tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_9[3] = 1'b1;
                @(posedge i_clk); #1;
                release tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_9;
                @(posedge i_clk);
            end else if (tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_10[3]) begin
                $display("\n========================================");
                $display("[%0t] [READ_GEN] *** ERROR INTERRUPT DETECTED (Queue 10) ***", $time);
                $display("[%0t] [READ_GEN] Q10 INTR_STATUS = 0x%h",
                         $time, tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_10);
                $display("========================================\n");
                force tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_10[3] = 1'b1;
                @(posedge i_clk); #1;
                release tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_10;
                @(posedge i_clk);
            end else if (tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_11[3]) begin
                $display("\n========================================");
                $display("[%0t] [READ_GEN] *** ERROR INTERRUPT DETECTED (Queue 11) ***", $time);
                $display("[%0t] [READ_GEN] Q11 INTR_STATUS = 0x%h",
                         $time, tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_11);
                $display("========================================\n");
                force tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_11[3] = 1'b1;
                @(posedge i_clk); #1;
                release tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_11;
                @(posedge i_clk);
            end else if (tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_12[3]) begin
                $display("\n========================================");
                $display("[%0t] [READ_GEN] *** ERROR INTERRUPT DETECTED (Queue 12) ***", $time);
                $display("[%0t] [READ_GEN] Q12 INTR_STATUS = 0x%h",
                         $time, tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_12);
                $display("========================================\n");
                force tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_12[3] = 1'b1;
                @(posedge i_clk); #1;
                release tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_12;
                @(posedge i_clk);
            end else if (tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_13[3]) begin
                $display("\n========================================");
                $display("[%0t] [READ_GEN] *** ERROR INTERRUPT DETECTED (Queue 13) ***", $time);
                $display("[%0t] [READ_GEN] Q13 INTR_STATUS = 0x%h",
                         $time, tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_13);
                $display("========================================\n");
                force tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_13[3] = 1'b1;
                @(posedge i_clk); #1;
                release tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_13;
                @(posedge i_clk);
            end else if (tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_14[3]) begin
                $display("\n========================================");
                $display("[%0t] [READ_GEN] *** ERROR INTERRUPT DETECTED (Queue 14) ***", $time);
                $display("[%0t] [READ_GEN] Q14 INTR_STATUS = 0x%h",
                         $time, tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_14);
                $display("========================================\n");
                force tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_14[3] = 1'b1;
                @(posedge i_clk); #1;
                release tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_14;
                @(posedge i_clk);
            end

            // Check for completion interrupt on all queues (Q0-Q14)
            completed_queue = 4'hF;  // Default: no queue

            if (tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_0[0]) begin
                completed_queue = 4'h0;
            end else if (tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_1[0]) begin
                completed_queue = 4'h1;
            end else if (tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_2[0]) begin
                completed_queue = 4'h2;
            end else if (tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_3[0]) begin
                completed_queue = 4'h3;
            end else if (tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_4[0]) begin
                completed_queue = 4'h4;
            end else if (tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_5[0]) begin
                completed_queue = 4'h5;
            end else if (tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_6[0]) begin
                completed_queue = 4'h6;
            end else if (tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_7[0]) begin
                completed_queue = 4'h7;
            end else if (tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_8[0]) begin
                completed_queue = 4'h8;
            end else if (tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_9[0]) begin
                completed_queue = 4'h9;
            end else if (tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_10[0]) begin
                completed_queue = 4'hA;
            end else if (tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_11[0]) begin
                completed_queue = 4'hB;
            end else if (tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_12[0]) begin
                completed_queue = 4'hC;
            end else if (tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_13[0]) begin
                completed_queue = 4'hD;
            end else if (tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_14[0]) begin
                completed_queue = 4'hE;
            end

            if (completed_queue != 4'hF) begin
                intr_count = intr_count + 1;

                $display("\n========================================");
                $display("[%0t] [READ_GEN] *** COMPLETION INTERRUPT #%0d (Queue %0d) ***", $time, intr_count, completed_queue);

                // Get WPTR and queue base address based on completed_queue
                case (completed_queue)
                    4'h0: begin
                        wptr_bytes = tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_0[15:0];
                        queue_base_addr = tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_0[31:0];
                    end
                    4'h1: begin
                        wptr_bytes = tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_1[15:0];
                        queue_base_addr = tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_1[31:0];
                    end
                    4'h2: begin
                        wptr_bytes = tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_2[15:0];
                        queue_base_addr = tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_2[31:0];
                    end
                    4'h3: begin
                        wptr_bytes = tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_3[15:0];
                        queue_base_addr = tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_3[31:0];
                    end
                    4'h4: begin
                        wptr_bytes = tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_4[15:0];
                        queue_base_addr = tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_4[31:0];
                    end
                    4'h5: begin
                        wptr_bytes = tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_5[15:0];
                        queue_base_addr = tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_5[31:0];
                    end
                    4'h6: begin
                        wptr_bytes = tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_6[15:0];
                        queue_base_addr = tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_6[31:0];
                    end
                    4'h7: begin
                        wptr_bytes = tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_7[15:0];
                        queue_base_addr = tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_7[31:0];
                    end
                    4'h8: begin
                        wptr_bytes = tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_8[15:0];
                        queue_base_addr = tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_8[31:0];
                    end
                    4'h9: begin
                        wptr_bytes = tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_9[15:0];
                        queue_base_addr = tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_9[31:0];
                    end
                    4'hA: begin
                        wptr_bytes = tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_10[15:0];
                        queue_base_addr = tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_10[31:0];
                    end
                    4'hB: begin
                        wptr_bytes = tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_11[15:0];
                        queue_base_addr = tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_11[31:0];
                    end
                    4'hC: begin
                        wptr_bytes = tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_12[15:0];
                        queue_base_addr = tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_12[31:0];
                    end
                    4'hD: begin
                        wptr_bytes = tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_13[15:0];
                        queue_base_addr = tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_13[31:0];
                    end
                    4'hE: begin
                        wptr_bytes = tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_14[15:0];
                        queue_base_addr = tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_14[31:0];
                    end
                    default: begin
                        wptr_bytes = 16'h0;
                        queue_base_addr = 32'h0;
                    end
                endcase

                $display("[%0t] [READ_GEN] Queue %0d: WPTR=%0d bytes, Base Addr=0x%h",
                         $time, completed_queue, wptr_bytes, queue_base_addr);

                $display("[%0t] [READ_GEN] Queue %0d Init Address: 0x%h",
                         $time, completed_queue, queue_base_addr);

                // Read and verify data if valid (queue 0 has addr 0x0, so don't skip it)
                if (wptr_bytes > 0 && completed_queue != 4'hF) begin
                    arlen_val = (wptr_bytes + 31) / 32 - 1;  // Round up and convert to arlen
                    $display("[%0t] [READ_GEN] Reading %0d beats (%0d bytes) from address 0x%h",
                             $time, arlen_val + 1, wptr_bytes, queue_base_addr);

                    // Perform AXI read
                    READ_COMPLETION_DATA(completed_queue, queue_base_addr, arlen_val, wptr_bytes);
                end else begin
                    $display("[%0t] [READ_GEN] Skip reading (WPTR=%0d, addr=0x%h)",
                             $time, wptr_bytes, queue_base_addr);
                end

                $display("========================================\n");

                // Clear completion interrupt based on completed_queue
                case (completed_queue)
                    4'h0: begin
                        force tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_0[0] = 1'b1;
                        @(posedge i_clk); #1;
                        release tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_0;
                    end
                    4'h1: begin
                        force tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_1[0] = 1'b1;
                        @(posedge i_clk); #1;
                        release tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_1;
                    end
                    4'h2: begin
                        force tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_2[0] = 1'b1;
                        @(posedge i_clk); #1;
                        release tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_2;
                    end
                    4'h3: begin
                        force tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_3[0] = 1'b1;
                        @(posedge i_clk); #1;
                        release tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_3;
                    end
                    4'h4: begin
                        force tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_4[0] = 1'b1;
                        @(posedge i_clk); #1;
                        release tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_4;
                    end
                    4'h5: begin
                        force tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_5[0] = 1'b1;
                        @(posedge i_clk); #1;
                        release tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_5;
                    end
                    4'h6: begin
                        force tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_6[0] = 1'b1;
                        @(posedge i_clk); #1;
                        release tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_6;
                    end
                    4'h7: begin
                        force tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_7[0] = 1'b1;
                        @(posedge i_clk); #1;
                        release tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_7;
                    end
                    4'h8: begin
                        force tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_8[0] = 1'b1;
                        @(posedge i_clk); #1;
                        release tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_8;
                    end
                    4'h9: begin
                        force tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_9[0] = 1'b1;
                        @(posedge i_clk); #1;
                        release tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_9;
                    end
                    4'hA: begin
                        force tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_10[0] = 1'b1;
                        @(posedge i_clk); #1;
                        release tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_10;
                    end
                    4'hB: begin
                        force tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_11[0] = 1'b1;
                        @(posedge i_clk); #1;
                        release tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_11;
                    end
                    4'hC: begin
                        force tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_12[0] = 1'b1;
                        @(posedge i_clk); #1;
                        release tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_12;
                    end
                    4'hD: begin
                        force tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_13[0] = 1'b1;
                        @(posedge i_clk); #1;
                        release tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_13;
                    end
                    4'hE: begin
                        force tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_14[0] = 1'b1;
                        @(posedge i_clk); #1;
                        release tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_14;
                    end
                endcase
            end

            @(posedge i_clk);
        end
    end

    // ========================================
    // Legacy Read Verification Tests
    // ========================================
    `ifdef RUN_ORIGINAL_TESTS
    initial begin
        // Wait for reset
        wait(i_reset_n);
        #6500;  // Wait for all assembly operations to complete (including bad header test)

        // TLP header base (same as write gen)
        tlp_base = 120'h0;
        tlp_base[7:5] = 3'b011;           // fmt
        tlp_base[4:3] = 2'b10;            // type
        tlp_base[31:24] = 8'h20;          // length (128B)
        tlp_base[51:48] = 4'b0000;        // pcie_tag
        tlp_base[63:56] = 8'b01111111;    // msg code
        tlp_base[87:80] = 8'h1A;          // vendor id
        tlp_base[95:88] = 8'hB4;          // vendor id
        tlp_base[99:96] = 4'b0001;        // header version
        tlp_base[119:112] = 8'h0;         // source endpoint id

        $display("\n========================================");
        $display("VERIFY TEST 1: S->L assembly (MSG_T0, 6 payload beats)");
        $display("========================================\n");
        // Test 1: S->L assembly (6 payload beats, header not stored in SRAM)
        // SRAM order: CCCC, BBBB, AAAA, 1111, FFFF, EEEE
        expected_header = {L_PKT, 2'b01, MSG_T0, tlp_base};
        READ_AND_CHECK_ASSEMBLY(
            4'h0,       // queue_tag = 0
            32'h0,      // address (queue 0 init addr)
            8'd5,       // arlen = 5 (6 beats)
            3'd5,       // 32 bytes
            2'b01,      // INCR
            expected_header,
            6,          // payload beats only
            {256'h0,  // Padding (MSB)
             256'h0,
             256'h00000000000000000000000000000000EEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE,
             256'h00000000000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
             256'h0000000000000000000000000000000011111111111111111111111111111111,
             256'h00000000000000000000000000000000AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA,
             256'h00000000000000000000000000000000BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB,
             256'h00000000000000000000000000000000CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC},  // First payload (LSB)
            32'd192    // expected_wptr_bytes = (6 beats) * 32 bytes
        );

        #200;

        $display("\n========================================");
        $display("VERIFY TEST 2: S->M->L assembly (MSG_T1, 6 payload beats)");
        $display("========================================\n");
        // Test 2: S->M->L assembly (6 payload beats, header not stored in SRAM)
        // SRAM order: 4444, 3333, 7777, 6666, AAAA, 9999
        expected_header = {L_PKT, 2'b10, MSG_T1, tlp_base};
        READ_AND_CHECK_ASSEMBLY(
            4'h1,       // queue_tag = 1
            32'h800,    // address (queue 1 init addr = 1*64*32 = 2048 = 0x800)
            8'd5,       // arlen = 5 (6 beats)
            3'd5,       // 32 bytes
            2'b01,      // INCR
            expected_header,
            6,          // payload beats only
            {256'h0,  // Padding (MSB)
             256'h0,
             256'h0000000000000000000000000000000099999999999999999999999999999999,
             256'h00000000000000000000000000000000AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA,
             256'h0000000000000000000000000000000066666666666666666666666666666666,
             256'h0000000000000000000000000000000077777777777777777777777777777777,
             256'h0000000000000000000000000000000033333333333333333333333333333333,
             256'h0000000000000000000000000000000044444444444444444444444444444444},  // First payload (LSB)
            32'd192    // expected_wptr_bytes = (6 beats) * 32 bytes
        );

        #200;

        $display("\n========================================");
        $display("VERIFY TEST 3: S->M->M->L assembly (MSG_T2, 4 payload beats)");
        $display("========================================\n");
        // Test 3: S->M->M->L assembly (4 payload beats, header not stored in SRAM)
        // SRAM order: DEADBEEF, 12345678, FEDCBA98, 11112222...
        expected_header = {L_PKT, 2'b11, MSG_T2, tlp_base};
        READ_AND_CHECK_ASSEMBLY(
            4'h2,       // queue_tag = 2
            32'h1000,   // address (queue 2 init addr = 2*64*32 = 4096 = 0x1000)
            8'd3,       // arlen = 3 (4 beats)
            3'd5,       // 32 bytes
            2'b01,      // INCR
            expected_header,
            4,          // payload beats only
            {256'h0,  // Padding (MSB)
             256'h0,
             256'h0,
             256'h0,
             256'h0000000000000000000000000000000011112222333344445555666677778888,
             256'h00000000000000000000000000000000FEDCBA98FEDCBA98FEDCBA98FEDCBA98,
             256'h0000000000000000000000000000000012345678123456781234567812345678,
             256'h00000000000000000000000000000000DEADBEEFDEADBEEFDEADBEEFDEADBEEF},  // First payload (LSB)
            32'd128    // expected_wptr_bytes = (4 beats) * 32 bytes
        );

        #200;

        $display("\n========================================");
        $display("VERIFY TEST 4: Single packet (MSG_T3, 2 payload beats)");
        $display("========================================\n");
        // Test 4: Single packet (2 payload beats, header not stored in SRAM)
        // SRAM order: 5555AAAA..., AAAA5555...
        expected_header = {SG_PKT, 2'b00, MSG_T3, tlp_base};
        READ_AND_CHECK_ASSEMBLY(
            4'h3,       // queue_tag = 3
            32'h1800,   // address (queue 3 init addr = 3*64*32 = 6144 = 0x1800)
            8'd1,       // arlen = 1 (2 beats)
            3'd5,       // 32 bytes
            2'b01,      // INCR
            expected_header,
            2,          // payload beats only
            {256'h0,  // Padding (MSB)
             256'h0,
             256'h0,
             256'h0,
             256'h0,
             256'h0,
             256'h00000000000000000000000000000000AAAA5555AAAA5555AAAA5555AAAA5555,
             256'h000000000000000000000000000000005555AAAA5555AAAA5555AAAA5555AAAA},  // First payload (LSB)
            32'd64     // expected_wptr_bytes = (2 beats) * 32 bytes
        );

        #200;
        $display("\n[READ_GEN] All assembly verifications completed\n");
        #200;
        // $finish; // Commented out to allow write_gen tests to complete
    end
    `endif  // RUN_ORIGINAL_TESTS

    // ========================================
    // AXI Read Task with Assembly Payload Verification
    // ========================================
    task automatic READ_AND_CHECK_ASSEMBLY;
        input [3:0]       queue_tag;
        input [31:0]      read_araddr;
        input [7:0]       read_arlen;
        input [2:0]       read_arsize;
        input [1:0]       read_arburst;
        input [127:0]     expected_header;
        input integer     exp_beats;
        input [256*16-1:0] expected_payload;  // Up to 16 beats
        input [31:0]      expected_wptr_bytes;  // Expected write pointer in bytes

        integer beat;
        reg [255:0] data_beat;
        reg [127:0] received_header;
        reg verification_pass;
        integer total_beats;
        reg [255:0] exp_beat_data;
        reg [31:0] queue_init_addr;

        begin
            total_beats = read_arlen + 1;

`ifdef DEBUG
            $display("\n========================================");
            $display("[%0t] [READ_GEN] READ_AND_CHECK_ASSEMBLY START", $time);
            $display("  Queue Tag: %0d", queue_tag);
            $display("  Address: 0x%h", read_araddr);
            $display("  Length:  %0d payload beats", total_beats);
            $display("  Expected WPTR: %0d bytes", expected_wptr_bytes);
            $display("  (Header assembled but not stored in SRAM)");
            $display("========================================");
`endif

            verification_pass = 1'b1;

            // Read Address Phase
            @(posedge i_clk);
            #1;
            arvalid = 1'b1;
            araddr  = read_araddr;
            arlen   = read_arlen;
            arsize  = read_arsize;
            arburst = read_arburst;
            arid    = 7'h0;

            @(posedge i_clk);
            while (!arready) begin
                @(posedge i_clk);
            end

`ifdef DEBUG
            $display("[%0t] [READ_GEN] Read Address Sent", $time);
`endif

            @(posedge i_clk);
            arvalid = 1'b0;
            rready  = 1'b1;

            // Read Data Phase
            beat = 0;
            while (beat < total_beats) begin
                @(posedge i_clk);
                #1;

                if (rvalid && rready) begin
                    data_beat = rdata;
                    read_data_mem[beat] = data_beat;

`ifdef DEBUG
                    $display("[%0t] [READ_GEN] Sampled beat %0d: data=0x%h", $time, beat, data_beat);
`endif

                    // Verify payload data (all beats are payload, header not stored in SRAM)
                    if (beat < exp_beats) begin
                        // Expected data: first payload beat is at lowest address
                        exp_beat_data = expected_payload[beat * 256 +: 256];
                        if (data_beat == exp_beat_data) begin
`ifdef DEBUG
                            $display("[%0t] [READ_GEN] Beat %0d: PAYLOAD MATCH (0x%h)",
                                     $time, beat, data_beat);
`endif
                        end else begin
                            $display("[%0t] [READ_GEN] Beat %0d: PAYLOAD MISMATCH", $time, beat);
                            $display("  Expected: 0x%h", exp_beat_data);
                            $display("  Received: 0x%h", data_beat);
                            verification_pass = 1'b0;
                        end
                    end

                    // Check response
                    if (rresp != 2'b00) begin
                        $display("[%0t] [READ_GEN] WARNING: Non-OKAY response: %0d", $time, rresp);
                        verification_pass = 1'b0;
                    end

                    // Check RLAST
                    if (rlast && (beat != total_beats - 1)) begin
                        $display("[%0t] [READ_GEN] WARNING: Unexpected RLAST at beat %0d", $time, beat);
                        verification_pass = 1'b0;
                    end else if (!rlast && (beat == total_beats - 1)) begin
                        $display("[%0t] [READ_GEN] WARNING: RLAST not asserted at last beat", $time);
                        verification_pass = 1'b0;
                    end

                    beat = beat + 1;
                end
            end

            // Wait one more cycle for AXI slave to see the last handshake
            @(posedge i_clk);
            #1;

            rready = 1'b0;

            // Now verify WPTR and queue address
            #10;  // Wait for any pending signals

            $display("\n========================================");
            $display("[%0t] [READ_GEN] WPTR and Queue Address Verification", $time);

            // Check write pointer
            $display("[%0t] [READ_GEN] Actual WPTR: %0d bytes",
                     $time,
                     tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_0[15:0]);

            if (tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_0[15:0] != expected_wptr_bytes) begin
                $display("[%0t] [READ_GEN] ERROR: WPTR mismatch! (expected %0d, got %0d)",
                         $time, expected_wptr_bytes,
                         tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_0[15:0]);
                verification_pass = 1'b0;
            end else begin
                $display("[%0t] [READ_GEN] WPTR verified correctly (%0d bytes)",
                         $time, expected_wptr_bytes);
            end

            // Get and display queue init address
            case (queue_tag)
                4'h0: queue_init_addr = tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_0[31:0];
                4'h1: queue_init_addr = tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_1[31:0];
                4'h2: queue_init_addr = tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_2[31:0];
                4'h3: queue_init_addr = tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_3[31:0];
                4'h4: queue_init_addr = tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_4[31:0];
                4'h5: queue_init_addr = tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_5[31:0];
                4'h6: queue_init_addr = tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_6[31:0];
                4'h7: queue_init_addr = tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_7[31:0];
                4'h8: queue_init_addr = tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_8[31:0];
                4'h9: queue_init_addr = tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_9[31:0];
                4'hA: queue_init_addr = tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_10[31:0];
                4'hB: queue_init_addr = tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_11[31:0];
                4'hC: queue_init_addr = tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_12[31:0];
                4'hD: queue_init_addr = tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_13[31:0];
                4'hE: queue_init_addr = tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_14[31:0];
                default: queue_init_addr = 32'h0;
            endcase

            $display("[%0t] [READ_GEN] Queue %0d Init Address: 0x%h",
                     $time, queue_tag, queue_init_addr);
            $display("[%0t] [READ_GEN] Read Address: 0x%h (should match Q init addr)",
                     $time, read_araddr);

            if (read_araddr == queue_init_addr) begin
                $display("[%0t] [READ_GEN] Address verified correctly", $time);
            end else begin
                $display("[%0t] [READ_GEN] WARNING: Address mismatch! (init_addr=0x%h, read_addr=0x%h)",
                         $time, queue_init_addr, read_araddr);
            end

            $display("========================================");
            if (verification_pass) begin
                $display("[%0t] [READ_GEN] *** ASSEMBLY VERIFICATION PASSED ***", $time);
            end else begin
                $display("[%0t] [READ_GEN] *** ASSEMBLY VERIFICATION FAILED ***", $time);
            end
            $display("[%0t] [READ_GEN] READ_AND_CHECK_ASSEMBLY COMPLETE", $time);
            $display("========================================\n");
        end
    endtask

    // ========================================
    // AXI Read Task with Internal Verification (Legacy)
    // ========================================
    task automatic READ_AND_CHECK;
        input [31:0]  read_araddr;
        input [7:0]   read_arlen;      // AXI len (beats - 1)
        input [2:0]   read_arsize;
        input [1:0]   read_arburst;
        input [127:0] expected_header;  // Expected header to verify

        integer beat;
        reg [255:0] data_beat;
        reg [127:0] received_header;
        reg verification_pass;
        integer total_beats;
        integer timeout_cnt;

        begin
            total_beats = read_arlen + 1;  // AXI len is (beats - 1)

            $display("\n========================================");
            $display("[%0t] [READ_GEN] READ_AND_CHECK START", $time);
            $display("  Address: 0x%h", read_araddr);
            $display("  Length:  %0d beats (arlen=%0d)", total_beats, read_arlen);
            $display("  Size:    %0d (2^%0d = %0d bytes)", read_arsize, read_arsize, 1 << read_arsize);
            $display("  Burst:   %0d (%s)", read_arburst,
                     (read_arburst == 2'b00) ? "FIXED" :
                     (read_arburst == 2'b01) ? "INCR" : "WRAP");
            $display("  Expected Header: 0x%h", expected_header);
            $display("========================================");

            verification_pass = 1'b1;

            // ====================================
            // 1. Read Address Phase
            // ====================================
            @(posedge i_clk);
            #1;
            arvalid = 1'b1;
            araddr  = read_araddr;
            arlen   = read_arlen;
            arsize  = read_arsize;
            arburst = read_arburst;
            arid    = 7'h0;

            // Wait for arready with timeout
            @(posedge i_clk);
            timeout_cnt = 0;
            while (!arready && timeout_cnt < 1000) begin
                @(posedge i_clk);
                timeout_cnt = timeout_cnt + 1;
            end

            if (timeout_cnt >= 1000) begin
                $display("[%0t] [READ_GEN] *** ERROR: ARREADY TIMEOUT ***", $time);
                verification_pass = 1'b0;
            end else begin
                $display("[%0t] [READ_GEN] Read Address Sent", $time);
            end

            @(posedge i_clk);
            #1;
            arvalid = 1'b0;
            rready  = 1'b1;  // Ready to receive data

            // ====================================
            // 2. Read Data Phase
            // ====================================
            beat = 0;
            timeout_cnt = 0;
            while (beat < total_beats) begin
                @(posedge i_clk);
                #1;  // Small delay to let signals settle

                if (rvalid && rready) begin
                    // Capture data immediately
                    data_beat = rdata;
                    read_data_mem[beat] = data_beat;

                    $display("[%0t] [READ_GEN] Read Data Beat %0d: data=0x%h, last=%0b, resp=%0d",
                             $time, beat, data_beat, rlast, rresp);

                    // Verify first beat contains expected header
                    if (beat == 0) begin
                        received_header = data_beat[127:0];
                        if (received_header == expected_header) begin
                            $display("[%0t] [READ_GEN] *** HEADER MATCH *** ", $time);
                            $display("  Expected: 0x%h", expected_header);
                            $display("  Received: 0x%h", received_header);
                        end else begin
                            $display("[%0t] [READ_GEN] *** HEADER MISMATCH *** ", $time);
                            $display("  Expected: 0x%h", expected_header);
                            $display("  Received: 0x%h", received_header);
                            verification_pass = 1'b0;
                        end
                    end

                    // Check response
                    if (rresp != 2'b00) begin
                        $display("[%0t] [READ_GEN] WARNING: Non-OKAY response: %0d", $time, rresp);
                        verification_pass = 1'b0;
                    end

                    // Check if this is the last beat
                    if (rlast && (beat != total_beats - 1)) begin
                        $display("[%0t] [READ_GEN] WARNING: Unexpected RLAST at beat %0d", $time, beat);
                        verification_pass = 1'b0;
                    end else if (!rlast && (beat == total_beats - 1)) begin
                        $display("[%0t] [READ_GEN] WARNING: RLAST not asserted at last beat %0d", $time, beat);
                        verification_pass = 1'b0;
                    end

                    beat = beat + 1;
                    timeout_cnt = 0;  // Reset timeout on successful beat
                end else begin
                    // No handshake, increment timeout counter
                    timeout_cnt = timeout_cnt + 1;
                    if (timeout_cnt >= 1000) begin
                        $display("[%0t] [READ_GEN] *** ERROR: RVALID TIMEOUT at beat %0d ***", $time, beat);
                        $display("  rvalid=%0b, rready=%0b", rvalid, rready);
                        verification_pass = 1'b0;
                        beat = total_beats;  // Force exit from loop
                    end
                end
            end

            rready = 1'b0;

            $display("\n========================================");
            if (verification_pass) begin
                $display("[%0t] [READ_GEN] *** VERIFICATION PASSED ***", $time);
            end else begin
                $display("[%0t] [READ_GEN] *** VERIFICATION FAILED ***", $time);
            end
            $display("[%0t] [READ_GEN] READ_AND_CHECK COMPLETE", $time);
            $display("========================================\n");
        end
    endtask

    // ========================================
    // Read Completion Data Task (Called from Interrupt Monitor)
    // ========================================
    task READ_COMPLETION_DATA;
        input [3:0] msg_tag;
        input [31:0] base_addr;
        input [7:0] arlen_beats;
        input [15:0] expected_wptr;

        integer beat_num;
        reg [255:0] rdata_beat;
        reg [255:0] expected_beat;
        integer match_count;
        integer mismatch_count;
        reg [3:0] exp_msg_tag;
        reg exp_tag_owner;
        reg [7:0] exp_source_id;
        reg data_valid;

        begin
            $display("[%0t] [READ_GEN] === Reading Queue %0d Data ===", $time, msg_tag);
            $display("[%0t] [READ_GEN] Base Address: 0x%h, Beats: %0d, WPTR: %0d bytes",
                     $time, base_addr, arlen_beats + 1, expected_wptr);

            match_count = 0;
            mismatch_count = 0;

            // Get expected metadata
            if (msg_tag < 15) begin
                exp_msg_tag = tb_pcie_sub_msg.expected_msg_tag[msg_tag];
                exp_tag_owner = tb_pcie_sub_msg.expected_tag_owner[msg_tag];
                exp_source_id = tb_pcie_sub_msg.expected_source_id[msg_tag];
                data_valid = tb_pcie_sub_msg.expected_data_valid[msg_tag];

                if (data_valid) begin
                    $display("[%0t] [READ_GEN] === Expected Metadata ===", $time);
                    $display("[%0t] [READ_GEN] MSG_TAG: 0x%h", $time, exp_msg_tag);
                    $display("[%0t] [READ_GEN] TAG_OWNER: %0b", $time, exp_tag_owner);
                    $display("[%0t] [READ_GEN] SOURCE_ID: 0x%h", $time, exp_source_id);
                    $display("[%0t] [READ_GEN] ========================\n", $time);
                end
            end else begin
                data_valid = 1'b0;
            end

            // Set up AXI read
            @(posedge i_clk);
            #1;
            arvalid = 1'b1;
            araddr = base_addr;
            arlen = arlen_beats;
            arsize = 3'd5;  // 32 bytes
            arburst = 2'b01;  // INCR
            arid = 7'h0;

            // Wait for address handshake
            @(posedge i_clk);
            while (!arready) @(posedge i_clk);
            $display("[%0t] [READ_GEN] Address phase complete", $time);

            @(posedge i_clk);
            #1;
            arvalid = 1'b0;
            rready = 1'b1;

            // Read data beats and verify
            beat_num = 0;
            while (beat_num <= arlen_beats) begin
                @(posedge i_clk);
                #1;
                if (rvalid && rready) begin
                    rdata_beat = rdata;

                    // Get expected data from testbench
                    if (msg_tag < 15 && beat_num < 64) begin
                        expected_beat = tb_pcie_sub_msg.expected_queue_data[msg_tag][beat_num];

                        // Verify data
                        if (expected_beat == 256'h0) begin
                            // No expected data (not a random write test)
                            $display("[%0t] [READ_GEN] Beat %0d: 0x%h (no verification data)",
                                     $time, beat_num, rdata_beat);
                        end else if (rdata_beat == expected_beat) begin
                            $display("[%0t] [READ_GEN] Beat %0d: MATCH ✓", $time, beat_num);
                            $display("  Read: 0x%h", rdata_beat);
                            match_count = match_count + 1;
                        end else begin
                            $display("[%0t] [READ_GEN] Beat %0d: MISMATCH ✗", $time, beat_num);
                            $display("  Expected: 0x%h", expected_beat);
                            $display("  Read:     0x%h", rdata_beat);
                            mismatch_count = mismatch_count + 1;
                        end
                    end else begin
                        $display("[%0t] [READ_GEN] Beat %0d: 0x%h",
                                 $time, beat_num, rdata_beat);
                    end

                    beat_num = beat_num + 1;
                end
            end

            @(posedge i_clk);
            #1;
            rready = 1'b0;

            // Print verification summary
            $display("\n[%0t] [READ_GEN] === Verification Summary ===", $time);

            // Verify metadata if this is a random data test
            if (data_valid && msg_tag < 15) begin
                reg [7:0] actual_src_id;
                reg actual_tag_owner;
                reg metadata_pass;

                metadata_pass = 1'b1;

                // Read actual values from receiver's queue context
                actual_src_id = tb_pcie_sub_msg.u_pcie_msg_receiver.src_endpoint_id[msg_tag];
                actual_tag_owner = tb_pcie_sub_msg.u_pcie_msg_receiver.tag_owner[msg_tag];

                $display("\n[%0t] [READ_GEN] === Metadata Verification ===", $time);

                // Verify MSG_TAG (4 bits: TO + TAG, where TAG maps to msg_tag)
                // MSG_TAG[2:0] should match msg_tag
                if (exp_msg_tag[2:0] == msg_tag[2:0]) begin
                    $display("[%0t] [READ_GEN] MSG_TAG: MATCH ✓ (4'b%b = TO=%0b, TAG=%0d -> Queue %0d)",
                             $time, exp_msg_tag, exp_msg_tag[3], exp_msg_tag[2:0], msg_tag);
                end else begin
                    $display("[%0t] [READ_GEN] MSG_TAG: MISMATCH ✗", $time);
                    $display("  Expected TAG: %0d (from MSG_TAG 4'b%b)", exp_msg_tag[2:0], exp_msg_tag);
                    $display("  Queue ID: %0d", msg_tag);
                    metadata_pass = 1'b0;
                end

                // Verify TAG_OWNER
                if (actual_tag_owner == exp_tag_owner) begin
                    $display("[%0t] [READ_GEN] TAG_OWNER: MATCH ✓ (%0b)", $time, exp_tag_owner);
                end else begin
                    $display("[%0t] [READ_GEN] TAG_OWNER: MISMATCH ✗", $time);
                    $display("  Expected: %0b", exp_tag_owner);
                    $display("  Actual:   %0b", actual_tag_owner);
                    metadata_pass = 1'b0;
                end

                // Verify SOURCE_ID
                if (actual_src_id == exp_source_id) begin
                    $display("[%0t] [READ_GEN] SOURCE_ID: MATCH ✓ (0x%h)", $time, exp_source_id);
                end else begin
                    $display("[%0t] [READ_GEN] SOURCE_ID: MISMATCH ✗", $time);
                    $display("  Expected: 0x%h", exp_source_id);
                    $display("  Actual:   0x%h", actual_src_id);
                    metadata_pass = 1'b0;
                end

                $display("[%0t] [READ_GEN] ===========================", $time);

                if (metadata_pass) begin
                    $display("[%0t] [READ_GEN] Metadata verification: PASSED ✓", $time);
                end else begin
                    $display("[%0t] [READ_GEN] Metadata verification: FAILED ✗", $time);
                end
            end

            // Data verification summary
            if (match_count > 0 || mismatch_count > 0) begin
                $display("\n[%0t] [READ_GEN] === Data Verification ===", $time);
                $display("[%0t] [READ_GEN] Total Beats: %0d", $time, match_count + mismatch_count);
                $display("[%0t] [READ_GEN] Matches:     %0d", $time, match_count);
                $display("[%0t] [READ_GEN] Mismatches:  %0d", $time, mismatch_count);
                if (mismatch_count == 0) begin
                    $display("[%0t] [READ_GEN] Data verification: PASSED ✓", $time);
                end else begin
                    $display("[%0t] [READ_GEN] Data verification: FAILED ✗", $time);
                end
            end else begin
                $display("[%0t] [READ_GEN] No data verification performed (fixed data test)", $time);
            end
            $display("[%0t] [READ_GEN] === Read Complete ===\n", $time);
        end
    endtask

    task WAIT_INTR_ERR;
      begin
        // Wait for error interrupt
        wait(tb_pcie_sub_msg.o_msg_interrupt == 1);
        $display("[%0t] [READ_GEN] Error interrupt detected", $time);

        // Clear the error interrupt by writing to INTR_CLEAR[3]
        force tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_0[3] = 1'b1;
        #10;
        release tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_0;

        $display("[%0t] [READ_GEN] Error interrupt cleared", $time);
      end
    endtask

    task WAIT_INTR;
      input [3:0] queue_tag;  // Which queue completed
      begin
        // Wait for completion interrupt (INTR_STATUS[0])
        wait(tb_pcie_sub_msg.o_msg_interrupt == 1);
        $display("[%0t] [READ_GEN] Completion interrupt detected for Queue %0d", $time, queue_tag);

        // Read all 15 queue initial addresses
        Q_ADDR_0 = tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_0[31:0];
        Q_ADDR_1 = tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_1[31:0];
        Q_ADDR_2 = tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_2[31:0];
        Q_ADDR_3 = tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_3[31:0];
        Q_ADDR_4 = tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_4[31:0];
        Q_ADDR_5 = tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_5[31:0];
        Q_ADDR_6 = tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_6[31:0];
        Q_ADDR_7 = tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_7[31:0];
        Q_ADDR_8 = tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_8[31:0];
        Q_ADDR_9 = tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_9[31:0];
        Q_ADDR_10 = tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_10[31:0];
        Q_ADDR_11 = tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_11[31:0];
        Q_ADDR_12 = tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_12[31:0];
        Q_ADDR_13 = tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_13[31:0];
        Q_ADDR_14 = tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_14[31:0];

        // Display all queue addresses
        $display("[%0t] [READ_GEN] Queue Initial Addresses:", $time);
        $display("[%0t] [READ_GEN]   Q0: 0x%h  Q1: 0x%h  Q2: 0x%h  Q3: 0x%h  Q4: 0x%h",
                 $time, Q_ADDR_0, Q_ADDR_1, Q_ADDR_2, Q_ADDR_3, Q_ADDR_4);
        $display("[%0t] [READ_GEN]   Q5: 0x%h  Q6: 0x%h  Q7: 0x%h  Q8: 0x%h  Q9: 0x%h",
                 $time, Q_ADDR_5, Q_ADDR_6, Q_ADDR_7, Q_ADDR_8, Q_ADDR_9);
        $display("[%0t] [READ_GEN]   Q10: 0x%h  Q11: 0x%h  Q12: 0x%h  Q13: 0x%h  Q14: 0x%h",
                 $time, Q_ADDR_10, Q_ADDR_11, Q_ADDR_12, Q_ADDR_13, Q_ADDR_14);

        // Get the base address for this queue
        case (queue_tag)
          4'h0: begin $display("[%0t] [READ_GEN] Queue %0d init address: 0x%h", $time, queue_tag, Q_ADDR_0); end
          4'h1: begin $display("[%0t] [READ_GEN] Queue %0d init address: 0x%h", $time, queue_tag, Q_ADDR_1); end
          4'h2: begin $display("[%0t] [READ_GEN] Queue %0d init address: 0x%h", $time, queue_tag, Q_ADDR_2); end
          4'h3: begin $display("[%0t] [READ_GEN] Queue %0d init address: 0x%h", $time, queue_tag, Q_ADDR_3); end
          4'h4: begin $display("[%0t] [READ_GEN] Queue %0d init address: 0x%h", $time, queue_tag, Q_ADDR_4); end
          4'h5: begin $display("[%0t] [READ_GEN] Queue %0d init address: 0x%h", $time, queue_tag, Q_ADDR_5); end
          4'h6: begin $display("[%0t] [READ_GEN] Queue %0d init address: 0x%h", $time, queue_tag, Q_ADDR_6); end
          4'h7: begin $display("[%0t] [READ_GEN] Queue %0d init address: 0x%h", $time, queue_tag, Q_ADDR_7); end
          4'h8: begin $display("[%0t] [READ_GEN] Queue %0d init address: 0x%h", $time, queue_tag, Q_ADDR_8); end
          4'h9: begin $display("[%0t] [READ_GEN] Queue %0d init address: 0x%h", $time, queue_tag, Q_ADDR_9); end
          4'hA: begin $display("[%0t] [READ_GEN] Queue %0d init address: 0x%h", $time, queue_tag, Q_ADDR_10); end
          4'hB: begin $display("[%0t] [READ_GEN] Queue %0d init address: 0x%h", $time, queue_tag, Q_ADDR_11); end
          4'hC: begin $display("[%0t] [READ_GEN] Queue %0d init address: 0x%h", $time, queue_tag, Q_ADDR_12); end
          4'hD: begin $display("[%0t] [READ_GEN] Queue %0d init address: 0x%h", $time, queue_tag, Q_ADDR_13); end
          4'hE: begin $display("[%0t] [READ_GEN] Queue %0d init address: 0x%h", $time, queue_tag, Q_ADDR_14); end
        endcase

        // Clear the completion interrupt by writing to INTR_CLEAR[0]
        force tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_0[0] = 1'b1;
        #10;
        release tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_0;

        $display("[%0t] [READ_GEN] Completion interrupt cleared", $time);
      end
    endtask


endmodule
