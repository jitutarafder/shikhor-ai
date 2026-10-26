# Product Requirements Document (PRD)

## Shikhor AI — Bangladesh Agricultural Support Platform

**Status:** Draft for validation  
**Version:** 1.0  
**Primary market:** Bangladesh  
**Primary language:** Bangla, with English as a secondary option  
**Delivery model:** Separate frontend and backend applications

---

## 1. Product Summary

Shikhor AI is a mobile-first agricultural support platform for Bangladeshi farmers. It brings six common needs into one simple product:

1. AI-assisted crop problem identification from a photo or Bangla/Banglish description
2. Nearby agricultural equipment discovery and rental requests
3. Weather-based farming guidance and three-day activity planning
4. Direct communication with equipment owners
5. Connections between farmers and potential crop buyers
6. Offline access to essential knowledge, with queued requests and messages that synchronize later

The product provides decision support—not a guaranteed diagnosis, marketplace guarantee, or replacement for an agricultural officer.

---

## 2. Problem Statement

Bangladeshi farmers often face fragmented access to crop guidance, machinery, weather information, buyers, and expert help. Existing digital services may be difficult to use because of complex language, low digital literacy, unreliable internet, or information that is not immediately actionable.

The product must turn these fragmented needs into short, understandable workflows that work well on budget Android phones and remain useful during weak or unavailable connectivity.

---

## 3. Goals

### Product goals

- Help farmers understand a possible crop problem and the next safe action.
- Help farmers find affordable, nearby machinery using transparent ranking.
- Convert raw weather data into practical activity windows and warnings.
- Enable direct, privacy-aware communication among farmers, owners, and buyers.
- Preserve essential functionality during network loss.
- Build trust through transparent AI confidence, moderation, and clear limitations.

### Business and adoption goals

- Validate that farmers can complete core tasks without assisted training.
- Establish a reliable supply of equipment listings in target districts.
- Build a repeatable onboarding process for farmers, equipment owners, buyers, and experts.
- Measure successful connections and completed workflows, not vanity traffic.

### Non-goals for the MVP

- Guaranteed medical/agronomic diagnosis
- Automated pesticide prescription
- Online payment settlement or escrow
- Full logistics and delivery management
- National-scale rollout on day one
- A separate microservice for every feature
- Blockchain, IoT, drone control, or satellite analytics
- Replacing government or certified agricultural advice

---

## 4. Success Metrics

Targets must be finalized after pilot research. Until then, measure baselines rather than inventing performance claims.

### Activation

- Percentage of new users who complete a first core action
- Signup completion rate by role
- Time to first crop check, equipment search, or weather plan

### Task success

- Crop submissions that produce a usable result or safe escalation
- Equipment searches that lead to a call, message, or rental request
- Weather plans viewed before a planned activity
- Offline actions successfully synchronized after reconnection

### Quality and trust

- AI results flagged as incorrect or unhelpful
- Low-confidence results correctly escalated
- Equipment listings reported or rejected
- Message/report resolution time
- User-rated clarity of Bangla guidance

### Reliability

- API availability and error rate
- P95 response time by endpoint category
- Image-analysis completion and failure rates
- Sync success rate and median time to recovery
- Crash-free frontend sessions

---

## 5. Users and Roles

### Farmer

Needs crop assistance, weather guidance, equipment, knowledge, and buyer connections. May have low digital literacy and intermittent internet.

### Equipment owner

Lists equipment, sets price and service area, manages availability, receives calls/messages and rental requests.

### Buyer

Finds crop availability and communicates with farmers. Verification and abuse controls are required.

### Agricultural expert/officer

Reviews escalated cases or contributes approved knowledge when the operational model supports it. The MVP may provide referral information before implementing in-platform case handling.

### Moderator

Reviews reports, suspicious listings, unsafe content, and disputes. Cannot access data beyond assigned duties.

### Administrator

Manages roles, reference data, moderation rules, content publication, and system configuration. Admin actions require audit logs.

---

## 6. Primary User Journeys

### Journey A — Crop problem assistance

1. Farmer chooses camera, gallery, or text description.
2. Product explains photo requirements and consent.
3. Farmer submits crop type, optional symptoms, and image.
4. Backend validates and analyzes the submission.
5. Product shows possible condition, confidence band, reason summary, basic safe guidance, and limitations.
6. If confidence is below the approved threshold or the case is unsupported, product recommends expert help.
7. The farmer may save the result to disease history.

### Journey B — Equipment discovery

1. Farmer chooses equipment type, location, date, and optional price range.
2. Backend returns available listings within a configurable radius.
3. Results are ranked using normalized price score (65%) and distance score (35%).
4. Product displays the ranking explanation, price unit, distance, availability, and owner status.
5. Farmer calls, messages, or creates a rental request.
6. Owner accepts, rejects, or proposes changes.

### Journey C — Weather planning

1. Farmer selects or confirms location.
2. Backend retrieves weather data from the configured provider.
3. Rules translate weather into a three-day activity plan and risk notices.
4. Product shows suitable windows and uncertainty/last-updated time.
5. Equipment workflows show relevant weather risks before a request.

### Journey D — Offline request

1. Network becomes unavailable.
2. Product clearly enters offline mode.
3. Farmer reads previously downloaded knowledge or prepares a request/message.
4. Action is stored in IndexedDB with an idempotency key.
5. When connectivity returns, the frontend retries safely.
6. Product shows synced, failed, or conflict status without claiming server success too early.

### Journey E — Buyer connection

1. Farmer publishes crop availability with quantity, unit, location, expected date, and optional images.
2. Buyer filters suitable listings.
3. Buyer starts a private conversation or uses an allowed contact method.
4. Users can block or report abusive behavior.

---

## 7. Functional Requirements

Priority labels: **P0 = MVP required**, **P1 = important after MVP**, **P2 = later**.

### 7.1 Public website

- **P0:** Home, Features, About, Contact, Login, and Signup pages
- **P0:** Bangla-first responsive layout
- **P0:** Language switch between Bangla and English
- **P0:** SEO metadata, Open Graph metadata, sitemap, and robots configuration
- **P0:** Accessible navigation and forms
- **P0:** Low-bandwidth image delivery
- **P1:** Product demo or guided tour
- **P2:** Verified case studies and partner logos

### 7.2 Authentication and onboarding

- **P0:** Phone or email account flow; final method depends on OTP provider availability
- **P0:** Secure password hashing if password login is used
- **P0:** Access and refresh-token lifecycle
- **P0:** Role selection and minimum profile information
- **P0:** District/upazila selection without mandatory GPS
- **P0:** Logout from current session
- **P1:** Session/device management and logout-all
- **P1:** Verified role badges for owners/buyers/experts
- **P2:** Federated login, only if a real adoption need exists

### 7.3 Crop assistant

- **P0:** JPEG/PNG/WebP image upload with documented size limit
- **P0:** Bangla/Banglish text description
- **P0:** Crop category selection
- **P0:** AI result with possible condition, confidence band, reason summary, and safe basic actions
- **P0:** Unsupported/uncertain state and expert referral
- **P0:** Disease history visible to the owning user
- **P0:** Feedback: helpful, not helpful, incorrect, unsafe
- **P1:** Expert review workflow
- **P1:** Multiple image angles
- **P2:** Region/season-aware model improvement after validated data collection

The product must never present an AI result as certain when evidence is insufficient.

### 7.4 Equipment marketplace

- **P0:** Equipment categories: tractor, harvester, pump, sprayer
- **P0:** Owner can create, edit, pause, and remove a listing
- **P0:** Price with explicit unit (per hour/day/acre or configured local unit)
- **P0:** Approximate location, service radius, availability, and contact options
- **P0:** Search by type, location, date, price, and distance
- **P0:** Transparent ranking: 65% normalized price + 35% normalized distance
- **P0:** Rental request with status: pending, accepted, rejected, cancelled, completed
- **P0:** Ownership checks on all listing/request actions
- **P1:** Owner verification and rating after completed rentals
- **P1:** Calendar availability
- **P2:** Payments and dispute workflow after legal/business validation

#### Ranking requirements

- Normalize price within comparable equipment type and pricing unit.
- Normalize distance within the active search radius.
- Lower combined score ranks higher.
- Missing/invalid values must not silently receive a better score.
- Surface sponsored placement separately if ever introduced; it must not alter organic ranking invisibly.

### 7.5 Weather guidance

- **P0:** Location-based forecast with manual location fallback
- **P0:** Current conditions and three-day forecast
- **P0:** Rule-based activity windows for spraying, harvesting, irrigation, and equipment use
- **P0:** Last updated time and provider attribution where required
- **P0:** Graceful unavailable/stale state
- **P1:** Saved locations and crop-specific preferences
- **P1:** Severe weather notification after consent

Weather guidance must distinguish provider data from product-generated recommendations.

### 7.6 Crop buyer connection

- **P0:** Farmer crop-availability listing
- **P0:** Buyer search and filtering
- **P0:** Private message or controlled contact action
- **P0:** Block and report
- **P0:** Listing lifecycle: draft, active, paused, closed
- **P1:** Buyer verification
- **P1:** Saved searches
- **P2:** Offers, contracts, and payments

### 7.7 Messaging

- **P0:** One-to-one conversations tied to equipment or crop listings
- **P0:** Text messages with offline queue support
- **P0:** Delivery state: queued, sent, failed
- **P0:** Pagination and unread count
- **P0:** Blocking and reporting
- **P1:** Image attachments after moderation and storage controls
- **P1:** Near-real-time updates using polling or WebSocket after MVP stability

### 7.8 Agricultural knowledge

- **P0:** Admin-published Bangla knowledge articles
- **P0:** Crop, fisheries, livestock, and farming-practice categories
- **P0:** Search and readable article pages
- **P0:** Download for offline use and show downloaded version/date
- **P0:** Content source and review status
- **P1:** Expert-authored updates and version history
- **P2:** Personalized recommendations

### 7.9 Offline behavior

- **P0:** Cache application shell and selected public content
- **P0:** Store selected knowledge articles locally
- **P0:** Queue rental requests and messages
- **P0:** Show queue count, state, and last successful sync
- **P0:** Use idempotency keys to prevent duplicate server actions
- **P0:** Manual retry and conflict/error states
- **P1:** Optional encrypted local storage for sensitive drafts where technically justified

Authentication secrets, full private profiles, and unnecessary personal data must not be stored in general-purpose offline caches.

### 7.10 Administration and moderation

- **P0:** Role-protected admin interface
- **P0:** Review reports, suspend listings, and restrict accounts
- **P0:** Manage equipment categories, geographic reference data, and knowledge articles
- **P0:** Audit admin/moderator actions
- **P0:** Dashboard based on real system data only
- **P1:** AI feedback review queue
- **P1:** Verification workflow

---

## 8. Content and Localization Requirements

- Bangla copy must be reviewed by a native speaker familiar with agricultural terminology.
- English translations must be linked through stable content keys.
- Dates, time, numbers, currency, and units must be localized.
- Use BDT (`৳`) with explicit rate units.
- Preserve common Banglish input for NLP, but display normalized Bangla guidance where possible.
- Avoid technical ML terms in farmer-facing text unless explained.

---

## 9. Non-Functional Requirements

### Performance

- Mobile-first and usable on low-end Android devices.
- Optimize the initial marketing route for a fast first render on slow networks.
- Compress and resize uploaded images client-side when safe, then validate again on the server.
- Defer maps and heavy libraries until needed.
- Define measured performance budgets before production release.

### Availability and resilience

- No frontend action should report server success before confirmation.
- External provider failures must return understandable fallback states.
- Retry only idempotent operations automatically.
- Database backups and restoration tests are required before production.

### Accessibility

- Target WCAG 2.2 AA.
- Minimum 44×44px touch targets.
- Keyboard navigation, visible focus, semantic HTML, and screen-reader labels.
- Respect reduced-motion preferences.

### Privacy

- Collect the minimum data needed for each workflow.
- Explain location, camera, contact, and notification permissions at the moment of use.
- Provide data export/correction/deletion processes appropriate to policy and law.

### Observability

- Structured logs without secrets or raw sensitive content.
- Request correlation IDs.
- Error monitoring, uptime checks, and provider failure metrics.
- Audit logs for privileged actions.

---

## 10. MVP Acceptance Criteria

The MVP is ready for a controlled pilot only when:

- A user can register, log in, and complete role onboarding.
- A farmer can submit a crop image/text and receive a transparent result or safe escalation.
- Equipment owners can manage listings and farmers can search and create rental requests.
- Ranking uses the documented 65/35 formula and is tested.
- Weather data produces a three-day plan with attribution and stale/error states.
- Farmers and buyers can create/search crop listings and communicate privately.
- Selected knowledge works offline.
- Queued rental requests/messages synchronize without duplication.
- Admin/moderator actions are role-protected and audited.
- Security tests, accessibility checks, backup restoration, and mobile QA pass.
- No fake metrics, testimonials, partners, or AI accuracy claims appear in production.

---

## 11. Dependencies and Open Decisions

- Final product name and visual identity
- Pilot districts and crop scope
- Approved agricultural knowledge sources and expert reviewers
- AI model choice, evaluation dataset, confidence thresholds, and escalation policy
- Weather provider, quota, attribution, and commercial terms
- OTP/SMS provider and cost
- Object-storage and hosting providers
- Buyer/equipment-owner verification process
- Privacy, retention, and incident-contact policy
- Whether calls expose personal phone numbers or use a mediated contact flow
- Operating model for expert referrals and moderation

---

## 12. Reference Standards

- OWASP API Security Top 10: <https://owasp.org/API-Security/editions/2023/en/0x11-t10>
- FastAPI security guidance: <https://fastapi.tiangolo.com/tutorial/security/>
- PWA offline data guidance: <https://web.dev/learn/pwa/offline-data>
- WCAG: <https://www.w3.org/WAI/standards-guidelines/wcag/>
