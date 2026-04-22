"""
DMA-330 Instruction Decoder Tests
====================================
Tests for dma330_instr_decoder.sv:
  - All instruction opcode decodings
  - Variable-length extraction (1/2/6 byte)
  - Operand fields (reg_select, imm32, imm16, event_num, periph_num, loop_cntr_sel)
  - Invalid encoding -> fault detection
  - Handshake (valid/ready)

RTL notes:
  - instr_len is predicted_len[1:0], so:
      1-byte instructions -> predicted_len=1 -> instr_len=1
      2-byte instructions -> predicted_len=2 -> instr_len=2
      6-byte instructions -> predicted_len=6 -> instr_len=2 (6[1:0]=2)
    (2-byte and 6-byte are indistinguishable by instr_len alone)
  - byte0 = opcode, byte1 = secondary, bytes 2-5 = 32-bit immediate (LE)
"""

import cocotb
from cocotb.triggers import RisingEdge, ReadOnly
from cocotb.clock import Clock

from testbase import ClockReset

# =============================================================================
# Opcode enum values (from dma330_pkg.sv instr_opcode_t)
# =============================================================================
OPC_DMAEND    = 0x00
OPC_DMAKILL   = 0x01
OPC_DMANOP    = 0x02
OPC_DMARMB    = 0x03
OPC_DMAWMB    = 0x04
OPC_DMALD     = 0x10
OPC_DMALDP    = 0x11
OPC_DMALDS    = 0x12
OPC_DMALDPS   = 0x13
OPC_DMAST     = 0x20
OPC_DMASTP    = 0x21
OPC_DMASTS    = 0x22
OPC_DMASTPS   = 0x23
OPC_DMAADDH   = 0x30
OPC_DMAADNH   = 0x31
OPC_DMALP     = 0x32
OPC_DMALPEND  = 0x33
OPC_DMAFLUSHP = 0x34
OPC_DMASEV    = 0x35
OPC_DMAWFE    = 0x36
OPC_DMAMOV    = 0x40
OPC_DMAGO     = 0x41
OPC_INVALID   = 0xFF

# instr_len values as produced by the RTL (encoded, not raw byte count)
# Encoding: 0=1-byte, 1=2-byte, 2=3-byte, 3=6-byte
INSTR_LEN_1BYTE = 0   # encoded value for 1-byte instructions
INSTR_LEN_2BYTE = 1   # encoded value for 2-byte instructions
INSTR_LEN_6BYTE = 3   # encoded value for 6-byte instructions


# =============================================================================
# Helpers
# =============================================================================

async def setup_decoder(dut):
    """Common setup: start clock, reset, clear inputs."""
    cr = ClockReset(dut, clk_name="clk", rst_name="rst_n", period_ns=10)
    cr.start_clock()
    dut.instr_valid.value = 0
    dut.instr_bytes.value = 0
    dut.instr_bytes_cnt.value = 0
    dut.decoded_ready.value = 1  # Always ready to accept
    dut.current_pc.value = 0x1000
    await cr.reset()
    return cr


async def decode_one(dut, instr_bytes, byte_count):
    """Feed an instruction and wait for decode.

    decoded_instr_t packed struct layout (71 bits, MSB-first):
      bit  70       : valid          (1 bit)
      bit  69       : fault          (1 bit)
      bits 68:61    : opcode         (8 bits)
      bits 60:59    : instr_len      (2 bits)
      bits 58:57    : reg_select     (2 bits)
      bits 56:25    : imm32          (32 bits)
      bits 24:9     : imm16          (16 bits)
      bit  8        : loop_cntr_sel  (1 bit)
      bits 7:4      : periph_num     (4 bits)
      bits 3:0      : event_num      (4 bits)
    """
    dut.instr_bytes.value = instr_bytes
    dut.instr_bytes_cnt.value = byte_count
    dut.instr_valid.value = 1
    dut.decoded_ready.value = 1

    # Wait for decoded_valid
    for _ in range(20):
        await RisingEdge(dut.clk)
        await ReadOnly()
        if dut.decoded_valid.value:
            break
    else:
        cocotb.log.error(
            f"decode_one TIMEOUT: decoded_valid=0, "
            f"instr_valid={dut.instr_valid.value}, "
            f"instr_ready={dut.instr_ready.value}"
        )
        assert False, "decode_one timed out waiting for decoded_valid"

    # Read decoded output as a flat integer (packed struct)
    raw = int(dut.decoded_o.value)
    cocotb.log.info(f"DECODED raw=0x{raw:018x}, decoded_valid=1")

    result = {
        'valid':         (raw >> 70) & 0x1,
        'fault':         (raw >> 69) & 0x1,
        'opcode':        (raw >> 61) & 0xFF,
        'instr_len':     (raw >> 59) & 0x3,
        'reg_select':    (raw >> 57) & 0x3,
        'imm32':         (raw >> 25) & 0xFFFFFFFF,
        'imm16':         (raw >> 9)  & 0xFFFF,
        'loop_cntr_sel': (raw >> 8)  & 0x1,
        'periph_num':    (raw >> 4)  & 0xF,
        'event_num':     (raw >> 0)  & 0xF,
    }

    # Exit ReadOnly phase before writing signals
    await RisingEdge(dut.clk)
    # Now safe to write
    dut.instr_valid.value = 0
    # Drain - wait for FSM to return to IDLE
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    return result


def make_6byte(opcode, byte1, imm32):
    """Pack a 6-byte instruction (little-endian bytes 2-5 for imm32)."""
    b0 = opcode
    b1 = byte1 & 0xFF
    b2 = imm32 & 0xFF
    b3 = (imm32 >> 8) & 0xFF
    b4 = (imm32 >> 16) & 0xFF
    b5 = (imm32 >> 24) & 0xFF
    return (b5 << 40) | (b4 << 32) | (b3 << 24) | (b2 << 16) | (b1 << 8) | b0


def make_2byte(opcode, byte1):
    """Pack a 2-byte instruction."""
    return ((byte1 & 0xFF) << 8) | (opcode & 0xFF)


# =============================================================================
# Test 1: All 1-byte instructions
# =============================================================================
@cocotb.test(timeout_time=100, timeout_unit="us")
async def test_01_one_byte_instrs(dut):
    """Test all 1-byte instruction decodings."""
    cr = await setup_decoder(dut)

    # DMAEND (0x00)
    r = await decode_one(dut, 0x00, 1)
    assert r['opcode'] == OPC_DMAEND,  f"DMAEND: opcode=0x{r['opcode']:02x}, expected 0x{OPC_DMAEND:02x}"
    assert r['instr_len'] == INSTR_LEN_1BYTE, f"DMAEND: instr_len={r['instr_len']}"
    assert r['valid'],     f"DMAEND: valid={r['valid']}"
    assert not r['fault'], f"DMAEND: fault={r['fault']}"

    # DMAKILL (0x01)
    r = await decode_one(dut, 0x01, 1)
    assert r['opcode'] == OPC_DMAKILL, f"DMAKILL: opcode=0x{r['opcode']:02x}"
    assert r['instr_len'] == INSTR_LEN_1BYTE
    assert not r['fault']

    # DMANOP (0x18)
    r = await decode_one(dut, 0x18, 1)
    assert r['opcode'] == OPC_DMANOP,  f"DMANOP: opcode=0x{r['opcode']:02x}"
    assert r['instr_len'] == INSTR_LEN_1BYTE
    assert not r['fault']

    # DMARMB (0x12)
    r = await decode_one(dut, 0x12, 1)
    assert r['opcode'] == OPC_DMARMB,  f"DMARMB: opcode=0x{r['opcode']:02x}"
    assert r['instr_len'] == INSTR_LEN_1BYTE
    assert not r['fault']

    # DMAWMB (0x13)
    r = await decode_one(dut, 0x13, 1)
    assert r['opcode'] == OPC_DMAWMB,  f"DMAWMB: opcode=0x{r['opcode']:02x}"
    assert r['instr_len'] == INSTR_LEN_1BYTE
    assert not r['fault']

    # DMALD (0x04)
    r = await decode_one(dut, 0x04, 1)
    assert r['opcode'] == OPC_DMALD,   f"DMALD: opcode=0x{r['opcode']:02x}"
    assert r['instr_len'] == INSTR_LEN_1BYTE
    assert not r['fault']

    # DMAST (0x08)
    r = await decode_one(dut, 0x08, 1)
    assert r['opcode'] == OPC_DMAST,   f"DMAST: opcode=0x{r['opcode']:02x}"
    assert r['instr_len'] == INSTR_LEN_1BYTE
    assert not r['fault']

    # DMALD ns-bit (0x05) — should still decode as DMALD
    r = await decode_one(dut, 0x05, 1)
    assert r['opcode'] == OPC_DMALD,   f"DMALD(ns): opcode=0x{r['opcode']:02x}"

    # DMAST ns-bit (0x09)
    r = await decode_one(dut, 0x09, 1)
    assert r['opcode'] == OPC_DMAST,   f"DMAST(ns): opcode=0x{r['opcode']:02x}"

    # DMALDS (0x0C)
    r = await decode_one(dut, 0x0C, 1)
    assert r['opcode'] == OPC_DMALDS,  f"DMALDS: opcode=0x{r['opcode']:02x}"

    # DMASTS (0x0E)
    r = await decode_one(dut, 0x0E, 1)
    assert r['opcode'] == OPC_DMASTS,  f"DMASTS: opcode=0x{r['opcode']:02x}"


# =============================================================================
# Test 2: DMALDP (0x24) — 2-byte with periph_num
# =============================================================================
@cocotb.test(timeout_time=50, timeout_unit="us")
async def test_02_dmaldp(dut):
    """DMALDP: 2-byte, extracts periph_num from byte1[3:0]."""
    cr = await setup_decoder(dut)

    for periph in [0, 1, 5, 15]:
        instr = make_2byte(0x24, periph)
        r = await decode_one(dut, instr, 2)
        assert r['opcode'] == OPC_DMALDP,  f"DMALDP periph={periph}: opcode=0x{r['opcode']:02x}"
        assert r['instr_len'] == INSTR_LEN_2BYTE
        assert r['periph_num'] == periph,   f"DMALDP: periph_num={r['periph_num']}, expected {periph}"
        assert not r['fault']

    # ns-bit variant (0x25)
    instr = make_2byte(0x25, 3)
    r = await decode_one(dut, instr, 2)
    assert r['opcode'] == OPC_DMALDP
    assert r['periph_num'] == 3


# =============================================================================
# Test 3: DMASTP (0x28) — 2-byte with periph_num
# =============================================================================
@cocotb.test(timeout_time=50, timeout_unit="us")
async def test_03_dmastp(dut):
    """DMASTP: 2-byte, extracts periph_num from byte1[3:0]."""
    cr = await setup_decoder(dut)

    for periph in [0, 2, 7, 15]:
        instr = make_2byte(0x28, periph)
        r = await decode_one(dut, instr, 2)
        assert r['opcode'] == OPC_DMASTP,  f"DMASTP periph={periph}: opcode=0x{r['opcode']:02x}"
        assert r['instr_len'] == INSTR_LEN_2BYTE
        assert r['periph_num'] == periph,   f"DMASTP: periph_num={r['periph_num']}, expected {periph}"
        assert not r['fault']


# =============================================================================
# Test 4: DMAMOV (0xBC) — 6-byte with reg_select + imm32
# =============================================================================
@cocotb.test(timeout_time=50, timeout_unit="us")
async def test_04_dmamov(dut):
    """DMAMOV: 6-byte, extracts reg_select from byte1[1:0] and imm32 from bytes 2-5."""
    cr = await setup_decoder(dut)

    # DMAMOV DA, 0x12345678:
    # byte0=0xBC, byte1[1:0]=01(DA), byte2..5=0x12345678 (LE)
    imm32 = 0x12345678
    instr = make_6byte(0xBC, 0x01, imm32)  # byte1=0x01 → reg_select=1 (DA)
    r = await decode_one(dut, instr, 6)
    assert r['opcode'] == OPC_DMAMOV,     f"DMAMOV: opcode=0x{r['opcode']:02x}"
    assert r['instr_len'] == INSTR_LEN_6BYTE, f"DMAMOV: instr_len={r['instr_len']}, expected {INSTR_LEN_6BYTE}"
    assert r['reg_select'] == 1,           f"DMAMOV: reg_select={r['reg_select']}, expected 1(DA)"
    assert r['imm32'] == imm32,            f"DMAMOV: imm32=0x{r['imm32']:08x}, expected 0x{imm32:08x}"
    assert not r['fault']

    # DMAMOV SA, 0xDEADBEEF: byte1[1:0]=00(SA)
    imm32 = 0xDEADBEEF
    instr = make_6byte(0xBC, 0x00, imm32)
    r = await decode_one(dut, instr, 6)
    assert r['opcode'] == OPC_DMAMOV
    assert r['reg_select'] == 0,           f"DMAMOV SA: reg_select={r['reg_select']}"
    assert r['imm32'] == imm32

    # DMAMOV CC, 0x00000001: byte1[1:0]=10(CC)
    imm32 = 0x00000001
    instr = make_6byte(0xBC, 0x02, imm32)
    r = await decode_one(dut, instr, 6)
    assert r['opcode'] == OPC_DMAMOV
    assert r['reg_select'] == 2,           f"DMAMOV CC: reg_select={r['reg_select']}"
    assert r['imm32'] == imm32


# =============================================================================
# Test 5: DMAADDH (0x54) — 2-byte with reg_select + imm
# =============================================================================
@cocotb.test(timeout_time=50, timeout_unit="us")
async def test_05_dmaaddh(dut):
    """DMAADDH: 2-byte, byte1[7]=reg(SA=1/DA=0), byte1[6:0]=7-bit imm."""
    cr = await setup_decoder(dut)

    # DMAADDH SA, 0x5A: byte1[7]=1(SA), byte1[6:0]=0x5A
    imm_val = 0x5A
    byte1 = 0x80 | imm_val   # bit7=1 -> SA
    instr = make_2byte(0x54, byte1)
    r = await decode_one(dut, instr, 2)
    assert r['opcode'] == OPC_DMAADDH,    f"DMAADDH: opcode=0x{r['opcode']:02x}"
    assert r['instr_len'] == INSTR_LEN_2BYTE
    # RTL: reg_select = byte1[7] ? 0 : 1 → SA → 0
    assert r['reg_select'] == 0,           f"DMAADDH SA: reg_select={r['reg_select']}"
    assert r['imm16'] == imm_val,          f"DMAADDH: imm16=0x{r['imm16']:04x}, expected 0x{imm_val:04x}"
    assert not r['fault']

    # DMAADDH DA, 0x7F: byte1[7]=0(DA), byte1[6:0]=0x7F
    imm_val = 0x7F
    byte1 = 0x00 | imm_val   # bit7=0 -> DA
    instr = make_2byte(0x54, byte1)
    r = await decode_one(dut, instr, 2)
    assert r['opcode'] == OPC_DMAADDH
    assert r['reg_select'] == 1,           f"DMAADDH DA: reg_select={r['reg_select']}"
    assert r['imm16'] == imm_val


# =============================================================================
# Test 6: DMAADNH (0x5C) — 2-byte subtract
# =============================================================================
@cocotb.test(timeout_time=50, timeout_unit="us")
async def test_06_dmaadnh(dut):
    """DMAADNH: 2-byte subtract, byte1[7]=reg, byte1[6:0]=imm."""
    cr = await setup_decoder(dut)

    # DMAADNH DA, 0x33: byte1[7]=0 -> DA
    imm_val = 0x33
    byte1 = 0x00 | imm_val
    instr = make_2byte(0x5C, byte1)
    r = await decode_one(dut, instr, 2)
    assert r['opcode'] == OPC_DMAADNH,    f"DMAADNH: opcode=0x{r['opcode']:02x}"
    assert r['instr_len'] == INSTR_LEN_2BYTE
    assert r['reg_select'] == 1,           f"DMAADNH DA: reg_select={r['reg_select']}"
    assert r['imm16'] == imm_val

    # DMAADNH SA, 0x01: byte1[7]=1 -> SA
    imm_val = 0x01
    byte1 = 0x80 | imm_val
    instr = make_2byte(0x5C, byte1)
    r = await decode_one(dut, instr, 2)
    assert r['opcode'] == OPC_DMAADNH
    assert r['reg_select'] == 0
    assert r['imm16'] == imm_val


# =============================================================================
# Test 7: DMALP (0x20/0x22) — 2-byte with loop_cntr_sel + imm
# =============================================================================
@cocotb.test(timeout_time=50, timeout_unit="us")
async def test_07_dmalp(dut):
    """DMALP: 2-byte, loop counter select and iteration count."""
    cr = await setup_decoder(dut)

    # DMALP LC0, 100 iterations: byte0=0x20, byte1=100
    instr = make_2byte(0x20, 100)
    r = await decode_one(dut, instr, 2)
    assert r['opcode'] == OPC_DMALP,      f"DMALP: opcode=0x{r['opcode']:02x}"
    assert r['instr_len'] == INSTR_LEN_2BYTE
    assert r['loop_cntr_sel'] == 0,        f"DMALP LC0: loop_cntr_sel={r['loop_cntr_sel']}"
    assert r['imm16'] == 100,              f"DMALP: imm16={r['imm16']}"

    # DMALP LC1, 50 iterations: byte0=0x22, byte1=50
    instr = make_2byte(0x22, 50)
    r = await decode_one(dut, instr, 2)
    assert r['opcode'] == OPC_DMALP
    assert r['loop_cntr_sel'] == 1,        f"DMALP LC1: loop_cntr_sel={r['loop_cntr_sel']}"
    assert r['imm16'] == 50


# =============================================================================
# Test 8: DMALPEND (0x21/0x23/0x31/0x33) — 2-byte loop end
# =============================================================================
@cocotb.test(timeout_time=50, timeout_unit="us")
async def test_08_dmalpend(dut):
    """DMALPEND: 2-byte, loop end with backward jump offset."""
    cr = await setup_decoder(dut)

    # DMALPEND LC0, offset=8: byte0=0x21, byte1=8
    instr = make_2byte(0x21, 8)
    r = await decode_one(dut, instr, 2)
    assert r['opcode'] == OPC_DMALPEND,   f"DMALPEND: opcode=0x{r['opcode']:02x}"
    assert r['instr_len'] == INSTR_LEN_2BYTE
    assert r['loop_cntr_sel'] == 0,        f"DMALPEND LC0: loop_cntr_sel={r['loop_cntr_sel']}"
    assert r['imm16'] == 8

    # DMALPEND LC1, offset=16: byte0=0x23, byte1=16
    instr = make_2byte(0x23, 16)
    r = await decode_one(dut, instr, 2)
    assert r['opcode'] == OPC_DMALPEND
    assert r['loop_cntr_sel'] == 1
    assert r['imm16'] == 16

    # Forever variants: 0x31 (LC0) and 0x33 (LC1)
    instr = make_2byte(0x31, 4)
    r = await decode_one(dut, instr, 2)
    assert r['opcode'] == OPC_DMALPEND,   f"DMALPEND forever LC0: opcode=0x{r['opcode']:02x}"
    assert r['loop_cntr_sel'] == 0        # 0x31 bit[1] = 0

    instr = make_2byte(0x33, 4)
    r = await decode_one(dut, instr, 2)
    assert r['opcode'] == OPC_DMALPEND
    assert r['loop_cntr_sel'] == 1        # 0x33 bit[1] = 1


# =============================================================================
# Test 9: DMASEV (0x34) — 2-byte with event_num
# =============================================================================
@cocotb.test(timeout_time=50, timeout_unit="us")
async def test_09_dmasev(dut):
    """DMASEV: 2-byte, event number from byte1[3:0]."""
    cr = await setup_decoder(dut)

    for evt in [0, 1, 7, 15]:
        instr = make_2byte(0x34, evt)
        r = await decode_one(dut, instr, 2)
        assert r['opcode'] == OPC_DMASEV,  f"DMASEV evt={evt}: opcode=0x{r['opcode']:02x}"
        assert r['instr_len'] == INSTR_LEN_2BYTE
        assert r['event_num'] == evt,       f"DMASEV: event_num={r['event_num']}, expected {evt}"


# =============================================================================
# Test 10: DMAWFE (0x36) — 2-byte with event_num
# =============================================================================
@cocotb.test(timeout_time=50, timeout_unit="us")
async def test_10_dmawfe(dut):
    """DMAWFE: 2-byte, wait for event."""
    cr = await setup_decoder(dut)

    for evt in [0, 3, 7, 15]:
        instr = make_2byte(0x36, evt)
        r = await decode_one(dut, instr, 2)
        assert r['opcode'] == OPC_DMAWFE,  f"DMAWFE evt={evt}: opcode=0x{r['opcode']:02x}"
        assert r['instr_len'] == INSTR_LEN_2BYTE
        assert r['event_num'] == evt,       f"DMAWFE: event_num={r['event_num']}, expected {evt}"


# =============================================================================
# Test 11: DMAFLUSHP (0x35) — 2-byte with periph_num
# =============================================================================
@cocotb.test(timeout_time=50, timeout_unit="us")
async def test_11_dmaflushp(dut):
    """DMAFLUSHP: 2-byte, peripheral flush."""
    cr = await setup_decoder(dut)

    for periph in [0, 2, 5, 15]:
        instr = make_2byte(0x35, periph)
        r = await decode_one(dut, instr, 2)
        assert r['opcode'] == OPC_DMAFLUSHP, f"DMAFLUSHP periph={periph}: opcode=0x{r['opcode']:02x}"
        assert r['instr_len'] == INSTR_LEN_2BYTE
        assert r['periph_num'] == periph,     f"DMAFLUSHP: periph_num={r['periph_num']}, expected {periph}"


# =============================================================================
# Test 12: DMAGO (0xA0) — 6-byte manager instruction
# =============================================================================
@cocotb.test(timeout_time=50, timeout_unit="us")
async def test_12_dmago(dut):
    """DMAGO: 6-byte, start channel. byte1[5:3]=channel, bytes 2-5=start PC."""
    cr = await setup_decoder(dut)

    # DMAGO channel 2, start_addr=0xABCD0000
    # byte1[5:3]=010=channel 2, byte1[0]=ns=0 → byte1 = 0x10
    ch = 2
    start_addr = 0xABCD0000
    byte1 = (ch << 3)  # channel in bits [5:3]
    instr = make_6byte(0xA0, byte1, start_addr)
    r = await decode_one(dut, instr, 6)
    assert r['opcode'] == OPC_DMAGO,      f"DMAGO: opcode=0x{r['opcode']:02x}"
    assert r['instr_len'] == INSTR_LEN_6BYTE
    # RTL: periph_num = byte1[5:3] = channel number
    assert r['periph_num'] == ch,          f"DMAGO: periph_num(ch)={r['periph_num']}, expected {ch}"
    assert r['imm32'] == start_addr,       f"DMAGO: imm32=0x{r['imm32']:08x}, expected 0x{start_addr:08x}"

    # DMAGO channel 0, start_addr=0x00000100
    ch = 0
    start_addr = 0x00000100
    byte1 = (ch << 3)
    instr = make_6byte(0xA0, byte1, start_addr)
    r = await decode_one(dut, instr, 6)
    assert r['opcode'] == OPC_DMAGO
    assert r['periph_num'] == ch
    assert r['imm32'] == start_addr


# =============================================================================
# Test 13: Invalid encoding -> fault
# =============================================================================
@cocotb.test(timeout_time=50, timeout_unit="us")
async def test_13_invalid_encoding(dut):
    """Invalid opcode byte -> fault=1, valid=1."""
    cr = await setup_decoder(dut)

    # Try several unallocated opcodes
    for bad_byte in [0xFF, 0xEE, 0x10, 0x80, 0x50]:
        r = await decode_one(dut, bad_byte, 1)
        assert r['fault'] == 1,  f"Invalid 0x{bad_byte:02x}: fault={r['fault']}, expected 1"
        assert r['valid'] == 1,  f"Invalid 0x{bad_byte:02x}: valid={r['valid']}, expected 1 (fault still valid)"
        assert r['opcode'] == OPC_INVALID, f"Invalid 0x{bad_byte:02x}: opcode=0x{r['opcode']:02x}"


# =============================================================================
# Test 14: Handshake — instr_valid/decoded_valid/decoded_ready
# =============================================================================
@cocotb.test(timeout_time=100, timeout_unit="us")
async def test_14_handshake(dut):
    """Verify valid/ready handshake protocol."""
    cr = await setup_decoder(dut)

    # With instr_valid=0, decoded_valid should be 0
    dut.decoded_ready.value = 1
    dut.instr_valid.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert not dut.decoded_valid.value, "decoded_valid should be 0 when instr_valid=0"

    # Exit ReadOnly before writing
    await RisingEdge(dut.clk)
    # Feed instruction with decoded_ready=1
    dut.instr_bytes.value = 0x00  # DMAEND
    dut.instr_bytes_cnt.value = 1
    dut.instr_valid.value = 1
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert dut.decoded_valid.value, "decoded_valid should be 1 after valid instruction"

    # Exit ReadOnly, accept it (decoded_ready=1 already)
    await RisingEdge(dut.clk)
    dut.instr_valid.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert not dut.decoded_valid.value, "decoded_valid should be 0 after acceptance"

    # Exit ReadOnly, test back-pressure: hold decoded_ready=0
    await RisingEdge(dut.clk)
    dut.decoded_ready.value = 0
    dut.instr_bytes.value = 0x18  # DMANOP
    dut.instr_bytes_cnt.value = 1
    dut.instr_valid.value = 1
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert dut.decoded_valid.value, "decoded_valid should be 1 while waiting for ready"

    # Wait a cycle with ready still low
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert dut.decoded_valid.value, "decoded_valid should remain 1 until ready"

    # Exit ReadOnly, release back-pressure
    await RisingEdge(dut.clk)
    dut.decoded_ready.value = 1
    dut.instr_valid.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert not dut.decoded_valid.value, "decoded_valid should clear after ready=1"


# =============================================================================
# Test 15: instr_ready reflects FSM state
# =============================================================================
@cocotb.test(timeout_time=100, timeout_unit="us")
async def test_15_instr_ready(dut):
    """Verify instr_ready is asserted in IDLE/COLLECTING, deasserted in READY."""
    cr = await setup_decoder(dut)

    # In IDLE: instr_ready should be 1
    dut.instr_valid.value = 0
    dut.decoded_ready.value = 1
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert dut.instr_ready.value, "instr_ready should be 1 in IDLE"

    # Exit ReadOnly before writing
    await RisingEdge(dut.clk)
    # Send a 1-byte instruction: goes to READY in 1 cycle
    dut.instr_bytes.value = 0x00
    dut.instr_bytes_cnt.value = 1
    dut.instr_valid.value = 1
    await RisingEdge(dut.clk)
    await ReadOnly()
    # Now in READY state — instr_ready should be 0
    assert not dut.instr_ready.value, "instr_ready should be 0 in READY state"

    # Exit ReadOnly before writing
    await RisingEdge(dut.clk)
    # Clear it
    dut.instr_valid.value = 0
    dut.decoded_ready.value = 1
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)


# =============================================================================
# Test 16: Consecutive instruction decodes
# =============================================================================
@cocotb.test(timeout_time=100, timeout_unit="us")
async def test_16_consecutive_decodes(dut):
    """Verify back-to-back instruction decoding works correctly."""
    cr = await setup_decoder(dut)

    # Decode several instructions in sequence without gaps
    test_cases = [
        # (byte_encoding, byte_count, expected_opcode, expected_instr_len)
        (0x00, 1, OPC_DMAEND,  INSTR_LEN_1BYTE),
        (0x18, 1, OPC_DMANOP,  INSTR_LEN_1BYTE),
        (make_2byte(0x34, 5), 2, OPC_DMASEV, INSTR_LEN_2BYTE),
        (0x04, 1, OPC_DMALD,   INSTR_LEN_1BYTE),
        (make_6byte(0xBC, 0x00, 0xCAFEBABE), 6, OPC_DMAMOV, INSTR_LEN_6BYTE),
    ]

    for i, (instr, cnt, exp_opc, exp_len) in enumerate(test_cases):
        r = await decode_one(dut, instr, cnt)
        assert r['opcode'] == exp_opc, \
            f"Instr #{i}: opcode=0x{r['opcode']:02x}, expected 0x{exp_opc:02x}"
        assert r['instr_len'] == exp_len, \
            f"Instr #{i}: instr_len={r['instr_len']}, expected {exp_len}"
        assert r['valid'] and not r['fault'], \
            f"Instr #{i}: valid={r['valid']}, fault={r['fault']}"
