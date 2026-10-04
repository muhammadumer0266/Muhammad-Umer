# ADR 0002: Hand-authored CSS instead of Tailwind, for now

Date: 2026-09-30
Status: Accepted (revisit before M9 launch)

## Context

The original project brief specifies Tailwind CSS (standalone CLI or `django-tailwind`)
compiled in the Docker build stage, with no Node in the production image. The
local development sandbox used to build M2 has no Node.js and no working path
to the Tailwind standalone binary (network-restricted `pip install
pytailwindcss` did not resolve). Blocking the design-system milestone on that
tooling gap was worse than the alternative below.

## Decision

`static/css/app.css` is hand-authored plain CSS, using the same design tokens
(CSS custom properties) specified in the project brief. Templates reference
it directly via Django's staticfiles, with no build step required for local
`runserver` development. `frontend/src/css/app.css` (with the `@tailwind`
directives) and the Docker build stage remain in place unchanged.

## Consequences

- No functional loss: the site's visual identity is token-driven, not
  utility-class-driven, so plain CSS expresses it exactly the same way.
- Some duplication risk: `static/css/app.css` and `frontend/src/css/app.css`
  must be kept in sync until this is resolved.
- **Before M9 (launch)**, either (a) get Tailwind actually compiling in CI/
  Docker (where Node is available) and cut over `static/css/app.css` to be
  the Tailwind build output, or (b) formally drop Tailwind from the stack and
  update the project brief with the owner's sign-off. Tracked in
  `docs/TODO_OWNER.md`.
