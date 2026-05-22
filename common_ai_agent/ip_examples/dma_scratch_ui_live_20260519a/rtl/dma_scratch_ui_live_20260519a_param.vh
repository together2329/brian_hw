// dma_scratch_ui_live_20260519a_param.vh
// Shared local constants derived from SSOT parameters.
localparam integer STRB_WIDTH = DATA_WIDTH/8;
localparam [2:0] FSM_IDLE      = 3'd0;
localparam [2:0] FSM_READ_REQ  = 3'd1;
localparam [2:0] FSM_WAIT_RDATA= 3'd2;
localparam [2:0] FSM_WRITE_REQ = 3'd3;
localparam [2:0] FSM_DONE      = 3'd4;
localparam [2:0] FSM_ERROR     = 3'd5;
