//============================================================================
// Module : arm_m0_soc
// Description : SoC top-level integration module
//               Wires CPU ↔ system_bus ↔ ROM + SRAM + peripheral registers
//               External ports: clk, rst_n, irq
//
// Memory Map:
//   0x00000000–0x0000FFFF : ROM  (64KB instruction memory)
//   0x20000000–0x2000FFFF : SRAM (64KB data memory)
//   0x40000000–0x40000FFF : Peripheral registers (4KB)
//============================================================================

module arm_m0_soc (
    input  logic         clk,
    input  logic         rst_n,
    input  logic         irq
);

    // ===============================================================
    // Internal wires — CPU to bus (Master 0: instruction fetch)
    // ===============================================================
    logic [31:0] instr_addr;
    logic        instr_req;
    logic [15:0] instr_rdata;
    logic        instr_ack;

    // ===============================================================
    // Internal wires — CPU to bus (Master 1: data access)
    // ===============================================================
    logic [31:0] mem_addr;
    logic [31:0] mem_wdata;
    logic [31:0] mem_rdata;
    logic        mem_we;
    logic        mem_req;
    logic [1:0]  mem_size;
    logic        mem_ack;

    // ===============================================================
    // Internal wires — Bus to Slave 0 (ROM)
    // ===============================================================
    logic [31:0] s0_addr;
    logic [31:0] s0_wdata;
    logic [31:0] s0_rdata;
    logic        s0_we;
    logic        s0_cs;
    logic        s0_ack;
    logic [1:0]  s0_size;

    // ===============================================================
    // Internal wires — Bus to Slave 1 (SRAM)
    // ===============================================================
    logic [31:0] s1_addr;
    logic [31:0] s1_wdata;
    logic [31:0] s1_rdata;
    logic        s1_we;
    logic        s1_cs;
    logic        s1_ack;
    logic [1:0]  s1_size;

    // ===============================================================
    // Internal wires — Bus to Slave 2 (Peripheral)
    // ===============================================================
    logic [31:0] s2_addr;
    logic [31:0] s2_wdata;
    logic [31:0] s2_rdata;
    logic        s2_we;
    logic        s2_cs;
    logic        s2_ack;
    logic [1:0]  s2_size;

    // ===============================================================
    // Internal wires — Bus master response
    // ===============================================================
    logic [31:0] bus_m0_rdata;
    logic        bus_m0_ack;
    logic [31:0] bus_m1_rdata;
    logic        bus_m1_ack;

    // ===============================================================
    // ROM slave wires (16-bit data)
    // ===============================================================
    logic [15:0] rom_rdata;
    logic        rom_ack;

    // ===============================================================
    // CPU instantiation (unchanged)
    // ===============================================================
    arm_m0_cpu u_cpu (
        .clk         (clk),
        .rst_n       (rst_n),
        .instr_addr  (instr_addr),
        .instr_req   (instr_req),
        .instr_rdata (instr_rdata),
        .instr_ack   (instr_ack),
        .mem_addr    (mem_addr),
        .mem_wdata   (mem_wdata),
        .mem_rdata   (mem_rdata),
        .mem_we      (mem_we),
        .mem_req     (mem_req),
        .mem_size    (mem_size),
        .mem_ack     (mem_ack),
        .irq         (irq)
    );

    // ===============================================================
    // System bus instantiation
    // ===============================================================
    system_bus u_bus (
        .clk      (clk),
        .rst_n    (rst_n),

        // Master 0: Instruction fetch
        .m0_addr  (instr_addr),
        .m0_wdata (32'd0),          // Instr fetch never writes
        .m0_rdata (bus_m0_rdata),
        .m0_we    (1'b0),           // Instr fetch never writes
        .m0_req   (instr_req),
        .m0_ack   (bus_m0_ack),
        .m0_size  (2'b01),          // Halfword fetch for Thumb

        // Master 1: Data access
        .m1_addr  (mem_addr),
        .m1_wdata (mem_wdata),
        .m1_rdata (bus_m1_rdata),
        .m1_we    (mem_we),
        .m1_req   (mem_req),
        .m1_ack   (bus_m1_ack),
        .m1_size  (mem_size),

        // Slave 0: ROM
        .s0_addr  (s0_addr),
        .s0_wdata (s0_wdata),
        .s0_rdata (s0_rdata),
        .s0_we    (s0_we),
        .s0_cs    (s0_cs),
        .s0_ack   (s0_ack),
        .s0_size  (s0_size),

        // Slave 1: SRAM
        .s1_addr  (s1_addr),
        .s1_wdata (s1_wdata),
        .s1_rdata (s1_rdata),
        .s1_we    (s1_we),
        .s1_cs    (s1_cs),
        .s1_ack   (s1_ack),
        .s1_size  (s1_size),

        // Slave 2: Peripheral
        .s2_addr  (s2_addr),
        .s2_wdata (s2_wdata),
        .s2_rdata (s2_rdata),
        .s2_we    (s2_we),
        .s2_cs    (s2_cs),
        .s2_ack   (s2_ack),
        .s2_size  (s2_size)
    );

    // ===============================================================
    // ROM slave instantiation (16-bit instruction memory)
    // ===============================================================
    rom_slave #(
        .ADDR_WIDTH (15),
        .DATA_WIDTH (16)
    ) u_rom (
        .clk   (clk),
        .rst_n (rst_n),
        .addr  (s0_addr),
        .wdata (s0_wdata[15:0]),  // Unused by ROM
        .rdata (rom_rdata),
        .we    (s0_we),           // Ignored by ROM
        .cs    (s0_cs),
        .ack   (rom_ack),
        .size  (s0_size)
    );

    // Width adapter: ROM 16-bit → bus 32-bit
    assign s0_rdata = {16'd0, rom_rdata};
    assign s0_ack   = rom_ack;

    // ===============================================================
    // SRAM slave instantiation (32-bit data memory)
    // ===============================================================
    sram_slave #(
        .ADDR_WIDTH (14),
        .DATA_WIDTH (32)
    ) u_sram (
        .clk   (clk),
        .rst_n (rst_n),
        .addr  (s1_addr),
        .wdata (s1_wdata),
        .rdata (s1_rdata),
        .we    (s1_we),
        .cs    (s1_cs),
        .ack   (s1_ack),
        .size  (s1_size)
    );

    // ===============================================================
    // Peripheral register slave instantiation
    // ===============================================================
    periph_slave u_periph (
        .clk   (clk),
        .rst_n (rst_n),
        .addr  (s2_addr),
        .wdata (s2_wdata),
        .rdata (s2_rdata),
        .we    (s2_we),
        .cs    (s2_cs),
        .ack   (s2_ack),
        .size  (s2_size)
    );

    // ===============================================================
    // CPU response wiring — bus master data → CPU inputs
    // ===============================================================
    // Instruction fetch: extract lower 16 bits for Thumb CPU
    assign instr_rdata = bus_m0_rdata[15:0];
    assign instr_ack   = bus_m0_ack;

    // Data access: full 32-bit path
    assign mem_rdata = bus_m1_rdata;
    assign mem_ack   = bus_m1_ack;

endmodule
