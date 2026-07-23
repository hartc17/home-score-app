# Phase E - Accounts and the Magic-Link Claim

Give a buyer a real account, with no password, so their taste rubric follows them across devices.

## Goal

Let an anonymous quiz taker claim their rubric onto an account addressed by email, verified through a one-time magic link.
Signing in on a second device that has already taken the quiz composes that device's rubric forward onto the account rather than clobbering either side.

## Definition of done

Requesting a link for an email sends a one-time sign-in link.
Verifying the link signs the user in and claims their anonymous rubric onto the account.
The session persists across reloads, and the one-time token cannot be replayed.
When the email already owns an account, the device's latest rubric is composed forward as a new version.

## Design

### Email sender seam

The email sender is a pluggable seam, mirroring the vision analyzer.
A real provider (Resend) is used when `RESEND_API_KEY` is set; otherwise a console sender records the link and the request endpoint returns it as `dev_link` so local development and the end-to-end test can complete the loop without sending mail.
`dev_link` is never populated when a real provider is configured.

### Tokens

A login token is a random one-time secret emailed as the magic link; only its SHA-256 hash is persisted in `login_tokens`, so a database read never yields a usable link.
Links expire after fifteen minutes, and there is one outstanding link per email: requesting a new one retires any prior unconsumed token.
Verification consumes the token in a single use.

A session token is stateless: an HMAC-SHA256 signature over the user id, issue time, and the user's session epoch, keyed by `HOUSEFLAVOR_SESSION_SECRET`.
It is returned to the client as a bearer token and verified by `GET /auth/me`.
`POST /auth/signout` bumps the user's session epoch, revoking every outstanding token server-side; the web client calls it best-effort on sign-out and clears local state regardless.
A signed bearer token was chosen over a cookie because the frontend is a single-page app talking to a separate API origin.

### Claim and compose-forward

With no prior account for the email, the claim is done in place: `email` is set on the existing anonymous `users` row, so the anonymous rubric is claimed with no migration.
When the email already owns an account and the current device is a different anonymous user, `compose_forward` merges the device's latest rubric onto the account as a new version: the fresh quiz taste (directions, weights, archetype) is preserved and the account's stated gates carry forward only when the incoming rubric has none.
Neither side is clobbered.

## Endpoints

`POST /auth/request` takes an email and an optional anon id and emails the link.
`POST /auth/verify` takes a token, claims the account, and returns a session plus the latest rubric.
`GET /auth/me` takes a bearer session and returns the signed-in user and their latest rubric.

## Testing strategy

Token hashing, session signing, expiry, and tamper rejection are unit tested.
The claim and compose-forward paths are tested against an in-memory database, including the second-device merge and version bump.
The full HTTP flow (request, verify with the returned dev link, and `me`) is covered with the test client, and an end-to-end browser test drives quiz to sign-in to a persisted session.

## Failing closed in production

When `HOUSEFLAVOR_ENV=production`, the two dev conveniences become hard errors so a misconfigured deploy cannot leak access.
Signing a session requires `HOUSEFLAVOR_SESSION_SECRET` to be set to a non-default value, otherwise `_secret` raises rather than signing with the key that ships in the repo.
`/auth/request` requires a real provider (`RESEND_API_KEY`); without one it raises rather than falling back to the console sender, so the magic link is never returned to the caller as `dev_link`.

## Deferred

A live email send needs a provider key.
`/auth/request` is rate limited per email (five links per fifteen-minute sliding window, backed by the `login_tokens` timestamps) and per source IP (thirty per hour via an in-process sliding window, keyed by the last `X-Forwarded-For` entry, which nginx appends and a client cannot spoof).
The IP limiter is process-local, which matches the single-worker deployment; a multi-worker deployment would move it to a shared store.
Full multi-device anonymous-id reconciliation remains deferred.
The SSRF exposure in the listing and photo fetch is closed by the `app/net/guard.py` public-URL guard, which also pins the validated resolved address for the connection, closing the DNS-rebinding window (see the architecture doc).
