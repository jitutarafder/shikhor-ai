# Bangladesh AI Agriculture Platform — UI/UX Design System

> **Working product name:** `Shikhor AI` (replace with the final brand name).  
> **Design goal:** A Bangla-first, trustworthy, warm, modern platform that feels easy for rural farmers while still looking credible to equipment owners, buyers, agricultural officers, and partners.

---

## 1. Product Experience

### Core feeling

The first screen should communicate three things within five seconds:

1. **This platform is made for Bangladeshi farmers.**
2. **It can help with crop disease, equipment, weather, and buyers.**
3. **It is simple enough to use from a phone—even with weak internet.**

### Brand personality

- **Helpful, not overly technical**
- **Local and human, not corporate or generic**
- **Modern, but familiar**
- **Calm and trustworthy, not flashy**
- **Optimistic, practical, and action-oriented**

### Primary audiences

- Farmers using budget Android phones
- Equipment owners
- Crop buyers
- Agricultural officers or experts
- Partners, NGOs, and administrators

### Experience principles

- Bangla is the primary language; English is optional.
- Use short sentences and one clear action per card.
- Prefer recognizable icons plus labels; never rely on icons alone.
- Important tasks must remain visible on mobile.
- Keep forms short, with large fields and clear error messages.
- Show online/offline/sync status honestly.
- AI results must communicate uncertainty and an escalation path.
- Avoid unrealistic claims such as “100% accurate disease detection.”

---

## 2. Visual Direction

### Creative concept: “Digital Bengal Field Guide”

Combine Bangladesh’s green agricultural landscape, warm sunlight, paddy-field geometry, and practical mobile tools. The interface should use clean white space and restrained illustration rather than a generic dark-green agriculture template.

### Signature visual motifs

- Soft contour lines inspired by agricultural land maps
- Rounded field-shaped masks for photography
- Fine dotted GPS paths around equipment/location visuals
- Small sunlight gradient accents for weather and positive actions
- Subtle Bengali alpana-inspired line details, used sparingly
- Real Bangladesh farming photography with natural colors

### Avoid

- Neon green gradients across the entire page
- Cartoon tractors or generic 3D farm clip art
- Heavy glassmorphism and excessive blur
- Fake dashboard statistics or unsupported testimonials
- Text placed over busy crop photos without a contrast layer
- Continuous animations that distract users or consume battery
- Excessively rounded “everything is a pill” layouts

---

## 3. Color System

The palette is nature-led but optimized for readable digital interfaces.

| Token | Hex | Usage |
|---|---:|---|
| `forest-900` | `#153D2C` | Main headings, dark hero surfaces |
| `forest-700` | `#216245` | Primary buttons, links, active states |
| `leaf-500` | `#42A66A` | Positive status, feature accents |
| `leaf-100` | `#E7F5EC` | Success/AI guidance backgrounds |
| `paddy-400` | `#D7B84A` | Warm highlights, weather windows |
| `sun-300` | `#F2CC67` | Small decorative accents only |
| `soil-700` | `#76543B` | Earth-tone illustrations and labels |
| `soil-100` | `#F5EEE7` | Warm section background |
| `sky-600` | `#2878A7` | Weather information and links |
| `danger-600` | `#C9463D` | High-risk warnings and errors |
| `ink-900` | `#17211B` | Primary body text |
| `ink-600` | `#5D685F` | Secondary text |
| `line-200` | `#DDE6DF` | Borders and dividers |
| `canvas` | `#FFFFFF` | Main background |
| `surface` | `#F7FAF7` | Alternate section background |

### Gradient accents

Use gradients only in selected hero or CTA details:

```css
--hero-glow: radial-gradient(circle at 80% 20%, #F2CC6755, transparent 34%);
--field-wash: linear-gradient(135deg, #E7F5EC 0%, #F7FAF7 55%, #F5EEE7 100%);
```

### Color rules

- Body text on white: `ink-900`.
- Primary button: `forest-700` with white text.
- Do not use `leaf-500` for small white text unless contrast is verified.
- Warning, error, success, and weather states must also include an icon and label.
- Minimum contrast: WCAG AA (`4.5:1` for normal text, `3:1` for large text/UI boundaries).

---

## 4. Typography

### Font stack

- **Bangla:** `Noto Sans Bengali`
- **English:** `Inter`
- **Fallback:** system sans-serif

```css
font-family: Inter, "Noto Sans Bengali", ui-sans-serif, system-ui, sans-serif;
```

### Type scale

| Style | Desktop | Mobile | Weight | Line height |
|---|---:|---:|---:|---:|
| Display | 64px | 40px | 700 | 1.08 |
| H1 | 52px | 36px | 700 | 1.12 |
| H2 | 40px | 30px | 700 | 1.18 |
| H3 | 26px | 22px | 650 | 1.25 |
| Body large | 20px | 18px | 400 | 1.6 |
| Body | 16px | 16px | 400 | 1.55 |
| Label | 14px | 14px | 600 | 1.4 |
| Caption | 13px | 13px | 500 | 1.4 |

### Copy style

- Use simple, respectful Bangla—not overly formal words.
- Provide Bangla/Banglish input examples where useful.
- CTA labels should begin with actions: “ছবি দিয়ে যাচাই করুন”, “যন্ত্র খুঁজুন”, “অ্যাকাউন্ট খুলুন”.
- Avoid long paragraphs; use two or three short lines.

---

## 5. Layout System

- Desktop content width: `1200px` maximum
- Reading width: `680–760px`
- Desktop gutter: `32–48px`
- Tablet gutter: `24px`
- Mobile gutter: `16px`
- Section spacing: `96px` desktop, `64px` tablet, `48px` mobile
- Grid: 12 columns desktop, 8 tablet, 4 mobile
- Base spacing: `4, 8, 12, 16, 24, 32, 48, 64, 96`
- Card radius: `16px`; button/input radius: `12px`
- Use borders before shadows.

```css
--shadow-soft: 0 1px 2px rgba(21, 61, 44, .05),
               0 12px 32px rgba(21, 61, 44, .08);
```

### Responsive breakpoints

- Mobile: `< 640px`
- Tablet: `640–1023px`
- Desktop: `≥ 1024px`
- Wide: `≥ 1440px`

Design mobile-first. Validate at `390px`, `768px`, `1280px`, and `1440px`.

---

## 6. Navigation

### Desktop header

**Left:** Logo + product name  
**Center:** Home, Features, About, Contact  
**Right:** Language switcher (`বাংলা | EN`), Log in, primary “Sign up” button

Behavior:

- Sticky after the user scrolls 24px.
- White/92% background with a thin bottom border; optional subtle blur.
- Current page uses a dark text label plus a 2px green underline.
- Header height: 76px.
- Never place all links inside pill containers.

### Mobile header

- Logo on the left; 44px menu button on the right.
- Full-width drawer from the top or right.
- Include all navigation, language switch, Log in, and Sign up.
- Keep “জরুরি সহায়তা” out of the main navigation unless a real support path exists.

---

## 7. Home Page

### 7.1 Hero

**Layout:** 6/6 split on desktop; stacked on mobile.

**Eyebrow:** `বাংলাদেশের কৃষকের জন্য AI সহায়তা`  
**Headline:** `ফসলের সমস্যা থেকে সঠিক সিদ্ধান্ত—সবকিছু এক জায়গায়`  
**Supporting copy:** `ছবি বা বাংলায় সমস্যা জানান, কাছের কৃষিযন্ত্র খুঁজুন, আবহাওয়া বুঝে পরিকল্পনা করুন এবং সম্ভাব্য ক্রেতার সঙ্গে যোগাযোগ করুন।`  
**Primary CTA:** `বিনামূল্যে শুরু করুন`  
**Secondary CTA:** `কীভাবে কাজ করে দেখুন` with play/arrow icon  
**Trust note:** `কম ইন্টারনেটেও প্রয়োজনীয় তথ্য ও অনুরোধ সংরক্ষণ করা যায়।`

#### Hero visual

Create a real, human-centered collage rather than a fake dashboard:

- Main image: a Bangladeshi farmer using a smartphone near a crop field
- Floating mini-card 1: crop scan preview with confidence and “বিশেষজ্ঞের পরামর্শ নিন” state
- Floating mini-card 2: nearest tractor, price, and distance
- Floating mini-card 3: 3-day weather strip
- Small offline status badge: `অফলাইনে সংরক্ষিত`

The cards should feel like believable product previews and contain no invented performance metrics.

#### Background detail

Use `field-wash`, subtle contour lines, and a small warm sun glow behind the image. No autoplay video in the first viewport.

### 7.2 Quick-action strip

Four large tappable actions:

1. `রোগ শনাক্ত করুন` — ScanLine icon
2. `কৃষিযন্ত্র খুঁজুন` — Tractor icon
3. `আবহাওয়া দেখুন` — CloudSun icon
4. `ক্রেতা খুঁজুন` — Handshake icon

On mobile, show a 2×2 grid. Each target must be at least 56px high.

### 7.3 Problem-to-solution section

**Headline:** `কৃষিকাজের প্রতিটি গুরুত্বপূর্ণ মুহূর্তে পাশে`  
Use an asymmetric layout: one large story card and three smaller cards.

- Crop disease uncertainty → AI-assisted guidance
- Expensive/distant equipment → price-and-distance ranking
- Weather risk → actionable three-day planning
- Limited buyer access → direct buyer connection

Use short outcome-oriented text rather than feature jargon.

### 7.4 How it works

A three-step, horizontally connected flow on desktop and vertical timeline on mobile:

1. `সমস্যা বা প্রয়োজন জানান`
2. `সহজ পরামর্শ ও কাছের অপশন দেখুন`
3. `যোগাযোগ করুন বা অনুরোধ সংরক্ষণ করুন`

Motion should animate the progress line only once when the section enters view.

### 7.5 AI crop assistant demo

Two-column interactive mockup:

- Left: upload/camera area with image guidance
- Right: sample result with possible disease, confidence range, visible reasoning summary, basic actions, and escalation notice

Mandatory safety language:

> `এটি AI-ভিত্তিক প্রাথমিক পরামর্শ। নিশ্চিত না হলে স্থানীয় কৃষি কর্মকর্তার সঙ্গে যোগাযোগ করুন।`

Never use red for low confidence alone; use an amber “অনিশ্চিত” state with explanatory text.

### 7.6 Equipment discovery

Use a map/list composition:

- Leaflet/OpenStreetMap visual
- Cards show equipment type, owner, approximate distance, rental price/unit, availability, Call, and Message
- Explain ranking clearly: `ভাড়ার মূল্য ৬৫% + দূরত্ব ৩৫%`
- Include filters for equipment type, price range, distance, and date

On mobile, default to list view with an optional map toggle to reduce complexity and data usage.

### 7.7 Weather planning

Use a three-day horizontal forecast with action labels:

- `স্প্রে করার ভালো সময়`
- `বৃষ্টির ঝুঁকি`
- `যন্ত্র ভাড়া নেওয়ার আগে যাচাই করুন`

Weather advice cards use sky blue as the category color; risks use amber/red only when necessary.

### 7.8 Offline-first story

Dark forest section with a phone mockup and a simple sync path:

- `ইন্টারনেট থাকলে প্রয়োজনীয় তথ্য ডিভাইসে রাখা হবে`
- `অফলাইনে জ্ঞান পড়ুন ও অনুরোধ তৈরি করুন`
- `নেটওয়ার্ক ফিরলে স্বয়ংক্রিয়ভাবে সিঙ্ক হবে`

Always show clear states:

- `অনলাইন`
- `অফলাইনে সংরক্ষিত`
- `সিঙ্ক হচ্ছে…`
- `সিঙ্ক ব্যর্থ—আবার চেষ্টা করুন`

### 7.9 Audience cards

Show four distinct entry points:

- কৃষক
- যন্ত্রের মালিক
- ফসল ক্রেতা
- কৃষি কর্মকর্তা/বিশেষজ্ঞ

Each card gets one sentence and one relevant action. Avoid role claims that are not implemented.

### 7.10 Trust and privacy

Before launch, use process-based trust indicators instead of fake usage numbers:

- `স্পষ্ট AI confidence`
- `অনিশ্চিত হলে মানব সহায়তার পরামর্শ`
- `ব্যক্তিগত যোগাযোগের নিয়ন্ত্রণ`
- `অফলাইন ডেটার স্বচ্ছ অবস্থা`

Once genuine data exists, this area may include verified user counts, partner logos, or case studies.

### 7.11 Final CTA

**Headline:** `আজকের কৃষি সিদ্ধান্ত আরও সহজ করুন`  
**Primary:** `অ্যাকাউন্ট খুলুন`  
**Secondary:** `আমাদের সঙ্গে কথা বলুন`

Use a warm field photo or restrained illustration on one side, not a generic green banner.

### 7.12 Footer

Columns:

- Product: Features, Crop Assistant, Equipment, Weather
- Company: About, Contact
- Support: Help, Privacy, Terms
- Language: বাংলা / English

Add real address, phone, email, and social links only when confirmed. Include a compact connectivity indicator only inside the authenticated product, not the marketing footer.

---

## 8. Features Page

### Page goal

Explain the product capabilities clearly without overwhelming users.

### Structure

1. Compact hero with a real field image
2. Sticky category navigation on desktop
3. Six alternating feature sections
4. Safety and offline behavior section
5. FAQ
6. Final CTA

### Feature sections

#### AI crop problem assistant

- Photo upload or camera capture
- Bangla/Banglish symptom description
- Possible disease and confidence
- Reasoning summary and basic guidance
- Agricultural officer escalation when uncertain

#### Equipment rental discovery

- Tractor, harvester, pump, and sprayer categories
- GPS-based nearby results
- 65% price + 35% distance ranking
- Call and private message actions
- Weather-risk notice before rental

#### Weather-based farm planning

- Three-day plan
- Suitable activity windows
- Rain/wind/heat risk indicators
- Contextual equipment warnings

#### Buyer connection

- Crop listing or availability summary
- Buyer discovery
- Direct, privacy-aware contact
- Clear status and message history

#### Agricultural knowledge

- Crop diseases and practices
- Fisheries and livestock topics
- Searchable, readable Bangla content
- Downloaded knowledge status

#### Offline queue and synchronization

- Save rental requests and messages offline
- Queue visibility
- Automatic retry with manual “Sync now” control
- Conflict and failure feedback

### Feature card behavior

Cards may tilt by a maximum of 1–2 degrees on pointer hover; no 3D spin. Mobile cards should not use hover-dependent information.

---

## 9. About Page

### Purpose

Build trust through mission, context, and responsible product principles—not invented achievements.

### Structure

1. **Hero:** `প্রযুক্তি যেন কৃষকের বাস্তব সমস্যার সহজ সমাধান হয়`
2. Bangladesh agriculture context with documentary-style photography
3. Mission and vision in a two-column layout
4. Product principles: accessible, practical, transparent, low-connectivity ready
5. Responsible AI statement
6. Team section using real people only
7. Partner/advisor logos only after confirmation
8. CTA to contact or join

### Responsible AI statement

Explain that predictions are decision support, confidence is shown, uncertain results prompt expert help, and the platform does not replace professional agricultural diagnosis.

---

## 10. Contact Page

### Layout

Use a calm two-column layout.

**Left:** purpose-specific contact cards  
**Right:** short contact form

### Contact cards

- General support
- Equipment owner onboarding
- Buyer/partner inquiry
- Agricultural expert collaboration

### Form fields

1. Name
2. Phone or email
3. I am a: Farmer / Equipment owner / Buyer / Expert / Other
4. Subject
5. Message
6. Preferred language
7. Consent checkbox

### UX details

- Use inline validation after blur, not on every keystroke.
- Preserve draft text if submission fails.
- Provide a clear success state with next-step expectations.
- Do not publish phone/email placeholders as real contact information.

---

## 11. Log In Page

### Visual style

Desktop split screen:

- Left: authentic Bangladesh farm image with one short benefit statement
- Right: focused authentication card

Mobile: form first; image becomes a small header visual or is removed for speed.

### Form

- Phone number or email
- Password
- Show/hide password
- Remember me
- Forgot password
- Primary `লগ ইন করুন`
- Secondary path to Sign up

### Recommended authentication UX

- Default to phone-number login if the product will verify Bangladeshi mobile numbers.
- Use country prefix `+880` with proper formatting.
- If OTP is supported, offer it as a clearly separate method.
- Do not show Google/social login unless actually implemented.
- Error messages must explain what to do next.

---

## 12. Sign Up Page

### Step-based flow

Keep onboarding to 3 short steps with a visible progress indicator.

#### Step 1 — Account

- Name
- Phone/email
- Password or OTP flow

#### Step 2 — Role

- Farmer
- Equipment owner
- Buyer
- Agricultural expert

Use large role cards with icons and one-line descriptions.

#### Step 3 — Basic profile

Ask only what is essential for the selected role. For a farmer, this may include district/upazila, preferred language, and major crop categories. Make GPS permission optional and explain its benefit.

### Consent

Use separate consent for Terms/Privacy and optional notifications. Never pre-check optional marketing consent.

---

## 13. Core Components

### Buttons

- Primary: forest fill, white label
- Secondary: white fill, forest border
- Tertiary: text + arrow
- Destructive: danger color, confirmation for irreversible actions
- Heights: 48px desktop, 52–56px for key mobile actions

States: default, hover, active, focus-visible, loading, disabled.

### Cards

- `FeatureCard`: icon, title, 2–3 line description, optional link
- `EquipmentCard`: thumbnail, type, price, distance, status, contact actions
- `WeatherCard`: date, condition, temperature, risk, recommended activity
- `AIResultCard`: possible diagnosis, confidence, reasoning, guidance, escalation
- `OfflineQueueCard`: request type, created time, sync state, retry action

### Forms

- Labels remain above fields; placeholders are examples, not labels.
- Minimum input height: 52px.
- Use input masks for Bangladeshi phone numbers.
- Error message directly below the field.
- Keyboard focus ring: `3px rgba(66, 166, 106, .28)` plus solid outline.

### Toasts and notices

- Do not use a toast for critical errors that require action.
- Offline and sync notices should remain visible until resolved or acknowledged.
- Success toasts disappear after 4–6 seconds and support screen-reader announcements.

### Icons

Recommended library: **Lucide React** for consistency.

Suggested mappings:

- Crop scan: `ScanLine`, `Leaf`, `Camera`
- Equipment: `Tractor`, `Wrench`
- Weather: `CloudSun`, `CloudRain`, `Wind`
- Buyer: `Handshake`, `Store`
- Location: `MapPin`, `Navigation`
- Offline: `WifiOff`, `CloudOff`, `RefreshCw`
- Confidence/safety: `ShieldCheck`, `TriangleAlert`, `CircleHelp`

Use 1.75–2px stroke weight. Standard sizes: 20px inline, 24px controls, 32px feature cards.

---

## 14. Motion System

Use Framer Motion for restrained, meaningful animation.

### Motion principles

- Motion explains hierarchy, state change, or direction.
- Maximum two concurrent animations in a viewport.
- Animate transform and opacity rather than layout-heavy properties.
- Stop decorative loops after one or two cycles.
- Disable non-essential motion under `prefers-reduced-motion`.

### Timing

| Motion | Duration | Easing |
|---|---:|---|
| Button/hover feedback | 120–180ms | `easeOut` |
| Card reveal | 350–450ms | `[0.22, 1, 0.36, 1]` |
| Page section reveal | 450–600ms | `[0.22, 1, 0.36, 1]` |
| Drawer/modal | 240–320ms | `easeInOut` |
| Sync progress/state | functional | linear or spring |

### Recommended variants

```tsx
export const fadeUp = {
  hidden: { opacity: 0, y: 18 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.48, ease: [0.22, 1, 0.36, 1] }
  }
};

export const stagger = {
  visible: { transition: { staggerChildren: 0.08 } }
};
```

### Specific animations

- Hero text: staggered fade-up once
- Hero cards: 8–12px slow drift only on capable devices; stop when offscreen
- Feature icons: small scale from `.96` to `1`
- Map pin: one controlled pulse when selected
- Offline sync: rotate `RefreshCw` only while syncing
- Page transitions: 150ms opacity crossfade; avoid large slides
- Buttons: translateY(-1px) on hover, reset on press

Never animate disease confidence numbers rapidly or create urgency through flashing colors.

---

## 15. Photography and Illustration

### Photo direction

Use authentic Bangladesh contexts:

- Natural daylight and realistic rural settings
- Farmers actively using tools or phones
- Paddy, vegetables, fisheries, livestock, irrigation, and farm machinery
- A balanced representation of women and men
- Clean framing with room for adjacent text
- Obtain proper usage rights and consent

### Do not use

- Obvious foreign farming landscapes presented as Bangladesh
- Staged “farmer holding a glowing tablet” imagery
- AI images with malformed hands, tools, crops, or fake text
- Poverty-focused imagery that removes dignity

### Hero-image generation prompt, if photography is unavailable

> Documentary-style editorial photograph of a Bangladeshi farmer standing beside a healthy vegetable field at soft morning light, naturally using a modern Android smartphone, realistic rural Bangladesh landscape, practical clothing, hopeful and calm expression, authentic agricultural tools in the background, room for UI composition on the left, natural colors, no text, no logos, no futuristic holograms, no distorted hands.

Generated images must be reviewed by a human before production use.

---

## 16. Accessibility and Rural Usability

- Meet WCAG 2.2 AA where possible.
- Minimum touch target: 44×44px; prefer 52px for primary mobile actions.
- Body text must not be below 16px.
- Support keyboard navigation and visible focus.
- Add descriptive alt text to meaningful images.
- Use labels with icons and state text.
- Allow text zoom to 200% without clipping.
- Avoid time-limited actions unless users can extend them.
- Provide Bangla screen-reader labels.
- Use clear numeric units for price, distance, date, rainfall, and wind.
- Optimize images and lazy-load below-the-fold media.
- Preserve the user’s form data when connectivity drops.
- Never require GPS; allow manual district/upazila selection.

---

## 17. Low-Connectivity Design

### Performance targets

- Keep initial marketing-page JavaScript minimal.
- Prefer AVIF/WebP images with responsive sizes.
- Avoid video backgrounds and large Lottie files.
- Lazy-load maps and non-critical animation libraries.
- Use skeletons only for content that is genuinely loading.
- Cache critical static knowledge and previously viewed items where appropriate.

### Offline states

The interface must distinguish:

1. `অফলাইন—সংরক্ষিত তথ্য দেখানো হচ্ছে`
2. `অনুরোধ ডিভাইসে সংরক্ষিত`
3. `নেটওয়ার্ক পাওয়া গেছে—সিঙ্ক হচ্ছে`
4. `সিঙ্ক সম্পন্ন`
5. `সিঙ্ক করা যায়নি—আবার চেষ্টা করুন`

Show queue count and last successful sync time. Do not tell the user that an action succeeded on the server until synchronization is confirmed.

---

## 18. Recommended Frontend Stack

- React.js
- Tailwind CSS
- Framer Motion
- Lucide React
- React Hook Form + Zod
- Leaflet + OpenStreetMap
- IndexedDB through Dexie.js or a similarly maintained wrapper
- i18next or a structured locale dictionary for Bangla/English

Use semantic HTML before adding ARIA. Keep animation components isolated so reduced-motion behavior is easy to maintain.

---

## 19. Suggested Routes

```text
/
/features
/about
/contact
/login
/signup
/privacy
/terms
/app
/app/crop-assistant
/app/equipment
/app/weather
/app/buyers
/app/knowledge
/app/messages
/app/offline-queue
/app/profile
```

The marketing header includes only: Home, Features, About, Contact, Log in, Sign up.

---

## 20. Content Checklist

Before design handoff, confirm:

- [ ] Final product name and logo
- [ ] Primary Bangla copy reviewed by a native speaker
- [ ] Actual support email and phone number
- [ ] Real team information
- [ ] Privacy policy and Terms
- [ ] AI safety and limitation wording
- [ ] Disease guidance source and expert review process
- [ ] Weather provider and attribution requirements
- [ ] OpenStreetMap attribution placement
- [ ] Equipment price unit and booking workflow
- [ ] Buyer verification and safety process
- [ ] Offline data retention and deletion rules
- [ ] Real screenshots or approved prototype states

---

## 21. Figma File Structure

```text
00 — Cover & Notes
01 — Foundations
     Colors
     Typography
     Spacing & Grid
     Icons
     Motion
02 — Components
     Navigation
     Buttons
     Inputs
     Cards
     Notices
     Modals
03 — Marketing / Desktop
     Home
     Features
     About
     Contact
     Log in
     Sign up
04 — Marketing / Mobile
05 — Product Preview States
06 — Prototype Flows
07 — Accessibility & Edge Cases
08 — Handoff
```

### Required prototype flows

1. Visitor → Sign up → Farmer onboarding
2. Visitor → Crop assistant preview
3. Farmer → Find equipment → Call/message owner
4. Farmer offline → Save request → Reconnect → Sync
5. Uncertain AI result → Agricultural officer guidance

---

## 22. Design QA Checklist

### Visual

- [ ] No overlapping, clipped, or overflowing elements
- [ ] Consistent spacing and alignment
- [ ] Clear visual hierarchy above the fold
- [ ] Photos are authentic, tasteful, and legally usable
- [ ] No fake text, logos, statistics, or testimonials
- [ ] Mobile layout feels designed, not merely stacked

### Functional

- [ ] Navigation works at all breakpoints
- [ ] Forms have loading, success, and error states
- [ ] Offline/sync states are visible and accurate
- [ ] Map has a usable list alternative
- [ ] AI result includes confidence, limitations, and escalation
- [ ] All interactive targets are at least 44×44px

### Accessibility

- [ ] Contrast passes WCAG AA
- [ ] Keyboard order is logical
- [ ] Focus is visible
- [ ] Screen-reader labels are present
- [ ] Reduced motion is respected
- [ ] 200% text zoom does not break layouts

### Performance

- [ ] Hero image is responsive and compressed
- [ ] No autoplay video
- [ ] Below-the-fold sections are lazy-loaded where appropriate
- [ ] Maps and heavy scripts are deferred
- [ ] Main tasks remain usable on a slow mobile connection

---

## 23. Reference Direction

Use references for layout quality and interaction principles—not for copying visuals.

- Agriculture UI inspiration: <https://dribbble.com/search/agriculture-ui-ux>
- Modern landing-page patterns: <https://unbounce.com/landing-page-examples/best-landing-page-examples/>
- Focused SaaS navigation and CTA principles: <https://blog.hubspot.com/marketing/saas-landing-page>
- React/Tailwind/Framer Motion implementation reference: <https://github.com/Bilal-EZ-ZAIM/saas-landing-page>
- OpenStreetMap attribution guidance: <https://www.openstreetmap.org/copyright>
- WCAG accessibility guidance: <https://www.w3.org/WAI/standards-guidelines/wcag/>

---

## 24. Final Art Direction Summary

The final site should feel like a **trusted digital agricultural companion built for Bangladesh**: bright but not childish, green but not generic, advanced but not intimidating. The strongest first impression will come from authentic local imagery, excellent Bangla typography, a clear four-action entry point, restrained motion, and transparent AI/offline states.
