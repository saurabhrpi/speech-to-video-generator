# Design System PRD

**Status:** Complete for now (all interview rounds finished)
**Last updated:** 2026-04-04
**Rounds completed:** 20

> All decisions are gut-feel first passes, subject to change after real device testing and user feedback.

---

## 1. Brand Identity

### Personality
Premium, warm, theatrical. The app should feel like an interior design magazine meets a film premiere — not a generic tech/AI tool.

### Color Direction
- **Theme:** Warm dark mode. Dark backgrounds with warm undertones (dark browns, charcoal with amber hints). Cards slightly warm-tinted. Feels "interior design" rather than "tech app."
- **Accent color:** Warm gold/amber. Evokes brass fixtures, warm lighting. Luxurious, premium feel. Works on dark warm backgrounds.
- **Depth/layering:** Subtle warmth shifts. Background is darkest charcoal-brown, cards a notch lighter with more amber warmth, bottom sheets/modals lighter still. All surfaces stay warm — warmth increases with elevation.

### Typography
- **Headings:** Playfair Display, Regular (400). High-contrast, editorial, "design magazine" feel. Lets the serif style do the talking — elegant and understated.
- **Body:** Inter. Clean, neutral, excellent readability. Regular (400) for long text, Medium (500) for labels/UI elements.
- **Type scale:** Minimal (4 sizes) — heading, subheading, body, caption. Simple, hard to mess up.
- **Rationale:** Serif headings + sans body creates distinction and reinforces the premium/editorial identity. Playfair's high contrast pairs well with Inter's neutrality.

### Spacing & Layout
- **Grid:** 8pt base. Steps of 8, 16, 24, 32, 40, 48. Fewer choices, naturally consistent.
- **Screen edge padding:** 20px. Standard iOS feel, balanced.
- **Card internal padding:** 16px. Balanced, standard.
- **Section spacing:** 32px vertical between dashboard sections. Clear separation without big gaps.

### Corner Radius
- **Standard:** 12-16px (medium). Modern and friendly without being bubbly. Works for both prosumer UGC creators and design agency users.

### Animation & Motion
- **Philosophy:** Considered. Functional motion plus occasional delight. Curtain-pull reveal is the star; elsewhere, tasteful easing and gentle fades. A few signature moments, not everything choreographed.
- **Timing curves:** Spring physics. Natural bounce/overshoot. Lively, iOS-native feel.
- **Page transitions:** iOS push (standard slide from right). Familiar, zero learning curve.
- **Loading states:** Shimmer placeholders. Standard grey shapes that shimmer left-to-right.
- **Thumbnail loop transition:** Quick dissolve (~0.3s) between the bookend clips (first 2s + last 2s). Brief cross-fade, slightly smoother than a hard cut.

### Icons & Visual Language
- **Style:** Mixed — outlined by default, filled when active/selected. iOS convention.
- **Weight:** Regular (1.5px stroke). Balanced visibility and elegance.
- **Source:** SF Symbols primary + custom for key moments. Native icons for standard actions, custom icons for brand-specific things (curtain-pull icon, generation status, etc.)
- **Status indicators:** Icon + color. Spinner (in progress), checkmark (done), X (failed). Colored accordingly (amber, green, red).

---

## 2. App Structure

### Navigation
- **Pattern:** Single-screen + drawer. Timelapse IS the app.
- **Home:** Personal dashboard (user's own past generations, active/pending jobs, quick-start).
- **Create:** Push screen from dashboard.
- **Drawer:** Profile, settings, experimental features (Video Studio, Speech-to-Video hidden here as "Labs").
- **No tab bar.** Dashboard is the home screen. Profile accessible from header icon or drawer.

### Organization
- **Model:** Lightweight tags. Optional tags/labels on generations (e.g. "Client: Acme", "Kitchen reno"). Filterable but no folder hierarchy.
- **Tag creation:** Free-text + suggestions. User types freely, app suggests tags based on room type/style from the generation.
- **Tag assignment:** Both before and after. Optional tag field on creation form, editable anytime from detail view or long-press context menu.
- **Filtering:** Filter icon -> bottom sheet. Tap filter icon in header, bottom sheet shows all tags. Cleaner dashboard, one extra tap.
- **Tag limit:** Max 3 per timelapse. Keeps things focused, prevents clutter.

---

## 3. Core Screens & Components

### 3.1 Dashboard (Home Screen)

**Purpose:** Personal command center. Shows user's generation history and active jobs.

**Content:**
- Active/pending job cards (medium size)
- Completed timelapse cards with auto-playing thumbnail loops
- Quick-start "Create" button

**Auto-play behavior:** Always auto-play. All visible thumbnails loop silently. Accept battery/bandwidth cost for maximum visual impact.

**Thumbnail loop style:** Bookend loop — first 2 seconds (bare room / before) + last 2 seconds (finished room / after) of the timelapse, seamlessly looped. Creates a punchy before/after effect in a small card.

### 3.2 In-Progress Job Card

**Size:** Medium card.
**Visual:** Blurred/abstract placeholder visual (no actual keyframe images shown — those are hidden for the cinematic reveal).
**Info:** Phase label ("Generating images..."), progress bar, ETA.
**Rationale:** Cinematic reveal means the actual content stays hidden during generation. The card shows progress without spoiling the reveal.

### 3.3 Cinematic Reveal

**Trigger:** One-time event. First time the user opens a completed timelapse, the curtain pull reveal plays. After that, it becomes a normal playable video card in the dashboard.

**Animation style:** Curtain pull. A textured curtain/overlay (matching the warm dark UI aesthetic) pulls away to reveal the playing timelapse beneath. Theatrical, matches the "premiere" feeling.

**Key brand moment.** This animation pattern should be a signature interaction.

### 3.4 Creation Flow

**Entry:** Floating CTA button on dashboard or drawer action.

**Form inputs:** 3 key inputs — room type (1 of 12), style (1 of 14), features (multi-select, up to ~20).

**Input pattern:** All bottom sheets. Tap any input row -> bottom sheet slides up with options. Room type and style are single-select lists. Features is a multi-select chip grid. Consistent interaction pattern across all inputs.

**Inspiration:** Curated presets. "Try this combo" button that cycles through hand-picked combinations known to produce stunning results. Doubles as social proof and quality demonstration.

**Confirmation:** Explicit confirm. After hitting "Generate", show a confirmation screen with:
- Cost (credits to be deducted)
- Estimated time
- Summary of user's inputs (room type, style, features)
- No AI preview — clean and honest, no risk of setting wrong expectations.

### 3.5 Completed Timelapse Card

**Sharing/export:** Native iOS share sheet. Single primary action — tap share, get the system share sheet. No custom share buttons for individual platforms.

### 3.6 Empty States & First-Time Experience

**First launch (no generations):** Preset showcase. Show 3-4 example timelapse thumbnails (auto-playing) with "Try this" buttons. User picks one as their first generation. Zero-friction start.

**Empty state visuals:** Stylized illustration. Warm-toned, on-brand illustration of a room transforming. Artistic, sets the mood.

**Credit onboarding:** Free credits for first generation. Let the user experience the magic before asking for money. Conversion happens after they've seen the quality.

**Return visit (all jobs complete):** Gallery mode. Completed timelapses front and center, auto-playing. Dashboard becomes a portfolio. Create button floats.

### 3.8 Buttons

| Level | Style | Details |
|-------|-------|---------|
| **Primary** | Solid gold/amber fill | Strong, unmissable. Dark text on gold. Standard 12-16px corner radius (consistent with cards). |
| **Secondary** | Muted fill | Subtle warm-tinted background (slightly lighter than card surface), light text. Visible but receded. |
| **Destructive** | Red fill | Unmistakable. Standard destructive pattern. |
| **FAB (Create)** | Extended pill, shrinks on scroll | Gold fill, "Create" label + icon when at top. Collapses to circular + icon when scrolling down. |

- **Touch target height:** 48px. Comfortable without feeling oversized.

### 3.9 Bottom Sheets

**Used for:** Room type selection, style selection, feature multi-select, and potentially other contextual actions.

**Behavior:** Slide up from bottom. Drag handle at top. Dismiss by swiping down or tapping scrim.

---

## 4. Monetization UI

### Model: Credit Packs
Users buy credits (e.g. 5 generations for $X). No subscription model.

### Credit Balance Display
- **Location:** Profile section only. Visible when tapping profile/account.
- **Rationale:** Less anxiety-inducing than a persistent counter. Credit balance shown contextually on the creation form and confirmation screen where it matters.

### No PRO Badge
Unlike the reference app, no PRO/subscription badge. Credits are consumable, not a status symbol.

---

## 5. Error Handling

### Tone: Minimal + silent retry
- Auto-retry up to 2 times silently on failure.
- Only show error to user if all retries fail.
- When shown: simple message + retry button. Don't burden the user with technical details they can't act on.
- Credits auto-refunded on failure.

### Notifications

| Trigger | Channel | Content |
|---------|---------|---------|
| Job complete | Push (always on) | Descriptive: "Your Modern Kitchen Timelapse is ready to view!" Reminds them what they created. |
| Job complete (user returns to app) | In-app banner | Slide-down banner: "Your timelapse is ready!" Tap to scroll to it. |
| Job failed | Push only if auto-retry also failed | "Something went wrong with your timelapse. Credits refunded." Silent during retry attempts. |

---

## 6. Haptics

> All haptic choices are initial gut-feel decisions. Subject to change after real device testing.

| Moment | Haptic | Rationale |
|--------|--------|-----------|
| Generation kick-off (confirm + spend credits) | Medium impact | Noticeable "it's happening" without being dramatic |
| Job completion | None | The curtain-pull reveal IS the feedback — haptic would undercut it |
| Bottom sheet selections | Light tap per selection + medium tap on confirm | Tactile browsing feel, satisfying close |
| Error/failure | None | Message is enough — don't alarm the user with a buzz |

---

## 7. Dark Mode & Accessibility

- **Theme modes:** Dark default + light option in settings. Warm dark IS the brand but some users prefer light. Don't prioritize light mode — build it eventually.
- **Contrast ratios:** Best effort WCAG AA. Aim for 4.5:1 body / 3:1 large text but don't compromise visual identity if gold needs to shift slightly off-brand.
- **Dynamic type:** Fixed sizes. Type scale is fixed — simpler layouts. May revisit in future.
- **VoiceOver:** Deferred. Focus on core product first. Address in a future version.

---

## 8. Splash Screen & App Launch

- **Content:** App icon + wordmark. Icon above, "Interior Decor Timelapse" below. Reinforces branding.
- **Background:** Subtle texture. Warm dark with a faint material texture (linen, concrete, wood grain). Tactile richness.
- **Transition to dashboard:** Logo scales down — splash logo shrinks and settles into the header position as the dashboard loads beneath. Connected feeling.
- **Warm return (backgrounded app):** Resume exactly where they left off. No splash, no dashboard reset. User sees whatever screen they were on.

---

## 9. Component Specs

### Color Palette
| Token | Hex | Usage |
|-------|-----|-------|
| Background | `#1C1614` | App background, darkest surface |
| Card | `#2C2422` | Card surfaces, list items |
| Elevated | `#3C3430` | Bottom sheets, modals, elevated cards |
| Gold accent | `#E8B84A` | Primary buttons, active icons, accent highlights |
| Text primary | `#FAF0E6` (linen) | Headings, body text |
| Text secondary | `#B09A86` | Captions, labels, muted text |
| Destructive | Red (TBD) | Delete buttons, error states |
| Success | Green (TBD) | Completion indicators |
| In-progress | Amber (TBD) | Spinner, progress states |

### Type Scale (Minimal — 4 levels)
| Level | Font | Size | Weight |
|-------|------|------|--------|
| Heading | Playfair Display | 28px | Regular (400) |
| Subheading | Playfair Display | 20px | Regular (400) |
| Body | Inter | 16px | Regular (400) / Medium (500) for labels |
| Caption | Inter | 13px | Regular (400) |

### Card Dimensions
- **Layout:** Two-column grid. Two cards per row, ~square thumbnails. More cards visible, less detail per card.
- **Corner radius (tiered):** Cards: 16px, Buttons: 12px, Inputs: 8px, Bottom sheet top corners: 20px.

### Bottom Sheets
- **Sizing:** Adaptive. Room type/style (short lists) get half-screen (~50%), features (long chip grid) gets two-thirds (~66%). Sheet size matches content.

### Detail View & Video Playback

- **Layout:** Full-screen video. Video takes the entire screen. Metadata in an overlay or below the fold. Immersive.
- **Player controls:** Tap to pause/play + scrubber on tap. Tap once shows scrubber/timeline briefly, user can seek. Tap again to dismiss.
- **Looping:** Play once, return to first frame. Stops, shows bare room "before" with replay button. Before/after comparison baked in.
- **Orientation:** Full-screen portrait (9:16). Content generated in portrait aspect ratio from the start — native TikTok/Reels format. No letterboxing, no rotation.
- **Generation details:** Hidden but accessible. "View details" button or info icon. Most users don't care, power users can see.

> **Pipeline impact:** Portrait (9:16) aspect ratio must be enforced at image generation (T2I/I2I) and video generation (I2V) stages. This is a generation parameter, not a display crop.

### Micro-interactions

| Interaction | Behavior |
|------------|----------|
| Dashboard refresh | No pull-to-refresh. Auto-updates via SSE. No manual refresh needed. |
| Long-press on completed card | iOS context menu: Share, Delete, Add Tag, View Details. |
| Swipe gestures | Left = delete (red), Right = share (gold). Full gesture support. |
| Primary button press | Scale down (0.96x) + darken. Springs back on release. |
| Card tap | Gold border flash briefly around the card. Draws attention, then navigates. |

---

## 10. Credit Purchase Flow

- **Store location:** Inline in profile. Credit packs listed as a section inside the profile/account screen. No separate screen or sheet.
- **Pack presentation:** Cards with emphasis. Each pack is a card. Best-value pack gets a gold "Best Value" badge and slightly larger treatment.
- **Out-of-credits:** Inline purchase. Confirmation screen itself shows credit pack options right there. Buy without leaving the flow.

## 11. Settings

- **Contents:** Detailed — Account info, notifications, theme toggle, credits/billing history, about/version, support/feedback, generation defaults (preferred room type, style), data/cache management, export all data, logout.
- **Layout:** Cards. Each settings group is a card. Consistent with the card-based UI elsewhere.

---

## 12. App Name / Brand

**Working name:** Interior Decor Timelapse. Subject to change. Good enough for development; final branding TBD.

---

## Open Questions (Future Interview Rounds)

All original topics addressed. Future rounds may revisit:

- Specific red/green/amber hex values for destructive/success/in-progress states
- Exact spring physics parameters (damping, stiffness)
- Curtain-pull reveal animation specs (duration, easing, texture)
- Bookend thumbnail loop generation (how to extract first 2s + last 2s programmatically)
- Credit pack pricing tiers
- Onboarding preset showcase — which 3-4 example timelapses to feature
