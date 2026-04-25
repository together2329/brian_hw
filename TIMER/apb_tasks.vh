//----------------------------------------------------------------------------
// File: apb_tasks.vh
// Description: Reusable APB3 bus tasks for testbenches.
//
// Tasks:
//   apb_write(addr, data) - Write to APB slave
//   apb_read(addr, data)  - Read from APB slave
//
// APB3 Protocol:
//   SETUP phase:  PSEL=1, PENABLE=0, PADDR/PWDATA/PWRITE valid
//   ACCESS phase: PSEL=1, PENABLE=1, data sampled by slave
//   IDLE phase:   PSEL=0, PENABLE=0
//----------------------------------------------------------------------------

task apb_write;
    input [7:0]  addr;
    input [31:0] data;
    begin
        @(negedge PCLK);
        // SETUP phase
        PSEL    <= 1'b1;
        PENABLE <= 1'b0;
        PWRITE  <= 1'b1;
        PADDR   <= addr;
        PWDATA  <= data;
        @(negedge PCLK);
        // ACCESS phase
        PENABLE <= 1'b1;
        @(negedge PCLK);
        // Return to IDLE
        PSEL    <= 1'b0;
        PENABLE <= 1'b0;
        PWRITE  <= 1'b0;
    end
endtask

task apb_read;
    input  [7:0]  addr;
    output [31:0] data;
    begin
        @(negedge PCLK);
        // SETUP phase
        PSEL    <= 1'b1;
        PENABLE <= 1'b0;
        PWRITE  <= 1'b0;
        PADDR   <= addr;
        @(negedge PCLK);
        // ACCESS phase - sample PRDATA
        PENABLE <= 1'b1;
        data    <= PRDATA;
        @(negedge PCLK);
        // Return to IDLE
        PSEL    <= 1'b0;
        PENABLE <= 1'b0;
    end
endtask
