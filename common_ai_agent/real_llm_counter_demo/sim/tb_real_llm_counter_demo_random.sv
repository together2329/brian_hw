`timescale 1ns/1ps

// Constrained-random self-checking simulation testbench for real_llm_counter_demo.
// Verification-only: this file does not modify synthesizable RTL semantics.
// Usage via sim/run_random_regression.sh, with plusargs:
//   +SEED=<int> +TXNS=<int> +MAX_GAP=<int> +RESET_PROB_PER_MILLE=<int> [+DUMP_RANDOM_VCD]
module tb_real_llm_counter_demo_random;
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

    integer seed;
    integer rng_state;
    integer txns;
    integer max_gap;
    integer reset_prob_per_mille;
    integer dump_enabled;
    integer dummy_rand;

    integer scoreboard_pass;
    integer scoreboard_fail;
    integer event_id;
    integer accepted_txns;
    integer idle_checks;
    integer reset_count;
    integer back_to_back_count;
    integer consecutive_valid_depth;
    integer csv_fd;
    integer json_fd;

    integer cmd_count_0;
    integer cmd_count_1;
    integer cmd_count_2;
    integer cmd_count_3;
    integer cmd_count_4;
    integer cmd_count_5;
    integer cmd_count_6;
    integer cmd_count_7;
    integer invalid_count;
    integer load_boundary_0;
    integer load_boundary_128;
    integer load_boundary_255;
    integer saw_zero_flag;
    integer saw_max_flag;
    integer saw_inc_saturation;
    integer saw_dec_saturation;

    integer txn_idx;
    integer gap;
    integer gap_i;
    integer pick;
    integer load_pick;
    integer reset_roll;
    reg [2:0] rand_cmd;
    reg [7:0] rand_load;

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
                end
                CMD_INC: begin
                    if (ref_count == 8'hff) begin
                        ref_count = 8'hff;
                        saw_inc_saturation = 1;
                    end else begin
                        ref_count = ref_count + 8'd1;
                    end
                    ref_status = CMD_INC;
                end
                CMD_DEC: begin
                    if (ref_count == 8'h00) begin
                        ref_count = 8'h00;
                        saw_dec_saturation = 1;
                    end else begin
                        ref_count = ref_count - 8'd1;
                    end
                    ref_status = CMD_DEC;
                end
                CMD_HOLD: begin
                    ref_count = ref_count;
                    ref_status = CMD_HOLD;
                end
                default: begin
                    ref_count = ref_count;
                    ref_status = tcmd;
                end
            endcase
            ref_accepted_count = ref_accepted_count + 32'd1;
        end
    endtask

    task note_command;
        input [2:0] tcmd;
        input [7:0] tload;
        begin
            case (tcmd)
                3'd0: cmd_count_0 = cmd_count_0 + 1;
                3'd1: begin
                    cmd_count_1 = cmd_count_1 + 1;
                    if (tload == 8'h00) load_boundary_0 = 1;
                    if (tload == 8'h80) load_boundary_128 = 1;
                    if (tload == 8'hff) load_boundary_255 = 1;
                end
                3'd2: cmd_count_2 = cmd_count_2 + 1;
                3'd3: cmd_count_3 = cmd_count_3 + 1;
                3'd4: cmd_count_4 = cmd_count_4 + 1;
                3'd5: begin cmd_count_5 = cmd_count_5 + 1; invalid_count = invalid_count + 1; end
                3'd6: begin cmd_count_6 = cmd_count_6 + 1; invalid_count = invalid_count + 1; end
                3'd7: begin cmd_count_7 = cmd_count_7 + 1; invalid_count = invalid_count + 1; end
            endcase
        end
    endtask

    task record_event;
        input [1023:0] phase;
        input integer pass;
        begin
            event_id = event_id + 1;
            $fdisplay(csv_fd, "%0d,%0t,%0s,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d",
                      event_id, $time, phase, pass,
                      cmd_valid, cmd, load_value,
                      count, ref_count, zero, (ref_count == 8'h00), max, (ref_count == 8'hff),
                      accepted_count, ref_accepted_count, status, ref_status);
        end
    endtask

    task check_outputs;
        input [1023:0] phase;
        integer pass;
        begin
            pass = 1;
            if (cmd_ready !== 1'b1) begin
                $display("[RANDOM_TB][FAIL] %0s cmd_ready=%0b expected=1", phase, cmd_ready);
                pass = 0;
            end
            if (count !== ref_count) begin
                $display("[RANDOM_TB][FAIL] %0s count=%0d expected=%0d", phase, count, ref_count);
                pass = 0;
            end
            if (zero !== (ref_count == 8'h00)) begin
                $display("[RANDOM_TB][FAIL] %0s zero=%0b expected=%0b", phase, zero, (ref_count == 8'h00));
                pass = 0;
            end
            if (max !== (ref_count == 8'hff)) begin
                $display("[RANDOM_TB][FAIL] %0s max=%0b expected=%0b", phase, max, (ref_count == 8'hff));
                pass = 0;
            end
            if (accepted_count !== ref_accepted_count) begin
                $display("[RANDOM_TB][FAIL] %0s accepted_count=%0d expected=%0d", phase, accepted_count, ref_accepted_count);
                pass = 0;
            end
            if (status !== ref_status) begin
                $display("[RANDOM_TB][FAIL] %0s status=%0d expected=%0d", phase, status, ref_status);
                pass = 0;
            end

            if (zero === 1'b1) saw_zero_flag = 1;
            if (max === 1'b1) saw_max_flag = 1;

            if (pass) begin
                scoreboard_pass = scoreboard_pass + 1;
            end else begin
                scoreboard_fail = scoreboard_fail + 1;
            end
            record_event(phase, pass);
        end
    endtask

    task apply_reset;
        input [1023:0] phase;
        begin
            @(negedge clk);
            rst_n = 1'b0;
            cmd_valid = 1'b0;
            cmd = CMD_CLEAR;
            load_value = 8'h00;
            ref_reset();
            consecutive_valid_depth = 0;
            reset_count = reset_count + 1;
            @(posedge clk);
            #1;
            check_outputs({phase, "_asserted"});
            @(negedge clk);
            rst_n = 1'b1;
            @(posedge clk);
            #1;
            check_outputs({phase, "_released"});
        end
    endtask

    task drive_idle_cycle;
        begin
            @(negedge clk);
            cmd_valid = 1'b0;
            cmd = CMD_HOLD;
            load_value = 8'h00;
            consecutive_valid_depth = 0;
            @(posedge clk);
            #1;
            idle_checks = idle_checks + 1;
            check_outputs("RAND_IDLE");
        end
    endtask

    task drive_transaction;
        input [2:0] tcmd;
        input [7:0] tload;
        begin
            @(negedge clk);
            cmd_valid = 1'b1;
            cmd = tcmd;
            load_value = tload;
            if (consecutive_valid_depth > 0) begin
                back_to_back_count = back_to_back_count + 1;
            end
            @(posedge clk);
            #1;
            ref_apply(tcmd, tload);
            note_command(tcmd, tload);
            accepted_txns = accepted_txns + 1;
            consecutive_valid_depth = consecutive_valid_depth + 1;
            check_outputs("RAND_TXN");
        end
    endtask

    task choose_random_transaction;
        begin
            pick = $urandom_range(99, 0);
            if (pick < 10) begin
                rand_cmd = CMD_CLEAR;
            end else if (pick < 30) begin
                rand_cmd = CMD_LOAD;
            end else if (pick < 48) begin
                rand_cmd = CMD_INC;
            end else if (pick < 66) begin
                rand_cmd = CMD_DEC;
            end else if (pick < 82) begin
                rand_cmd = CMD_HOLD;
            end else begin
                rand_cmd = 3'd5 + $urandom_range(2, 0);
            end

            load_pick = $urandom_range(99, 0);
            if (load_pick < 20) begin
                rand_load = 8'h00;
            end else if (load_pick < 40) begin
                rand_load = 8'hff;
            end else if (load_pick < 50) begin
                rand_load = 8'h80;
            end else begin
                rand_load = $urandom_range(255, 0);
            end
        end
    endtask

    task write_json_results;
        begin
            json_fd = $fopen("sim/random/current_random_results.json", "w");
            if (json_fd == 0) begin
                $display("[RANDOM_TB][FAIL] could not open sim/random/current_random_results.json");
                scoreboard_fail = scoreboard_fail + 1;
            end else begin
                $fdisplay(json_fd, "{");
                $fdisplay(json_fd, "  \"schema_version\": 1,");
                $fdisplay(json_fd, "  \"ip\": \"real_llm_counter_demo\",");
                $fdisplay(json_fd, "  \"type\": \"constrained_random_sim_results\",");
                $fdisplay(json_fd, "  \"tool\": \"iverilog_vvp\",");
                $fdisplay(json_fd, "  \"seed\": %0d,", seed);
                $fdisplay(json_fd, "  \"requested_txns\": %0d,", txns);
                $fdisplay(json_fd, "  \"max_gap\": %0d,", max_gap);
                $fdisplay(json_fd, "  \"reset_prob_per_mille\": %0d,", reset_prob_per_mille);
                $fdisplay(json_fd, "  \"passed\": %0s,", (scoreboard_fail == 0) ? "true" : "false");
                $fdisplay(json_fd, "  \"scoreboard_pass\": %0d,", scoreboard_pass);
                $fdisplay(json_fd, "  \"scoreboard_fail\": %0d,", scoreboard_fail);
                $fdisplay(json_fd, "  \"accepted_txns\": %0d,", accepted_txns);
                $fdisplay(json_fd, "  \"idle_checks\": %0d,", idle_checks);
                $fdisplay(json_fd, "  \"reset_count\": %0d,", reset_count);
                $fdisplay(json_fd, "  \"back_to_back_count\": %0d,", back_to_back_count);
                $fdisplay(json_fd, "  \"scoreboard_events_csv\": \"sim/random/current_scoreboard_events.csv\",");
                $fdisplay(json_fd, "  \"command_counts\": {");
                $fdisplay(json_fd, "    \"cmd_0_clear\": %0d,", cmd_count_0);
                $fdisplay(json_fd, "    \"cmd_1_load\": %0d,", cmd_count_1);
                $fdisplay(json_fd, "    \"cmd_2_inc\": %0d,", cmd_count_2);
                $fdisplay(json_fd, "    \"cmd_3_dec\": %0d,", cmd_count_3);
                $fdisplay(json_fd, "    \"cmd_4_hold\": %0d,", cmd_count_4);
                $fdisplay(json_fd, "    \"cmd_5_invalid\": %0d,", cmd_count_5);
                $fdisplay(json_fd, "    \"cmd_6_invalid\": %0d,", cmd_count_6);
                $fdisplay(json_fd, "    \"cmd_7_invalid\": %0d", cmd_count_7);
                $fdisplay(json_fd, "  },");
                $fdisplay(json_fd, "  \"coverage_hints\": {");
                $fdisplay(json_fd, "    \"all_cmd_encodings_seen\": %0s,", ((cmd_count_0 > 0) && (cmd_count_1 > 0) && (cmd_count_2 > 0) && (cmd_count_3 > 0) && (cmd_count_4 > 0) && (cmd_count_5 > 0) && (cmd_count_6 > 0) && (cmd_count_7 > 0)) ? "true" : "false");
                $fdisplay(json_fd, "    \"invalid_commands_seen\": %0s,", (invalid_count > 0) ? "true" : "false");
                $fdisplay(json_fd, "    \"load_boundary_0_seen\": %0s,", (load_boundary_0 > 0) ? "true" : "false");
                $fdisplay(json_fd, "    \"load_boundary_128_seen\": %0s,", (load_boundary_128 > 0) ? "true" : "false");
                $fdisplay(json_fd, "    \"load_boundary_255_seen\": %0s,", (load_boundary_255 > 0) ? "true" : "false");
                $fdisplay(json_fd, "    \"zero_flag_seen\": %0s,", (saw_zero_flag > 0) ? "true" : "false");
                $fdisplay(json_fd, "    \"max_flag_seen\": %0s,", (saw_max_flag > 0) ? "true" : "false");
                $fdisplay(json_fd, "    \"inc_saturation_seen\": %0s,", (saw_inc_saturation > 0) ? "true" : "false");
                $fdisplay(json_fd, "    \"dec_saturation_seen\": %0s", (saw_dec_saturation > 0) ? "true" : "false");
                $fdisplay(json_fd, "  }");
                $fdisplay(json_fd, "}");
                $fclose(json_fd);
            end
        end
    endtask

    initial begin
        if (!$value$plusargs("SEED=%d", seed)) begin
            seed = 32'h1bad_c0de;
        end
        if (!$value$plusargs("TXNS=%d", txns)) begin
            txns = 512;
        end
        if (!$value$plusargs("MAX_GAP=%d", max_gap)) begin
            max_gap = 3;
        end
        if (!$value$plusargs("RESET_PROB_PER_MILLE=%d", reset_prob_per_mille)) begin
            reset_prob_per_mille = 10;
        end
        if (txns < 1) txns = 1;
        if (max_gap < 0) max_gap = 0;
        if (reset_prob_per_mille < 0) reset_prob_per_mille = 0;
        if (reset_prob_per_mille > 1000) reset_prob_per_mille = 1000;
        dump_enabled = $test$plusargs("DUMP_RANDOM_VCD");
        rng_state = seed;
        dummy_rand = $urandom(rng_state);

        if (dump_enabled) begin
            $dumpfile("sim/random/current_random.vcd");
            $dumpvars(0, tb_real_llm_counter_demo_random);
        end

        csv_fd = $fopen("sim/random/current_scoreboard_events.csv", "w");
        if (csv_fd == 0) begin
            $display("[RANDOM_TB][FAIL] could not open sim/random/current_scoreboard_events.csv");
            $fatal(1);
        end
        $fdisplay(csv_fd, "event_id,time,phase,pass,cmd_valid,cmd,load_value,dut_count,ref_count,dut_zero,ref_zero,dut_max,ref_max,dut_accepted_count,ref_accepted_count,dut_status,ref_status");

        scoreboard_pass = 0;
        scoreboard_fail = 0;
        event_id = 0;
        accepted_txns = 0;
        idle_checks = 0;
        reset_count = 0;
        back_to_back_count = 0;
        consecutive_valid_depth = 0;
        cmd_count_0 = 0;
        cmd_count_1 = 0;
        cmd_count_2 = 0;
        cmd_count_3 = 0;
        cmd_count_4 = 0;
        cmd_count_5 = 0;
        cmd_count_6 = 0;
        cmd_count_7 = 0;
        invalid_count = 0;
        load_boundary_0 = 0;
        load_boundary_128 = 0;
        load_boundary_255 = 0;
        saw_zero_flag = 0;
        saw_max_flag = 0;
        saw_inc_saturation = 0;
        saw_dec_saturation = 0;

        rst_n = 1'b1;
        cmd_valid = 1'b0;
        cmd = CMD_CLEAR;
        load_value = 8'h00;
        ref_reset();

        $display("[RANDOM_TB][INFO] seed=%0d txns=%0d max_gap=%0d reset_prob_per_mille=%0d", seed, txns, max_gap, reset_prob_per_mille);
        apply_reset("RAND_INITIAL_RESET");

        for (txn_idx = 0; txn_idx < txns; txn_idx = txn_idx + 1) begin
            reset_roll = $urandom_range(999, 0);
            if (reset_roll < reset_prob_per_mille) begin
                apply_reset("RAND_MID_RESET");
            end

            gap = (max_gap == 0) ? 0 : $urandom_range(max_gap, 0);
            for (gap_i = 0; gap_i < gap; gap_i = gap_i + 1) begin
                drive_idle_cycle();
            end

            choose_random_transaction();
            drive_transaction(rand_cmd, rand_load);
        end

        drive_idle_cycle();
        write_json_results();
        $fclose(csv_fd);

        if (scoreboard_fail == 0) begin
            $display("[RANDOM_TB][RESULT] PASS seed=%0d txns=%0d scoreboard_pass=%0d scoreboard_fail=%0d accepted_txns=%0d resets=%0d back_to_back=%0d",
                     seed, txns, scoreboard_pass, scoreboard_fail, accepted_txns, reset_count, back_to_back_count);
            $finish;
        end else begin
            $display("[RANDOM_TB][RESULT] FAIL seed=%0d txns=%0d scoreboard_pass=%0d scoreboard_fail=%0d accepted_txns=%0d resets=%0d back_to_back=%0d",
                     seed, txns, scoreboard_pass, scoreboard_fail, accepted_txns, reset_count, back_to_back_count);
            $fatal(1);
        end
    end
endmodule
