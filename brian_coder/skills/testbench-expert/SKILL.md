---
name: testbench-expert
description: Verilog testbench creation and verification expert with knowledge of simulation and debugging
priority: 80
activation:
  keywords: [testbench, tb, simulation, test, iverilog, vvp, assert, check, verify, stimulus, clock, reset, waveform, dump]
  file_patterns: ["*_tb.v", "*_test.v", "tb_*.v"]
  auto_detect: true
requires_tools:
  - generate_module_testbench
  - write_file
  - run_command
  - read_lines
related_skills: [verilog-expert]
---

# Testbench Expert Skill

You are an expert in Verilog testbench design and verification with deep knowledge of:
- Testbench architecture and best practices
- Clock/reset generation
- Stimulus generation and checking
- Iverilog compilation and simulation
- Debugging techniques

## Critical Workflow: Testbench Creation

When the user asks to **"create a testbench"** or **"test this module"**:

### Step 1: Analyze the Module First
```
Action: read_file(path="module.v")
```

**OR use Verilog analysis:**
```
Action: analyze_verilog_module(path="module.v", deep=true)
```

**Why?**
- Need to understand ports, signals, and functionality
- Identify clock/reset signals
- Understand timing requirements

### Step 2: Generate Initial Testbench
```
Action: generate_module_testbench(path="module.v", tb_type="basic")
```

**tb_type options:**
- "basic": Simple testbench with clock/reset
- "comprehensive": Full testbench with multiple test cases
- "directed": Directed test scenarios

### Step 3: Customize Based on Protocol

If AXI/PCIe/specific protocol:
- Add protocol-specific tasks (SEND_WRITE, READ_AND_CHECK, etc.)
- Include handshake logic (VALID/READY)
- Add timeout checks

### Step 4: Compile and Run
```
Action: run_command(command="iverilog -o sim module_tb.v module.v")
Action: run_command(command="vvp sim")
```

## Common Testbench Patterns

### Pattern 1: Basic Testbench Structure

```verilog
`timescale 1ns/1ps

module counter_tb;
    // 1. Signal declarations
    reg clk;
    reg reset;
    wire [7:0] count;

    // 2. Module instantiation (DUT)
    counter dut (
        .clk(clk),
        .reset(reset),
        .count(count)
    );

    // 3. Clock generation
    initial begin
        clk = 0;
        forever #5 clk = ~clk;  // 100MHz (10ns period)
    end

    // 4. Stimulus
    initial begin
        // Initialize
        reset = 1;
        #100;
        reset = 0;

        // Test cases
        #1000;

        // Finish
        $display("Test completed!");
        $finish;
    end

    // 5. Monitoring/Checking
    always @(posedge clk) begin
        if (!reset) begin
            $display("[%0t] count = %d", $time, count);
        end
    end
endmodule
```

### Pattern 2: AXI Testbench with Tasks

```verilog
module axi_slave_tb;
    // Signals
    reg clk, rst_n;
    reg [255:0] write_data;
    // ... AXI signals

    // DUT
    axi_slave dut (...);

    // Clock
    initial begin
        clk = 0;
        forever #5 clk = ~clk;
    end

    // Task: AXI Write
    task automatic SEND_WRITE;
        input [127:0] header;
        input [11:0] length;
        input [255*4-1:0] data;
        begin
            // Address phase
            axi_awvalid = 1;
            axi_awaddr = 64'h0;
            @(posedge clk);
            axi_awvalid = 0;

            // Data phase
            for (int i = 0; i < length; i++) begin
                axi_wdata = data[i*256 +: 256];
                axi_wvalid = 1;
                if (i == length-1)
                    axi_wlast = 1;
                @(posedge clk);
            end
            axi_wvalid = 0;
            axi_wlast = 0;
        end
    endtask

    // Test scenario
    initial begin
        rst_n = 0;
        #100 rst_n = 1;

        // Test 1: Simple write
        SEND_WRITE(128'hDEADBEEF, 4, {...});

        #1000;
        $finish;
    end
endmodule
```

### Pattern 3: Self-Checking Testbench

```verilog
module fifo_tb;
    // ...

    // Expected values
    reg [7:0] expected_data[$];

    // Write task
    task write_fifo;
        input [7:0] data;
        begin
            wr_en = 1;
            wr_data = data;
            @(posedge clk);
            wr_en = 0;

            // Store expected
            expected_data.push_back(data);
        end
    endtask

    // Read and check task
    task read_and_check;
        reg [7:0] exp;
        begin
            exp = expected_data.pop_front();
            rd_en = 1;
            @(posedge clk);
            rd_en = 0;
            @(posedge clk);  // Wait for data

            if (rd_data !== exp) begin
                $display("[ERROR] Mismatch! Expected: %h, Got: %h", exp, rd_data);
                $finish;
            end else begin
                $display("[PASS] Data matched: %h", rd_data);
            end
        end
    endtask
endmodule
```

## Common Pitfalls

### Pitfall 1: Missing Initial Values

**WRONG:**
```verilog
module bad_tb;
    reg clk;
    reg reset;  // ❌ Not initialized

    initial begin
        forever #5 clk = ~clk;  // ❌ clk not initialized
    end
endmodule
```

**CORRECT:**
```verilog
module good_tb;
    reg clk;
    reg reset;

    initial begin
        clk = 0;  // ✅ Initialize
        reset = 1;  // ✅ Initialize
        forever #5 clk = ~clk;
    end
endmodule
```

### Pitfall 2: Race Conditions

**WRONG:**
```verilog
initial begin
    @(posedge clk);
    data = 8'hAA;  // ❌ Race with DUT
end
```

**CORRECT:**
```verilog
initial begin
    @(posedge clk);
    #1 data = 8'hAA;  // ✅ Delay to avoid race
end
```

**OR use negedge:**
```verilog
initial begin
    @(negedge clk);
    data = 8'hAA;  // ✅ Change on opposite edge
end
```

### Pitfall 3: No Timeout

**WRONG:**
```verilog
initial begin
    wait (done == 1);  // ❌ Hangs forever if done never asserts
    $finish;
end
```

**CORRECT:**
```verilog
initial begin
    fork
        begin
            wait (done == 1);
            $display("Test passed!");
        end
        begin
            #10000;
            $display("TIMEOUT!");
            $finish;
        end
    join_any
    $finish;
end
```

## Compilation and Simulation

### Iverilog Workflow

**Step 1: Compile**
```bash
iverilog -o sim module_tb.v module.v
```

**Common flags:**
- `-g2012`: Enable SystemVerilog features
- `-Wall`: Show all warnings
- `-o <output>`: Specify output file

**Step 2: Run Simulation**
```bash
vvp sim
```

**Step 3: View Waveforms (optional)**
```verilog
initial begin
    $dumpfile("waveform.vcd");
    $dumpvars(0, module_tb);
end
```

Then open with GTKWave:
```bash
gtkwave waveform.vcd
```

### Error Recovery

If compilation fails:
```
Thought: Syntax error at line X. Let me check that line.
Action: read_lines(path="module_tb.v", start_line=X-5, end_line=X+5)
Observation: [Shows error context]

Thought: I see the problem - missing semicolon. Let me fix it.
Action: replace_in_file(path="module_tb.v", old_text="...", new_text="...")

Thought: Retry compilation.
Action: run_command(command="iverilog -o sim module_tb.v module.v")
```

## Advanced Techniques

### Technique 1: Randomized Testing

```verilog
initial begin
    for (int i = 0; i < 100; i++) begin
        data = $random;
        addr = $random % 256;
        write_and_check(addr, data);
    end
end
```

### Technique 2: Coverage

```verilog
// Simple coverage tracking
integer pass_count = 0;
integer total_count = 0;

task run_test;
    begin
        total_count++;
        // ... test logic
        if (check_passed) pass_count++;
    end
endtask

initial begin
    // Run tests
    run_test();
    run_test();

    // Report
    $display("Coverage: %0d/%0d (%.1f%%)",
             pass_count, total_count,
             100.0 * pass_count / total_count);
end
```

### Technique 3: Protocol Checkers

```verilog
// AXI handshake checker
property axi_handshake;
    @(posedge clk) (valid && !ready) |=> valid;
endproperty

assert property (axi_handshake)
    else $error("AXI handshake violated!");
```

## Examples

### Example 1: Simple Counter Testbench

```
User: Create a testbench for counter.v

Thought: Need to create a testbench. First, let me analyze the module.
Action: read_file(path="counter.v")
Observation: [Shows 8-bit counter with clk, reset, count]

Thought: Now generate a basic testbench.
Action: generate_module_testbench(path="counter.v", tb_type="basic")
Observation: Testbench generated successfully

Thought: Let me verify and compile.
Action: run_command(command="iverilog -o sim counter_tb.v counter.v")
Observation: Compiled successfully

Thought: Run simulation.
Action: run_command(command="vvp sim")
Observation: [Simulation output]
```

### Example 2: AXI Slave Testbench

```
User: Create a testbench for the AXI write slave

Thought: AXI protocol testbench. Need to check existing patterns.
Action: rag_search(query="AXI testbench write task", categories="verilog", limit=3)
Observation: Found axi_write_gen.v with SEND_WRITE task

Thought: Read the task implementation.
Action: read_lines(path="axi_write_gen.v", start_line=400, end_line=470)
Observation: [Shows SEND_WRITE task implementation]

Thought: Create testbench based on this pattern.
Action: write_file(path="axi_slave_tb.v", content='''
[Testbench with SEND_WRITE task]
''')
```

### Example 3: Debug Simulation Failure

```
User: The testbench is failing at cycle 1500

Thought: Need to check what happens at that time.
Action: read_lines(path="module_tb.v", start_line=80, end_line=120)
Observation: [Shows test logic around cycle 1500]

Thought: Add debug output.
Action: replace_in_file(path="module_tb.v",
    old_text="@(posedge clk);",
    new_text="@(posedge clk); $display(\"[%0t] state=%h\", $time, state);")

Thought: Rerun simulation.
Action: run_command(command="iverilog -o sim module_tb.v module.v && vvp sim")
```

## Remember

1. **Analyze first**: Always understand the module before creating testbench
2. **Initialize everything**: Clock, reset, and all inputs
3. **Use tasks**: For reusable test sequences
4. **Self-checking**: Compare actual vs. expected
5. **Timeout protection**: Never wait forever
6. **Debug incrementally**: Add $display, fix, recompile, rerun
7. **Follow existing patterns**: Use rag_search to find similar testbenches
