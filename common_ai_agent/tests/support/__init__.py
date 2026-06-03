"""Shared, importable test doubles for the Atlas session-worker suites.

This is a tracked package (not under .omc) so the reusable
:class:`FakeProcessManager` can be imported by every capacity / owner-slot /
activation test instead of each suite re-declaring a slightly different inline
fake. See ``plans/single-active-session-worker-100-users.md`` (Wave-3 H11).
"""

from tests.support.fake_process_manager import FakeProcessManager, ManualClock

__all__ = ["FakeProcessManager", "ManualClock"]
