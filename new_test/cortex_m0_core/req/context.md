# Cortex-M0 Core — Module Context

## Module Name
`cortex_m0_core`

## Purpose
A 32-bit CPU core implementing a subset of the ARMv6-M instruction set architecture,
inspired by the ARM Cortex-M0. Designed as a minimal, area-optimized embedded processor
suitable for IoT, sensor hubs, and microcontroller applications.

## SoC Position
- **Bus Interface:** AHB-Lite (AHB5 subset) — matches real Cortex-M0 bus
- **Role:** Processor core (bus master) — drives instruction fetches and data accesses
- **Integration:** Standalone initially; integrates into SoC as AHB-Lite master

## Technology
- Technology-independent RTL (SystemVerilog)
- Portable across FPGA and ASIC targets
- No technology-specific primitives

## Key Characteristics
| Feature              | Value                          |
|----------------------|--------------------------------|
| Architecture         | ARMv6-M (subset)               |
| Data Width           | 32-bit                         |
| Address Space        | 4 GB (32-bit addressing)       |
| Pipeline             | 3-stage (Fetch, Decode, Execute) |
| Bus Protocol         | AHB-Lite                       |
| Interrupts           | NVIC (Nested Vectored Interrupt Controller) |
| Endianness           | Little-endian                  |
| Registers            | R0-R12, SP (MSP/PSP), LR, PC, xPSR |

## References
- ARMv6-M Architecture Reference Manual
- Cortex-M0 Technical Reference Manual
