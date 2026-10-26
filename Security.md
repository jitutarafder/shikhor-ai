# Security and Privacy Requirements

## Shikhor AI

**Version:** 1.0  
**Applies to:** Public website, React/PWA frontend, FastAPI backend, database, AI pipeline, admin tools, integrations, and operational processes

---

## 1. Security Objectives

1. Protect identities, phone/email details, location, messages, crop images, and account credentials.
2. Prevent users from reading or modifying resources they do not own.
3. Prevent abuse of login, OTP, messaging, AI analysis, uploads, and external-provider quotas.
4. Keep offline data and synchronization behavior honest and recoverable.
5. Protect agricultural guidance from unauthorized or unsafe modification.
6. Preserve evidence of privileged actions without logging sensitive content.
7. Make incident response, revocation, backup restoration, and rollback practical.

Security is a release requirement, not a final-phase feature.

---

## 2. Security Governance

### Ownership

- Assign a security owner before pilot launch.
- Assign an incident lead and backup contact.
- Maintain an inventory of applications, domains, APIs, databases, storage, models, and external providers.
- Review this document for every major release or architecture change.

### Policies required before production

- Privacy notice
- Terms of use
- Data retention/deletion policy
- Acceptable use and marketplace conduct
- Vulnerability reporting contact
- Incident response plan
- Access-control and offboarding process
- Backup and restoration policy
- AI safety and content-review policy

---

## 3. Data Classification

| Class | Examples | Handling |
|---|---|---|
| Public | Marketing content, published knowledge | Cacheable after content review |
| Internal | Operational metrics, non-sensitive configuration | Staff need-to-know |
| Confidential | Phone/email, approximate private location, rental requests, private messages | Encrypted in transit/at rest, strict authorization |
| Restricted | Password hashes, refresh sessions, OTP records, precise location, original private crop images, admin secrets | Minimum access, short retention, audited access |

Never store passwords, API secrets, access tokens, refresh tokens, or OTP codes in logs, analytics, URLs, client telemetry, or general-purpose offline caches.

---

## 4. Threat Model

### Primary threats

- Account takeover through credential stuffing, OTP abuse, or stolen refresh sessions
- Broken object-level authorization across equipment, messages, crop cases, and buyer listings
- Role escalation into owner, expert, moderator, or admin actions
- Malicious file uploads and oversized-image resource exhaustion
- Automated scraping, spam, harassment, and fraudulent listings
- Exact-location exposure or unwanted phone-number disclosure
- Prompt injection or unsafe AI-generated agricultural advice
- External-provider compromise or unsafe responses
- Duplicate offline synchronization creating repeated requests/messages
- XSS through profile/listing/message/knowledge content
- CSRF when cookie-based authentication is used
- SQL injection, SSRF, insecure direct object references, and mass assignment
- Dependency, CI/CD, and leaked-secret compromise
- Stale PWA caches delivering outdated code/content
- Unauthorized admin access or audit-log tampering

The API controls must explicitly address the OWASP API Security Top 10, including broken object authorization, broken authentication, unrestricted resource consumption, function-level authorization, SSRF, misconfiguration, inventory management, and unsafe consumption of APIs: <https://owasp.org/API-Security/editions/2023/en/0x11-t10>.

---

## 5. Authentication

### Passwords

If password login is enabled:

- Hash with Argon2id using parameters reviewed for the production runtime.
- Never encrypt or reversibly store passwords.
- Minimum length: 10 characters; permit long passphrases.
- Check against commonly compromised passwords where practical.
- Do not require arbitrary periodic rotation unless compromise is suspected.
- Password reset responses must not reveal whether the account exists (non-enumerating).

### Federated Authentication (Google Sign-In)

- Google Sign-In is authenticated client-side via Firebase Auth (`signInWithPopup`).
- The backend authoritatively verifies Google ID Tokens (`accounts:lookup` / Google public keys) via the Firebase Verifier integration.
- Backend extracts verified email, display name, and provider subject ID.
- Issues standard, short-lived Argon2id/JWT access and refresh tokens.

### Password Reset & Email OTP

- Generated OTPs are 6 cryptographically secure digits.
- Store only the SHA-256 hash of the OTP in `password_reset_otps`.
- Valid for 10 minutes with single-use consumption.
- Rate-limited to max 5 failed verification attempts per OTP.
- On successful verification, issues an opaque, single-use 32-byte `reset_token` valid for 15 minutes.
- Password reset immediately hashes the new password with Argon2id and revokes all existing refresh sessions.

### Registration Email OTP Verification

- Registration mandates a valid email address and authoritative email ownership verification.
- Farmers initiate signup by receiving a cryptographically secure 6-digit OTP to their email address (`/api/v1/auth/signup/send-email-otp`).
- Email uniqueness is authoritatively verified prior to OTP issuance.
- OTP records are stored with SHA-256 hash in `signup_email_otps` table (restricted classification, never logged or exposed in production).
- Valid for 10 minutes with single-use consumption and rate-limited to max 5 failed attempts per OTP.
- On successful verification (`/api/v1/auth/signup/verify-email-otp`), server mints an opaque, cryptographically secure 32-byte `verification_token`.
- Account creation (`/api/v1/auth/register`) strictly requires and authoritatively consumes the `verification_token`, ensuring the client cannot bypass email verification.
- Upon successful account creation, the user record is marked with `is_email_verified: True`.

### Identity Verification (National ID - NID & Photo Upload)

- Bangladeshi National ID (NID) is strictly validated during registration.
- Accepted formats: 10-digit Smart Card, 13-digit traditional NID, or 17-digit birth-year prefixed NID (`^(\d{10}|\d{13}|\d{17})$`).
- Uniqueness is authoritatively enforced by database constraint and application service.
- **4-Stage Registration Sequence & Account Approval Gate**:
  - Stage 1: Basic personal credentials (Full Name, Phone, NID Number, Date of Birth, Password >= 10 chars).
  - Stage 2: Account Role selection (Farmer, Owner, Buyer, Expert).
  - Stage 3: Mandatory Gmail OTP verification with single-use verification token issuance.
  - Stage 4: NID front and back photo upload with district/upazila location onboarding.
  - Image uploads are strictly sanitized: validated against allowed MIME types (JPEG, PNG, WebP) and maximum 5MB size limit.
  - Newly created accounts have `is_nid_verified: False`, `is_verified: False`, and `nid_verification_status: "pending"`.
  - **Feature Access Lock**: Users can authenticate and log in, but all operational platform features (`/app/*`) are gated behind `AppRouteGuard` and display the `AccountApprovalLock` screen until manual administrator review.
  - Authorized Administrators and Moderators manually inspect photos and details in the Admin Dashboard (`/app/admin`).
  - Approval or rejection records an immutable audit log entry (`NID_VERIFICATION_APPROVED` / `NID_VERIFICATION_REJECTED`) containing reviewer actor ID, phone, role, and rejection rationale (Rule 26).
  - On administrator approval, `is_verified = True`, `is_nid_verified = True`, `nid_verification_status = "approved"`, and all operational features unlock immediately.

### Phone OTP

- Generate cryptographically secure random values / Firebase Phone Authentication.
- Store only a keyed hash of the OTP when generated internally.
- Expire after a short period, such as 5 minutes.
- Single use; invalidate after success.
- Limit send and verify attempts by account, phone, IP/risk signal, and time window.
- Add cooldown and progressive delay.
- Monitor SMS pumping and quota abuse.
- Never log the OTP in production.

### Sessions and tokens

- Access credential lifetime should be short.
- Refresh tokens must rotate on use.
- Store refresh-session hashes/identifiers server-side for revocation and reuse detection.
- Revoke sessions after password reset, security incident, or explicit logout-all.
- Use strong signing keys stored in a secret manager or protected platform configuration.
- Include issuer, audience, subject, issued-at, expiration, and unique token/session identifiers.
- Reject weak/unexpected algorithms.

### Browser storage

Preferred option when deployment allows:

- Secure, HTTP-only, SameSite cookie for refresh session
- Access token in memory or a similarly constrained mechanism
- CSRF protection for state-changing cookie-authenticated requests

Do not put long-lived credentials in `localStorage` or IndexedDB.

### Administrative accounts

- Require multi-factor authentication before production.
- Use separate named accounts; no shared admin credentials.
- Require recent authentication for high-risk actions.
- Restrict admin access by role and environment.

---

## 6. Authorization

Use deny-by-default policies.

### Layers

1. Endpoint-level authentication
2. Role/capability check
3. Object-level ownership or participant check
4. Field-level write allowlist
5. State-transition validation

Examples:

- A farmer can read only their private crop cases.
- An equipment owner can update only equipment they own.
- Conversation messages are available only to active participants.
- A moderator can perform only assigned moderation functions.
- An admin cannot retrieve raw secrets through any API.

### Implementation requirements

- Central policy functions/dependencies; do not scatter ad hoc checks.
- Query resources scoped by actor/tenant/ownership where possible.
- Never trust role, owner ID, price score, or moderation status from the client.
- Use response schemas to prevent excessive data exposure.
- Test an authorization matrix for every resource and action.

---

## 7. API Security

### Validation

- Pydantic request models with strict types and length/range limits
- Reject unknown fields for sensitive write models
- Enumerations for roles, states, units, and categories
- Server-calculated owner/user IDs
- Parameterized ORM/database operations
- Pagination limits and bounded filters
- Explicit response models

### Rate limiting and resource controls

Apply endpoint-specific limits to:

- Login, password reset, OTP send/verify
- Crop-image analysis
- Equipment/location searches
- Messaging and contact actions
- Contact form and reports
- AI/provider-backed endpoints
- Export or bulk operations

Also enforce maximum request body, JSON depth, string length, array size, upload size, database timeout, external-call timeout, and per-user concurrent AI jobs. OWASP recommends bounding payloads and applying operation-specific rate limits to prevent unrestricted resource consumption: <https://owasp.org/API-Security/editions/2023/en/0xa4-unrestricted-resource-consumption>.

### Error handling

- Use stable public error codes.
- Do not expose stack traces, SQL, internal paths, secrets, provider responses, or model prompts.
- Return a request ID for support correlation.
- Log sanitized technical details server-side.

### CORS

- Allow only exact production/staging frontend origins.
- Do not combine wildcard origins with credentials.
- Restrict methods and headers to those needed.

### CSRF

If cookies authenticate requests:

- Use SameSite settings appropriate to deployment.
- Require a CSRF token or a robust origin-based strategy for state-changing requests.
- Validate `Origin`/`Referer` for browser mutations as defense in depth.

### Idempotency

- Require a unique idempotency key for offline-created rental requests and messages.
- Bind the key to user, operation, and normalized request body hash.
- Store the original outcome for a defined retention window.
- Replays return the original result; conflicting payloads return an error.

---

## 8. File Upload Security

Crop images and future attachments are untrusted input.

- Allow only required formats: JPEG, PNG, WebP.
- Validate extension, MIME type, and file signature.
- Set conservative upload and pixel-dimension limits.
- Reject decompression bombs and malformed images.
- Decode and re-encode into a safe derivative before analysis/display.
- Strip EXIF/GPS metadata unless explicit consent and a documented need exist.
- Generate random storage object names; never use user filenames as paths.
- Store outside the application web root in private object storage.
- Serve through authorization checks or short-lived signed URLs.
- Add malware scanning where attachment types expand.
- Apply retention/deletion rules to originals and derivatives.
- Never execute uploaded content.

SVG, HTML, PDF, archives, and executable formats should not be accepted for crop analysis.

---

## 9. Frontend and PWA Security

### XSS

- Rely on React escaping for text.
- Avoid `dangerouslySetInnerHTML`.
- If rich knowledge content is required, sanitize with an allowlist on both publication and rendering paths.
- Encode URLs and reject unsafe schemes.
- Use Content Security Policy (CSP) with nonces/hashes where the hosting model permits.

### Security headers

Recommended baseline:

```text
Content-Security-Policy: default-src 'self'; ...
Strict-Transport-Security: max-age=31536000; includeSubDomains
X-Content-Type-Options: nosniff
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(self), geolocation=(self), microphone=()
Cross-Origin-Opener-Policy: same-origin
```

Finalize CSP from actual providers; do not deploy an untested copied policy.

### Service worker

- Cache only explicit routes/assets.
- Version caches and remove old versions during activation.
- Do not cache authenticated API responses by default.
- Prevent the service worker from storing tokens or private admin content.
- Provide a safe update flow when a new frontend build is available.
- Test logout to ensure private cached data is removed where required.

### Offline data

- Store only data necessary for offline workflows.
- Mark private local records by account ID and clear them on logout/account change.
- Avoid storing precise location, tokens, private profile data, or entire conversation history unless explicitly approved.
- Device storage is not a trusted secret store.
- Show users what is queued and allow deletion before sync.

---

## 10. Database Security

- Use managed encryption at rest or equivalent disk/database encryption.
- Require TLS from backend to database in production.
- Use a dedicated application DB role without superuser privileges.
- Separate migration and read-only analytics privileges.
- Restrict network access to approved runtime environments.
- Use parameterized queries/ORM.
- Back up on a defined schedule and encrypt backups.
- Test restoration regularly.
- Protect database snapshots and exports as Restricted data.
- Apply retention to sessions, audit logs, crop images, and messages.

Do not expose PostgreSQL directly to the public internet.

---

## 11. Location and Contact Privacy

- Ask for GPS only when needed and explain the benefit.
- Allow manual district/upazila selection.
- Do not show exact home coordinates on public maps.
- Round, grid, or offset public listing coordinates.
- Reveal detailed location only to authorized parties at the correct workflow stage.
- Let users choose whether their phone number is visible.
- Prefer in-platform messaging before direct contact where feasible.
- Log and review repeated contact scraping or enumeration behavior.

---

## 12. Messaging, Marketplace, and Abuse Controls

- Block/report controls in every conversation and listing.
- Message send limits for new/unverified accounts.
- URL and spam detection with human-review appeal.
- Prevent phone/email scraping through list endpoints.
- Avoid publishing full user directories.
- Record listing ownership and moderation state.
- Preserve moderation evidence under a documented retention policy.
- Clearly separate verified and unverified status.
- Do not allow client-supplied ratings or completed-transaction claims without server validation.

Threats include fraud, harassment, false machinery listings, unsafe agricultural advice, and buyer impersonation—not only technical attacks.

---

## 13. AI and Model Security

### Input controls

- Treat image captions, Bangla/Banglish descriptions, knowledge documents, and external content as untrusted data.
- Separate system instructions from user input.
- Use structured schemas for model output.
- Set time, token, and cost limits.
- Do not allow model output to call tools or URLs without an explicit allowlisted workflow.

### Guidance safety

- Use reviewed knowledge for actionable agricultural guidance.
- Do not let a general language model invent pesticide names, dosage, or emergency advice.
- Apply confidence thresholds and unsupported-case detection.
- Show model limitations and escalate uncertain cases.
- Store model/prompt/config version for audit and regression.
- Provide user feedback and expert review channels.

### Provider privacy

Before sending data to Gemini, Claude, or another provider:

- Review provider data usage, retention, location, and training terms.
- Remove unnecessary identifiers.
- Do not send phone numbers, private message history, or precise address.
- Use enterprise/API settings appropriate for private data.
- Document international transfer implications where applicable.

### Model supply chain

- Pin model artifacts and dependencies.
- Verify checksums/signatures when available.
- Restrict who can promote a model to production.
- Evaluate every new version before rollout.
- Support rollback.

---

## 14. External Integration Security

- Store provider keys server-side in secrets management.
- Separate keys by environment.
- Give each key the minimum scope and quota.
- Rotate keys after exposure and on a defined schedule.
- Validate TLS certificates.
- Apply strict outbound timeouts and bounded retries.
- Validate and normalize external responses.
- Do not follow arbitrary user-supplied URLs from the server.
- Allowlist outbound hosts where practical to reduce SSRF risk.
- Monitor quota, error, and cost anomalies.

External data is untrusted even when it comes from a contracted provider.

---

## 15. Logging, Monitoring, and Audit

### Security events

Capture:

- Login success/failure without credentials
- OTP send/verify outcome
- Session creation, rotation, revocation, reuse detection
- Authorization denials
- Rate-limit events
- Admin/moderator actions
- Listing suspension and report resolution
- Model version and result status
- Provider failures
- Data export/deletion events

### Do not log

- Passwords or hashes
- OTP values
- Access/refresh tokens
- Authorization headers or cookies
- Full private messages
- Raw precise coordinates unless strictly needed and protected
- Unredacted crop images
- Full provider prompts containing user data

### Audit integrity

- Audit entries are append-oriented.
- Include actor, action, resource, timestamp, request ID, and before/after summary where safe.
- Limit access and monitor deletion/export.
- Synchronize server clocks.

---

## 16. Secrets and CI/CD

- No secrets in Git, frontend bundles, Dockerfiles, screenshots, tickets, or chat.
- Use secret scanning in pre-commit and CI.
- Protect production deployment environments with approval rules.
- Use short-lived CI credentials where supported.
- Pin actions/build tools to trusted versions.
- Generate SBOMs for release artifacts where feasible.
- Scan dependencies and container images.
- Sign or record immutable digests for deployed images.
- Restrict who can modify pipelines and branch protection.

---

## 17. Vulnerability Management

- Weekly automated dependency scanning; urgent review for actively exploited issues.
- Static analysis on every pull request.
- Dynamic/API scanning against staging.
- Manual authorization and business-logic testing before pilot.
- External penetration test before large-scale launch or payments.
- Track findings with severity, owner, due date, and verification.

Suggested remediation targets:

| Severity | Target |
|---|---|
| Critical | Immediate containment; fix/mitigate within 24–48 hours |
| High | 7 days |
| Medium | 30 days |
| Low | 90 days or accepted with rationale |

Adjust targets to team capacity and real risk; documented exceptions require an owner and expiration date.

---

## 18. Incident Response

1. Detect and record the event.
2. Triage scope, affected data/users, and current exposure.
3. Contain: revoke sessions/keys, block abuse, isolate systems.
4. Preserve evidence with controlled access.
5. Eradicate root cause and validate fixes.
6. Restore from trusted state and monitor.
7. Notify affected parties/regulators when required by applicable law/policy.
8. Complete a blameless post-incident review with actions and owners.

Prepare runbooks for credential leak, account takeover, malicious upload, database exposure, provider-key abuse, unsafe AI guidance, and lost/stolen admin access.

---

## 19. Security Verification Checklist

### Before every release

- [ ] No secrets in code, logs, build artifacts, or frontend bundle
- [ ] Dependency and container scans reviewed
- [ ] Authentication and authorization tests pass
- [ ] CORS, CSRF, cookies, and headers verified in deployed environment
- [ ] Upload limits and image re-encoding tested
- [ ] Rate limits active on abuse-prone endpoints
- [ ] Error responses contain no internal detail
- [ ] Service-worker cache behavior tested
- [ ] Provider timeouts and failures tested
- [ ] Audit events generated for privileged actions

### Before pilot

- [ ] Threat model reviewed
- [ ] Admin MFA enabled
- [ ] Backup restoration tested
- [ ] Data retention rules implemented
- [ ] Privacy notice and consent flows approved
- [ ] Unsafe AI output evaluation completed
- [ ] Authorization matrix manually tested
- [ ] Incident contacts and runbooks confirmed

### Before public scale

- [ ] Independent penetration test completed
- [ ] Load and abuse tests completed
- [ ] Monitoring and on-call alerts exercised
- [ ] Model/provider privacy review complete
- [ ] Verification and moderation capacity validated
- [ ] Disaster recovery exercise complete

---

## 20. References

- OWASP API Security Top 10 2023: <https://owasp.org/API-Security/editions/2023/en/0x11-t10>
- OWASP API4 resource consumption: <https://owasp.org/API-Security/editions/2023/en/0xa4-unrestricted-resource-consumption>
- FastAPI security: <https://fastapi.tiangolo.com/tutorial/security/>
- FastAPI OAuth2/JWT example: <https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt>
- PWA offline data: <https://web.dev/learn/pwa/offline-data>
