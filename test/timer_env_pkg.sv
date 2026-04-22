// ============================================================================
// Package: timer_env_pkg
// Description: Verification environment for the timer module.
//              Compatible with Icarus Verilog 12.0 (no dynamic arrays,
//              no mailbox, no virtual interface, no constraints).
//
// Contains:
//   1. timer_tx         — Transaction data class (control fields)
//   2. timer_scoreboard — Reference model + comparison engine
//
// Note: Driver, monitor, and generator logic live in tb_timer.sv as tasks
//       because iverilog 12.0 does not support virtual interface in classes.
// ============================================================================

package timer_env_pkg;

    // =======================================================================
    // Class 1: timer_tx — Transaction data container
    // =======================================================================
    class timer_tx;
        bit          timer_en;
        bit          mode;        // 0=one-shot, 1=periodic
        int unsigned prescaler;
        int unsigned compare_val;
        string       label;

        function new;
            timer_en    = 1'b0;
            mode        = 1'b0;
            prescaler   = 0;
            compare_val = 0;
            label       = "";
        endfunction

        function void display(string prefix);
            $display("%s TX: en=%0b mode=%0s ps=%0d cmp=%0d [%s]",
                     prefix, timer_en,
                     mode ? "PERIODIC" : "ONESHOT",
                     prescaler, compare_val, label);
        endfunction
    endclass

    // =======================================================================
    // Class 2: timer_scoreboard — Reference model + comparison
    //   Maintains a golden reference model of the timer behavior.
    //   set_inputs() — update reference with current control inputs
    //   ref_tick()   — advance reference model by one clock cycle
    //   compare()    — compare DUT outputs against reference expectations
    //   report()     — print pass/fail summary
    // =======================================================================
    class timer_scoreboard;
        // Counters
        int pass_count;
        int fail_count;
        int timeout_count;
        int check_count;

        // Reference model state
        bit [15:0]   ref_count;
        int          ref_ps_counter;
        int unsigned ref_prescaler;
        bit          ref_stopped;
        int unsigned ref_compare_val;
        bit          ref_mode;
        bit          ref_timer_en;

        function new;
            pass_count     = 0;
            fail_count     = 0;
            timeout_count  = 0;
            check_count    = 0;
            ref_count      = '0;
            ref_ps_counter = 0;
            ref_prescaler  = 0;
            ref_stopped    = 1'b0;
            ref_compare_val = 0;
            ref_mode       = 1'b0;
            ref_timer_en   = 1'b0;
        endfunction

        // Update reference inputs
        function void set_inputs(bit timer_en_, bit mode_,
                                 int unsigned ps, int unsigned cmp);
            ref_timer_en   = timer_en_;
            ref_mode       = mode_;
            ref_prescaler  = ps;
            ref_compare_val = cmp;
        endfunction

        // Tick the reference model one clock cycle
        function void ref_tick;
            bit ps_tick;

            ps_tick = 0;

            if (!ref_timer_en) begin
                ref_stopped    = 0;
                ref_ps_counter = 0;
            end else if (ref_stopped) begin
                // One-shot stopped: no action
            end else begin
                // Prescaler tick generation
                if (ref_ps_counter == ref_prescaler) begin
                    ps_tick        = 1;
                    ref_ps_counter = 0;
                end else begin
                    ref_ps_counter = ref_ps_counter + 1;
                end

                // Counter logic
                if (ps_tick) begin
                    if (ref_count == ref_compare_val) begin
                        if (ref_mode) begin
                            ref_count = 0;
                        end else begin
                            ref_stopped = 1;
                        end
                    end else begin
                        ref_count = ref_count + 1;
                    end
                end
            end
        endfunction

        // Compare DUT output with expected behavior
        function void compare(bit [15:0] dut_count, bit dut_timeout,
                              bit dut_running, int cycle, string label);
            bit ok;
            bit exp_running;

            ok = 1;
            check_count = check_count + 1;

            // Compute expected running inline
            exp_running = 0;
            if (ref_timer_en && !ref_stopped)
                exp_running = 1;

            // Check timeout
            if (dut_timeout) begin
                timeout_count = timeout_count + 1;
                // Periodic: count reloads to 0 on timeout (matches ref_count)
                // One-shot: count holds at compare_val (matches ref_count)
                if (dut_count == ref_count) begin
                    pass_count = pass_count + 1;
                    $display("  [SB] PASS: timeout #%0d at cyc %0d count=%0d [%s]",
                             timeout_count, cycle, dut_count, label);
                end else begin
                    fail_count = fail_count + 1;
                    ok = 0;
                    $display("  [SB] FAIL: timeout at cyc %0d count=%0d exp=%0d [%s]",
                             cycle, dut_count, ref_count, label);
                end
            end

            // Check count matches reference (when timer active)
            if (ref_timer_en && !ref_stopped) begin
                if (dut_count != ref_count) begin
                    fail_count = fail_count + 1;
                    ok = 0;
                    $display("  [SB] FAIL: count mismatch cyc %0d got=%0d exp=%0d [%s]",
                             cycle, dut_count, ref_count, label);
                end
            end

            // Check running flag
            if (dut_running != exp_running) begin
                fail_count = fail_count + 1;
                ok = 0;
                $display("  [SB] FAIL: running mismatch cyc %0d got=%0b exp=%0b [%s]",
                         cycle, dut_running, exp_running, label);
            end

            if (ok && !dut_timeout) begin
                pass_count = pass_count + 1;
            end
        endfunction

        // Print final report
        function void report;
            $display("[SB] ====== Scoreboard Report ======");
            $display("[SB] Checks performed  : %0d", check_count);
            $display("[SB] Timeouts detected : %0d", timeout_count);
            $display("[SB] PASS              : %0d", pass_count);
            $display("[SB] FAIL              : %0d", fail_count);
            $display("[SB] ================================");
        endfunction
    endclass

endpackage
