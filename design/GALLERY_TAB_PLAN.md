# Gallery Tab + Video Save

## Context

The Speech tab currently freezes during video generation (~2-5 min). User wants a non-blocking flow: tap "Generate Video" → generation runs in background → app navigates to a Gallery tab showing all videos (in-progress as spinners, completed as playable). Also wants a save-to-Camera-Roll button on completed videos. Gallery replaces the Video Studio tab (can be recreated later).

## Plan

### Step 0: Install dependencies

```bash
cd mobile && npx expo install expo-media-library expo-file-system @react-native-async-storage/async-storage
```

- `expo-file-system` is already in node_modules (transitive dep) but needs explicit install
- `@react-native-async-storage/async-storage` not currently installed
- All three are included in Expo Go SDK 55 — no native rebuild needed

Update `app.json`: add `expo-media-library` plugin + `NSPhotoLibraryAddUsageDescription` in `ios.infoPlist`.

### Step 1: Create gallery store

**New: `mobile/store/gallery-store.ts`**

```typescript
interface GalleryJob {
  id: string;              // job_id from API
  prompt: string;          // display text
  model: string;           // "Kling" / "Hailuo"
  duration: number;
  status: 'generating' | 'completed' | 'failed';
  statusMsg: string;
  videoUrl: string | null;
  error: string | null;
  createdAt: number;
}
```

Key methods:
- `startGeneration(formData, meta)` — creates job entry with `status: 'generating'`, prepends to `jobs`, calls `apiPost('/api/generate/speech-to-video', formData, true)` to get `job_id`, then fires `streamJob()` in a fire-and-forget async call. SSE callbacks update the job via `set()`. Returns job ID immediately.
- `removeJob(id)` — removes job, aborts if generating, persists
- `hydrate()` — loads completed/failed jobs from AsyncStorage on app start

Follows `pipeline-store.ts` pattern: AbortControllers in a module-level Map (not serialized). Keep-awake managed in store (`activateKeepAwake` when any job generating, deactivate when all done). Persistence: write completed/failed jobs to AsyncStorage after each status change.

### Step 2: Modify Speech tab

**Modify: `mobile/app/(tabs)/index.tsx`**

- Remove local state: `busy`, `progress`, `statusMsg`, `videoUrl` and their effects (keep-awake, etc.)
- Import `useGalleryStore` and `router` from `expo-router`
- `generateVideo()` becomes: dispatch to gallery store → `router.navigate('/(tabs)/gallery')`
- Remove `ProgressBar` and `VideoPlayer` from JSX
- Remove `disabled={busy}` from all inputs — tab is always interactive
- Keep recording + transcript modal flow intact

### Step 3: Create Gallery tab screen

**New: `mobile/app/(tabs)/gallery.tsx`** (replaces video-studio.tsx)

- `FlatList` with `numColumns={2}`, cells are half-screen-width cards
- **Completed cell**: dark card (`bg-card`, `rounded-card`, glassy border), prompt text (2 lines), centered play icon, download button bottom-right
- **Generating cell**: same size card, `ActivityIndicator`, status message
- **Failed cell**: same size, error text, remove button
- **Empty state**: "No videos yet" centered text
- Tap completed cell → set `selectedJobId` state → render full-width `VideoPlayer` + save button above the grid
- Save button: `FileSystem.downloadAsync()` → `MediaLibrary.saveToLibraryAsync()` → success haptic + alert

### Step 4: Update tab layout

**Modify: `mobile/app/(tabs)/_layout.tsx`**

Replace Video Studio tab entry with:
```
name="gallery", title="Gallery", icon="th-large"
```

### Step 5: Delete Video Studio

**Delete: `mobile/app/(tabs)/video-studio.tsx`**

### Step 6: Hydrate gallery on app start

**Modify: `mobile/app/_layout.tsx`**

Add `useEffect` to call `useGalleryStore.getState().hydrate()` after fonts loaded.

## Files

| File | Action |
|------|--------|
| `mobile/store/gallery-store.ts` | CREATE |
| `mobile/app/(tabs)/gallery.tsx` | CREATE |
| `mobile/app/(tabs)/index.tsx` | MODIFY — remove blocking state, dispatch to store |
| `mobile/app/(tabs)/_layout.tsx` | MODIFY — swap Video Studio → Gallery |
| `mobile/app/_layout.tsx` | MODIFY — hydrate gallery store |
| `mobile/app.json` | MODIFY — media-library plugin + permission |
| `mobile/app/(tabs)/video-studio.tsx` | DELETE |

## Verification

1. Launch app in simulator
2. Type a prompt on Speech tab → tap "Generate Video" → should navigate to Gallery, show spinner cell
3. Speech tab should be immediately usable again (not blocked)
4. Wait for generation to complete → spinner becomes playable card
5. Tap completed card → VideoPlayer appears, video plays
6. Tap save button → permission prompt → video saved to Camera Roll
7. Kill and relaunch app → completed videos still appear in Gallery
8. Check other tabs (Timelapse) still work — no regressions
