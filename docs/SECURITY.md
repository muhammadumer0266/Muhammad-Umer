# Security model

Zero trust here means: no request, network position, upload, or piece of
content is trusted by default -- each layer verifies on its own, so one
failure doesn't open the next.

## Network edge (docker/Caddyfile, docker-compose.yml)
- Only Caddy is published. `web` has **no host port**, so nothing can reach
  Django without TLS, the security headers, or Caddy's rewritten
  `X-Forwarded-For`/`-Proto` headers.
- Caddy only *fills in* headers Django didn't set (`?Header`), so it can't
  weaken Django's stricter CSP/HSTS. The `Server` header is stripped.
- `/media/` (uploads) is served by Caddy as static files under a
  `sandbox` CSP (PDFs: a no-resources CSP), with `nosniff`.
- Containers run with `no-new-privileges`. The image runs as a non-root user
  that can only write `/app/media`. `.dockerignore` keeps `.env`, databases
  and local tooling out of the image.
- `POSTGRES_PASSWORD` has no default; compose refuses to start without it.

## Identity: the admin
| Control | Where |
|---|---|
| Secret, non-default path (`ADMIN_URL`) | settings + deploy check `core.W001` |
| Optional IP/CIDR allowlist; everyone else gets a 404 (`ADMIN_ALLOWED_IPS`) | `apps.core.middleware.AdminAccessMiddleware` |
| Password + TOTP 2FA, with one-time backup codes (`ADMIN_REQUIRE_OTP`, on in prod) | `config/urls.py`, `manage.py enroll_admin_otp` |
| Lockout after 5 failures for 1 h (django-axes), keyed on the real client IP | `AXES_*` settings |
| 2-hour sessions that end when the browser closes; `__Host-` cookies in prod | `SESSION_*` settings |
| Admin pages sent `Cache-Control: no-store` | `AdminAccessMiddleware` |

**Enroll before deploying** (otherwise you're locked out by design):

    python manage.py enroll_admin_otp <username>          # first device
    python manage.py enroll_admin_otp <username> --reset  # lost phone

## Requests
- The real client IP comes from `apps/core/net.py`. It counts proxies from the
  right of `X-Forwarded-For` (`TRUSTED_PROXY_COUNT`, 1 in prod), so a client
  can't spoof its IP to dodge rate limits, lockouts or the admin allowlist.
- Rate limits: contact 5/h, Ask is set in the admin (default 20/h), API 60/min.
- CSP: `script-src 'self'` + nonce only; `form-action`, `frame-src`,
  `object-src`, `base-uri` and `frame-ancestors` are locked down;
  `upgrade-insecure-requests` in prod. Also COOP/CORP, `nosniff`,
  `Referrer-Policy`, and a deny-all `Permissions-Policy`.
- Public API: anonymous, **read-only**, and it accepts no credentials at all
  (an admin session can't raise its privileges). JSON only in production.

## Uploads (apps/core/uploads.py)
Photo, résumé and certificates accept JPG/PNG/WebP (5 MB) or PDF (10 MB)
only. Each file is checked by its contents, not its name: images are fully
decoded and PDFs must start with `%PDF-`. Each file is also stored under a
random name, so the original filename never reaches disk or a URL. SVG and
HTML are never accepted.

## Ask / RAG guardrails (apps/ai/guardrails.py)
Three checkpoints, logged per question in **Ask logs → guardrail**:
1. **Input**: length bounds, prompt-injection and jailbreak detection after
   Unicode normalization (so zero-width and full-width tricks don't help),
   and admin rules. A blocked question never reaches the provider.
2. **Context**: retrieved chunks that contain instructions are dropped
   before they reach the prompt.
3. **Output**: blocks echoes of the system prompt, strips citations of chunks
   that weren't retrieved, refuses uncited answers, redacts emails, phone
   numbers and API-key-shaped tokens, and applies admin rules.

The baseline is code and can't be disabled. On top of it, **Admin → Ai →
Guardrail policy** offers a kill switch, length limits, the similarity
threshold, top-k, the rate limit, citation and PII toggles, and the user-facing
messages. **Guardrail rules** add keyword or regex block/redact rules per stage,
with hit counts. Regex rules are validated: nested quantifiers are rejected to
prevent ReDoS. Changes apply to the next question (the cache is invalidated
on save).

The index rebuilds itself after any entry, profile or certification change
(`AI_AUTO_REINDEX`), and unpublished content is **removed** from it.

## Release checklist
    python manage.py check --deploy --settings=config.settings.prod
