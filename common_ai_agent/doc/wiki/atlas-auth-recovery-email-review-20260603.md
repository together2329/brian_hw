# ATLAS Auth Recovery and Email Send Review - 2026-06-03

Related: [[auth-cookie-expiry-20260519]] · [[atlas-test-feature-coverage]]

## Scope

Reviewed the ATLAS login, registration, ID recovery, password reset, and
email-delivery path across:

- `frontend/atlas/login.tsx`
- `core/atlas_auth.py`
- `core/session_names.py`
- `tests/test_atlas_account_recovery.py`

This was a code inspection plus a small TestClient spot check for recovery
response shape. No code was changed in this review.

## Current Behavior

- Login is username-based. Email is stored and used for verification/recovery,
  but `/api/auth/login` looks up users by username.
- The login UI contains `find-id`, `reset-request`, and `reset-confirm` modes.
  The visible `Find ID` and `Forgot PW` buttons render only when
  `/api/auth/status` returns `recovery_enabled: true`.
- The registration UI already supports email-first verification: it shows an
  email field in register mode, shows a `Code` button when
  `email_verification_enabled` is true, and shows a verification-code input for
  signup completion.
- Account recovery is disabled by default:
  `account_recovery_enabled()` reads `ATLAS_ACCOUNT_RECOVERY_ENABLED`, default
  `false`.
- Email sending exists. `_send_smtp_email()` sends through SMTP when
  `ATLAS_SMTP_HOST` is set and at least one sender source is configured:
  `ATLAS_SMTP_FROM`, `ATLAS_ADMIN_EMAIL`, or `ATLAS_SMTP_USERNAME`.
- Without SMTP config, recovery/code requests can still return `ok: true`, but
  `email_sent` stays `false`. With debug flags, the API may expose verification
  codes or reset tokens for development/tests.
- Feedback admin notification also reuses the same SMTP function.

## Relevant Flags

| Flag | Default | Effect |
|---|---:|---|
| `ATLAS_ACCOUNT_RECOVERY_ENABLED` | `false` | Enables recovery APIs and lets the frontend show `Find ID` / `Forgot PW`. |
| `ATLAS_ACCOUNT_RECOVERY_EMAIL_ENABLED` | `false` | Allows direct recovery emails for ID recovery and reset links via `_send_recovery_email()`. |
| `ATLAS_AUTH_EMAIL_VERIFICATION_ENABLED` | `false` | Requires a registration verification code. |
| `ATLAS_AUTH_EMAIL_REQUIRED` | `false` | Requires email during registration. Recovery or verification also make email required. |
| `ATLAS_AUTH_EMAIL_DEBUG` | `false` | Can expose verification codes in API responses. Development/test only. |
| `ATLAS_ACCOUNT_RECOVERY_DEBUG` | `false` | Can expose usernames/reset tokens in API responses. Development/test only. |
| `ATLAS_SMTP_HOST` | unset | Required for any SMTP send. |
| `ATLAS_SMTP_FROM` / `ATLAS_ADMIN_EMAIL` / `ATLAS_SMTP_USERNAME` | unset | One is required as sender identity. |
| `ATLAS_SMTP_PORT` | `587` | SMTP port. |
| `ATLAS_SMTP_TLS` | `true` | Calls `starttls()` before login/send. |

## Findings

| Severity | Finding | Evidence |
|---|---|---|
| High | Default admin password is hardcoded as `admin` / `1151` and default admin bootstrap is enabled unless disabled by env. Fresh DBs are takeover-prone if the app is exposed beyond trusted local use. | `core/atlas_auth.py:47`, `core/atlas_auth.py:49`, `core/atlas_auth.py:428`, `core/atlas_auth.py:803` |
| High | Public registration can create an admin when the username is listed in `ATLAS_ADMIN_USERS`; role assignment is derived from username at signup time. | `core/atlas_auth.py:422`, `core/atlas_auth.py:783` |
| High | Login, registration, and email-code issuance have no visible rate limit, lockout, or abuse throttling. | `core/atlas_auth.py:675`, `core/atlas_auth.py:749`, `core/atlas_auth.py:793` |
| Medium | Recovery endpoints can leak account existence. In a TestClient spot check, an existing email returned `email_hint` and `expires_at`; a missing email returned no expiry. | `core/atlas_auth.py:706`, `core/atlas_auth.py:719`, `core/atlas_auth.py:738` |
| Medium | Session cookies are deterministic user-id HMACs, last 90 days, and are set with `secure=False`. Logout only deletes the browser cookie; there is no server-side session revocation. | `core/atlas_auth.py:45`, `core/atlas_auth.py:46`, `core/atlas_auth.py:523`, `core/atlas_auth.py:540`, `core/atlas_auth.py:549`, [[auth-cookie-expiry-20260519]] |
| Medium | Username validation is too loose for downstream session namespace use. Registration accepts any non-empty stripped string, but session namespace segments allow only `[A-Za-z0-9_.-]+`. | `core/atlas_auth.py:752`, `core/atlas_auth.py:758`, `core/session_names.py:13` |
| Low/Medium | Password reset tokens loaded from URL query are not immediately removed from browser history/address bar. | `frontend/atlas/login.tsx:97`, `frontend/atlas/login.tsx:99`, `frontend/atlas/login.tsx:103` |
| Product gap | ID/PW recovery UI exists, but it is hidden by default because `recovery_enabled` defaults to false. If recovery is a required product feature, this needs either default enablement or an explicit disabled-state explanation. | `frontend/atlas/login.tsx:457`, `core/atlas_auth.py:120` |

## Email Send Details

SMTP mail types currently implemented:

- Auth verification code email for signup, ID recovery, and password reset:
  `_send_auth_code_email()`.
- ID recovery email with username: `/api/auth/recover/id` through
  `_send_recovery_email()`.
- Password reset link email: `/api/auth/recover/password` through
  `_send_recovery_email()`.
- Feedback admin notification: `send_feedback_email()`.

Important distinction:

- Verification-code email uses SMTP when the relevant endpoint is enabled and
  SMTP is configured.
- Direct recovery emails are additionally gated by
  `ATLAS_ACCOUNT_RECOVERY_EMAIL_ENABLED`.
- Debug flags may make API responses appear usable without SMTP because the
  code/token is returned directly. That must stay out of production.

## Signup Email Verification Product Note

Desired signup flow:

1. User enters username, password, and email on the first registration screen.
2. User clicks `Code`.
3. Server creates a `register` verification code and sends it to that email.
4. User enters the verification code.
5. `/api/auth/register` consumes the code and creates the account.

This flow is already implemented behind `ATLAS_AUTH_EMAIL_VERIFICATION_ENABLED`.
For production, enable it only together with SMTP delivery; otherwise the UI can
ask for a code that no user can receive. If signup email verification should be
the default product behavior, make `ATLAS_AUTH_EMAIL_VERIFICATION_ENABLED=1`
part of the production environment and add a visible warning or hard startup
check when SMTP is missing.

## Existing Tests

Covered:

- SMTP sender fallback to `ATLAS_ADMIN_EMAIL`.
- Debug recovery happy path for finding ID and resetting password.
- Verification-code recovery flow.
- Feedback email to admin recipients via a monkeypatched send function.

Not covered enough:

- Rate limits or brute-force lockout.
- Generic public response shape for account recovery enumeration resistance.
- Frontend visibility of `Find ID` / `Forgot PW` under `recovery_enabled`.
- Removal of `reset_token` from the URL after loading.
- Production SMTP failure behavior across all recovery modes.
- Username/password policy validation.

## Recommended Fix Order

1. Decide whether account recovery is a production feature. If yes, make the UI
   discoverable by default or show a clear disabled state tied to config.
2. Decide whether signup email verification is mandatory in production. If yes,
   enable `ATLAS_AUTH_EMAIL_VERIFICATION_ENABLED=1` with working SMTP and add a
   guard against enabling it without deliverability.
3. Remove the hardcoded default admin password path or restrict it to explicit
   local bootstrap only.
4. Prevent public signup from claiming admin usernames without an invite,
   bootstrap token, or pre-created admin account.
5. Add rate limits for login, register, and `/api/auth/email-code`, keyed by IP,
   username/email, and purpose.
6. Make recovery responses indistinguishable for existing and missing accounts.
7. Add username/password validation before user creation, aligned with session
   namespace constraints.
8. Move auth cookies to server-side sessions or signed tokens with expiry,
   rotation, Secure-on-HTTPS, and revocation.
9. Scrub `reset_token` from the URL immediately after the frontend reads it.
