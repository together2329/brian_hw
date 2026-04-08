"""Scoreboard for comparing DUT outputs against reference model predictions."""

from counter_txn import CounterOutput


class CounterScoreboard:
    """Compares DUT output against reference model each cycle.

    Usage:
        sb = CounterScoreboard()
        sb.compare(expected, actual, cycle=0, test_name="test")
        sb.report()  # print summary
    """

    def __init__(self):
        self.pass_count = 0
        self.fail_count = 0
        self.total_count = 0
        self._failures = []

    def compare(
        self,
        expected: CounterOutput,
        actual: CounterOutput,
        cycle: int = 0,
        test_name: str = "",
    ) -> bool:
        """Compare expected vs actual output.

        Returns True if match, False otherwise.
        """
        self.total_count += 1
        if expected == actual:
            self.pass_count += 1
            return True
        else:
            self.fail_count += 1
            msg = (f"[FAIL] {test_name} cycle {cycle}: "
                   f"expected count={expected.count_out} overflow={expected.overflow}, "
                   f"got count={actual.count_out} overflow={actual.overflow}")
            self._failures.append(msg)
            return False

    def check(
        self,
        actual_count: int,
        actual_overflow: int,
        expected_count: int,
        expected_overflow: int,
        cycle: int = 0,
        test_name: str = "",
    ) -> bool:
        """Convenience method — compare using raw integers."""
        return self.compare(
            CounterOutput(expected_count, expected_overflow),
            CounterOutput(actual_count, actual_overflow),
            cycle,
            test_name,
        )

    def report(self) -> bool:
        """Print summary. Returns True if all passed."""
        print("=" * 60)
        print("  SCOREBOARD SUMMARY")
        print(f"  Total checks: {self.total_count}")
        print(f"  Passed:       {self.pass_count}")
        print(f"  Failed:       {self.fail_count}")
        if self._failures:
            print("  Failures:")
            for f in self._failures[:20]:  # limit output
                print(f"    {f}")
            if len(self._failures) > 20:
                print(f"    ... and {len(self._failures) - 20} more")
        print("=" * 60)
        return self.fail_count == 0
