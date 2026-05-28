"""SSOT Q&A board helpers — extracted from src/atlas_ui.py.

Phase 10 of refactor/atlas-modular: start the Q&A cluster extraction. PoC
moves the section-key→label mapping and the lookup function. Subsequent
phases (10b, 10c, …) will move the larger helpers (load/save/upsert/view)
once the file-IO deps are factored cleanly.
"""
from __future__ import annotations

from typing import Tuple

# Maps an SSOT decision key (e.g. "purpose", "register_map") to a stable
# (section_id, display_label) pair used by the Q&A board grouping UI.
_SSOT_QA_SECTIONS: dict = {
    "purpose": ("00_overview", "0. Overview / Intent"),
    "parameters": ("01_parameters", "1. Parameters"),
    "clock_reset": ("02_clock_reset", "2. Clock / Reset"),
    "bus_interface": ("03_interface", "3. Interface"),
    "submodule_structure": ("04_architecture", "4. Architecture / Decomposition"),
    "memory_map": ("05_memory", "5. Memory / Buffering"),
    "register_map": ("06_registers", "6. Register Map"),
    "interrupt": ("07_interrupt_error", "7. Interrupt / Error Policy"),
    "test_expectation": ("18_verification", "18. Verification / Gates"),
}


def _ssot_qa_section(decision_key: str) -> Tuple[str, str]:
    """Resolve a decision key to its (section_id, display_label) pair."""
    return _SSOT_QA_SECTIONS.get(
        decision_key,
        ("99_other", "99. Other / Open Decisions"),
    )
