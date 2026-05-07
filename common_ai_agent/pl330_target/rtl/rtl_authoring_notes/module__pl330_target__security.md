# module__pl330_target__security

Updated `rtl/pl330_target.sv` for packet `module__pl330_target__security` with todo_plan_sha256 `67f1ff9bf1c0231e8ac6b228f14bf8866bb926d7596a6c36deeabfbcb3a528fc`.

LLM-actionable security asset coverage:
- `security.assets.asset_1`: added real `boot_manager_ns_q` state, decoded secure boot write path, boot lock enforcement, and response visibility.
- `security.assets.asset_2`: added real `boot_irq_ns_q` state, decoded per-IRQ non-secure boot mapping update path, boot lock enforcement, and response visibility.
- `security.assets.asset_3`: added real `boot_periph_ns_q` state, decoded per-peripheral non-secure boot mapping update path, boot lock enforcement, and response visibility.

The packet has no human-locked tasks. Production PASS remains blocked by plan-level locked-truth gates outside this packet.