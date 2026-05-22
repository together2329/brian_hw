class FunctionalModel:
    """Executable SSOT-derived model for generic_counter_ip.

    The apply() method is the expected-behavior authority: value = input * 2.
    """

    def __init__(self):
        self.accepted_count = 0

    def _transactions(self):
        return [{"id": "FM_PRIMARY", "name": "primary_behavior"}]

    def reset(self):
        self.accepted_count = 0

    def apply(self, txn):
        value = int(txn.get("value", 0))
        self.accepted_count += 1
        return {
            "resp": 0,
            "value": value * 2,
            "accepted_count": self.accepted_count,
        }
