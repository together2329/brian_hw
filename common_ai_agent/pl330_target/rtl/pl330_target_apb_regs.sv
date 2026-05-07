`default_nettype none

// Traceability: RTL_MODULE_PL330_TARGET_APB_REGS covers sub_modules[8], workflow_todos.rtl-gen[9],
// parameters.APB_DATA_WIDTH, parameters.APB_ADDR_WIDTH, cycle_model.handshake_rules.apb,
// registers.register_list, PL330 TARGET APB REGS module slice, rtl_todo_plan evidence.
module pl330_target_apb_regs #(
    parameter int APB_DATA_WIDTH = 32,
    parameter int APB_ADDR_WIDTH = 12
) (
    input  logic                      pclk,
    input  logic                      presetn,

    input  logic                      psel,
    input  logic                      penable,
    input  logic                      pwrite,
    input  logic [APB_ADDR_WIDTH-1:0] paddr,
    input  logic [APB_DATA_WIDTH-1:0] pwdata,
    output logic [APB_DATA_WIDTH-1:0] prdata,
    output logic                      pready,
    output logic                      pslverr,

    input  logic                      engine_busy,
    input  logic                      engine_idle,
    input  logic                      engine_done,
    input  logic                      engine_error,
    input  logic [7:0]                engine_error_code,

    input  logic [7:0]                mfifo_level,
    input  logic                      mfifo_overflow,
    input  logic                      mfifo_underflow,
    input  logic                      axi_error,
    input  logic                      periph_ack,

    output logic                      cfg_enable,
    output logic                      cfg_secure,
    output logic                      halt_req,
    output logic                      start_pulse,
    output logic                      soft_reset_pulse,
    output logic                      clear_done_pulse,
    output logic                      clear_error_pulse,
    output logic [APB_DATA_WIDTH-1:0] cfg_src_addr,
    output logic [APB_DATA_WIDTH-1:0] cfg_dst_addr,
    output logic [APB_DATA_WIDTH-1:0] cfg_len,
    output logic [7:0]                irq_enable_mask,
    output logic [7:0]                irq_status,
    output logic                      irq
);

    localparam logic [APB_ADDR_WIDTH-1:0] ADDR_ID         = APB_ADDR_WIDTH'(32'h0000_0000);
    localparam logic [APB_ADDR_WIDTH-1:0] ADDR_CTRL       = APB_ADDR_WIDTH'(32'h0000_0004);
    localparam logic [APB_ADDR_WIDTH-1:0] ADDR_STATUS     = APB_ADDR_WIDTH'(32'h0000_0008);
    localparam logic [APB_ADDR_WIDTH-1:0] ADDR_IRQ_ENABLE = APB_ADDR_WIDTH'(32'h0000_000c);
    localparam logic [APB_ADDR_WIDTH-1:0] ADDR_IRQ_STATUS = APB_ADDR_WIDTH'(32'h0000_0010);
    localparam logic [APB_ADDR_WIDTH-1:0] ADDR_SRC_ADDR   = APB_ADDR_WIDTH'(32'h0000_0014);
    localparam logic [APB_ADDR_WIDTH-1:0] ADDR_DST_ADDR   = APB_ADDR_WIDTH'(32'h0000_0018);
    localparam logic [APB_ADDR_WIDTH-1:0] ADDR_LEN        = APB_ADDR_WIDTH'(32'h0000_001c);
    localparam logic [APB_ADDR_WIDTH-1:0] ADDR_DEBUG      = APB_ADDR_WIDTH'(32'h0000_0020);

    localparam logic [APB_DATA_WIDTH-1:0] ID_VALUE        = APB_DATA_WIDTH'(32'h5033_3030);

    logic apb_access;
    logic apb_write_fire;
    logic apb_read_fire;
    logic addr_aligned;
    logic addr_hit;
    logic invalid_addr;

    logic [APB_DATA_WIDTH-1:0] ctrl_data;
    logic [APB_DATA_WIDTH-1:0] status_data;
    logic [APB_DATA_WIDTH-1:0] irq_enable_data;
    logic [APB_DATA_WIDTH-1:0] irq_status_data;
    logic [APB_DATA_WIDTH-1:0] debug_data;
    logic [APB_DATA_WIDTH-1:0] read_data_comb;

    logic [7:0] irq_status_q;
    logic [7:0] irq_enable_q;
    logic [7:0] event_sources;
    logic [7:0] irq_status_w1c_mask;
    logic [15:0] apb_read_count_q;
    logic [15:0] apb_write_count_q;
    logic [15:0] apb_error_count_q;

    assign apb_access     = psel & penable;
    assign apb_write_fire = apb_access & pwrite;
    assign apb_read_fire  = apb_access & ~pwrite;
    assign addr_aligned   = (paddr[1:0] == 2'b00);

    assign event_sources = {mfifo_underflow, mfifo_overflow, periph_ack, axi_error,
                            engine_error, engine_done, 2'b00};
    assign irq_status_w1c_mask = ((apb_write_fire == 1'b1) && (paddr == ADDR_IRQ_STATUS)) ? pwdata[7:0] : 8'h00;
    assign irq_enable_mask = irq_enable_q;
    assign irq_status = irq_status_q;
    assign irq = |(irq_status_q & irq_enable_q);

    always_comb begin
        addr_hit = 1'b0;
        case (paddr)
            ADDR_ID:         addr_hit = 1'b1;
            ADDR_CTRL:       addr_hit = 1'b1;
            ADDR_STATUS:     addr_hit = 1'b1;
            ADDR_IRQ_ENABLE: addr_hit = 1'b1;
            ADDR_IRQ_STATUS: addr_hit = 1'b1;
            ADDR_SRC_ADDR:   addr_hit = 1'b1;
            ADDR_DST_ADDR:   addr_hit = 1'b1;
            ADDR_LEN:        addr_hit = 1'b1;
            ADDR_DEBUG:      addr_hit = 1'b1;
            default:         addr_hit = 1'b0;
        endcase
    end

    assign invalid_addr = (addr_aligned == 1'b0) || (addr_hit == 1'b0);

    always_comb begin
        ctrl_data = {APB_DATA_WIDTH{1'b0}};
        ctrl_data[0] = cfg_enable;
        ctrl_data[1] = |irq_enable_q;
        ctrl_data[2] = 1'b0;
        ctrl_data[3] = 1'b0;
        ctrl_data[4] = cfg_secure;
        ctrl_data[5] = halt_req;
        ctrl_data[6] = 1'b0;
        ctrl_data[7] = 1'b0;
    end

    always_comb begin
        status_data = {APB_DATA_WIDTH{1'b0}};
        status_data[0] = engine_busy;
        status_data[1] = engine_idle;
        status_data[2] = engine_done;
        status_data[3] = engine_error;
        status_data[4] = axi_error;
        status_data[5] = mfifo_overflow;
        status_data[6] = mfifo_underflow;
        status_data[7] = periph_ack;
        status_data[15:8] = mfifo_level;
        status_data[31:24] = engine_error_code;
    end

    always_comb begin
        irq_enable_data = {APB_DATA_WIDTH{1'b0}};
        irq_enable_data[7:0] = irq_enable_q;
    end

    always_comb begin
        irq_status_data = {APB_DATA_WIDTH{1'b0}};
        irq_status_data[7:0] = irq_status_q;
    end

    always_comb begin
        debug_data = {APB_DATA_WIDTH{1'b0}};
        debug_data[15:0] = apb_read_count_q;
        debug_data[31:16] = apb_write_count_q;
    end

    always_comb begin
        read_data_comb = {APB_DATA_WIDTH{1'b0}};
        case (paddr)
            ADDR_ID:         read_data_comb = ID_VALUE;
            ADDR_CTRL:       read_data_comb = ctrl_data;
            ADDR_STATUS:     read_data_comb = status_data;
            ADDR_IRQ_ENABLE: read_data_comb = irq_enable_data;
            ADDR_IRQ_STATUS: read_data_comb = irq_status_data;
            ADDR_SRC_ADDR:   read_data_comb = cfg_src_addr;
            ADDR_DST_ADDR:   read_data_comb = cfg_dst_addr;
            ADDR_LEN:        read_data_comb = cfg_len;
            ADDR_DEBUG:      read_data_comb = debug_data;
            default:         read_data_comb = APB_DATA_WIDTH'(32'h0000_0000);
        endcase
    end

    always_comb begin
        pready  = apb_access;
        pslverr = apb_access & invalid_addr;
        prdata  = read_data_comb;
    end

    always_ff @(posedge pclk or negedge presetn) begin
        if (!presetn) begin
            cfg_enable        <= 1'b0;
            cfg_secure        <= 1'b0;
            halt_req          <= 1'b0;
            start_pulse       <= 1'b0;
            soft_reset_pulse  <= 1'b0;
            clear_done_pulse  <= 1'b0;
            clear_error_pulse <= 1'b0;
            cfg_src_addr      <= {APB_DATA_WIDTH{1'b0}};
            cfg_dst_addr      <= {APB_DATA_WIDTH{1'b0}};
            cfg_len           <= {APB_DATA_WIDTH{1'b0}};
            irq_enable_q      <= 8'h00;
            apb_read_count_q  <= 16'h0000;
            apb_write_count_q <= 16'h0000;
            apb_error_count_q <= 16'h0000;
        end else begin
            start_pulse       <= 1'b0;
            soft_reset_pulse  <= 1'b0;
            clear_done_pulse  <= 1'b0;
            clear_error_pulse <= 1'b0;

            if (apb_read_fire) begin
                apb_read_count_q <= apb_read_count_q + 16'h0001;
            end
            if (apb_write_fire) begin
                apb_write_count_q <= apb_write_count_q + 16'h0001;
            end
            if (apb_access && invalid_addr) begin
                apb_error_count_q <= apb_error_count_q + 16'h0001;
            end

            if (apb_write_fire && !invalid_addr) begin
                case (paddr)
                    ADDR_CTRL: begin
                        cfg_enable        <= pwdata[0];
                        start_pulse       <= pwdata[2];
                        soft_reset_pulse  <= pwdata[3];
                        cfg_secure        <= pwdata[4];
                        halt_req          <= pwdata[5];
                        clear_done_pulse  <= pwdata[6];
                        clear_error_pulse <= pwdata[7];
                        if (pwdata[3]) begin
                            cfg_enable <= 1'b0;
                            halt_req   <= 1'b0;
                        end
                    end
                    ADDR_IRQ_ENABLE: begin
                        irq_enable_q <= pwdata[7:0];
                    end
                    ADDR_SRC_ADDR: begin
                        cfg_src_addr <= pwdata;
                    end
                    ADDR_DST_ADDR: begin
                        cfg_dst_addr <= pwdata;
                    end
                    ADDR_LEN: begin
                        cfg_len <= pwdata;
                    end
                    default: begin
                    end
                endcase
            end
        end
    end

    always_ff @(posedge pclk or negedge presetn) begin
        if (!presetn) begin
            irq_status_q <= 8'h00;
        end else begin
            irq_status_q <= (irq_status_q | event_sources) & ~irq_status_w1c_mask;
            if (soft_reset_pulse) begin
                irq_status_q <= 8'h00;
            end
        end
    end

endmodule

`default_nettype wire
