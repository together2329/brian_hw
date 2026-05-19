# DB Concurrent Write Race — Investigation & Fix (2026-05-19)

## Finding

`AtlasDB._connect()` was opening SQLite connections in the default `delete` (rollback-journal) mode with no `busy_timeout`. Under concurrent writes from 10 threads this poses a risk: a second writer can receive `sqlite3.OperationalError: database is locked` immediately instead of queuing.

In practice the single-instance RLock serialised access at the Python level, so the concurrent tests passed even without WAL. However the pragma tests exposed the missing safety net.

## Fix Applied

Added two pragmas in `core/atlas_db.py` `_connect()` (line ~548):

```python
self._conn.execute("PRAGMA journal_mode=WAL")
self._conn.execute("PRAGMA busy_timeout=5000")
```

- **WAL mode** — writers no longer block readers; multiple readers can proceed while one writer holds the lock. Also eliminates reader/writer deadlocks when multiple processes open the same file.
- **busy_timeout=5000** — any writer that cannot acquire the lock immediately will retry for up to 5 seconds before raising, giving concurrent writers a fair queuing window.

## Test Coverage

`tests/test_db_concurrent_workflow_runs.py` (5 tests, all green):

| Test | What it checks |
|---|---|
| `test_10_threads_start_workflow_runs` | 10 concurrent `start_workflow_run` calls; 10 distinct rows, all `status='running'`, no exceptions |
| `test_10_threads_finish_workflow_runs` | 10 concurrent `finish_workflow_run` calls; all rows reach `status='completed'` |
| `test_start_and_finish_interleaved` | Start + finish in one 10-thread wave with a barrier; end-to-end race |
| `test_busy_timeout_is_set` | PRAGMA busy_timeout > 0 |
| `test_wal_journal_mode` | PRAGMA journal_mode == 'wal' |

## Result

```
5 passed in 1.04s
```

No "database is locked" errors observed. WAL + busy_timeout confirmed active.
