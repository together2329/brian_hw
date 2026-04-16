"""512-bit pattern generators mirroring the SV testbench pattern modes."""

from enum import IntEnum
import config


class PatternMode(IntEnum):
    """Mirrors the SV pattern_mode_e enum."""
    PAT_ZERO        = 0
    PAT_WORD_INDEX  = 1
    PAT_LANE_SWEEP  = 2
    PAT_ALT_TOGGLE  = 3


def build_pattern(mode: PatternMode, base_word: int, offset: int) -> int:
    """Build a DATA_WIDTH-bit word matching the SV build_pattern function.

    Args:
        mode: Pattern mode enum value.
        base_word: Source base word index (word address).
        offset: Word offset within the region.

    Returns:
        Integer representing the DATA_WIDTH-bit pattern value.
    """
    mask32 = (1 << 32) - 1
    result = 0

    for lane in range(config.LANES_PER_WORD):
        if mode == PatternMode.PAT_ZERO:
            lane_val = 0
        elif mode == PatternMode.PAT_WORD_INDEX:
            lane_val = (base_word + offset) & mask32
        elif mode == PatternMode.PAT_LANE_SWEEP:
            lane_val = (lane + offset) & mask32
        elif mode == PatternMode.PAT_ALT_TOGGLE:
            if (base_word + offset + lane) & 1:
                lane_val = 0xAAAA_FFFF
            else:
                lane_val = 0x5555_0000
        else:
            lane_val = 0xDEAD_BEEF

        result |= (lane_val & mask32) << (lane * 32)

    return result & ((1 << config.DATA_WIDTH) - 1)


def build_region(mode: PatternMode, base_word: int, num_words: int) -> list:
    """Build a list of pattern words for an entire region.

    Args:
        mode: Pattern mode.
        base_word: Starting word index.
        num_words: Number of words to generate.

    Returns:
        List of DATA_WIDTH-bit integer values.
    """
    return [build_pattern(mode, base_word, i) for i in range(num_words)]
