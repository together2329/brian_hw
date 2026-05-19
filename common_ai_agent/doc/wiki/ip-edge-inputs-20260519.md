# IP Input Edge Case Validation — 2026-05-19

## Summary

Tested all IP input edge cases against `/api/pipeline/dispatch` and `/api/pipeline/orchestrator/chat`. Found and fixed two bugs.

## Bugs Found and Fixed

### Bug 1: Missing length check on `/api/pipeline/dispatch`

**File:** `src/atlas_api_jobs.py` line 3381

**Before:**
```python
if ip and not re.match(r"^[A-Za-z][A-Za-z0-9_]*$", ip):
```

**After:**
```python
if ip and (len(ip) > 64 or not re.match(r"^[A-Za-z][A-Za-z0-9_]*$", ip)):
```

A 500-character all-lowercase IP passed the regex check (valid chars, valid start) and returned 200. Added `len(ip) > 64` guard.

### Bug 2: Silent coercion in `_extract_ip_from_orchestrator_message`

**File:** `src/atlas_api_jobs.py` lines 3514-3517 (removed)

The function was sanitizing invalid IPs into valid ones via `re.sub(r"[^A-Za-z0-9_]", "_", candidate)` and prepending `ip_` to digit-starting names. This meant:
- `ip-with-dashes` → `ip_with_dashes` (accepted)
- `0digit_start` → `ip_0digit_start` (accepted)
- `x'; DROP TABLE users--` → `x__DROP_TABLE_users__` (accepted)

Removed the sanitization block. Invalid candidates now fall through to the downstream validator which returns 400.

### Bug 3: Missing length check on `/api/pipeline/orchestrator/chat`

**File:** `src/atlas_api_jobs.py` line 3579

**Before:**
```python
if not ip or not re.match(r"^[A-Za-z][A-Za-z0-9_]*$", ip):
```

**After:**
```python
if not ip or len(ip) > 64 or not re.match(r"^[A-Za-z][A-Za-z0-9_]*$", ip):
```

## Test Results (post-fix)

All 12 tests return HTTP 400 as expected.

| # | Input | Endpoint | Expected | Result |
|---|-------|----------|----------|--------|
| T1 | `한글ip` (Korean) | `/api/pipeline/dispatch` | 400 | 400 |
| T2 | 500× `a` | `/api/pipeline/dispatch` | 400 | 400 |
| T3 | `ip-with-dashes` | `/api/pipeline/dispatch` | 400 | 400 |
| T4 | `0digit_start` | `/api/pipeline/dispatch` | 400 | 400 |
| T5 | `🚀` | `/api/pipeline/dispatch` | 400 | 400 |
| T6 | `x'; DROP TABLE users--` | `/api/pipeline/dispatch` | 400 | 400 |
| OC1 | `한글ip` (Korean) | `/api/pipeline/orchestrator/chat` | 400 | 400 |
| OC2 | 500× `a` | `/api/pipeline/orchestrator/chat` | 400 | 400 |
| OC3 | `ip-with-dashes` | `/api/pipeline/orchestrator/chat` | 400 | 400 |
| OC4 | `0digit_start` | `/api/pipeline/orchestrator/chat` | 400 | 400 |
| OC5 | `🚀` | `/api/pipeline/orchestrator/chat` | 400 | 400 |
| OC6 | `x'; DROP TABLE users--` | `/api/pipeline/orchestrator/chat` | 400 | 400 |

## Valid IP Regex

```
^[A-Za-z][A-Za-z0-9_]*$   max length: 64
```
