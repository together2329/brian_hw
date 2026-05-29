from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List

from pyuvm import uvm_sequence_item


@dataclass
class ApbTransaction(uvm_sequence_item):
    addr: int
    data: int
    write: bool = True

    def __post_init__(self) -> None:
        uvm_sequence_item.__init__(self, f"apb_{self.addr:03x}")


@dataclass
class AxiBeatTransaction(uvm_sequence_item):
    data: int
    wstrb: int
    wlast: bool

    def __post_init__(self) -> None:
        uvm_sequence_item.__init__(self, "axi_beat")


@dataclass
class TlpBurstTransaction(uvm_sequence_item):
    scenario_id: str
    awaddr: int
    beats: List[AxiBeatTransaction] = field(default_factory=list)
    tlp_bytes: List[int] = field(default_factory=list)

    def __post_init__(self) -> None:
        uvm_sequence_item.__init__(self, self.scenario_id)

    @property
    def transaction(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "awaddr": self.awaddr,
            "tlp_bytes": list(self.tlp_bytes),
            "beats": [
                {"data": b.data, "wstrb": b.wstrb, "wlast": b.wlast}
                for b in self.beats
            ],
        }
