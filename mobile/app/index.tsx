import { useEffect, useState } from 'react';
import {
  View,
  Text,
  Pressable,
  ScrollView,
  StyleSheet,
  Dimensions,
  NativeScrollEvent,
  NativeSyntheticEvent,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { Video, ResizeMode } from 'expo-av';
import { useTemplateStore, groupByCategory, type Template } from '@/store/template-store';
import { useAuthStore } from '@/store/auth-store';
import { Colors } from '@/lib/design-tokens';

function isUsableMediaUrl(url: string | null | undefined): url is string {
  return !!url && /^https?:\/\//.test(url) && !url.includes('placeholder.example');
}

// S66: V2 home — root route. V1 Speech-to-Video flow moved to
// mobile/app/create-video.tsx, reachable via the floating "Create" button.
// Tabs were removed S66 — gallery is reached via the profile icon overlaid on
// the hero, settings via the gear icon on /gallery.

const { width: SCREEN_W, height: SCREEN_H } = Dimensions.get('window');
const HERO_H = Math.round(SCREEN_H * 0.4);

const TILE_W = 140;
const TILE_H = 200;

export default function HomeScreen() {
  const templates = useTemplateStore((s) => s.templates);
  const loading = useTemplateStore((s) => s.loading);
  const error = useTemplateStore((s) => s.error);
  const hydrated = useTemplateStore((s) => s.hydrated);
  const hydrate = useTemplateStore((s) => s.hydrate);
  const fetchTemplates = useTemplateStore((s) => s.fetchTemplates);
  const router = useRouter();
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
  const heroItems = pickHeroItems(templates);

  return (
    <View style={styles.root}>
      <ScrollView
        contentContainerStyle={styles.scroll}
        showsVerticalScrollIndicator={false}
      >
        <HeroSection items={heroItems} />

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
        onPress={() => router.push('/create-video' as any)}
        accessibilityLabel="Create a video"
      >
        <Ionicons name="mic" size={24} color={Colors.background} />
        <Text style={styles.fabLabel}>Create</Text>
      </Pressable>
    </View>
  );
}

function HeroSection({ items }: { items: Template[] }) {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const creditBalance = useAuthStore((s) => s.creditBalance);
  const [activeIndex, setActiveIndex] = useState(0);

  const onMomentumScrollEnd = (e: NativeSyntheticEvent<NativeScrollEvent>) => {
    const idx = Math.round(e.nativeEvent.contentOffset.x / SCREEN_W);
    if (idx !== activeIndex) setActiveIndex(idx);
  };

  return (
    <View style={[styles.heroSection, { height: HERO_H }]}>
      {items.length > 0 ? (
        <ScrollView
          horizontal
          pagingEnabled
          showsHorizontalScrollIndicator={false}
          decelerationRate="fast"
          onMomentumScrollEnd={onMomentumScrollEnd}
        >
          {items.map((t) => (
            <HeroCard key={t.id} template={t} onPress={() => router.push(`/template/${t.id}` as any)} />
          ))}
        </ScrollView>
      ) : (
        <View style={styles.heroPlaceholder}>
          <Text style={styles.heroPlaceholderTitle}>Top Trends</Text>
          <Text style={styles.heroPlaceholderSub}>(curation pending)</Text>
        </View>
      )}

      {/* Overlay row — title (left), credits | profile (right). Positioned
          inside the safe area so it never hides under the status bar. */}
      <View style={[styles.heroOverlay, { top: insets.top + 4 }]}>
        <Text style={styles.brand}>AIVO</Text>
        <View style={styles.overlayRight}>
          <Text style={styles.creditsText}>
            {creditBalance != null ? `${creditBalance} Credits` : '— Credits'}
          </Text>
          <Text style={styles.divider}>|</Text>
          <Pressable
            onPress={() => router.push('/gallery')}
            hitSlop={12}
            accessibilityLabel="Open gallery"
          >
            <Ionicons name="person-circle-outline" size={32} color="#fff" />
          </Pressable>
        </View>
      </View>

      {/* Page indicator — one pill per hero card, active pill widens. Hidden
          when there's only one (or zero) cards to page through. */}
      {items.length > 1 && (
        <View style={styles.pageIndicator} pointerEvents="none">
          {items.map((_, i) => (
            <View
              key={i}
              style={[styles.pageDot, i === activeIndex && styles.pageDotActive]}
            />
          ))}
        </View>
      )}
    </View>
  );
}

function HeroCard({ template, onPress }: { template: Template; onPress: () => void }) {
  const videoUrl =
    template.assets?.preview_video_url ?? template.assets?.driving_video_url;
  return (
    <Pressable style={styles.heroCard} onPress={onPress}>
      {isUsableMediaUrl(videoUrl) ? (
        <Video
          source={{ uri: videoUrl }}
          style={styles.heroMedia}
          resizeMode={ResizeMode.COVER}
          isLooping
          isMuted
          shouldPlay
        />
      ) : (
        <View style={[styles.heroMedia, styles.heroMediaPlaceholder]}>
          <Ionicons name="image-outline" size={36} color={Colors.textSecondary} />
        </View>
      )}
    </Pressable>
  );
}

function pickHeroItems(templates: Template[]): Template[] {
  return templates
    .filter((t) => t.is_hero === true)
    .sort((a, b) => {
      const ao = a.hero_order ?? Number.POSITIVE_INFINITY;
      const bo = b.hero_order ?? Number.POSITIVE_INFINITY;
      if (ao !== bo) return ao - bo;
      return a.title.localeCompare(b.title);
    });
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
  const videoUrl =
    template.assets?.preview_video_url ?? template.assets?.driving_video_url;

  const onPress = () => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    router.push(`/template/${template.id}` as any);
  };

  return (
    <Pressable style={styles.tile} onPress={onPress}>
      {isUsableMediaUrl(videoUrl) ? (
        <Video
          source={{ uri: videoUrl }}
          style={styles.tileThumb}
          resizeMode={ResizeMode.COVER}
          isLooping
          isMuted
          shouldPlay
        />
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
    .split(/[_\-\s]+/)
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ');
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: Colors.background },
  scroll: { paddingBottom: 120 },
  // Hero
  heroSection: {
    width: SCREEN_W,
    backgroundColor: '#000',
    overflow: 'hidden',
  },
  heroCard: {
    width: SCREEN_W,
    height: '100%',
  },
  heroMedia: {
    width: '100%',
    height: '100%',
    backgroundColor: '#000',
  },
  heroMediaPlaceholder: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  heroPlaceholder: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: Colors.card,
  },
  heroPlaceholderTitle: { color: Colors.textPrimary, fontSize: 18, fontWeight: '600' },
  heroPlaceholderSub: { color: Colors.textSecondary, fontSize: 13, marginTop: 6 },
  heroOverlay: {
    position: 'absolute',
    left: 16,
    right: 16,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  brand: {
    color: '#fff',
    fontSize: 24,
    fontWeight: '700',
    letterSpacing: 1,
  },
  overlayRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  creditsText: { color: '#fff', fontSize: 14, fontWeight: '500' },
  divider: { color: 'rgba(255,255,255,0.55)', fontSize: 16 },
  pageIndicator: {
    position: 'absolute',
    bottom: 10,
    left: 0,
    right: 0,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 6,
  },
  pageDot: {
    width: 6,
    height: 4,
    borderRadius: 2,
    backgroundColor: 'rgba(255,255,255,0.5)',
  },
  pageDotActive: {
    width: 18,
    backgroundColor: '#fff',
  },
  // Category rows + tiles (below the hero)
  rowWrap: { paddingTop: 16, paddingBottom: 16 },
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
    bottom: 50,
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
