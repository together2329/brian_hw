"""Reusable cocotb protocol monitors driven by derived IP contracts.

The helpers here stay protocol-shaped but IP-neutral.  Generated or hand-written
cocotb tests pass DUT signal handles and expected timing from the per-IP SSOT /
ip_contract instead of selecting a fixed profile.
"""

from __future__ import annotations

from typing import Any


def as_int(value: Any) -> int:
    """Return a cocotb signal-like value as an integer."""

    return int(value.value)


async def sample_signal_hold(clk: Any, signals: dict[str, Any], *, cycles: int, settle_ns: int = 1) -> dict[str, list[int]]:
    """Sample named signals for a fixed number of core-clock cycles."""

    from cocotb.triggers import RisingEdge, Timer

    samples = {name: [] for name in signals}
    for _ in range(cycles):
        await RisingEdge(clk)
        await Timer(settle_ns, units="ns")
        for name, signal in signals.items():
            samples[name].append(as_int(signal))
    return samples


async def capture_clocked_serial_frame(
    clk: Any,
    serial_clk: Any,
    data: Any,
    *,
    idle_level: int,
    select_signal: Any | None = None,
    select_active_level: int = 0,
    done_signal: Any | None = None,
    max_cycles: int = 512,
    settle_ns: int = 1,
) -> dict[str, Any]:
    """Capture data bits on active serial-clock edges.

    The active edge is defined generically as leaving the clock idle level.  For
    SPI mode 0 this is the rising edge; for mode 2 this is the falling edge.
    """

    from cocotb.triggers import RisingEdge, Timer

    await Timer(settle_ns, units="ns")
    idle = int(idle_level) & 1
    prev_clk = as_int(serial_clk)
    serial_bits: list[int] = []
    sample_edge_cycles: list[int] = []
    select_samples_at_edges: list[int] = []
    done_cycle = None

    for cycle in range(1, max_cycles + 1):
        await RisingEdge(clk)
        await Timer(settle_ns, units="ns")
        current_clk = as_int(serial_clk)
        if prev_clk == idle and current_clk != idle:
            serial_bits.append(as_int(data))
            sample_edge_cycles.append(cycle)
            if select_signal is not None:
                select_samples_at_edges.append(as_int(select_signal))
        if done_signal is not None and as_int(done_signal):
            done_cycle = cycle
            break
        prev_clk = current_clk

    if done_signal is not None and done_cycle is None:
        raise AssertionError("done_signal did not assert while capturing clocked serial frame")

    result: dict[str, Any] = {
        "serial_bits": serial_bits,
        "sample_edge_cycles": sample_edge_cycles,
    }
    if select_signal is not None:
        result["select_samples_at_edges"] = select_samples_at_edges
        result["select_active_level"] = int(select_active_level) & 1
    if done_signal is not None:
        result["done_cycle"] = done_cycle
    return result


async def capture_uart_tx_frame(
    clk: Any,
    tx: Any,
    *,
    bit_cycles: int,
    data_bits: int = 8,
    stop_bits: int = 1,
    lsb_first: bool = True,
    done_signal: Any | None = None,
    max_cycles: int = 1024,
    settle_ns: int = 1,
) -> dict[str, Any]:
    """Capture a single UART TX frame from an already-idle serial line.

    The monitor waits for the start bit (`tx == 0`), then samples data and stop
    bits at integer bit-cycle boundaries.  This matches the bounded synchronous
    UART demos used by the workflow while keeping the observation contract
    explicit in the scoreboard evidence.
    """

    from cocotb.triggers import RisingEdge, Timer

    if bit_cycles <= 0:
        raise ValueError("bit_cycles must be positive")
    if data_bits <= 0:
        raise ValueError("data_bits must be positive")
    if stop_bits <= 0:
        raise ValueError("stop_bits must be positive")

    await Timer(settle_ns, units="ns")
    start_cycle = 0 if as_int(tx) == 0 else None
    observed: dict[int, int] = {}
    done_cycle = None

    for cycle in range(1, max_cycles + 1):
        await RisingEdge(clk)
        await Timer(settle_ns, units="ns")
        value = as_int(tx)
        if start_cycle is None and value == 0:
            start_cycle = cycle
        if start_cycle is None:
            continue

        rel = cycle - start_cycle
        observed[rel] = value
        if done_signal is not None and as_int(done_signal):
            done_cycle = rel
            break

        last_required_sample = bit_cycles * (1 + data_bits + stop_bits)
        if done_signal is None and rel >= last_required_sample:
            break

    if start_cycle is None:
        raise AssertionError("UART start bit was not observed")
    if done_signal is not None and done_cycle is None:
        raise AssertionError("done_signal did not assert while capturing UART frame")

    data_sample_cycles = [bit_cycles * (index + 1) for index in range(data_bits)]
    stop_sample_cycles = [bit_cycles * (data_bits + 1 + index) for index in range(stop_bits)]
    captured_bits = [observed.get(cycle) for cycle in data_sample_cycles]
    captured_stop = [observed.get(cycle) for cycle in stop_sample_cycles]
    if any(bit is None for bit in captured_bits):
        raise AssertionError("UART frame ended before all data bits were sampled")
    if any(bit is None for bit in captured_stop):
        raise AssertionError("UART frame ended before all stop bits were sampled")

    bits = [int(bit) for bit in captured_bits]
    if lsb_first:
        value = sum(bit << index for index, bit in enumerate(bits))
    else:
        value = 0
        for bit in bits:
            value = (value << 1) | bit

    result: dict[str, Any] = {
        "start_bit": 0,
        "data_bits": bits,
        "stop_bits": [int(bit) for bit in captured_stop],
        "data_value": value,
        "data_sample_cycles": data_sample_cycles,
        "stop_sample_cycles": stop_sample_cycles,
    }
    if done_signal is not None:
        result["done_cycle"] = done_cycle
    return result
