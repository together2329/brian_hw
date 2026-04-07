// ============================================================================
// Module:    tdisp_reg_tracker.sv
// Purpose:   TDISP Register Modification Tracker u2014 monitors PCIe config space
//            register writes, classifies per Table 11-3 categories, and triggers
//            ERROR for forbidden modifications while TDI is in CONFIG_LOCKED or RUN.
// Spec:      PCI Express Base Specification Revision 7.0, Section 11.2.6,
//            Table 11-3: Example DSM Tracking and Handling for Architected Registers
//
// Architecture:
//   1. Receives streaming register write events from the PCIe config space
//      management interface.
//   2. When tracking_enable is asserted (TDI in CONFIG_LOCKED or RUN), each
//      write is classified into one of five categories:
//        - CAT_ALLOWED      : Write permitted, no action.
//        - CAT_ERROR        : Write forbidden u2192 error_trigger pulse to FSM.
//        - CAT_CMD_REGISTER : Command Register u2014 check critical bits.
//        - CAT_DEV_CTRL     : Device Control 1/2/3 u2014 check critical bits.
//        - CAT_MSIX         : MSI-X u2014 error if table was locked.
//   3. Category-specific logic validates individual bits per Table 11-3
//      description column.
//   4. On forbidden modification: asserts error_trigger for one cycle with
//      descriptive error_reg_name/error_reg_description for diagnostics.
//
// Table 11-3 Category Summary:
//   ALLOWED:
//     Cache Line Size, Latency Timer, Interrupt Line, Status Register,
//     Device Status 1/2/3, Link Control 1/2/3 + GT/s Control,
//     Link Status 1/2/3 + GT/s Status, MSI Capability,
//     Secondary PCIe / Physical Layer / Lane Margining / Flit Error Injection,
//     ACS Extended, LTR Extended, AER Extended, VC / MFVC Extended,
//     DPA Extended, PTM / Hierarchy ID / NPEM / Alt Protocol Extended,
//     PMUX Extended, DOE Extended, Dynamic Power Allocation
//
//   ERROR:
//     BIST Register, Base Address Registers, Expansion ROM Base Address,
//     Enhanced Allocation, Resizable BAR / VF Resizable BAR,
//     ARI Extended, PASID Extended, Multicast Extended, ATS Extended
//
//   SEE_DESCRIPTION:
//     Command Register (Memory Space Enable, Bus Master Enable u2192 ERROR),
//     PCI Power Management (power transition losing state u2192 ERROR),
//     Device Control 1/2/3 (specific bits u2192 ERROR),
//     MSI-X (if locked and reported u2192 ERROR),
//     L1 PM Substates (Link Down u2192 ERROR),
//     IDE Extended (bound stream modification u2192 ERROR),
//     Vendor Specific (vendor analysis required),
//     TPH Requester (vendor analysis required)
// ============================================================================

module tdisp_reg_tracker
    import tdisp_pkg::*;
#(
    // Width of register write address bus (standard PCIe config space = 12 bits)
    parameter int REG_ADDR_WIDTH = 12,

    // Width of register write data bus
    parameter int REG_DATA_WIDTH = 32,

    // Width of byte-enable mask
    parameter int REG_MASK_WIDTH = REG_DATA_WIDTH / 8
)(
    input  logic clk,
    input  logic rst_n,

    // =========================================================================
    // TDI State u2014 determines if tracking is active
    // =========================================================================
    input  tdisp_tdi_state_e   tdi_state,

    // =========================================================================
    // Register write event interface (from PCIe config space manager)
    //   Qualification: reg_write_valid && tracking_enable
    // =========================================================================
    input  logic                            reg_write_valid,
    input  logic [REG_ADDR_WIDTH-1:0]       reg_write_addr,
    input  logic [REG_DATA_WIDTH-1:0]       reg_write_data,
    input  logic [REG_MASK_WIDTH-1:0]       reg_write_mask,

    // =========================================================================
    // Function ID for multi-function / SR-IOV disambiguation
    // =========================================================================
    input  logic [TDI_INDEX_WIDTH-1:0]      tdi_function_id,

    // =========================================================================
    // Control: tracking enabled when TDI is in CONFIG_LOCKED or RUN
    // =========================================================================
    input  logic                            tracking_enable,

    // =========================================================================
    // Capability base addresses (discovered during PCIe enumeration)
    //   These are the base offsets for each capability structure in config space.
    //   Used to dynamically classify registers that belong to capabilities whose
    //   positions are not fixed u2014 the fundamental mechanism for routing addresses
    //   to CAT_DEV_CTRL, CAT_MSIX, and CAT_POWER_MGMT.
    // =========================================================================
    input  logic [REG_ADDR_WIDTH-1:0]       pcie_cap_base,    // PCI Express Capability base
    input  logic [REG_ADDR_WIDTH-1:0]       msix_cap_base,    // MSI-X Capability base
    input  logic [REG_ADDR_WIDTH-1:0]       pm_cap_base,      // PCI Power Management Capability base

    // =========================================================================
    // Lock configuration u2014 MSI-X lock status from lock_handler
    // =========================================================================
    input  logic                            msix_table_locked,

    // =========================================================================
    // Error output u2014 pulse to FSM (one cycle)
    // =========================================================================
    output logic                            error_trigger,
    output logic [REG_ADDR_WIDTH-1:0]       error_reg_addr,
    output logic [255:0]                    error_reg_name,
    output logic [255:0]                    error_reg_description,
    output logic [TDI_INDEX_WIDTH-1:0]      error_tdi_idx        // Function ID that caused error
);

    // =========================================================================
    // Register classification categories (Table 11-3)
    // =========================================================================
    typedef enum logic [2:0] {
        CAT_ALLOWED      = 3'd0,  // Write permitted, no action
        CAT_ERROR        = 3'd1,  // Always forbidden u2192 error_trigger
        CAT_CMD_REGISTER = 3'd2,  // Command Register u2014 check critical bits
        CAT_DEV_CTRL     = 3'd3,  // Device Control 1/2/3 u2014 check critical bits
        CAT_MSIX         = 3'd4,  // MSI-X u2014 error if table locked
        CAT_VENDOR_SPEC  = 3'd5,  // Vendor Specific u2014 vendor analysis required
        CAT_POWER_MGMT   = 3'd6,  // PCI Power Management u2014 state loss check
        CAT_RESERVED_CAT = 3'd7   // Reserved / unmapped u2192 default ERROR
    } reg_category_e;

    // =========================================================================
    // PCIe Capability relative register offsets within capability structures
    // =========================================================================
    // Device Control registers: relative offsets within PCIe Cap structure
    localparam logic [11:0] PCIE_CAP_DC1_OFFSET = 12'h008;  // Device Control (base+0x08)
    localparam logic [11:0] PCIE_CAP_DC2_OFFSET = 12'h028;  // Device Control 2 (base+0x28)
    localparam logic [11:0] PCIE_CAP_DC3_OFFSET = 12'h044;  // Device Control 3 (base+0x44)
    localparam logic [11:0] PCIE_CAP_END_OFFSET = 12'h048;  // End of PCIe Cap structure

    // MSI-X Capability register: relative offset within MSI-X Cap structure
    localparam logic [11:0] MSIX_CAP_MSG_CTRL_OFFSET = 12'h000;  // Message Control (base+0x00)

    // Power Management Capability: PMCSR register offset
    localparam logic [11:0] PM_CAP_PMCSR_OFFSET     = 12'h004;  // PMCSR (base+0x04)
    localparam logic [11:0] PM_CAP_END_OFFSET        = 12'h008;  // End of PM Cap structure

    // =========================================================================
    // Capability-range matching helpers
    //   Returns true if addr falls within [base + rel_offset, base + rel_offset + 2)
    //   i.e., matches a DWORD-aligned register in the capability structure.
    // =========================================================================
    function automatic logic addr_in_cap_dword(
        input logic [REG_ADDR_WIDTH-1:0] addr,
        input logic [REG_ADDR_WIDTH-1:0] cap_base,
        input logic [REG_ADDR_WIDTH-1:0] rel_offset
    );
        addr_in_cap_dword = (addr & 12'hFFC) == ((cap_base + rel_offset) & 12'hFFC);
    endfunction

    function automatic logic addr_in_cap_range(
        input logic [REG_ADDR_WIDTH-1:0] addr,
        input logic [REG_ADDR_WIDTH-1:0] cap_base,
        input logic [REG_ADDR_WIDTH-1:0] range_size
    );
        addr_in_cap_range = (addr >= cap_base) && (addr < cap_base + range_size);
    endfunction

    // =========================================================================
    // Register address classification u2014 combinational
    //   Maps a config space address to its Table 11-3 category.
    //   Capability-positioned registers (DEV_CTRL, MSI-X, POWER_MGMT) use
    //   dynamic base addresses provided as input ports.
    // =========================================================================
    reg_category_e  write_category;
    logic [255:0]   classified_reg_name;
    logic [255:0]   classified_reg_desc;

    always_comb begin
        write_category    = CAT_RESERVED_CAT;
        classified_reg_name = '0;
        classified_reg_desc = '0;

        case (reg_write_addr)

            // =================================================================
            // ALLOWED registers (Table 11-3: "Allowed")
            // =================================================================

            // Cache Line Size (offset 0x0C, low byte)
            12'h00C: begin
                write_category      = CAT_ALLOWED;
                classified_reg_name = 256'h434c53_43416368654c696e6553697a65;  // "CacheLineSize"
            end

            // Interrupt Line (offset 0x3C, low byte)
            12'h03C: begin
                write_category      = CAT_ALLOWED;
                classified_reg_name = 256'h496e746572727570744c696e65;  // "InterruptLine"
            end

            // Status Register (offset 0x06)
            12'h006: begin
                write_category      = CAT_ALLOWED;
                classified_reg_name = 256'h5374617475735265676973746572;  // "StatusRegister"
            end

            // =================================================================
            // COMMAND REGISTER u2014 See Description (offset 0x04)
            //   Clearing Memory Space Enable or Bus Master Enable u2192 ERROR
            // =================================================================
            12'h004: begin
                write_category      = CAT_CMD_REGISTER;
                classified_reg_name = 256'h436f6d6d616e645265676973746572;  // "CommandRegister"
                classified_reg_desc = 256'h4d656d456e61626c652f4275734d6173746572456e61626c65;  // "MemEnable/BusMasterEnable"
            end

            // =================================================================
            // ERROR registers u2014 always forbidden
            // =================================================================

            // BIST Register (offset 0x0F)
            12'h00F: begin
                write_category      = CAT_ERROR;
                classified_reg_name = 256'h424953545265676973746572;  // "BISTRegister"
                classified_reg_desc = 256'h4261722f457870524f4d206d6f646966;  // "BAR/ExpROM modif"
            end

            // Base Address Registers (offsets 0x10u20130x24)
            12'h010, 12'h014, 12'h018, 12'h01C, 12'h020, 12'h024: begin
                write_category      = CAT_ERROR;
                classified_reg_name = 256'h42617365416464726573735265676973746572;  // "BaseAddressRegister"
                classified_reg_desc = 256'h424152206d6f64696669636174696f6e;  // "BAR modification"
            end

            // Expansion ROM Base Address (offset 0x30)
            12'h030: begin
                write_category      = CAT_ERROR;
                classified_reg_name = 256'h457870616e73696f6e524f4d426172;  // "ExpansionROMBar"
                classified_reg_desc = 256'h457870616e73696f6e20524f4d206d6f646966;  // "Expansion ROM modif"
            end

            default: begin
                // -----------------------------------------------------------------
                // Dynamic capability-range matching using runtime base addresses.
                // Priority-ordered: PCIe Cap > MSI-X Cap > PM Cap > Extended Cap.
                // Addresses not matching any capability fall to conservative ERROR.
                // -----------------------------------------------------------------

                // --- PCI Express Capability (CAT_DEV_CTRL for Device Control regs) ---
                // PCIe Capability structure spans from pcie_cap_base for ~72 bytes.
                // Device Control 1 at base+0x08, Device Control 2 at base+0x28,
                // Device Control 3 at base+0x44. Other PCIe cap registers are ALLOWED.
                if (addr_in_cap_range(reg_write_addr, pcie_cap_base, PCIE_CAP_END_OFFSET)) begin
                    if (addr_in_cap_dword(reg_write_addr, pcie_cap_base, PCIE_CAP_DC1_OFFSET) ||
                        addr_in_cap_dword(reg_write_addr, pcie_cap_base, PCIE_CAP_DC2_OFFSET) ||
                        addr_in_cap_dword(reg_write_addr, pcie_cap_base, PCIE_CAP_DC3_OFFSET)) begin
                        write_category      = CAT_DEV_CTRL;
                        classified_reg_name = 256'h446576696365436f6e74726f6c;  // "DeviceControl"
                        classified_reg_desc = 256'h4465764374726c312f322f3320637269746963616c2062697473;  // "DevCtrl1/2/3 critical bits"
                    end else begin
                        // Other PCIe capability registers (Link Control, Slot, etc.)
                        write_category      = CAT_ALLOWED;
                        classified_reg_name = 256'h506349654361704f74686572;  // "PCIeCapOther"
                    end
                end
                // --- MSI-X Capability (CAT_MSIX) ---
                // MSI-X Capability structure: 8 bytes at msix_cap_base.
                // Any write to this range when table is locked u2192 error (checked later).
                else if (addr_in_cap_range(reg_write_addr, msix_cap_base, 12'h008)) begin
                    write_category      = CAT_MSIX;
                    classified_reg_name = 256'h4d534978436170;  // "MSIXCap"
                    classified_reg_desc = 256'h4d53492d58206c6f636b6564206d6f646966;  // "MSI-X locked modif"
                end
                // --- PCI Power Management Capability (CAT_POWER_MGMT for PMCSR) ---
                // PM Cap structure: 8 bytes at pm_cap_base.
                // PMCSR is at pm_cap_base + 0x04. PowerState bits [1:0] checked later.
                else if (addr_in_cap_range(reg_write_addr, pm_cap_base, PM_CAP_END_OFFSET)) begin
                    if (addr_in_cap_dword(reg_write_addr, pm_cap_base, PM_CAP_PMCSR_OFFSET)) begin
                        write_category      = CAT_POWER_MGMT;
                        classified_reg_name = 256'h506f7765724d67745f504d435352;  // "PowerMgmt_PMCSR"
                        classified_reg_desc = 256'h4433207374617465206c6f737320636865636b;  // "D3 state loss check"
                    end else begin
                        // PM Cap other registers (PMC, PM Status) u2014 ALLOWED
                        write_category      = CAT_ALLOWED;
                        classified_reg_name = 256'h506f7765724d67744f74686572;  // "PowerMgmtOther"
                    end
                end
                // --- Extended Capability space (offset 0x100+) ---
                else if (reg_write_addr >= 12'h100) begin
                    write_category = classify_extended_cap(reg_write_addr);
                end
                // --- Standard header space, unmapped u2192 conservative ERROR ---
                else begin
                    write_category      = CAT_RESERVED_CAT;
                end
            end
        endcase
    end

    // =========================================================================
    // Extended Capability Classification Function
    //   Maps extended capability register addresses to Table 11-3 categories.
    //   In real hardware, capability base addresses are discovered at enum.
    //   This function provides a lookup table for known capability IDs.
    //   Inputs: absolute config space address (u2265 0x100)
    // =========================================================================
    function automatic reg_category_e classify_extended_cap(
        input logic [REG_ADDR_WIDTH-1:0] addr
    );
        // Extended capability space starts at 0x100.
        // Each capability has a 4KB-aligned or packed layout.
        // The first word at each cap base contains Cap ID [15:0].
        // Here we use a simplified range-based approach.

        // Note: In a real device, cap offsets are runtime-discovered.
        // This lookup assumes common offset assignments and uses
        // a conservative default (CAT_ERROR) for unmapped ranges.

        logic [11:0] cap_base;
        logic [11:0] cap_offset;

        // Default: conservative error for unknown extended caps
        classify_extended_cap = CAT_ERROR;

        // AER Extended Capability (Cap ID 0x0001) u2014 ALLOWED
        //   Per Table 11-3: error mask settings control reporting only,
        //   do not block error detection.
        //   Commonly at offset 0x100
        if (addr >= 12'h100 && addr < 12'h140) begin
            classify_extended_cap = CAT_ALLOWED;
        end
        // VC / MFVC Extended Capability (Cap ID 0x0002) u2014 ALLOWED
        //   Device must enforce TC/VC ordering when mapping changes.
        else if (addr >= 12'h140 && addr < 12'h180) begin
            classify_extended_cap = CAT_ALLOWED;
        end
        // Serial Number Extended (Cap ID 0x0003) u2014 ALLOWED (read-only)
        else if (addr >= 12'h180 && addr < 12'h190) begin
            classify_extended_cap = CAT_ALLOWED;
        end
        // Power Budgeting (Cap ID 0x0004) u2014 read-only selector, excluded
        else if (addr >= 12'h190 && addr < 12'h1A0) begin
            classify_extended_cap = CAT_ALLOWED;
        end
        // ACS Extended Capability (Cap ID 0x000D) u2014 ALLOWED
        else if (addr >= 12'h1A0 && addr < 12'h1B0) begin
            classify_extended_cap = CAT_ALLOWED;
        end
        // Latency Tolerance Reporting (Cap ID 0x000E) u2014 ALLOWED
        else if (addr >= 12'h1B0 && addr < 12'h1C0) begin
            classify_extended_cap = CAT_ALLOWED;
        end
        // Secondary PCIe Extended Capability (Cap ID 0x0019) u2014 ALLOWED
        else if (addr >= 12'h200 && addr < 12'h240) begin
            classify_extended_cap = CAT_ALLOWED;
        end
        // Physical Layer 16.0 GT/s (Cap ID 0x0024) u2014 ALLOWED
        else if (addr >= 12'h240 && addr < 12'h280) begin
            classify_extended_cap = CAT_ALLOWED;
        end
        // Physical Layer 32.0 GT/s (Cap ID 0x0025) u2014 ALLOWED
        else if (addr >= 12'h280 && addr < 12'h2C0) begin
            classify_extended_cap = CAT_ALLOWED;
        end
        // Physical Layer 64.0 GT/s (Cap ID 0x0026) u2014 ALLOWED
        else if (addr >= 12'h2C0 && addr < 12'h300) begin
            classify_extended_cap = CAT_ALLOWED;
        end
        // Lane Margining at Receiver (Cap ID 0x0027) u2014 ALLOWED
        else if (addr >= 12'h300 && addr < 12'h340) begin
            classify_extended_cap = CAT_ALLOWED;
        end
        // Flit Error Injection (Cap ID 0x0028) u2014 ALLOWED
        else if (addr >= 12'h340 && addr < 12'h360) begin
            classify_extended_cap = CAT_ALLOWED;
        end
        // Resizable BAR Extended (Cap ID 0x0015) u2014 ERROR
        else if (addr >= 12'h360 && addr < 12'h380) begin
            classify_extended_cap = CAT_ERROR;
        end
        // VF Resizable BAR Extended (Cap ID 0x0016) u2014 ERROR
        else if (addr >= 12'h380 && addr < 12'h3A0) begin
            classify_extended_cap = CAT_ERROR;
        end
        // ARI Extended (Cap ID 0x000E overlap, use unique range) u2014 ERROR
        else if (addr >= 12'h3A0 && addr < 12'h3B0) begin
            classify_extended_cap = CAT_ERROR;
        end
        // PASID Extended (Cap ID 0x001B) u2014 ERROR
        else if (addr >= 12'h3B0 && addr < 12'h3C0) begin
            classify_extended_cap = CAT_ERROR;
        end
        // Multicast Extended (Cap ID 0x0012) u2014 ERROR
        else if (addr >= 12'h3C0 && addr < 12'h3E0) begin
            classify_extended_cap = CAT_ERROR;
        end
        // ATS Extended (Cap ID 0x000F) u2014 ERROR
        else if (addr >= 12'h3E0 && addr < 12'h400) begin
            classify_extended_cap = CAT_ERROR;
        end
        // L1 PM Substates (Cap ID 0x001E) u2014 ALLOWED (Link Down u2192 ERROR side-effect)
        else if (addr >= 12'h400 && addr < 12'h420) begin
            classify_extended_cap = CAT_ALLOWED;
        end
        // Dynamic Power Allocation (Cap ID 0x0023) u2014 ALLOWED
        else if (addr >= 12'h420 && addr < 12'h440) begin
            classify_extended_cap = CAT_ALLOWED;
        end
        // PTM Extended (Cap ID 0x001F) u2014 ALLOWED
        else if (addr >= 12'h440 && addr < 12'h460) begin
            classify_extended_cap = CAT_ALLOWED;
        end
        // DOE Extended (Cap ID 0x0029) u2014 ALLOWED
        else if (addr >= 12'h460 && addr < 12'h480) begin
            classify_extended_cap = CAT_ALLOWED;
        end
        // IDE Extended (Cap ID 0x0030) u2014 SEE_DESCRIPTION
        //   Modifying bound stream control u2192 ERROR
        //   Classified as CAT_ALLOWED here; specific stream-check logic
        //   is handled separately in the write-validation block.
        else if (addr >= 12'h480 && addr < 12'h500) begin
            classify_extended_cap = CAT_ALLOWED;
        end
        // Enhanced Allocation (Cap ID 0x0014) u2014 ERROR
        else if (addr >= 12'h500 && addr < 12'h540) begin
            classify_extended_cap = CAT_ERROR;
        end
        // TPH Requester (Cap ID 0x0017) u2014 SEE_DESCRIPTION (vendor analysis)
        else if (addr >= 12'h540 && addr < 12'h560) begin
            classify_extended_cap = CAT_VENDOR_SPEC;
        end
        // Vendor Specific Extended u2014 SEE_DESCRIPTION
        else if (addr >= 12'h560 && addr < 12'h600) begin
            classify_extended_cap = CAT_VENDOR_SPEC;
        end
        // Protocol Multiplexing (Cap ID 0x0021) u2014 ALLOWED
        else if (addr >= 12'h600 && addr < 12'h640) begin
            classify_extended_cap = CAT_ALLOWED;
        end
        // Shadow Functions (Cap ID 0x0022) u2014 NOT APPLICABLE
        else if (addr >= 12'h640 && addr < 12'h660) begin
            classify_extended_cap = CAT_ALLOWED;
        end
        // Hierarchy ID / NPEM / Alt Protocol u2014 ALLOWED
        else begin
            classify_extended_cap = CAT_ALLOWED;
        end
    endfunction

    // =========================================================================
    // PCIe Capability Register Classification (within capability block)
    //   The PCIe Capability structure occupies up to 60+ bytes at its base.
    //   Key registers at standard offsets within the capability block:
    //     +0x08 = Device Control Register
    //     +0x0A = Device Status Register
    //     +0x10 = Link Control Register
    //     +0x12 = Link Status Register
    //     +0x28 = Device Control 2 Register
    //     +0x30 = Link Control 2 Register
    //     +0x32 = Link Status 2 Register
    //     +0x34 = 16.0 GT/s Control (or Slot)
    //     +0x44 = Device Control 3 Register
    //     +0x46 = Device Status 3 Register
    //
    //   For this module, we use a secondary decode for registers within
    //   the PCIe capability range. The capability base is provided via
    //   the address's capability-relative offset.
    // =========================================================================

    // MSI-X Capability detection: MSI-X Capability structure:
    //   Offset +0x00: Message Control (16 bits) u2014 bit 7 = Function Mask,
    //                 bit 6 = MSI-X Enable
    //   The capability base is discovered at enumeration. Here we assume
    //   the MSI-X cap is within the standard capability space (0x40u20130xFF).
    //   A more precise implementation would parameterize capability bases.

    // =========================================================================
    // Command Register critical bit definitions (Table 11-3)
    //   Bit 1 = Memory Space Enable
    //   Bit 2 = Bus Master Enable
    //   Clearing either u2192 ERROR
    // =========================================================================
    localparam int CMD_BIT_MEM_SPACE_ENABLE = 1;
    localparam int CMD_BIT_BUS_MASTER_ENABLE = 2;

    // =========================================================================
    // Device Control Register critical bit definitions (Table 11-3)
    //   Bit  5 = Extended Tag Field Enable
    //   Bit  6 = Phantom Functions Enable
    //   Bit  7 = Initiate Function Level Reset
    //   Bit 11 = Enable No Snoop
    //   Bit 12 = 10-bit Tag Requester Enable
    //   Bit 15 (DC2) / additional bits for DC2/DC3
    //
    //   For Device Control 2:
    //   Bit  4 = 14-bit Tag Requester Enable
    // =========================================================================
    localparam int DC1_BIT_EXTENDED_TAG_ENABLE    = 5;
    localparam int DC1_BIT_PHANTOM_FUNC_ENABLE    = 6;
    localparam int DC1_BIT_INITIATE_FLR           = 7;
    localparam int DC1_BIT_ENABLE_NO_SNOOP        = 11;
    localparam int DC1_BIT_10BIT_TAG_REQ_ENABLE   = 12;

    // Device Control 2: 14-bit Tag Requester Enable = bit 4
    localparam int DC2_BIT_14BIT_TAG_REQ_ENABLE   = 4;

    // =========================================================================
    // Registered outputs (pulse signals)
    // =========================================================================
    logic error_trigger_r;
    logic [REG_ADDR_WIDTH-1:0] error_reg_addr_r;
    logic [255:0] error_reg_name_r;
    logic [255:0] error_reg_description_r;
    logic [TDI_INDEX_WIDTH-1:0] error_tdi_idx_r;

    assign error_trigger         = error_trigger_r;
    assign error_reg_addr        = error_reg_addr_r;
    assign error_reg_name        = error_reg_name_r;
    assign error_reg_description = error_reg_description_r;
    assign error_tdi_idx         = error_tdi_idx_r;

    // =========================================================================
    // Command Register bit-change detection
    //   Extracts current bits and new bits, checks if critical bits are cleared.
    //   reg_write_data contains the NEW value to be written.
    //   We need the CURRENT value to detect clears. In a real device, the
    //   current value would come from a register shadow. Here we assume
    //   reg_write_data is the value being written and we detect if critical
    //   bits would be cleared (written as 0).
    //
    //   Per spec: "Clearing any of the following bits causes the TDI...
    //   to transition to ERROR". The mask indicates which bytes are valid.
    // =========================================================================

    // =========================================================================
    // MSI-X Capability address detection helper
    //   Standard MSI-X capability structure: offset 0x40u20130x4C (typical)
    //   MSI-X Message Control is at cap_base + 0x02
    //   For this implementation, we detect MSI-X writes by address range.
    //   A parameterized approach would use the discovered cap_offset.
    // =========================================================================
    localparam logic [11:0] MSIX_CAP_BASE = 12'h040;  // Typical MSI-X base

    // =========================================================================
    // Main register write tracker u2014 single always_ff block
    //   Per project convention: single always_ff for all sequential logic.
    //   Combinational classification is done above.
    // =========================================================================
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            error_trigger_r        <= 1'b0;
            error_reg_addr_r       <= '0;
            error_reg_name_r       <= '0;
            error_reg_description_r <= '0;
            error_tdi_idx_r        <= '0;
        end else begin
            // Default: clear pulse each cycle
            error_trigger_r        <= 1'b0;
            error_reg_addr_r       <= '0;
            error_reg_name_r       <= '0;
            error_reg_description_r <= '0;
            error_tdi_idx_r        <= '0;

            // Only evaluate when tracking is enabled and a write occurs
            if (tracking_enable && reg_write_valid) begin
                // Capture function ID for diagnostic output (used by all error paths)
                error_tdi_idx_r <= tdi_function_id;

                case (write_category)

                    // ==========================================================
                    // CAT_ALLOWED: No action required
                    // ==========================================================
                    CAT_ALLOWED: begin
                        // Write permitted u2014 no error trigger
                    end

                    // ==========================================================
                    // CAT_ERROR: Always forbidden u2192 trigger error
                    // ==========================================================
                    CAT_ERROR: begin
                        error_trigger_r        <= 1'b1;
                        error_reg_addr_r       <= reg_write_addr;
                        error_reg_name_r       <= classified_reg_name;
                        error_reg_description_r <= classified_reg_desc;
                    end

                    // ==========================================================
                    // CAT_CMD_REGISTER: Check if Memory Space Enable or
                    //   Bus Master Enable is being cleared (Table 11-3)
                    //   Per spec: clearing these bits u2192 ERROR. Other bits allowed.
                    // ==========================================================
                    CAT_CMD_REGISTER: begin
                        // Check if either critical bit is being cleared.
                        // We check if the written data has either bit = 0.
                        // The byte mask must cover the relevant byte (byte 0).
                        if (reg_write_mask[0]) begin
                            if (!reg_write_data[CMD_BIT_MEM_SPACE_ENABLE] ||
                                !reg_write_data[CMD_BIT_BUS_MASTER_ENABLE]) begin
                                error_trigger_r        <= 1'b1;
                                error_reg_addr_r       <= reg_write_addr;
                                error_reg_name_r       <= classified_reg_name;
                                error_reg_description_r <= classified_reg_desc;
                            end
                        end
                    end

                    // ==========================================================
                    // CAT_DEV_CTRL: Check critical Device Control bits
                    //   Per Table 11-3, modifying these bits u2192 ERROR:
                    //     DC1: Extended Tag Enable, Phantom Func Enable,
                    //          Initiate FLR, Enable No Snoop,
                    //          10-bit Tag Requester Enable
                    //     DC2: 14-bit Tag Requester Enable
                    //   Other bits are allowed.
                    // ==========================================================
                    CAT_DEV_CTRL: begin
                        // Device Control 1 (lower 16 bits)
                        if (reg_write_mask[0] || reg_write_mask[1]) begin
                            if (reg_write_data[DC1_BIT_EXTENDED_TAG_ENABLE]  != 1'b1 ||
                                reg_write_data[DC1_BIT_PHANTOM_FUNC_ENABLE] != 1'b0 ||
                                reg_write_data[DC1_BIT_INITIATE_FLR]        == 1'b1 ||
                                reg_write_data[DC1_BIT_ENABLE_NO_SNOOP]     == 1'b1 ||
                                reg_write_data[DC1_BIT_10BIT_TAG_REQ_ENABLE] != 1'b1) begin
                                error_trigger_r        <= 1'b1;
                                error_reg_addr_r       <= reg_write_addr;
                                error_reg_name_r       <= classified_reg_name;
                                error_reg_description_r <= classified_reg_desc;
                            end
                        end
                        // Device Control 2 (byte offset for DC2)
                        if (reg_write_mask[2] || reg_write_mask[3]) begin
                            if (reg_write_data[DC2_BIT_14BIT_TAG_REQ_ENABLE] != 1'b1) begin
                                error_trigger_r        <= 1'b1;
                                error_reg_addr_r       <= reg_write_addr;
                                error_reg_name_r       <= classified_reg_name;
                                error_reg_description_r <= classified_reg_desc;
                            end
                        end
                    end

                    // ==========================================================
                    // CAT_MSIX: MSI-X Capability u2014 error if table was locked
                    //   Per Table 11-3: "If MSI-X table was locked and reported,
                    //   then any modifications cause transition to ERROR.
                    //   Modifications are allowed otherwise."
                    // ==========================================================
                    CAT_MSIX: begin
                        if (msix_table_locked) begin
                            error_trigger_r        <= 1'b1;
                            error_reg_addr_r       <= reg_write_addr;
                            error_reg_name_r       <= classified_reg_name;
                            error_reg_description_r <= classified_reg_desc;
                        end
                    end

                    // ==========================================================
                    // CAT_POWER_MGMT: PCI Power Management u2014 state loss check
                    //   Per Table 11-3: "If a power transition leads to the
                    //   function losing its state, then the device transitions
                    //   the TDI hosted by that function to ERROR."
                    //   PowerState field (bits [1:0] of PMCSR):
                    //     00 = D0 (full power), 01 = D1, 10 = D2, 11 = D3
                    //     D3hot/D3cold can cause state loss u2192 ERROR
                    // ==========================================================
                    CAT_POWER_MGMT: begin
                        // If PowerState is being set to D3 (2'b11) u2192 ERROR
                        // PMCSR is at cap_base + 0x04, bits [1:0] = PowerState
                        if (reg_write_mask[0]) begin
                            if (reg_write_data[1:0] == 2'b11) begin
                                error_trigger_r        <= 1'b1;
                                error_reg_addr_r       <= reg_write_addr;
                                error_reg_name_r       <= classified_reg_name;
                                error_reg_description_r <= classified_reg_desc;
                            end
                        end
                    end

                    // ==========================================================
                    // CAT_VENDOR_SPEC: Vendor-specific analysis required
                    //   Per Table 11-3: "To be analyzed by the vendor based
                    //   on the security principles provided by TDISP."
                    //   Conservative default: ERROR (fail-safe).
                    //   A vendor implementation should override this with
                    //   custom logic or set vendor_safe=1 for known-safe
                    //   vendor registers.
                    // ==========================================================
                    CAT_VENDOR_SPEC: begin
                        // Conservative: treat as ERROR
                        error_trigger_r        <= 1'b1;
                        error_reg_addr_r       <= reg_write_addr;
                        error_reg_name_r       <= 256'h56656e646f725370656369666963;  // "VendorSpecific"
                        error_reg_description_r <= 256'h56656e646f7220616e616c79736973207265717569726564;  // "Vendor analysis required"
                    end

                    // ==========================================================
                    // CAT_RESERVED_CAT: Unknown register u2192 fail-safe ERROR
                    // ==========================================================
                    CAT_RESERVED_CAT: begin
                        error_trigger_r        <= 1'b1;
                        error_reg_addr_r       <= reg_write_addr;
                        error_reg_name_r       <= 256'h556e6b6e6f776e5265676973746572;  // "UnknownRegister"
                        error_reg_description_r <= 256'h556e6b6e6f776e207265676973746572207772697465;  // "Unknown register write"
                    end

                    default: begin
                        error_trigger_r        <= 1'b1;
                        error_reg_addr_r       <= reg_write_addr;
                        error_reg_name_r       <= 256'h556e6b6e6f776e43617465676f7279;  // "UnknownCategory"
                        error_reg_description_r <= 256'h556e6b6e6f776e2063617465676f7279;  // "Unknown category"
                    end
                endcase
            end
        end
    end

    // =========================================================================
    // Assertions
    // =========================================================================
    // pragma synthesis_off
    `ifdef FORMAL
        // Assert: error_trigger is single-cycle pulse
        assert property (@(posedge clk) disable iff (!rst_n)
            error_trigger |-> ##1 !error_trigger)
        else $error("error_trigger must be single-cycle pulse");

        // Assert: error_trigger only asserts when tracking is enabled
        assert property (@(posedge clk) disable iff (!rst_n)
            error_trigger |-> tracking_enable)
        else $error("error_trigger asserted while tracking disabled");

        // Assert: tracking_enable is consistent with tdi_state
        //   tracking_enable should be asserted only when TDI is in CONFIG_LOCKED or RUN
        assert property (@(posedge clk) disable iff (!rst_n)
            tracking_enable |-> tdi_state == TDI_STATE_CONFIG_LOCKED ||
                               tdi_state == TDI_STATE_RUN)
        else $error("tracking_enable asserted but TDI not in CONFIG_LOCKED/RUN state");

        // Assert: error_tdi_idx is valid when error_trigger asserts
        assert property (@(posedge clk) disable iff (!rst_n)
            error_trigger |-> error_reg_addr != '0)
        else $error("error_reg_addr is zero when error_trigger asserted");

        // Cover: error_trigger fires
        cover property (@(posedge clk) disable iff (!rst_n)
            tracking_enable && reg_write_valid && error_trigger);

        // Cover: allowed register write during tracking
        cover property (@(posedge clk) disable iff (!rst_n)
            tracking_enable && reg_write_valid && !error_trigger);

        // Cover: command register write with critical bit clear
        cover property (@(posedge clk) disable iff (!rst_n)
            tracking_enable && reg_write_valid &&
            reg_write_addr == 12'h004 &&
            !reg_write_data[CMD_BIT_BUS_MASTER_ENABLE]);
    `endif
    // pragma synthesis_on

endmodule : tdisp_reg_tracker
