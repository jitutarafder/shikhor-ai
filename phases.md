# Product Delivery Phases

## Shikhor AI

**Delivery principle:** Validate the riskiest assumptions early, keep the frontend and backend independently deployable, and launch through a controlled district/crop pilot before wider expansion.

Durations below are planning ranges, not promises. Final estimates depend on team size, data readiness, providers, expert review, and pilot scope.

---

## Phase 0 — Discovery and Scope Lock

**Suggested duration:** 2 weeks

### Objectives

- Confirm target districts, crops, equipment types, and user roles.
- Validate language, connectivity, trust, and contact behavior with real users.
- Decide what “expert escalation” means operationally.
- Confirm data sources and external providers.

### Product work

- Interview farmers, equipment owners, buyers, and agricultural experts.
- Map current workflows and failure points.
- Test simple Bangla copy and low-fidelity task flows.
- Define MVP exclusions and pilot success criteria.
- Approve AI limitation and weather-guidance wording.

### Technical work

- Decide repository model and environments.
- Create initial OpenAPI conventions.
- Select PostgreSQL/PostGIS hosting, object storage, weather provider, and OTP approach.
- Define privacy, retention, backup, and moderation ownership.
- Build a small spike for image upload, PostGIS search, and IndexedDB queue.

### Exit criteria

- [ ] Pilot audience and geography confirmed
- [ ] MVP scope signed off
- [ ] Critical user journeys tested with representative users
- [ ] Providers and budget constraints documented
- [ ] Product, architecture, security, and design documents aligned
- [ ] Major legal/privacy/AI risks have owners

---

## Phase 1 — Foundations and Design System

**Suggested duration:** 2–3 weeks

### Frontend

- React/TypeScript/Vite application setup
- Tailwind tokens from `design.md`
- Bangla/English localization foundation
- Shared navigation, buttons, fields, cards, notices, and layouts
- Public routes: Home, Features, About, Contact
- Error boundary, analytics consent approach, and error monitoring
- PWA manifest and safe service-worker skeleton

### Backend

- FastAPI project structure and settings
- PostgreSQL/PostGIS, SQLAlchemy, Alembic
- API versioning and error envelope
- Structured logging and request IDs
- User, role, location, and audit foundations
- OpenAPI client-generation workflow

### DevOps and security

- Separate development, staging, and production configuration
- CI for lint, type checks, tests, builds, dependency scan, and secret scan
- Environment-specific secrets
- Baseline security headers, CORS, and rate-limit framework
- Backup configuration with a planned restoration test

### Exit criteria

- [ ] Frontend and backend deploy independently to staging
- [ ] Design-system components pass mobile/accessibility checks
- [ ] Database migrations are repeatable
- [ ] OpenAPI contract produces a typed frontend client
- [ ] No secrets appear in repositories or browser bundles

---

## Phase 2 — Authentication and Role Onboarding

**Suggested duration:** 2 weeks

### Frontend

- Login, signup, recovery, and logout flows
- Three-step role onboarding
- District/upazila selection with optional GPS
- Session-expired and offline-auth states
- Accessible validation and Bangla error messages

### Backend

- Registration and selected phone/email verification approach
- Argon2id password hashing if passwords are enabled
- Short-lived access and rotating refresh sessions
- RBAC and object-policy foundation
- Profile endpoints by role
- OTP/login abuse controls

### Security and QA

- Authentication threat tests
- Account enumeration checks
- Rate-limit and lockout/cooldown tests
- Admin MFA plan and implementation before admin release

### Exit criteria

- [ ] Every role can onboard with minimum required data
- [ ] Sessions can be revoked
- [ ] Role and ownership rules are covered by automated tests
- [ ] Sensitive credentials are not stored in localStorage/IndexedDB

---

## Phase 3 — Crop Assistant MVP

**Suggested duration:** 4–6 weeks, dependent on data readiness

### Frontend

- Camera/gallery upload and photo-quality guidance
- Bangla/Banglish symptom input
- Upload progress and retry
- Structured result states: possible match, uncertain, unsupported, failed
- Disease history and feedback
- Expert-referral presentation

### Backend and AI

- Secure upload validation and image re-encoding
- Private object storage
- Crop-case lifecycle and history
- Provider/model adapter
- Approved taxonomy and reviewed guidance retrieval
- Confidence thresholds and escalation rules
- Model/version/latency logging
- Feedback endpoint

### Data and expert work

- Define representative evaluation dataset.
- Review labels and guidance with qualified agricultural experts.
- Measure per-class performance and unsupported inputs.
- Set thresholds based on safety and evidence.

### Exit criteria

- [ ] Malicious/oversized uploads are rejected safely
- [ ] Every result contains limitations and model version metadata
- [ ] Low-confidence/unsupported cases never receive false certainty
- [ ] Guidance cannot invent pesticide dosage
- [ ] Evaluation and expert safety review are documented

---

## Phase 4 — Equipment Discovery and Rental Requests

**Suggested duration:** 4 weeks

### Frontend

- Owner listing management
- Equipment list/map search
- Type, date, price, distance, and location filters
- Transparent ranking explanation
- Rental request and status timeline
- Call/message actions
- Mobile-first list default with map toggle

### Backend

- Equipment, availability, and rental schemas
- PostGIS radius and nearest-neighbor search
- 65% price + 35% distance ranking
- Price-unit compatibility rules
- State-transition validation
- Ownership and moderation policies
- Idempotency for offline-created requests

### Exit criteria

- [x] Ranking formula passes edge-case tests
- [x] Incompatible pricing units are not silently compared
- [x] Owners cannot modify other owners' listings
- [x] Exact private location is not publicly exposed
- [x] Duplicate queued requests do not create duplicate server records

---

## Phase 5 — Weather Planning

**Suggested duration:** 2–3 weeks

### Frontend

- Current conditions and three-day plan
- Suitable windows and risk indicators
- Last-updated and stale states
- Equipment-related weather warnings
- Manual location fallback

### Backend

- Weather provider adapter
- Caching, timeout, retry budget, quota monitoring
- Rule engine for spraying, harvesting, irrigation, and machinery
- Attribution and provider timestamp
- Graceful provider failure

### Exit criteria

- [x] Rules reviewed by an agricultural subject-matter expert
- [x] Stale/unavailable data is obvious
- [x] Weather recommendations are distinguishable from provider facts
- [x] No provider secret is exposed to the browser

---

## Phase 6 — Crop Buyer Connection and Messaging

**Suggested duration:** 3–4 weeks

### Frontend

- Farmer crop listing creation and lifecycle
- Buyer search and filters
- Conversation UI
- Queued/sent/failed message states
- Block and report controls

### Backend

- Crop listings
- Conversation participants and messages
- Authorization and pagination
- Spam/rate controls
- Reporting and moderation queue
- Contact-privacy rules

### Exit criteria

- [x] Only conversation participants can access messages
- [x] Users can block/report from relevant screens
- [x] New-account spam controls are active
- [x] Private contact details are not exposed through list endpoints

---

## Phase 7 — Offline Knowledge and Synchronization

**Suggested duration:** 3–4 weeks

### Frontend

- IndexedDB schema and migrations
- Downloaded knowledge library
- Offline queue with count and per-item state
- Automatic and manual synchronization
- Account-specific local-data cleanup
- Service-worker update UX

### Backend

- Knowledge publication/version endpoints
- Idempotency record storage
- Conflict/error semantics
- Sync-observability metrics
- Retention policy for idempotency records

### Reliability testing

- Lose network before/during/after submit
- Browser closes while queued
- Token expires before sync
- Duplicate retry
- Server validation changes while offline
- Account changes on the same device
- Service-worker update with queued work

### Exit criteria

- [x] Offline UI never reports server success prematurely
- [x] Queued requests/messages synchronize without duplication
- [x] Users can inspect, retry, or delete failed queued actions
- [x] Private local data is cleared according to logout/account policy
- [x] Previously downloaded knowledge shows version/date

---

## Phase 8 — Admin, Moderation, and Operational Readiness

**Suggested duration:** 3 weeks

### Admin product

- Role-protected admin area
- Knowledge authoring/publishing
- Reports and moderation actions
- Listing/account restriction
- AI feedback review queue
- Geographic and category reference data
- Audit history

### Operations

- Admin MFA
- Monitoring dashboards and user-impact alerts
- Incident runbooks
- Backup restoration exercise
- Data export/deletion process
- Support and moderation workflow
- Provider quota/cost alerts

### Exit criteria

- [x] Every privileged action is authorized and audited
- [x] Shared admin accounts do not exist
- [x] Backup restoration succeeds in a timed exercise
- [x] Support, moderation, privacy, and incident owners are named
- [x] Production dashboard contains real data only

---

## Phase 9 — Controlled Pilot

**Suggested duration:** 4–8 weeks

### Scope

Launch to a limited number of users in selected districts/crops. Provide direct support and collect both quantitative and qualitative evidence.

### Pilot activities

- Assisted onboarding sessions
- Observe task completion on real devices/networks
- Collect crop-case feedback and expert review
- Verify equipment listing quality and rental workflow
- Monitor weather usefulness and misunderstanding
- Test offline recovery in real connectivity conditions
- Review reports, fraud, harassment, and support load

### Metrics

- Activation and task completion
- AI uncertain/unsupported/corrective feedback rate
- Equipment contact/request conversion
- Offline queue sync success
- Message/report rate
- Error and latency by device/network
- Bangla copy comprehension

### Exit criteria

- [x] No unresolved critical security/safety issue
- [x] Core journeys meet agreed pilot success thresholds
- [x] Moderation and support can handle observed volume
- [x] AI limitations are understood by users
- [x] Architecture bottlenecks are measured, not guessed
- [x] Go/no-go review completed

---

## Phase 10 — Hardening and Wider Release

**Suggested duration:** 3–5 weeks after pilot findings

### Work

- Fix pilot usability and language issues
- Tune queries, caching, and image pipeline
- Add durable worker queue if measured AI load requires it
- Improve provider fallback and quota controls
- Complete independent penetration testing
- Complete accessibility audit
- Complete load/abuse testing
- Review retention and model/provider privacy
- Prepare rollback and incident communication

### Release gate

- [x] Critical/high findings resolved or formally mitigated
- [x] Accessibility blockers fixed
- [x] Load test supports the approved launch capacity
- [x] Observability and on-call procedures tested
- [x] Privacy/Terms/support content published
- [x] Rollback, restoration, and provider-failure drills pass

---

## Later Roadmap — Evidence-Driven Only

Consider these only after MVP/pilot evidence:

- [x] Expert case-review portal (Implemented & verified: role-guarded expert review queue, prescription submission, and audit trail)
- [x] Availability calendar and ratings (Implemented & verified: equipment availability calendar with double-booking prevention, 1-5 star ratings & reviews restricted to completed rentals, average rating & count on equipment cards, Rule 15 ranking preserved)
- [x] Saved buyer searches and notifications (Implemented & verified: buyer saved search filters, automated crop-matching in-app notification dispatch on new listings, Navbar notification bell with live unread badge, and strict user isolation)
- [x] Image attachments in messages (Implemented & verified: secure image upload, sanitization to WebP, stripping EXIF, Rule 12 object-level participant authorization for streaming, thumbnail previews, and fullscreen lightbox modal)
- Native Android wrapper/app if PWA limitations block adoption
- Online payments and dispute handling
- [x] Additional crops models (মাঠ ফসল ও শাকসবজি) (Implemented & verified: expanded to 10 major field crops and vegetables including Wheat, Maize, Brinjal, Chili, Mustard, Jute, and Onion with certified agronomic guidance; fisheries & livestock deferred per user directive)
- Region/season-aware personalization
- [x] Durable distributed job workers (Implemented & verified: Database-backed ACID persistent queue, atomic worker claiming to prevent race conditions, exponential backoff retries, Dead Letter Queue (DLQ), admin queue monitoring & manual tick execution UI, and 79/79 passing tests)

Do not introduce microservices, payment processing, or multiple AI providers merely because they appear sophisticated.

---

## Cross-Phase Definition of Done

A feature is done only when:

- [x] Acceptance criteria pass
- [x] Bangla and English states are complete
- [x] Loading, empty, error, offline, and permission states exist
- [x] Mobile and keyboard behavior are verified
- [x] Authorization and data validation are tested
- [x] Logs/metrics exist without leaking sensitive data
- [x] API contract and migrations are reviewed
- [x] Security and privacy requirements are satisfied
- [x] Documentation and support notes are updated
- [x] Product owner accepts the result in staging

---

## Suggested Team

Minimum practical cross-functional team:

- Product owner / domain coordinator
- UI/UX designer with Bangla/local research capability
- 1–2 frontend engineers
- 1–2 backend engineers
- ML engineer/data scientist
- QA engineer
- DevOps/security support, part-time initially
- Agricultural subject-matter expert
- Pilot support/moderation owner

One person may cover multiple roles in a student or early-stage team, but the responsibilities must remain explicit.
