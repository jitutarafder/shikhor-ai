# AGENTS.md — Standing Rules for Shikhor AI

> Read this file at the start of every coding session, before changing code. Also read the relevant source documents: `PRD.md` defines the product, `design.md` defines UI/UX, `Architecher.md` defines the system structure, `Security.md` defines mandatory controls, and `phases.md` defines delivery order. If the documents conflict, stop and ask instead of silently choosing one.

## Project purpose

Shikhor AI is a Bangladesh-focused, Bangla-first agricultural support platform. It helps farmers obtain AI-assisted crop guidance, find nearby agricultural equipment, plan work around weather, connect with crop buyers, access reviewed agricultural knowledge, and save selected actions for synchronization when internet connectivity returns.

The product provides decision support. It does **not** guarantee a crop diagnosis, replace an agricultural officer, guarantee a marketplace transaction, or automatically prescribe pesticide dosage.

## Approved technology stack — do not deviate without asking

### Frontend

- React + TypeScript + Vite
- React Router
- Tailwind CSS
- Framer Motion with reduced-motion support
- TanStack Query for server state
- React Hook Form + Zod for forms
- i18next or a typed locale dictionary for Bangla/English
- Dexie.js over IndexedDB for approved offline data
- Workbox or Vite PWA integration for service-worker behavior
- Leaflet + OpenStreetMap for maps
- Lucide React for icons

### Backend

- Python 3.12+
- FastAPI
- Pydantic v2
- SQLAlchemy 2.x
- Alembic
- PostgreSQL 16+ with PostGIS
- HTTPX for outbound provider calls
- Argon2id when password authentication is enabled
- Pytest

### AI and integrations

- TensorFlow or PyTorch for an approved crop-image model
- Scikit-learn for an approved lightweight NLP/intent model where appropriate
- Gemini **or** Claude behind a provider adapter when a language model is justified
- Weather, OTP/SMS, AI, and object-storage providers must be accessed through backend adapters
- Do not call multiple paid AI providers by default
- Do not expose provider secrets to the browser

### Repository and deployment

- Separate `frontend/` and `backend/` applications
- Each application has its own dependency file, tests, Dockerfile, and deployment pipeline
- Backend begins as a modular monolith, not premature microservices
- The OpenAPI schema is the API contract and should generate or validate frontend types

## 1. Implement only the requested scope

Do exactly what the current task requires. Do not add speculative features, routes, tables, components, providers, abstractions, or “nice-to-have” refactors. If an unrequested change is genuinely required, explain why and ask before implementing it.

Do not expand the MVP into payments, escrow, logistics, IoT, drones, satellite analytics, or microservices without explicit approval.

## 2. Never commit or publish without explicit permission

Never run `git commit`, `git push`, merge a branch, create a pull request, publish a package, deploy to staging/production, or run a production migration unless the user explicitly asks for that action. Permission is required each time.

Read-only Git commands such as `git status`, `git diff`, and `git log` are allowed when needed. Staging changes is allowed only when requested.

## 3. Report exactly what was changed and executed

At the end of a task, state:

- files created or modified
- commands, migrations, tests, builds, or scans executed
- which folder/environment each command used
- pass/fail result
- anything not executed and why
- remaining risks or required decisions

Never claim a test, build, security check, model evaluation, or visual review passed unless it actually ran.

## 4. No hardcoded configuration or secrets

Never hardcode database URLs, JWT/signing secrets, OTP credentials, AI keys, weather keys, storage credentials, allowed origins, production domains, or environment-specific ports.

- Backend reads configuration from environment variables through a typed settings module.
- Frontend exposes only explicitly public build-time values.
- Keep placeholders in `.env.example` without real secrets.
- Never put secrets in Git, logs, screenshots, fixtures, frontend bundles, URLs, or documentation examples.
- Use separate values for local, development, staging, and production.

## 5. Preserve the separate frontend/backend boundary

- The frontend handles presentation, local interaction, localization, and approved offline storage.
- The backend owns validation, authentication, authorization, business rules, ranking, provider calls, and persistence.
- Never trust a frontend calculation or role check as authoritative.
- Never connect the browser directly to PostgreSQL.
- Never place AI, weather, OTP, or private-storage secrets in the frontend.
- Route guards are UX only; backend authorization is mandatory.

## 6. Keep code clean and typed

- Follow existing formatter, linter, and type-checking configuration.
- Use meaningful names and small, focused modules.
- Avoid duplicate business logic.
- Remove temporary debugging output before delivery.
- No dead code, unused imports, abandoned scaffolding, or commented-out replacements.
- Do not perform unrelated repository-wide formatting.
- In TypeScript, do not use `any` without a narrow, commented justification.
- In Python, add type annotations to public functions and important domain boundaries.
- Prefer explicit domain types/enums over magic strings.

## 7. Comments explain why

Comment non-obvious decisions, safety constraints, business formulas, state-transition rules, authorization boundaries, synchronization behavior, and provider workarounds.

Do not add noisy comments that simply repeat the code. Public modules/functions should have short documentation where their purpose or contract is not obvious.

## 8. Ask before adding or replacing dependencies

Do not install a new npm, Python, system, model, map, analytics, or external-provider dependency without approval.

Before proposing one, explain:

- what problem it solves
- why the current stack cannot solve it adequately
- client/server bundle or runtime impact
- security/privacy/licensing implications
- ongoing cost or provider lock-in
- how it would be removed or replaced later

Use locked dependency versions and update the relevant architecture documentation after approval.

## 9. Ask before destructive actions

Get explicit permission before:

- deleting files or migrations
- dropping/renaming tables or columns
- destructive data migration or backfill
- deleting object-storage content
- resetting a database
- clearing real user/offline data
- rotating production credentials
- changing retention rules

Prefer reversible changes and document rollback steps.

## 10. Update project documentation with meaningful changes

When a task changes architecture, product scope, security behavior, delivery phase, route structure, API contract, external provider, offline behavior, or an open decision, update the relevant document in the same task:

- `PRD.md`
- `design.md`
- `Architecher.md`
- `Security.md`
- `phases.md`

Do not allow implementation and documentation to silently diverge. If documentation changes were not requested but are necessary, call them out and ask before expanding the task.

## 11. Backend validation is always authoritative

Treat every request, upload, token, provider response, and offline command as untrusted.

- Use strict Pydantic schemas and field limits.
- Reject unknown fields for sensitive write operations.
- Derive user ID and role from the authenticated session.
- Calculate ownership, ranking, status, and moderation fields on the server.
- Use SQLAlchemy/parameterized queries only; never concatenate SQL.
- Use explicit response schemas to prevent data leakage.
- Validate external-provider responses before use.
- Return the standard public error envelope, never raw exceptions.

```json
{
  "error": {
    "code": "STABLE_MACHINE_CODE",
    "message": "Safe user-facing message",
    "fieldErrors": {},
    "requestId": "correlation-id"
  }
}
```

## 12. Authorization is role plus object-level policy

Every protected backend operation must check:

1. valid authentication
2. required role or capability
3. object ownership or active participation
4. permitted fields
5. allowed state transition

Examples:

- Farmers access only their private crop cases.
- Equipment owners update only equipment they own.
- Users read only conversations in which they are active participants.
- Moderators perform only assigned moderation actions.
- Admin status never bypasses logging or input validation.

Use deny-by-default policy functions/dependencies. Add negative tests proving one user cannot access another user's records.

## 13. Authentication and session rules

- Use Argon2id for passwords.
- Access credentials are short-lived.
- Refresh sessions rotate and are revocable server-side.
- Do not store long-lived credentials in `localStorage` or IndexedDB.
- OTPs are random, short-lived, single-use, hashed at rest, and rate-limited.
- Password/OTP recovery must not reveal whether an account exists.
- Logout and account switching must clear account-specific private offline data according to policy.
- Admin accounts require MFA before production.

Follow the detailed requirements in `Security.md`; do not replace them with a simplified custom scheme.

## 14. Centralize state transitions

Do not directly assign workflow status at arbitrary call sites. Equipment listings, rental requests, crop listings, crop cases, messages/sync operations, moderation reports, and sessions must use centralized transition functions or domain services with an allowed-transition map.

Any change to an allowed transition requires updated unit tests and documentation.

Important rental states include: `pending`, `accepted`, `rejected`, `cancelled`, and `completed`. Do not invent additional states without approval.

## 15. Equipment ranking is fixed and transparent

The approved organic ranking is:

```text
ranking_score = (0.65 × normalized_price_score)
              + (0.35 × normalized_distance_score)
```

Lower scores rank higher.

Rules:

- Filter unavailable, paused, out-of-radius, or disallowed listings first.
- Compare only the same equipment type and compatible pricing unit.
- Never compare per-hour, per-day, and per-acre prices without an approved conversion.
- Handle equal min/max values without division by zero.
- Missing or invalid values must not receive a better score.
- Return ranking components so the UI can explain the result.
- Do not secretly mix sponsored placement into organic results.

Any change to this formula or normalization requires explicit approval plus updated unit/integration tests.

## 16. Money, quantity, and units must be exact

- Store monetary values in an integer smallest unit where practical; do not use binary floating-point for money.
- Always store the currency and price unit.
- Validate equipment rental units and crop quantity units using enums/reference data.
- Perform conversions only through reviewed central functions.
- Display BDT and local units explicitly.
- Store timestamps in UTC; localize for display.

## 17. Geospatial and privacy rules

- Use PostGIS `geography(Point, 4326)` for earth-distance queries.
- Use `ST_DWithin` to filter before distance ordering.
- Add GiST indexes to frequently queried geospatial columns.
- Never expose a user's exact private/home coordinates in public results.
- Use approximate, rounded, gridded, or offset public listing locations.
- GPS permission is optional; manual district/upazila selection must remain available.
- Exact-location access requires a documented workflow and authorization rule.

## 18. Crop-image upload security is mandatory

For crop-analysis uploads:

- accept only approved JPEG, PNG, and WebP formats
- validate extension, MIME type, and file signature
- enforce byte-size and pixel-dimension limits
- reject malformed files and decompression bombs
- decode and re-encode to a sanitized derivative
- strip EXIF/GPS metadata unless explicitly required and consented
- store objects under random names in private storage
- use authorized access or short-lived signed URLs
- never execute or serve uploads as active content

Do not accept SVG, HTML, archives, executables, or arbitrary documents for crop analysis.

Any upload-related change must include malicious/oversized/mismatched-file tests.

## 19. AI output must be constrained, reviewable, and honest

- AI results are possible matches, not guaranteed diagnoses.
- Use structured output with: status, possible condition, confidence, confidence band, reason summary, reviewed guidance, escalation flag, model version, and disclaimer.
- Low-confidence, unsupported, or poor-quality inputs must produce an uncertain/unsupported state and recommend appropriate expert help.
- Do not let a general-purpose language model invent pesticide names, dosage, chemical mixing, or emergency instructions.
- Actionable guidance must come from reviewed agricultural knowledge.
- Store the model/configuration version and feedback linkage.
- Remove unnecessary personal data before sending input to an external AI provider.
- Do not call Gemini and Claude together by default.
- Never claim accuracy without a representative evaluation dataset and recorded results.

Changes to confidence thresholds, taxonomy, model version, guidance mapping, or escalation logic require tests and documented expert review.

## 20. Weather guidance must separate facts from recommendations

- Fetch weather through a backend provider adapter.
- Set strict timeouts, bounded retries, cache rules, and quota monitoring.
- Keep provider timestamp, location resolution, and attribution.
- Clearly mark stale/unavailable data.
- Product-generated activity windows must be visually and structurally distinguishable from provider forecast facts.
- Weather rules require tests and agricultural subject-matter review.
- Never expose the provider API key to the browser.

## 21. Offline synchronization must be idempotent

Approved offline storage is limited to selected knowledge, necessary reference data, and explicitly supported queued commands.

Every queued mutation must include:

- local UUID
- idempotency key
- operation name
- validated payload
- account ID association
- creation time
- retry count
- status

Synchronization rules:

1. Do not report server success before receiving confirmation.
2. Bind idempotency records to user, operation, and request-body hash.
3. Retry temporary failures with bounded exponential backoff and jitter.
4. Stop automatic retry for validation, authorization, or conflict errors.
5. Let users inspect, retry, or remove failed items.
6. Clear account-specific local data on logout/account change as required.
7. Background Sync is an enhancement; foreground/manual retry must work.

Any change to the queue, idempotency, conflict handling, or service worker requires offline interruption and duplicate-delivery tests.

## 22. Service-worker and cache safety

- Precache only the application shell and approved public assets.
- Do not cache authenticated API responses by default.
- Never cache tokens, admin content, or unrestricted private messages.
- Version caches and delete obsolete caches safely.
- Test update behavior when queued offline work exists.
- Do not let stale caches hide critical security or guidance updates.
- Logout must remove private account-specific cached data according to policy.

## 23. Bangla-first accessibility and design rules

Follow `design.md`.

- Bangla is primary; English is secondary.
- Use `Noto Sans Bengali` and `Inter` with safe fallbacks.
- Minimum body text is 16px.
- Interactive targets are at least 44×44px; prefer larger primary mobile actions.
- Meet WCAG 2.2 AA where possible.
- Provide keyboard navigation, visible focus, semantic HTML, labels, and useful alt text.
- Respect `prefers-reduced-motion`.
- Icons never replace labels for important actions.
- Do not hide required information behind hover.
- Test at approximately 390px, 768px, and 1280px.
- Preserve form data during recoverable network failures.

Do not add fake testimonials, partner logos, usage numbers, accuracy percentages, or unsupported performance claims.

## 24. Framer Motion must be restrained

Motion should explain hierarchy, state change, or direction.

- Prefer transform and opacity.
- Avoid permanent decorative loops and large parallax effects.
- Limit simultaneous animation in a viewport.
- Stop animation when offscreen where practical.
- Provide reduced-motion behavior.
- Never flash urgent colors or animate confidence numbers in a misleading way.
- Do not make core tasks depend on animation.

## 25. Performance rules

### Frontend

- Design for budget Android devices and unreliable networks.
- Defer maps, heavy animations, and non-critical code.
- Use responsive AVIF/WebP images.
- Avoid autoplay video and large Lottie files.
- Prevent unnecessary React rerenders; memoize only with evidence.
- Keep route bundles measurable and document meaningful regressions.

### Backend

- Paginate/limit collection endpoints.
- Avoid N+1 database queries.
- Add indexes for frequently filtered/sorted/joined columns.
- Bound external calls, uploads, AI concurrency, and payload sizes.
- Use caching only with a clear invalidation/staleness policy.
- Move long-running critical work to a durable queue when measured need justifies it; do not use FastAPI `BackgroundTasks` as a durable job system.

Do not optimize blindly. Measure first and document meaningful trade-offs.

## 26. Error, logging, and audit rules

- Never return raw database errors, stack traces, provider errors, prompts, or internal paths.
- Use correlation/request IDs.
- Use structured logs with PII/secret redaction.
- Never log passwords, hashes, OTPs, tokens, cookies, authorization headers, full private messages, exact sensitive coordinates, or raw private crop images.
- Audit authentication events and all moderator/admin changes.
- Audit entries include actor, action, resource, timestamp, and request ID.
- User-facing error messages must be actionable in Bangla and English where supported.

## 27. Rate limiting and abuse prevention

Use endpoint-specific limits for:

- login, password reset, and OTP send/verify
- crop analysis and uploads
- equipment/location search
- messaging and contact actions
- reports and public contact forms
- external-provider-backed endpoints
- export/bulk/admin operations

Also enforce request-size, string-length, array-size, pagination, timeout, and per-user concurrency limits. Add block/report controls to marketplace and messaging work.

## 28. Tests are required with business and security logic

A code change is incomplete without relevant tests.

Mandatory examples:

- Equipment ranking: normalization, units, equal values, missing values, order
- State transitions: valid and invalid transitions
- Authorization: cross-user access denied
- Offline sync: duplicate delivery, token expiry, validation conflict, reconnection
- Uploads: MIME/signature mismatch, oversized image, decompression limits
- AI: low confidence, unsupported input, provider failure, unsafe-output guard
- Weather: stale data, timeout, rule boundaries
- Authentication: rotation, revocation, OTP limits, account enumeration
- Localization/accessibility: critical Bangla states and keyboard flows

Run the smallest relevant suite during iteration and the broader affected suite before handoff.

## 29. Database migration rules

- Every schema change uses Alembic.
- Review generated migrations manually.
- Separate schema changes from risky data backfills where practical.
- Plan compatibility for independently deployed frontend/backend versions.
- Do not run migrations automatically from every API replica.
- Document rollback or forward-fix strategy.
- Test migrations on representative staging data before production approval.

## 30. External content and provider responses are untrusted

- Validate weather, AI, geocoding, storage, and SMS responses.
- Do not follow arbitrary user-supplied URLs from the server.
- Use outbound host allowlists where practical.
- Apply timeouts and bounded retries.
- Track provider errors, quota, latency, and cost.
- Respect OpenStreetMap/tile-provider attribution and usage policy.
- Review provider privacy/retention terms before sending user data.

## 31. Definition of done

A feature is complete only when:

- requested acceptance criteria pass
- Bangla and English states are handled
- loading, empty, error, offline, and permission states are covered where relevant
- backend validation and authorization are implemented
- tests for changed business/security behavior pass
- mobile, keyboard, and reduced-motion behavior are verified
- logs/metrics exist without leaking sensitive information
- API contract and migrations are updated
- affected documentation is updated or the gap is explicitly reported
- no fake claims or placeholder production data remain
- the final report states what ran and what did not

## Per-task checklist

- [ ] Read `AGENTS.md` and the relevant project documents
- [ ] Confirm exact scope; do not add speculative features
- [ ] Preserve separate frontend/backend responsibilities
- [ ] Ask before dependencies, destructive actions, commits, or deployments
- [ ] Use typed configuration and no hardcoded secrets
- [ ] Validate all input and authorize every protected object server-side
- [ ] Route workflow changes through central transition functions
- [ ] Preserve the 65% price / 35% distance ranking unless explicitly approved
- [ ] Apply crop-upload, AI-safety, weather, location, and privacy rules
- [ ] Make offline mutations idempotent and test duplicate/reconnect behavior
- [ ] Add or update tests for every changed business/security rule
- [ ] Check Bangla, mobile, accessibility, reduced motion, and low connectivity
- [ ] Check N+1 queries, indexes, unbounded responses, and heavy bundles
- [ ] Run relevant lint, type-check, tests, build, and security scans
- [ ] Update affected documentation
- [ ] Report files changed, commands run, results, and remaining risks
