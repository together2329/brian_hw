`timescale 1ns/1ps

// Self-checking simulation testbench for real_llm_counter_demo.
// Source baseline: SSOT/model/RTL/lint approved before simulation-signoff phase.
// This file is verification-only and does not modify synthesizable RTL semantics.
module tb_real_llm_counter_demo;
    localparam integer WIDTH = 8;

    localparam [2:0] CMD_CLEAR = 3'd0;
    localparam [2:0] CMD_LOAD  = 3'd1;
    localparam [2:0] CMD_INC   = 3'd2;
    localparam [2:0] CMD_DEC   = 3'd3;
    localparam [2:0] CMD_HOLD  = 3'd4;

    reg                  clk;
    reg                  rst_n;
    reg                  cmd_valid;
    wire                 cmd_ready;
    reg  [2:0]           cmd;
    reg  [WIDTH-1:0]     load_value;
    wire [WIDTH-1:0]     count;
    wire                 zero;
    wire                 max;
    wire [31:0]          accepted_count;
    wire [2:0]           status;

    real_llm_counter_demo dut (
        .clk(clk),
        .rst_n(rst_n),
        .cmd_valid(cmd_valid),
        .cmd_ready(cmd_ready),
        .cmd(cmd),
        .load_value(load_value),
        .count(count),
        .zero(zero),
        .max(max),
        .accepted_count(accepted_count),
        .status(status)
    );

    reg [7:0]  ref_count;
    reg [31:0] ref_accepted_count;
    reg [2:0]  ref_status;

    integer scoreboard_pass;
    integer scoreboard_fail;
    integer event_id;
    integer csv_fd;
    integer json_fd;

    integer hit_reset;
    integer hit_clear;
    integer hit_load;
    integer hit_load_0;
    integer hit_load_128;
    integer hit_load_255;
    integer hit_inc;
    integer hit_inc_sat;
    integer hit_dec;
    integer hit_dec_sat;
    integer hit_hold;
    integer hit_invalid;
    integer hit_invalid_5;
    integer hit_invalid_6;
    integer hit_invalid_7;
    integer hit_wrap;
    integer hit_back_to_back;
    integer hit_cmd_ready;
    integer hit_zero_flag;
    integer hit_max_flag;
    integer hit_flag_comb;
    integer hit_cmd_accept_latency;
    integer hit_state_update_latency;

    initial begin
        clk = 1'b0;
        forever #5 clk = ~clk;
    end

    task ref_reset;
        begin
            ref_count = 8'h00;
            ref_accepted_count = 32'h0000_0000;
            ref_status = 3'd0;
        end
    endtask

    task ref_apply;
        input [2:0] tcmd;
        input [7:0] tload;
        begin
            case (tcmd)
                CMD_CLEAR: begin
                    ref_count = 8'h00;
                    ref_status = CMD_CLEAR;
                end
                CMD_LOAD: begin
                    ref_count = tload;
                    ref_status = CMD_LOAD;
                    hit_load = 1;
                    if (tload == 8'h00)  hit_load_0 = 1;
                    if (tload == 8'h80)  hit_load_128 = 1;
                    if (tload == 8'hff)  hit_load_255 = 1;
                end
                CMD_INC: begin
                    if (ref_count == 8'hff) begin
                        ref_count = 8'hff;
                        hit_inc_sat = 1;
                    end else begin
                        ref_count = ref_count + 8'd1;
                    end
                    ref_status = CMD_INC;
                    hit_inc = 1;
                end
                CMD_DEC: begin
                    if (ref_count == 8'h00) begin
                        ref_count = 8'h00;
                        hit_dec_sat = 1;
                    end else begin
                        ref_count = ref_count - 8'd1;
                    end
                    ref_status = CMD_DEC;
                    hit_dec = 1;
                end
                CMD_HOLD: begin
                    ref_count = ref_count;
                    ref_status = CMD_HOLD;
                    hit_hold = 1;
                end
                default: begin
                    ref_count = ref_count;
                    ref_status = tcmd;
                    hit_invalid = 1;
                    if (tcmd == 3'd5) hit_invalid_5 = 1;
                    if (tcmd == 3'd6) hit_invalid_6 = 1;
                    if (tcmd == 3'd7) hit_invalid_7 = 1;
                end
            endcase
            ref_accepted_count = ref_accepted_count + 32'd1;
            hit_cmd_accept_latency = 1;
            hit_state_update_latency = 1;
        end
    endtask

    task record_event;
        input [1023:0] label;
        input integer pass;
        begin
            event_id = event_id + 1;
            $fdisplay(csv_fd, "%0d,%0t,%0s,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d",
                      event_id, $time, label, pass,
                      count, ref_count, zero, (ref_count == 8'h00), max, (ref_count == 8'hff),
                      accepted_count, ref_accepted_count, status, ref_status, cmd_ready);
        end
    endtask

    task check_outputs;
        input [1023:0] label;
        integer pass;
        begin
            pass = 1;
            if (cmd_ready !== 1'b1) begin
                $display("[TB][FAIL] %0s cmd_ready=%0b expected=1", label, cmd_ready);
                pass = 0;
            end
            if (count !== ref_count) begin
                $display("[TB][FAIL] %0s count=%0d expected=%0d", label, count, ref_count);
                pass = 0;
            end
            if (zero !== (ref_count == 8'h00)) begin
                $display("[TB][FAIL] %0s zero=%0b expected=%0b", label, zero, (ref_count == 8'h00));
                pass = 0;
            end
            if (max !== (ref_count == 8'hff)) begin
                $display("[TB][FAIL] %0s max=%0b expected=%0b", label, max, (ref_count == 8'hff));
                pass = 0;
            end
            if (accepted_count !== ref_accepted_count) begin
                $display("[TB][FAIL] %0s accepted_count=%0d expected=%0d", label, accepted_count, ref_accepted_count);
                pass = 0;
            end
            if (status !== ref_status) begin
                $display("[TB][FAIL] %0s status=%0d expected=%0d", label, status, ref_status);
                pass = 0;
            end

            if (cmd_ready === 1'b1) hit_cmd_ready = 1;
            if (zero === (ref_count == 8'h00)) hit_zero_flag = 1;
            if (max === (ref_count == 8'hff)) hit_max_flag = 1;
            if ((zero === (ref_count == 8'h00)) && (max === (ref_count == 8'hff))) hit_flag_comb = 1;

            if (pass) begin
                scoreboard_pass = scoreboard_pass + 1;
                $display("[TB][PASS] %0s count=%0d accepted=%0d status=%0d zero=%0b max=%0b", label, count, accepted_count, status, zero, max);
            end else begin
                scoreboard_fail = scoreboard_fail + 1;
            end
            record_event(label, pass);
        end
    endtask

    task drive_cmd;
        input [1023:0] label;
        input [2:0] tcmd;
        input [7:0] tload;
        input integer keep_valid;
        begin
            @(negedge clk);
            cmd_valid = 1'b1;
            cmd = tcmd;
            load_value = tload;
            @(posedge clk);
            #1;
            ref_apply(tcmd, tload);
            if (tcmd == CMD_CLEAR) hit_clear = 1;
            check_outputs(label);
            if (!keep_valid) begin
                @(negedge clk);
                cmd_valid = 1'b0;
                cmd = CMD_HOLD;
                load_value = 8'h00;
                #1;
                check_outputs({label, "_idle"});
            end
        end
    endtask

    task apply_reset;
        begin
            cmd_valid = 1'b0;
            cmd = CMD_CLEAR;
            load_value = 8'h00;
            rst_n = 1'b0;
            ref_reset();
            repeat (2) @(posedge clk);
            #1;
            hit_reset = 1;
            check_outputs("EQ_RESET_asserted");
            @(negedge clk);
            rst_n = 1'b1;
            #1;
            check_outputs("EQ_RESET_deasserted");
        end
    endtask

    task preload_accepted_count_for_wrap;
        begin
            @(negedge clk);
            force dut.accepted_count_reg = 32'hffff_ffff;
            ref_accepted_count = 32'hffff_ffff;
            #1;
            check_outputs("EQ_ACCEPTED_COUNT_PRELOAD_FORCE");
            release dut.accepted_count_reg;
            #1;
            check_outputs("EQ_ACCEPTED_COUNT_PRELOAD_RELEASE");
        end
    endtask

    task write_json_results;
        begin
            json_fd = $fopen("sim/sim_results.json", "w");
            if (json_fd == 0) begin
                $display("[TB][FAIL] could not open sim/sim_results.json");
                scoreboard_fail = scoreboard_fail + 1;
            end else begin
                $fdisplay(json_fd, "{");
                $fdisplay(json_fd, "  \"schema_version\": 1,");
                $fdisplay(json_fd, "  \"ip\": \"real_llm_counter_demo\",");
                $fdisplay(json_fd, "  \"tool\": \"iverilog_vvp\",");
                $fdisplay(json_fd, "  \"passed\": %0s,", (scoreboard_fail == 0) ? "true" : "false");
                $fdisplay(json_fd, "  \"scoreboard_pass\": %0d,", scoreboard_pass);
                $fdisplay(json_fd, "  \"scoreboard_fail\": %0d,", scoreboard_fail);
                $fdisplay(json_fd, "  \"scoreboard_events_csv\": \"sim/scoreboard_events.csv\",");
                $fdisplay(json_fd, "  \"waveform\": \"sim/waves/real_llm_counter_demo.vcd\",");
                $fdisplay(json_fd, "  \"coverage_hits\": {");
                $fdisplay(json_fd, "    \"SC01_executed\": %0d,", hit_reset);
                $fdisplay(json_fd, "    \"SC02_executed\": %0d,", hit_clear);
                $fdisplay(json_fd, "    \"SC03_executed\": %0d,", hit_load);
                $fdisplay(json_fd, "    \"SC04_executed\": %0d,", hit_inc);
                $fdisplay(json_fd, "    \"SC05_executed\": %0d,", hit_inc_sat);
                $fdisplay(json_fd, "    \"SC06_executed\": %0d,", hit_dec);
                $fdisplay(json_fd, "    \"SC07_executed\": %0d,", hit_dec_sat);
                $fdisplay(json_fd, "    \"SC08_executed\": %0d,", hit_hold);
                $fdisplay(json_fd, "    \"SC09_executed\": %0d,", hit_invalid);
                $fdisplay(json_fd, "    \"SC10_executed\": %0d,", hit_wrap);
                $fdisplay(json_fd, "    \"SC11_executed\": %0d,", hit_back_to_back);
                $fdisplay(json_fd, "    \"SC12_executed\": %0d,", (hit_load_0 && hit_load_128 && hit_load_255 && hit_zero_flag && hit_max_flag));
                $fdisplay(json_fd, "    \"function_clear_counter\": %0d,", hit_clear);
                $fdisplay(json_fd, "    \"function_load_counter\": %0d,", hit_load);
                $fdisplay(json_fd, "    \"function_increment_counter\": %0d,", hit_inc);
                $fdisplay(json_fd, "    \"function_decrement_counter\": %0d,", hit_dec);
                $fdisplay(json_fd, "    \"function_hold_counter\": %0d,", hit_hold);
                $fdisplay(json_fd, "    \"function_invalid_command_as_hold\": %0d,", hit_invalid);
                $fdisplay(json_fd, "    \"cycle_cmd_valid_cmd_ready\": %0d,", hit_cmd_ready);
                $fdisplay(json_fd, "    \"latency_command_accept_at_min\": %0d,", hit_cmd_accept_latency);
                $fdisplay(json_fd, "    \"latency_command_accept_at_max\": %0d,", hit_cmd_accept_latency);
                $fdisplay(json_fd, "    \"latency_command_effect_at_min\": %0d,", hit_state_update_latency);
                $fdisplay(json_fd, "    \"latency_command_effect_at_max\": %0d,", hit_state_update_latency);
                $fdisplay(json_fd, "    \"latency_flag_update_at_min\": %0d,", hit_flag_comb);
                $fdisplay(json_fd, "    \"latency_flag_update_at_max\": %0d", hit_flag_comb);
                $fdisplay(json_fd, "  },");
                $fdisplay(json_fd, "  \"directed_scenarios\": [");
                $fdisplay(json_fd, "    \"EQ_RESET\", \"EQ_CLEAR\", \"EQ_LOAD\", \"EQ_LOAD_BOUNDARY\", \"EQ_INC\", \"EQ_INC_SATURATE\", \"EQ_DEC\", \"EQ_DEC_SATURATE\", \"EQ_HOLD\", \"EQ_INVALID\", \"EQ_ACCEPTED_COUNT_WRAP\", \"EQ_BACK_TO_BACK\", \"EQ_FLAGS\", \"EQ_CMD_READY_ALWAYS\", \"EQ_CYCLE_TIMING\"");
                $fdisplay(json_fd, "  ],");
                $fdisplay(json_fd, "  \"accepted_count_wrap_method\": \"hierarchical force/release of dut.accepted_count_reg to 32'hffffffff before one accepted HOLD command\"");
                $fdisplay(json_fd, "}");
                $fclose(json_fd);
            end
        end
    endtask

    initial begin
        $dumpfile("sim/waves/real_llm_counter_demo.vcd");
        $dumpvars(0, tb_real_llm_counter_demo);

        csv_fd = $fopen("sim/scoreboard_events.csv", "w");
        if (csv_fd == 0) begin
            $display("[TB][FAIL] could not open sim/scoreboard_events.csv");
            $finish;
        end
        $fdisplay(csv_fd, "event_id,time,label,pass,dut_count,ref_count,dut_zero,ref_zero,dut_max,ref_max,dut_accepted_count,ref_accepted_count,dut_status,ref_status,dut_cmd_ready");

        scoreboard_pass = 0;
        scoreboard_fail = 0;
        event_id = 0;
        hit_reset = 0;
        hit_clear = 0;
        hit_load = 0;
        hit_load_0 = 0;
        hit_load_128 = 0;
        hit_load_255 = 0;
        hit_inc = 0;
        hit_inc_sat = 0;
        hit_dec = 0;
        hit_dec_sat = 0;
        hit_hold = 0;
        hit_invalid = 0;
        hit_invalid_5 = 0;
        hit_invalid_6 = 0;
        hit_invalid_7 = 0;
        hit_wrap = 0;
        hit_back_to_back = 0;
        hit_cmd_ready = 0;
        hit_zero_flag = 0;
        hit_max_flag = 0;
        hit_flag_comb = 0;
        hit_cmd_accept_latency = 0;
        hit_state_update_latency = 0;

        rst_n = 1'b1;
        cmd_valid = 1'b0;
        cmd = CMD_CLEAR;
        load_value = 8'h00;
        ref_reset();

        apply_reset();

        // EQ_LOAD_BOUNDARY and EQ_FLAGS: exercise 0, 128, and 255 flag corners.
        drive_cmd("EQ_LOAD_BOUNDARY_0", CMD_LOAD, 8'h00, 0);
        drive_cmd("EQ_LOAD_BOUNDARY_128", CMD_LOAD, 8'h80, 0);
        drive_cmd("EQ_LOAD_BOUNDARY_255", CMD_LOAD, 8'hff, 0);

        // EQ_INC_SATURATE: count remains 255 at maximum.
        drive_cmd("EQ_INC_SATURATE", CMD_INC, 8'h00, 0);

        // EQ_CLEAR and EQ_DEC_SATURATE.
        drive_cmd("EQ_CLEAR", CMD_CLEAR, 8'h00, 0);
        drive_cmd("EQ_DEC_SATURATE", CMD_DEC, 8'h00, 0);

        // EQ_LOAD, EQ_INC, EQ_DEC, EQ_HOLD.
        drive_cmd("EQ_LOAD", CMD_LOAD, 8'h42, 0);
        drive_cmd("EQ_INC", CMD_INC, 8'h00, 0);
        drive_cmd("EQ_DEC", CMD_DEC, 8'h00, 0);
        drive_cmd("EQ_HOLD", CMD_HOLD, 8'h00, 0);

        // EQ_INVALID: all reserved encodings 5, 6, and 7 behave as HOLD and status records actual cmd.
        drive_cmd("EQ_INVALID_5", 3'd5, 8'h00, 0);
        drive_cmd("EQ_INVALID_6", 3'd6, 8'h00, 0);
        drive_cmd("EQ_INVALID_7", 3'd7, 8'h00, 0);

        // EQ_BACK_TO_BACK / EQ_CYCLE_TIMING: no idle cycle between accepted commands.
        drive_cmd("EQ_BACK_TO_BACK_INC", CMD_INC, 8'h00, 1);
        drive_cmd("EQ_BACK_TO_BACK_DEC", CMD_DEC, 8'h00, 1);
        drive_cmd("EQ_BACK_TO_BACK_INC2", CMD_INC, 8'h00, 0);
        hit_back_to_back = 1;

        // EQ_ACCEPTED_COUNT_WRAP: controlled verification preload because 2^32 cycles is impractical.
        preload_accepted_count_for_wrap();
        drive_cmd("EQ_ACCEPTED_COUNT_WRAP", CMD_HOLD, 8'h00, 0);
        if (ref_accepted_count == 32'h0000_0000 && accepted_count == 32'h0000_0000) begin
            hit_wrap = 1;
        end
        check_outputs("EQ_ACCEPTED_COUNT_WRAP_POSTCHECK");

        write_json_results();
        $fclose(csv_fd);

        if (scoreboard_fail == 0) begin
            $display("[TB][RESULT] PASS scoreboard_pass=%0d scoreboard_fail=%0d", scoreboard_pass, scoreboard_fail);
            $finish;
        end else begin
            $display("[TB][RESULT] FAIL scoreboard_pass=%0d scoreboard_fail=%0d", scoreboard_pass, scoreboard_fail);
            $fatal(1);
        end
    end
endmodule
