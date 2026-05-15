module gray_counter #(
    parameter integer WIDTH = 4,
    parameter integer CLOCK_FREQ_MHZ = 200
) (
    input  logic             clk,
    input  logic             rst_n,
    input  logic             enable,
    input  logic             clear,
    output logic [WIDTH-1:0] gray_value,
    output logic [WIDTH-1:0] bin_value,
    output logic             done
);

    // Keep SSOT timing parameter in the synthesizable contract surface.
    // This binds timing intent to the top integration interface even though
    // the core behavior is functionally independent of clock frequency.
    localparam integer TOP_CLOCK_FREQ_MHZ = CLOCK_FREQ_MHZ;

    // Width-safe self-reference prevents lint UNUSED warnings for
    // TOP_CLOCK_FREQ_MHZ while preserving zero functional impact.
    logic unused_clock_freq_ref;
    assign unused_clock_freq_ref = (TOP_CLOCK_FREQ_MHZ == TOP_CLOCK_FREQ_MHZ);

    // Top-level integration shell: direct one-to-one wiring from SSOT
    // io_list/integration contracts into the manifest-owned core.
    gray_counter_core #(
        .WIDTH(WIDTH)
    ) u_gray_counter_core (
        .clk       (clk),
        .rst_n     (rst_n),
        .enable    (enable),
        .clear     (clear),
        .gray_value(gray_value),
        .bin_value (bin_value),
        .done      (done)
    );

endmodule
