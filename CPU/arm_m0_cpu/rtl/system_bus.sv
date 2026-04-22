//============================================================================
// Module : system_bus
// Description : Shared system bus with address decode and arbitration
//               2 masters (instr fetch, data access), 3 slaves (ROM, SRAM, periph)
//               Data access has priority over instr fetch when same slave
//               Non-conflicting masters can access different slaves simultaneously
//============================================================================

module system_bus (
    input  logic         clk,
    input  logic         rst_n,

    // Master 0: Instruction fetch (from CPU instr_* interface)
    input  logic [31:0]  m0_addr,
    input  logic [31:0]  m0_wdata,   // unused for instr fetch
    output logic [31:0]  m0_rdata,    // lower 16 bits used for instr
    input  logic         m0_we,       // always 0 for instr fetch
    input  logic         m0_req,
    output logic         m0_ack,
    input  logic [1:0]   m0_size,

    // Master 1: Data access (from CPU mem_* interface)
    input  logic [31:0]  m1_addr,
    input  logic [31:0]  m1_wdata,
    output logic [31:0]  m1_rdata,
    input  logic         m1_we,
    input  logic         m1_req,
    output logic         m1_ack,
    input  logic [1:0]   m1_size,

    // Slave 0: ROM (instruction memory at 0x00000000–0x0000FFFF)
    output logic [31:0]  s0_addr,
    output logic [31:0]  s0_wdata,
    input  logic [31:0]  s0_rdata,
    output logic         s0_we,
    output logic         s0_cs,
    input  logic         s0_ack,
    output logic [1:0]   s0_size,

    // Slave 1: SRAM (data memory at 0x20000000–0x2000FFFF)
    output logic [31:0]  s1_addr,
    output logic [31:0]  s1_wdata,
    input  logic [31:0]  s1_rdata,
    output logic         s1_we,
    output logic         s1_cs,
    input  logic         s1_ack,
    output logic [1:0]   s1_size,

    // Slave 2: Peripheral registers (at 0x40000000–0x40000FFF)
    output logic [31:0]  s2_addr,
    output logic [31:0]  s2_wdata,
    input  logic [31:0]  s2_rdata,
    output logic         s2_we,
    output logic         s2_cs,
    input  logic         s2_ack,
    output logic [1:0]   s2_size
);

    // ===============================================================
    // Address decode — determine which slave each master targets
    // ===============================================================
    logic [1:0] m0_slave;  // 0=ROM, 1=SRAM, 2=PERIPH, 3=none
    logic [1:0] m1_slave;

    always @(*) begin
        // Master 0 (instr fetch) address decode
        casez (m0_addr[31:16])
            16'h0000: m0_slave = 2'd0;  // ROM region
            16'h2000: m0_slave = 2'd1;  // SRAM region (instr fetch from SRAM possible)
            16'h4000: m0_slave = 2'd2;  // Peripheral region
            default:  m0_slave = 2'd3;  // No slave (default)
        endcase

        // Master 1 (data access) address decode
        casez (m1_addr[31:16])
            16'h0000: m1_slave = 2'd0;  // ROM region
            16'h2000: m1_slave = 2'd1;  // SRAM region
            16'h4000: m1_slave = 2'd2;  // Peripheral region
            default:  m1_slave = 2'd3;  // No slave (default)
        endcase
    end

    // ===============================================================
    // Conflict detection — both masters target same slave
    // ===============================================================
    logic m0_m1_conflict;
    assign m0_m1_conflict = (m0_req && m1_req && (m0_slave == m1_slave) && (m0_slave != 2'd3));

    // ===============================================================
    // Arbitration: data (M1) has priority over instr fetch (M0)
    // When conflict: M1 wins, M0 is stalled (ack held low)
    // When no conflict: both can proceed simultaneously
    // ===============================================================
    logic m0_granted;
    logic m1_granted;

    always @(*) begin
        m0_granted = 1'b0;
        m1_granted = 1'b0;

        if (m0_m1_conflict) begin
            // Conflict: data access wins
            m1_granted = m1_req;
            m0_granted = 1'b0;  // M0 stalled
        end else begin
            // No conflict: both can go
            m0_granted = m0_req;
            m1_granted = m1_req;
        end
    end

    // ===============================================================
    // Slave select generation — route granted master to correct slave
    // ===============================================================
    logic [1:0] s0_winner;  // which master won access to slave 0
    logic [1:0] s1_winner;
    logic [1:0] s2_winner;

    always @(*) begin
        // Default: no slave selected
        s0_cs    = 1'b0;
        s0_addr  = 32'd0;
        s0_wdata = 32'd0;
        s0_we    = 1'b0;
        s0_size  = 2'b10;
        s0_winner = 2'd0;

        s1_cs    = 1'b0;
        s1_addr  = 32'd0;
        s1_wdata = 32'd0;
        s1_we    = 1'b0;
        s1_size  = 2'b10;
        s1_winner = 2'd0;

        s2_cs    = 1'b0;
        s2_addr  = 32'd0;
        s2_wdata = 32'd0;
        s2_we    = 1'b0;
        s2_size  = 2'b10;
        s2_winner = 2'd0;

        // Master 0 routing (instr fetch)
        if (m0_granted) begin
            case (m0_slave)
                2'd0: begin  // ROM
                    s0_cs    = 1'b1;
                    s0_addr  = m0_addr;
                    s0_wdata = m0_wdata;
                    s0_we    = m0_we;
                    s0_size  = m0_size;
                    s0_winner = 2'd0;
                end
                2'd1: begin  // SRAM
                    s1_cs    = 1'b1;
                    s1_addr  = m0_addr;
                    s1_wdata = m0_wdata;
                    s1_we    = m0_we;
                    s1_size  = m0_size;
                    s1_winner = 2'd0;
                end
                2'd2: begin  // Peripheral
                    s2_cs    = 1'b1;
                    s2_addr  = m0_addr;
                    s2_wdata = m0_wdata;
                    s2_we    = m0_we;
                    s2_size  = m0_size;
                    s2_winner = 2'd0;
                end
                default: ;  // No slave — ignore
            endcase
        end

        // Master 1 routing (data access)
        // Can coexist with M0 if targeting different slave
        if (m1_granted) begin
            case (m1_slave)
                2'd0: begin  // ROM
                    s0_cs    = 1'b1;
                    s0_addr  = m1_addr;
                    s0_wdata = m1_wdata;
                    s0_we    = m1_we;
                    s0_size  = m1_size;
                    s0_winner = 2'd1;
                end
                2'd1: begin  // SRAM
                    s1_cs    = 1'b1;
                    s1_addr  = m1_addr;
                    s1_wdata = m1_wdata;
                    s1_we    = m1_we;
                    s1_size  = m1_size;
                    s1_winner = 2'd1;
                end
                2'd2: begin  // Peripheral
                    s2_cs    = 1'b1;
                    s2_addr  = m1_addr;
                    s2_wdata = m1_wdata;
                    s2_we    = m1_we;
                    s2_size  = m1_size;
                    s2_winner = 2'd1;
                end
                default: ;  // No slave — ignore
            endcase
        end
    end

    // ===============================================================
    // Master response mux — route slave ack/rdata back to masters
    // ===============================================================
    always @(*) begin
        // Default: no ack, zero data
        m0_rdata = 32'd0;
        m0_ack   = 1'b0;
        m1_rdata = 32'd0;
        m1_ack   = 1'b0;

        // M0 gets response from the slave it was routed to
        if (m0_granted) begin
            case (m0_slave)
                2'd0: begin  // ROM
                    m0_rdata = s0_rdata;
                    m0_ack   = s0_ack;
                end
                2'd1: begin  // SRAM
                    m0_rdata = s1_rdata;
                    m0_ack   = s1_ack;
                end
                2'd2: begin  // Peripheral
                    m0_rdata = s2_rdata;
                    m0_ack   = s2_ack;
                end
                default: begin
                    m0_rdata = 32'd0;
                    m0_ack   = m0_req;  // Immediate ack for unmapped regions
                end
            endcase
        end

        // M1 gets response from the slave it was routed to
        if (m1_granted) begin
            case (m1_slave)
                2'd0: begin  // ROM
                    m1_rdata = s0_rdata;
                    m1_ack   = s0_ack;
                end
                2'd1: begin  // SRAM
                    m1_rdata = s1_rdata;
                    m1_ack   = s1_ack;
                end
                2'd2: begin  // Peripheral
                    m1_rdata = s2_rdata;
                    m1_ack   = s2_ack;
                end
                default: begin
                    m1_rdata = 32'd0;
                    m1_ack   = m1_req;  // Immediate ack for unmapped regions
                end
            endcase
        end
    end

endmodule
