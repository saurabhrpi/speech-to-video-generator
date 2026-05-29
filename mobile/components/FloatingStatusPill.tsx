import { useEffect } from 'react';
import { Pressable, Text, View, StyleSheet } from 'react-native';
import { useRouter, useSegments } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useGalleryStore } from '@/store/gallery-store';
import { useGenerationTick } from '@/hooks/useGenerationTick';
import { computePhase } from '@/lib/generation-status';

/**
 * Global bottom-right pill that surfaces an in-flight generation's countdown
 * (or retry / failure state) on every screen. Mounted at the root layout next
 * to <Paywall />. Hidden when there's no `generating` job.
 *
 * Tap → /gallery, where the user can watch the same job land.
 *
 * Drives the retry watcher: every 30s tick also calls
 * `gallery-store.tickAndRetryIfDue()` so a stuck job (>12 min, attempts=0)
 * resubmits once without needing any other component to be mounted.
 */
export default function FloatingStatusPill() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const segments = useSegments();
  const jobs = useGalleryStore((s) => s.jobs);
  const tickAndRetryIfDue = useGalleryStore((s) => s.tickAndRetryIfDue);

  // 30s ticker — forces re-render so the countdown label refreshes.
  useGenerationTick(30_000);

  // On every tick (and on first mount), kick the retry watcher. Idempotent.
  useEffect(() => {
    tickAndRetryIfDue();
  });

  // Per-route placement:
  //   /gallery        → hidden (the gallery card already surfaces the same info)
  //   /template/[id]  → centered at the bottom (template detail's own CTA
  //                     sits inline in the scroll, so center is free)
  //   anything else   → bottom-right (next to the home Generate FAB)
  const route = segments[0] ?? '';
  if (route === 'gallery') return null;
  const centered = route === 'template';

  // Show the most-recently-created in-flight job. There's almost never more
  // than one (the credit gate blocks concurrent submits), but `prepend on
  // submit` ordering in the store means jobs[0] is the newest.
  const inflight = jobs.find((j) => j.status === 'generating');
  if (!inflight) return null;

  const { label, subtitle } = computePhase(inflight);

  // Shared bottom offset; tracks the safe-area inset so the home Generate FAB
  // can sit at the SAME level (see GenerateFab in app/index.tsx). User-spec'd
  // "a couple of mm lower" — was insets.bottom + 26, now + 8.
  const bottom = Math.max(insets.bottom, 24) + 8;

  return (
    <Pressable
      onPress={() => router.push('/gallery')}
      style={[
        styles.pill,
        centered
          ? { alignSelf: 'center', bottom }
          : { right: 16, bottom },
      ]}
      accessibilityLabel={`${label}. ${subtitle}. Tap to open gallery.`}
    >
      <View style={styles.dotsWrap}>
        <Text style={styles.dots}>•••</Text>
      </View>
      <View style={styles.textStack}>
        <Text style={styles.label} numberOfLines={1}>
          {label}
        </Text>
        <Text style={styles.subtitle} numberOfLines={1}>
          {subtitle}
        </Text>
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  // Sizing bumped ~20% per user spec (padding 16→19, label 13→15, subtitle
  // 11→13). Fixed `height: 60` so the home Generate FAB (same height) lines
  // up visually — paddingVertical removed in favour of explicit height.
  // `right`/`alignSelf` + `bottom` injected per-route in the JSX above.
  pill: {
    position: 'absolute',
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    paddingHorizontal: 19,
    height: 60,
    borderRadius: 32,
    backgroundColor: '#0E0E10',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.08)',
    elevation: 6,
    shadowColor: '#000',
    shadowOpacity: 0.4,
    shadowRadius: 10,
    shadowOffset: { width: 0, height: 4 },
    zIndex: 50,
    // Cap width so it never crowds the (squeezed) Generate FAB on the left
    // at small device widths. The FAB's `right: PILL_TRACK` in index.tsx
    // assumes this max.
    maxWidth: 240,
  },
  dotsWrap: {
    width: 20,
    height: 20,
    alignItems: 'center',
    justifyContent: 'center',
  },
  dots: { color: '#FFFFFF', fontSize: 15, letterSpacing: 1 },
  textStack: { flexShrink: 1 },
  label: { color: '#FFFFFF', fontSize: 15, fontWeight: '600' },
  subtitle: { color: 'rgba(255,255,255,0.7)', fontSize: 13, marginTop: 1 },
});
