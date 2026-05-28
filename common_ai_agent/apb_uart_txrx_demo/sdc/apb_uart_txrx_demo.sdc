# apb_uart_txrx_demo.sdc — generic integration timing constraints
#
# This file intentionally provides bounded placeholder constraints for the
# standalone APB UART demo. SoC/board timing owners must replace the numeric
# values below with integration-specific clock period, APB launch/capture
# budgets, board/package delays, and CDC policy before signoff.

# -----------------------------------------------------------------------------
# Clock
# -----------------------------------------------------------------------------
# Placeholder 100 MHz APB clock. Tighten/relax PCLK_PERIOD_NS to match the
# integrating subsystem; do not treat this value as a board timing claim.
set PCLK_PERIOD_NS 10.000
create_clock -name pclk -period $PCLK_PERIOD_NS [get_ports pclk]

# -----------------------------------------------------------------------------
# Generic APB synchronous interface budgets
# -----------------------------------------------------------------------------
# Conservative placeholder budgets expressed as fractions of pclk. Replace with
# the real upstream/downstream launch/capture budgets for the selected SoC.
set APB_INPUT_DELAY_MAX_NS  [expr {$PCLK_PERIOD_NS * 0.40}]
set APB_INPUT_DELAY_MIN_NS  0.000
set APB_OUTPUT_DELAY_MAX_NS [expr {$PCLK_PERIOD_NS * 0.40}]
set APB_OUTPUT_DELAY_MIN_NS 0.000

set APB_INPUT_PORTS  [get_ports {preset_n psel penable pwrite paddr[*] pwdata[*]}]
set APB_OUTPUT_PORTS [get_ports {prdata[*] pready pslverr irq}]

set_input_delay  -clock pclk -max $APB_INPUT_DELAY_MAX_NS  $APB_INPUT_PORTS
set_input_delay  -clock pclk -min $APB_INPUT_DELAY_MIN_NS  $APB_INPUT_PORTS
set_output_delay -clock pclk -max $APB_OUTPUT_DELAY_MAX_NS $APB_OUTPUT_PORTS
set_output_delay -clock pclk -min $APB_OUTPUT_DELAY_MIN_NS $APB_OUTPUT_PORTS

# -----------------------------------------------------------------------------
# UART serial pins
# -----------------------------------------------------------------------------
# uart_rx is asynchronous to pclk and is synchronized inside the UART RX logic.
# Do not constrain it as a synchronous APB input; cut the external asynchronous
# launch path and verify synchronizer/CDC structure in the implementation flow.
set_false_path -from [get_ports uart_rx]

# uart_tx is launched by pclk but observed by an external asynchronous UART peer.
# This placeholder output delay documents the pin intent only; replace with
# board/package/receiver timing if the integration environment requires it.
set UART_TX_OUTPUT_DELAY_MAX_NS [expr {$PCLK_PERIOD_NS * 0.40}]
set UART_TX_OUTPUT_DELAY_MIN_NS 0.000
set_output_delay -clock pclk -max $UART_TX_OUTPUT_DELAY_MAX_NS [get_ports uart_tx]
set_output_delay -clock pclk -min $UART_TX_OUTPUT_DELAY_MIN_NS [get_ports uart_tx]
