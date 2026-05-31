# MCTP Source References

Fetched on 2026-05-31 from official DMTF public URLs.

## DSP0236 MCTP Base

- Document: Management Component Transport Protocol (MCTP) Base Specification.
- DSP: DSP0236.
- Version used: 1.3.3.
- Publication date on DMTF version index: 2024-03-25.
- Official version index: https://www.dmtf.org/dsp/DSP0236
- Official PDF: https://www.dmtf.org/sites/default/files/standards/documents/DSP0236_1.3.3.pdf
- Local fetched copy: `artifacts/local/standards/DSP0236_1.3.3.pdf`
- SHA-256: `9ddcda905c784493bec4be6686282a41d00c73f5c90be03d70f6c7a99c14b6de`

Relevant requirement anchors:

- MCTP packet fields and header version.
- Destination/source EID fields.
- SOM/EOM and packet sequence number behavior.
- Tag Owner and Message Tag behavior.
- Message body and message type location.
- Baseline transmission unit.
- Message assembly key fields.
- Dropped packet conditions.

## DSP0238 MCTP PCIe VDM Transport Binding

- Document: Management Component Transport Protocol (MCTP) PCIe VDM Transport Binding Specification.
- DSP: DSP0238.
- Version used: 1.4.0.
- Publication date on DMTF version index: 2026-02-28.
- Official version index: https://www.dmtf.org/dsp/DSP0238
- Official PDF: https://www.dmtf.org/sites/default/files/standards/documents/DSP0238_1.4.0.pdf
- Local fetched copy: `artifacts/local/standards/DSP0238_1.4.0.pdf`
- SHA-256: `40593171b59175be74e37da3d4d4298e562e7cfbea7487afae1c207a0d76a756`

Relevant requirement anchors:

- MCTP-over-PCIe VDM uses PCIe Type 1 VDMs with data.
- MCTP VDM Code value `0000b`.
- Non-Flit Mode packet format.
- Message Code `0x7F`.
- DMTF Vendor ID `0x1AB4`.
- Pad length rules.
- Header version value `0001b`.
- TLP Digest/ECRC policy boundary.
- Flit Mode support is separately defined and remains out of scope for this first target.
