// priority_enc_param.vh — shared constants for priority_enc RTL modules
// Constants mirror the SSOT APB CSR map and fixed APB data/address shapes.
localparam [11:0] PRIORITY_ENC_CTRL_ADDR   = 12'h000;
localparam [11:0] PRIORITY_ENC_MASK_ADDR   = 12'h004;
localparam [11:0] PRIORITY_ENC_STATUS_ADDR = 12'h008;
localparam integer PRIORITY_ENC_APB_ADDR_W = 12;
localparam integer PRIORITY_ENC_APB_DATA_W = 32;
