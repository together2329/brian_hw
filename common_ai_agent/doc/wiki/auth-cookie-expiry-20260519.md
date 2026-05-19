# Auth Cookie Expiry & Multi-Session Policy

**Date**: 2026-05-19  
**Method**: Live curl against port 8001 (atlas_ui.py), user `validator`/`validate123`  
**Source**: `core/atlas_auth.py`

---

## Cookie Attributes (from Set-Cookie header)

```
set-cookie: atlas_session=<value>; HttpOnly; Max-Age=7776000; Path=/; SameSite=lax
```

| Attribute  | Value       | Notes |
|------------|-------------|-------|
| Max-Age    | 7776000 s   | **90 days** (`_MAX_AGE = 90 * 24 * 60 * 60`, line 46). Well above 30-day threshold — see risk note below. |
| HttpOnly   | yes         | JS cannot access the cookie. |
| Secure     | **absent**  | Expected for localhost/HTTP; would be a risk on a public HTTPS deployment. |
| SameSite   | lax         | Protects against most CSRF vectors. |
| Path       | /           | Full-site scope. |

---

## Step-by-Step Test Results

### Step 1 — Login
```
POST /api/auth/login {"username":"validator","password":"validate123"}
→ HTTP 200, Set-Cookie: atlas_session=d53cabe8...; HttpOnly; Max-Age=7776000; Path=/; SameSite=lax
```

### Step 2 — Valid cookie → /api/users/me
```
GET /api/users/me (cookie1)
→ HTTP 200 {"user": {"id": "d53cabe8...", "username": "validator", "role": "user", ...}}
```

### Step 3 — Invalid cookie → 401
```
GET /api/users/me (empty cookie header)   → HTTP 401 {"detail":"login required"}
GET /api/users/me (tampered cookie value) → HTTP 401 {"detail":"login required"}
```
HMAC verification correctly rejects bad tokens.

### Step 4 — Multi-session (re-login)
Second login issues the **exact same cookie value** as the first:
```
set-cookie: atlas_session=d53cabe8b4054e75b30cac4c4f47a76d:6a31a1665adba454  (identical)
```
**Root cause**: `GuestAuth._sign(user_id)` is deterministic — `HMAC(secret, user_id)` with no nonce or timestamp. Every login for the same user produces the same token.

- cookie1 after re-login: HTTP 200 ✓ (still valid)
- cookie2 after re-login: HTTP 200 ✓ (same value as cookie1)

**Multi-session policy: effectively single token per user** — there is no concept of independent sessions.

### Step 5 — Logout cross-invalidation
```
POST /api/auth/logout (cookie1) → HTTP 200 {"ok":true}
GET  /api/users/me  (cookie1)  → HTTP 200  ← STILL VALID (expected, see below)
GET  /api/users/me  (cookie2)  → HTTP 200  ← STILL VALID
```

**Root cause**: `_clear_cookie()` calls `response.delete_cookie()` which instructs the *browser* to discard the cookie, but the server has **no session store**. The HMAC token remains valid for the full 90-day Max-Age window. Any client holding the raw cookie value can continue making authenticated requests after logout.

---

## Risk Summary

| Finding | Severity | Notes |
|---------|----------|-------|
| Max-Age = 90 days | Low-Medium | Very long-lived for a local tool; acceptable for desktop-local use, but worth noting if ever exposed externally. No change made per task instructions. |
| Secure flag absent | Low | Correct for local HTTP; would be a P0 on an HTTPS deployment. |
| Logout does not revoke token server-side | Medium | Cookie holder stays authenticated until expiry. Mitigated by: (a) local-only deployment, (b) HMAC prevents forgery, (c) deterministic token means re-login issues same value anyway. To fix: add a server-side revocation list or per-session nonce. |
| No multi-session isolation | Low | All sessions share one token value. Logging out from one device/browser has no effect on another. Same mitigation context as above. |

---

## Relevant Code

- `core/atlas_auth.py:46` — `_MAX_AGE = 90 * 24 * 60 * 60`
- `core/atlas_auth.py:336-346` — `_set_cookie()` — sets HttpOnly, Secure=False, SameSite=lax, Max-Age
- `core/atlas_auth.py:322-333` — `_sign()` / `_verify()` — deterministic HMAC with no nonce
- `core/atlas_auth.py:348-351` — `_clear_cookie()` — client-side delete only, no server revocation
- `core/atlas_auth.py:627-630` — `/api/auth/logout` endpoint
