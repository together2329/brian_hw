// adder_kogge_stone_param.vh — shared defaults from SSOT parameters
// Included inside modules; not listed as a standalone RTL source.
parameter integer DATA_WIDTH = 32;      // Overrides operand/result width for the adder datapath.
parameter integer ADDR_WIDTH = 8;       // Overrides APB byte-address width.
parameter integer APB_DATA_WIDTH = 32;  // Overrides APB data bus width; SSOT register map is 32-bit.
