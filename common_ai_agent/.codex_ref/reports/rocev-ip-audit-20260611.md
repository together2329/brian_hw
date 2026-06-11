# ROCEV IP Audit

| IP | Validation | Key evidence | Gaps |
|---|---|---|---|
| `pwm_gen_cx1` | partial | rtl_compile:pass, lint:pass, simulation:pass, coverage:blocked, scoreboard:18 rows, waveform | coverage is blocked |
| `fifo_sync_cx1` | partial | rtl_compile:pass, lint:pass, simulation:pass, coverage:blocked, signoff:fail, scoreboard:14 rows, waveform | scoreboard has failed rows; coverage is blocked |
| `counter8_cx1` | partial | rtl_compile:pass, lint:pass, simulation:pass, signoff:pass, scoreboard:15 rows | coverage is missing |
| `debounce_cx1` | partial | rtl_compile:pass, lint:pass, simulation:pass, coverage:pass, scoreboard:21 rows, waveform | scoreboard has failed rows |
| `edge_det_cx1` | partial | rtl_compile:pass, lint:pass, simulation:pass, coverage:blocked, signoff:fail, scoreboard:19 rows, waveform | scoreboard has failed rows; coverage is blocked |
| `gray_code_cx1` | partial | rtl_compile:pass, lint:pass, simulation:pass, coverage:blocked, signoff:fail, scoreboard:12 rows, waveform | scoreboard has failed rows; coverage is blocked |
| `parity_gen_cx1` | partial | rtl_compile:pass, lint:pass, simulation:pass, coverage:blocked, signoff:fail, scoreboard:21 rows, waveform | scoreboard has failed rows; coverage is blocked |
| `shift_reg_cx1` | partial | rtl_compile:pass, lint:pass, simulation:pass, signoff:pass, scoreboard:25 rows | coverage is missing |
| `uart_tx_lite_cx1` | partial | rtl_compile:pass, lint:pass, simulation:pass, signoff:pass, scoreboard:6 rows, waveform | coverage is missing |
| `watchdog_cx1` | partial | rtl_compile:pass, lint:pass, simulation:pass, signoff:pass, scoreboard:9 rows, waveform | coverage is missing |
| `mctp_assembler_v3` | partial | rtl_compile:pass, lint:pass, simulation:pass, coverage:pass, signoff:pass, scoreboard:106 rows, waveform, formal:optional_not_run | missing obligations.json |
