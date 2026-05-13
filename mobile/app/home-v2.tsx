import { useEffect } from 'react';
import {
  View,
  Text,
  Image,
  Pressable,
  ScrollView,
  ActivityIndicator,
  StyleSheet,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useRouter, Stack } from 'expo-router';
import { useTemplateStore, groupByCategory, type Template } from '@/store/template-store';
import { Colors } from '@/lib/design-tokens';

// AIV-30 carousel home — SHELL ONLY (S63). Pipeline Review wiring + real
// thumbnails + hero curation land later (AIV-31 + Track 2 assets).
//
// Plan refs: docs/V2_motion_transfer_plan.md (no tabs, floating Create Video
// button, profile-icon top-right → gallery). Floating button + profile icon
// are stubs here; wired once nav structure decisions land.

const TILE_W = 140;
const TILE_H = 200;

export default function HomeV2Screen() {
  const router = useRouter();
  const templates = useTemplateStore((s) => s.templates);
  const loading = useTemplateStore((s) => s.loading);
  const error = useTemplateStore((s) => s.error);
  const hydrated = useTemplateStore((s) => s.hydrated);
  const hydrate = useTemplateStore((s) => s.hydrate);
  const fetchTemplates = useTemplateStore((s) => s.fetchTemplates);

  useEffect(() => {
    // Hydrate first so cold-start shows cached templates immediately, then
    // re-fetch in the background. fetch sends If-None-Match → 304 keeps the
    // cache when unchanged.
    (async () => {
      await hydrate();
      fetchTemplates();
    })();
  }, [hydrate, fetchTemplates]);

  const grouped = groupByCategory(templates);

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <Stack.Screen options={{ headerShown: false }} />
      <View style={styles.topBar}>
        <Text style={styles.brand}>Speech to Video</Text>
        <Pressable
          onPress={() => router.push('/(tabs)/gallery')}
          hitSlop={12}
          accessibilityLabel="Open profile"
        >
          <Ionicons name="person-circle-outline" size={32} color={Colors.textPrimary} />
        </Pressable>
      </View>

      <ScrollView
        contentContainerStyle={styles.scroll}
        showsVerticalScrollIndicator={false}
      >
        <HeroPlaceholder />

        {!hydrated || (loading && templates.length === 0) ? (
          <SkeletonRows />
        ) : error && templates.length === 0 ? (
          <ErrorState message={error} onRetry={fetchTemplates} />
        ) : grouped.length === 0 ? (
          <EmptyState />
        ) : (
          grouped.map((g) => (
            <CategoryRow key={g.category} category={g.category} items={g.items} />
          ))
        )}
      </ScrollView>

      <Pressable
        style={styles.fab}
        onPress={() => router.push('/(tabs)')}
        accessibilityLabel="Create with speech to video"
      >
        <Ionicons name="mic" size={24} color={Colors.background} />
        <Text style={styles.fabLabel}>Create</Text>
      </Pressable>
    </SafeAreaView>
  );
}

function HeroPlaceholder() {
  // Hero curation deferred — V2 plan calls for landscape "top trends" carousel.
  // Placeholder strip keeps the visual hierarchy intact during the shell phase.
  return (
    <View style={styles.heroWrap}>
      <Text style={styles.sectionTitle}>Top Trends</Text>
      <View style={styles.heroTile}>
        <Text style={styles.heroPlaceholderText}>Hero carousel</Text>
        <Text style={styles.heroSubText}>(curation pending)</Text>
      </View>
    </View>
  );
}

function CategoryRow({ category, items }: { category: string; items: Template[] }) {
  return (
    <View style={styles.rowWrap}>
      <Text style={styles.sectionTitle}>{prettyCategory(category)}</Text>
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.rowScroll}
      >
        {items.map((t) => (
          <TemplateTile key={t.id} template={t} />
        ))}
      </ScrollView>
    </View>
  );
}

function TemplateTile({ template }: { template: Template }) {
  const router = useRouter();
  const thumb = template.assets?.thumbnail_url;

  const onPress = () => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    router.push(`/template/${template.id}` as any);
  };

  return (
    <Pressable style={styles.tile} onPress={onPress}>
      {thumb ? (
        <Image source={{ uri: thumb }} style={styles.tileThumb} />
      ) : (
        <View style={[styles.tileThumb, styles.tileThumbPlaceholder]}>
          <Ionicons name="image-outline" size={28} color={Colors.textSecondary} />
        </View>
      )}
      <Text style={styles.tileTitle} numberOfLines={1}>
        {template.title}
      </Text>
      <Text style={styles.tileCost}>{template.credit_cost} cr</Text>
    </Pressable>
  );
}

function SkeletonRows() {
  return (
    <View>
      {[0, 1].map((i) => (
        <View key={i} style={styles.rowWrap}>
          <View style={styles.skeletonHeader} />
          <View style={styles.rowScroll}>
            {[0, 1, 2, 3].map((j) => (
              <View key={j} style={[styles.tile, styles.skeletonTile]} />
            ))}
          </View>
        </View>
      ))}
    </View>
  );
}

function EmptyState() {
  return (
    <View style={styles.emptyWrap}>
      <Ionicons name="film-outline" size={48} color={Colors.textSecondary} />
      <Text style={styles.emptyTitle}>Templates coming soon</Text>
      <Text style={styles.emptyBody}>
        We&apos;re curating the first batch. Check back shortly.
      </Text>
    </View>
  );
}

function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <View style={styles.emptyWrap}>
      <Ionicons name="alert-circle-outline" size={48} color={Colors.destructive} />
      <Text style={styles.emptyTitle}>Couldn&apos;t load templates</Text>
      <Text style={styles.emptyBody}>{message}</Text>
      <Pressable onPress={onRetry} style={styles.retryBtn}>
        <Text style={styles.retryLabel}>Retry</Text>
      </Pressable>
    </View>
  );
}

function prettyCategory(c: string): string {
  return c
    .split(/[_-\s]+/)
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ');
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: Colors.background },
  topBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  brand: { color: Colors.textPrimary, fontSize: 20, fontWeight: '600' },
  scroll: { paddingBottom: 96 },
  heroWrap: { paddingHorizontal: 16, paddingTop: 8, paddingBottom: 16 },
  heroTile: {
    height: 200,
    backgroundColor: Colors.card,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: Colors.border,
    alignItems: 'center',
    justifyContent: 'center',
  },
  heroPlaceholderText: { color: Colors.textPrimary, fontSize: 16 },
  heroSubText: { color: Colors.textSecondary, fontSize: 12, marginTop: 4 },
  rowWrap: { paddingTop: 8, paddingBottom: 16 },
  sectionTitle: {
    color: Colors.textPrimary,
    fontSize: 16,
    fontWeight: '600',
    paddingHorizontal: 16,
    marginBottom: 8,
  },
  rowScroll: { paddingHorizontal: 12 },
  tile: {
    width: TILE_W,
    marginHorizontal: 4,
  },
  tileThumb: {
    width: TILE_W,
    height: TILE_H,
    borderRadius: 8,
    backgroundColor: Colors.card,
  },
  tileThumbPlaceholder: {
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: Colors.border,
  },
  tileTitle: { color: Colors.textPrimary, fontSize: 13, marginTop: 6 },
  tileCost: { color: Colors.textSecondary, fontSize: 11, marginTop: 2 },
  skeletonHeader: {
    height: 14,
    width: 120,
    backgroundColor: Colors.card,
    borderRadius: 4,
    marginHorizontal: 16,
    marginBottom: 8,
  },
  skeletonTile: {
    backgroundColor: Colors.card,
    height: TILE_H + 24,
    borderRadius: 8,
  },
  emptyWrap: {
    alignItems: 'center',
    paddingHorizontal: 24,
    paddingTop: 40,
    paddingBottom: 24,
  },
  emptyTitle: {
    color: Colors.textPrimary,
    fontSize: 16,
    fontWeight: '600',
    marginTop: 12,
  },
  emptyBody: {
    color: Colors.textSecondary,
    fontSize: 13,
    textAlign: 'center',
    marginTop: 4,
  },
  retryBtn: {
    marginTop: 16,
    paddingHorizontal: 16,
    paddingVertical: 8,
    backgroundColor: Colors.elevated,
    borderRadius: 8,
  },
  retryLabel: { color: Colors.textPrimary, fontSize: 13 },
  fab: {
    position: 'absolute',
    bottom: 24,
    alignSelf: 'center',
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 28,
    backgroundColor: Colors.textPrimary,
    elevation: 4,
    shadowColor: '#000',
    shadowOpacity: 0.3,
    shadowRadius: 8,
    shadowOffset: { width: 0, height: 4 },
  },
  fabLabel: { color: Colors.background, fontSize: 14, fontWeight: '600', marginLeft: 6 },
});
