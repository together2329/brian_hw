from __future__ import annotations

from typing import Iterable

from pyuvm import uvm_sequence

from transactions import ApbTransaction, AxiBeatTransaction, TlpBurstTransaction


class ApbWriteSequence(uvm_sequence):
    def __init__(self, name: str, writes: Iterable[ApbTransaction]):
        super().__init__(name)
        self.writes = list(writes)

    async def body(self) -> None:
        driver = self.sequencer  # bound externally
        for txn in self.writes:
            await driver.write(txn.addr, txn.data)


class TlpBurstSequence(uvm_sequence):
    def __init__(self, name: str, bursts: Iterable[TlpBurstTransaction]):
        super().__init__(name)
        self.bursts = list(bursts)

    async def body(self) -> None:
        driver = self.sequencer
        for burst in self.bursts:
            await driver.write_burst(burst.awaddr, burst.beats)


def apb_txns_from_writes(writes) -> list[ApbTransaction]:
    return [ApbTransaction(addr=w.addr, data=w.data, write=True) for w in writes]


def burst_txn_from_scenario(scenario) -> TlpBurstTransaction:
    beats = [
        AxiBeatTransaction(data=b.data, wstrb=b.wstrb, wlast=b.wlast)
        for burst in scenario.axi_bursts
        for b in burst.beats
    ]
    awaddr = scenario.axi_bursts[0].awaddr if scenario.axi_bursts else 0x1000
    return TlpBurstTransaction(
        scenario_id=scenario.scenario_id,
        awaddr=awaddr,
        beats=beats,
        tlp_bytes=list(scenario.tlps[0]) if len(scenario.tlps) == 1 else [],
    )
