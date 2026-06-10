# Signoff Workflow

The signoff workflow checks whether an IP has enough local evidence to claim
machine-checked readiness against `IP_SIGNOFF.md`.

It does not define the IP's behavior.  It reads locked-truth artifacts and
stage reports already produced by the SSOT/FL/CL/RTL/TB/sim/coverage flow.
It also requires `<ip>/verify/ip_contract.json`, which is derived from the
IP's own SSOT/IO/goals rather than from a static profile.

Run:

```bash
python3 workflow/signoff/scripts/check_ip_signoff.py <ip> --root <ip-parent>
```

For the demo IPs under `ip_examples/`:

```bash
python3 workflow/signoff/scripts/check_ip_signoff.py apb_popcount_demo --root ip_examples
```

Outputs:

```text
<ip>/signoff/ip_signoff.json
<ip>/signoff/ip_signoff.md
```

The script exits non-zero when required local evidence is missing or failing.
If `<ip>/mutation/mutation_report.json` exists, signoff also records the
mutation kill-rate.  Missing mutation evidence is currently advisory and does
not block local signoff unless a human enables an enforced mutation policy.
