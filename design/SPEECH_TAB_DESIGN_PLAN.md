# Design System Overhaul — Speech Tab

## Context

The Speech tab currently uses a generic blue-accented, cool-gray theme. The design PRD (`design/DESIGN_SYSTEM_PRD.md`) specifies a warm dark mode with gold accents, editorial typography (Playfair Display + Inter), and premium spacing/radii. We're applying the design system to the Speech tab first, with foundational token changes that cascade to all tabs.

## Plan

### Phase 1: Foundation (tokens + fonts)

**1a. Update dark mode colors in `mobile/global.css`**
Replace the cool blue-gray HSL values in the `@media (prefers-color-scheme: dark)` block with warm PRD palette:
- Background: `#1C1614` → `15 22% 9%`
- Card: `#2C2422` → `12 14% 15%`
- Primary (gold): `#E8B84A` → `41 78% 60%`
- Primary-foreground (dark text on gold): `#1C1614` → `15 22% 9%`
- Secondary/elevated: `#3C3430` → `14 11% 21%`
- Muted-foreground: `#B09A86` → `25 22% 61%`
- Foreground (linen): `#FAF0E6` → `34 67% 94%`
- Destructive: warm red
- Border/input: warm subtle `14 11% 24%`

This single change makes every token-based component (ProgressBar, MicVisualizer, Button, etc.) warm automatically — no per-component changes needed for colors.

**1b. Add fonts**
- Download Playfair Display Regular, Inter Regular, Inter Medium TTFs to `mobile/assets/fonts/`
- Register in `mobile/app/_layout.tsx` `useFonts()` call
- Add `fontFamily` entries in `mobile/tailwind.config.js`: `heading`, `body`, `body-medium`

**1c. Extend `mobile/tailwind.config.js`**
- Font sizes: `heading` (28px), `subheading` (20px), `body` (16px), `caption` (13px)
- Border radii: `card` (16px), `button` (12px), `input` (8px), `sheet` (20px)
- New color token: `elevated` for modals/sheets

**1d. Create `mobile/lib/design-tokens.ts`**
Export raw hex constants for non-NativeWind contexts (ActivityIndicator color, React Navigation theme, inline styles):
```
background: '#1C1614', card: '#2C2422', elevated: '#3C3430',
gold: '#E8B84A', textPrimary: '#FAF0E6', textSecondary: '#B09A86'
```

**1e. Extract `cn()` from `mobile/components/Button.tsx` to `mobile/lib/utils.ts`**

**Checkpoint:** Run app — entire UI should be warm dark. All token-based components gold/warm automatically.

### Phase 2: Shared Components

**2a. `mobile/components/Button.tsx`**
- Import `cn` from `@/lib/utils`
- Update base radius from `rounded-md` to `rounded-button` (12px)
- Add press animation: `Animated.createAnimatedComponent(Pressable)` with scale 0.96x + opacity 0.9 on press, spring back on release (Reanimated already installed and used in ProgressBar/MicVisualizer)

**2b. `mobile/components/VideoPlayer.tsx`**
- Replace hard-coded `color="#3b82f6"` on ActivityIndicator with `Colors.gold`

**2c. `mobile/components/ConfirmModal.tsx`**
- Update modal container: `rounded-xl bg-card` → `rounded-[16px] bg-elevated`
- Title typography: add `font-heading text-[20px]`

**2d. No changes needed:** ProgressBar (uses `bg-primary`/`bg-secondary` → auto warm), MicVisualizer (uses `bg-primary` → auto gold bars)

### Phase 3: Speech Tab + Navigation Chrome

**3a. `mobile/app/_layout.tsx`**
- Create custom `WarmDarkTheme` using design token hex values for React Navigation (header, tab bar backgrounds)
- Pass to `ThemeProvider` instead of stock `DarkTheme`

**3b. `mobile/app/(tabs)/_layout.tsx`**
- Replace hard-coded `#3b82f6` / `#6ea8fe` tint with `Colors.gold`
- Set `tabBarStyle`, `headerStyle` backgrounds to `Colors.background`
- Set `tabBarInactiveTintColor` to `Colors.textSecondary`

**3c. `mobile/app/(tabs)/index.tsx` — the main event**
- Heading: `font-heading text-[28px]` (Playfair Display)
- Subtitle: `font-body text-[16px]`
- Section labels: `font-body-medium text-[13px]`
- Screen padding: `p-5` (20px), section gap: `gap-8` (32px)
- Model/Duration selectors: replace inline `style` with NativeWind — active = `bg-primary` with `text-primary-foreground`, inactive = plain with `text-muted-foreground`
- TextInput: `rounded-[8px] bg-card`, `placeholderTextColor={Colors.textSecondary}`
- Login banner: `rounded-[16px]`
- ConfirmModal transcript TextInput: same input styling

**3d. `mobile/app.json`**
- Update `splash.backgroundColor` to `#1C1614`

**Checkpoint:** Full visual QA of Speech tab against PRD.

## Files Modified

| File | Change |
|------|--------|
| `mobile/global.css` | Dark mode HSL values → warm palette |
| `mobile/tailwind.config.js` | Font families, sizes, radii, elevated color |
| `mobile/app/_layout.tsx` | Load fonts, custom nav theme |
| `mobile/app/(tabs)/_layout.tsx` | Gold tint, warm chrome |
| `mobile/app/(tabs)/index.tsx` | Full Speech tab restyle |
| `mobile/components/Button.tsx` | Radius, press animation, extract cn() |
| `mobile/components/VideoPlayer.tsx` | Gold spinner |
| `mobile/components/ConfirmModal.tsx` | Elevated bg, heading font |
| `mobile/lib/design-tokens.ts` | NEW — raw hex exports |
| `mobile/lib/utils.ts` | NEW — cn() utility |
| `mobile/app.json` | Splash background |
| `mobile/assets/fonts/` | NEW — Playfair + Inter TTFs |

## Verification

1. Launch app in simulator — warm dark background, gold tab icons
2. Speech tab: Playfair heading, Inter body, gold selectors, gold button
3. Press "Generate Video" — button scales 0.96x + springs back
4. Trigger auth banner — warm destructive styling
5. ProgressBar — gold fill on dark track
6. MicVisualizer — gold bars
7. ConfirmModal — elevated surface, Playfair title
8. Other tabs (Timelapse, Video Studio, Settings) — warm colors cascade, no visual breakage
