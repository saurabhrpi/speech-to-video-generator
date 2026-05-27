import { useCallback, useEffect, useRef, useState } from 'react';
import {
  View,
  Text,
  Image,
  Pressable,
  ScrollView,
  FlatList,
  StyleSheet,
  Dimensions,
  NativeScrollEvent,
  NativeSyntheticEvent,
  ViewToken,
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

// Tile sizing (S71): width = 40% of screen. Height keeps the original
// 140:200 aspect (~7:10) so the video thumb doesn't crop or letterbox when
// the width grows. At 40% two tiles fit fully and the third peeks ~40% — a
// clear scroll-affordance hint. (45% pre-tightened ~5-10% of the third tile,
// which read as "row ends here" rather than "scroll right.")
const TILE_W = Math.round(SCREEN_W * 0.40);
const TILE_H = Math.round(TILE_W * (10 / 7));

// Tiles visible at rest (horizontal offset 0) for a 40%-width tile: two fit
// fully. We paint those two on first frame so a freshly-revealed row isn't
// black for a beat; live horizontal viewability refines it on scroll, and the
// row only plays them when the row itself is on screen (rowOnScreen) — so this
// never plays a row that's off-screen vertically.
const INITIAL_VISIBLE_TILES = 2;

export default function HomeScreen() {
  const templates = useTemplateStore((s) => s.templates);
  const loading = useTemplateStore((s) => s.loading);
  const error = useTemplateStore((s) => s.error);
  const hydrated = useTemplateStore((s) => s.hydrated);
  const hydrate = useTemplateStore((s) => s.hydrate);
  const fetchTemplates = useTemplateStore((s) => s.fetchTemplates);
  const router = useRouter();

  // Slider-phone pattern: hero is a fixed background layer; content scrolls
  // OVER it. The freeze flag flips when scrolled past HERO_H (content has
  // fully covered the hero). State only changes when crossing the threshold,
  // so we don't re-render on every scroll frame.
  const [heroFrozen, setHeroFrozen] = useState(false);
  const onScroll = useCallback(
    (e: NativeSyntheticEvent<NativeScrollEvent>) => {
      const frozen = e.nativeEvent.contentOffset.y >= HERO_H;
      setHeroFrozen((prev) => (prev !== frozen ? frozen : prev));
    },
    [],
  );

  // Which category ROWS are currently on screen vertically. Combined with each
  // row's own horizontal tile-visibility (see CategoryRow), a tile plays only
  // when its row is on screen AND the tile is within the row's viewport. This
  // bounds live <Video> decoders to ~the rows actually in the viewport, keeping
  // it well under iOS's concurrent hardware-decode ceiling (the prod stutter /
  // "off-screen tiles still play" cause). A row counts as on-screen at >=60%
  // vertical visibility so its tiles light up only once it's mostly in view —
  // the "sensitive, plays as it enters" feel. The outer container is now a
  // FlatList (was a plain ScrollView) so rows virtualize AND get viewability;
  // the S71 sticky-hero gesture bug was about overlapping layers, not a list,
  // so a plain vertical list does not reintroduce it.
  const [visibleRows, setVisibleRows] = useState<Set<string>>(new Set());
  const rowViewabilityConfig = useRef({ itemVisiblePercentThreshold: 90 }).current;
  const onRowViewableChanged = useRef(
    ({ viewableItems }: { viewableItems: ViewToken[] }) => {
      setVisibleRows(
        new Set(viewableItems.map((v) => (v.item as { category: string }).category)),
      );
    },
  ).current;

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

  const renderEmpty = () => {
    if (!hydrated || (loading && templates.length === 0)) return <SkeletonRows />;
    if (error && templates.length === 0)
      return <ErrorState message={error} onRetry={fetchTemplates} />;
    return <EmptyState />;
  };

  return (
    <View style={styles.root}>
      {/* Vertical FlatList of category rows; hero is the list header so it
          scrolls off naturally. Sticky / slider-phone hero layering was
          attempted but reverted in S71 (native pan-gesture beats JS
          pointerEvents in overlap regions) — a plain list avoids that. */}
      <FlatList
        data={grouped}
        keyExtractor={(g) => g.category}
        contentContainerStyle={styles.scroll}
        showsVerticalScrollIndicator={false}
        onScroll={onScroll}
        scrollEventThrottle={16}
        ListHeaderComponent={<HeroSection items={heroItems} frozen={heroFrozen} />}
        ListEmptyComponent={renderEmpty}
        renderItem={({ item }) => (
          <CategoryRow
            category={item.category}
            items={item.items}
            rowOnScreen={visibleRows.has(item.category)}
          />
        )}
        viewabilityConfig={rowViewabilityConfig}
        onViewableItemsChanged={onRowViewableChanged}
      />

      <Pressable
        style={styles.fab}
        onPress={() => router.push('/create-video' as any)}
        accessibilityLabel="Create a video"
      >
        <Ionicons name="mic" size={24} color="#FFFFFF" />
        <Text style={styles.fabLabel}>Create a Video</Text>
      </Pressable>
    </View>
  );
}

function HeroSection({
  items,
  frozen,
}: {
  items: Template[];
  frozen: boolean;
}) {
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
          {items.map((t, i) => (
            <HeroCard
              key={t.id}
              template={t}
              isActive={i === activeIndex && !frozen}
              onPress={() => router.push(`/template/${t.id}` as any)}
            />
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

function HeroCard({
  template,
  isActive,
  onPress,
}: {
  template: Template;
  isActive: boolean;
  onPress: () => void;
}) {
  const videoUrl =
    template.assets?.preview_video_url ?? template.assets?.driving_video_url;
  // Mount the <Video> only for the ACTIVE hero card (same decoder-pool reason as
  // TemplateTile) — inactive cards and the scrolled-past state (isActive already
  // folds in !frozen) render a placeholder, freeing the player.
  const poster = template.assets?.thumbnail_url;
  const hasPoster = isUsableMediaUrl(poster);
  const showVideo = isActive && isUsableMediaUrl(videoUrl);
  return (
    <Pressable style={styles.heroCard} onPress={onPress}>
      <View style={styles.heroMedia}>
        {hasPoster && (
          <Image
            source={{ uri: poster as string }}
            style={StyleSheet.absoluteFill}
            resizeMode="cover"
          />
        )}
        {showVideo && (
          <Video
            source={{ uri: videoUrl as string }}
            style={StyleSheet.absoluteFill}
            resizeMode={ResizeMode.COVER}
            isLooping
            isMuted
            shouldPlay
          />
        )}
        {!hasPoster && !showVideo && (
          <View style={[StyleSheet.absoluteFill, styles.heroMediaPlaceholder]}>
            <Ionicons name="image-outline" size={36} color={Colors.textSecondary} />
          </View>
        )}
      </View>
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

function CategoryRow({
  category,
  items,
  rowOnScreen,
}: {
  category: string;
  items: Template[];
  rowOnScreen: boolean;
}) {
  // Which tiles are within this row's HORIZONTAL viewport. Live-updated by the
  // inner FlatList's viewability; seeded with the tiles that fit at rest so the
  // row isn't black on first paint (refined immediately on scroll). A tile
  // plays only when rowOnScreen (vertical) AND it's in this set (horizontal).
  const [visibleIds, setVisibleIds] = useState<Set<string>>(
    () => new Set(items.slice(0, INITIAL_VISIBLE_TILES).map((t) => t.id)),
  );

  // RN requires viewabilityConfig + onViewableItemsChanged to be stable refs;
  // changing them between renders throws at runtime. 70% threshold = a tile
  // lights up as it mostly enters the row (more "sensitive" than 100%, which
  // waited until fully in); rowOnScreen still bounds total live decoders.
  const viewabilityConfig = useRef({ itemVisiblePercentThreshold: 70 }).current;
  const onViewableItemsChanged = useRef(
    ({ viewableItems }: { viewableItems: ViewToken[] }) => {
      setVisibleIds(new Set(viewableItems.map((v) => (v.item as Template).id)));
    },
  ).current;

  return (
    <View style={styles.rowWrap}>
      <Text style={styles.sectionTitle}>{prettyCategory(category)}</Text>
      <FlatList
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.rowScroll}
        data={items}
        keyExtractor={(t) => t.id}
        renderItem={({ item }) => (
          <TemplateTile
            template={item}
            isVisible={rowOnScreen && visibleIds.has(item.id)}
          />
        )}
        viewabilityConfig={viewabilityConfig}
        onViewableItemsChanged={onViewableItemsChanged}
        initialNumToRender={4}
      />
    </View>
  );
}

function TemplateTile({
  template,
  isVisible,
}: {
  template: Template;
  isVisible: boolean;
}) {
  const router = useRouter();
  const videoUrl =
    template.assets?.preview_video_url ?? template.assets?.driving_video_url;

  const onPress = () => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    router.push(`/template/${template.id}` as any);
  };

  // First-frame poster is ALWAYS the base layer, so a non-playing tile shows
  // its first frame instead of black (matches the competitor's "paused = first
  // frame"). The looping <Video> mounts on TOP only while visible — expo-av
  // holds a live AVPlayer per mounted <Video> regardless of shouldPlay, so
  // mounting only on-screen tiles bounds iOS's decoder pool. A fresh mount also
  // auto-starts from frame 0 (restart-on-reentry, no replayAsync needed).
  const poster = template.assets?.thumbnail_url;
  const hasPoster = isUsableMediaUrl(poster);
  const showVideo = isVisible && isUsableMediaUrl(videoUrl);

  return (
    <Pressable style={styles.tile} onPress={onPress}>
      <View style={styles.tileThumb}>
        {hasPoster && (
          <Image
            source={{ uri: poster as string }}
            style={StyleSheet.absoluteFill}
            resizeMode="cover"
          />
        )}
        {showVideo && (
          <Video
            source={{ uri: videoUrl as string }}
            style={StyleSheet.absoluteFill}
            resizeMode={ResizeMode.COVER}
            isLooping
            isMuted
            shouldPlay
          />
        )}
        {!hasPoster && !showVideo && (
          <View style={[StyleSheet.absoluteFill, styles.tileThumbCenter]}>
            <Ionicons name="image-outline" size={28} color={Colors.textSecondary} />
          </View>
        )}
      </View>
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

// Slug → display-label overrides. Mechanical title-case loses uppercase
// abbreviations (e.g. "mj_dances" → "Mj Dances"); list those here.
const CATEGORY_LABEL_OVERRIDES: Record<string, string> = {
  mj_dances: 'MJ Dances',
};

function prettyCategory(c: string): string {
  if (CATEGORY_LABEL_OVERRIDES[c]) return CATEGORY_LABEL_OVERRIDES[c];
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
    overflow: 'hidden',
  },
  tileThumbCenter: {
    alignItems: 'center',
    justifyContent: 'center',
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
    backgroundColor: '#007AFF',
    elevation: 4,
    shadowColor: '#000',
    shadowOpacity: 0.3,
    shadowRadius: 8,
    shadowOffset: { width: 0, height: 4 },
  },
  fabLabel: { color: '#FFFFFF', fontSize: 14, fontWeight: '600', marginLeft: 6 },
});
