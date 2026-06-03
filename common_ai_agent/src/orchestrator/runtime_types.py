from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SubmitOutcome:
    run_id: str
    status: str
