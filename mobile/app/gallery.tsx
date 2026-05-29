import { useCallback } from 'react';
import {
  View,
  Text,
  FlatList,
  Image,
  Pressable,
  ActivityIndicator,
  useWindowDimensions,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Stack, useRouter } from 'expo-router';
import { useGalleryStore, type GalleryJob } from '@/store/gallery-store';
import { Colors } from '@/lib/design-tokens';
import { computePhase } from '@/lib/generation-status';
import { useGenerationTick } from '@/hooks/useGenerationTick';

const CARD_GAP = 12;
const PADDING = 20;

export default function GalleryScreen() {
  const router = useRouter();
  const { width } = useWindowDimensions();
  const cardWidth = (width - PADDING * 2 - CARD_GAP) / 2;
  // Taller 2:3 portrait cards (was 1.2 ratio); matches social-video aesthetic.
  const cardHeight = cardWidth * 1.5;

  const jobs = useGalleryStore((s) => s.jobs);
  const clearThumbnail = useGalleryStore((s) => s.clearThumbnail);

  // 30s ticker so the per-card "Ready in X mins" countdown re-renders. Included
  // in renderItem deps below so FlatList re-invokes per tick.
  const tick = useGenerationTick(30_000);

  const renderItem = useCallback(({ item }: { item: GalleryJob }) => {
    if (item.status === 'generating' || item.status === 'paused') {
      const paused = item.status === 'paused';
      const { label, subtitle } = paused
        ? { label: 'Paused', subtitle: 'Will resume when back online' }
        : computePhase(item);
      return (
        <View
          style={{
            width: cardWidth,
            height: cardHeight,
            backgroundColor: Colors.card,
            borderRadius: 16,
            borderWidth: 1,
            borderColor: Colors.glassyBorder,
            justifyContent: 'center',
            alignItems: 'center',
            padding: 16,
          }}
        >
          {paused ? (
            <Ionicons name="cloud-offline-outline" size={32} color={Colors.textSecondary} />
          ) : (
            <ActivityIndicator color={Colors.textPrimary} size="large" />
          )}
          <Text
            style={{
              color: Colors.textPrimary,
              fontSize: 15,
              fontWeight: '600',
              marginTop: 14,
              textAlign: 'center',
            }}
            numberOfLines={2}
            adjustsFontSizeToFit
            minimumFontScale={0.8}
          >
            {label}
          </Text>
          <Text
            style={{
              color: Colors.textSecondary,
              fontSize: 11,
              marginTop: 4,
              textAlign: 'center',
            }}
            numberOfLines={2}
          >
            {subtitle}
          </Text>
        </View>
      );
    }

    if (item.status === 'failed') return null;

    // Completed — tap navigates to the dedicated playback screen (ToDo #28).
    return (
      <Pressable onPress={() => router.push(`/clip/${item.id}`)}>
        <View
          style={{
            width: cardWidth,
            height: cardHeight,
            backgroundColor: Colors.card,
            borderRadius: 16,
            borderWidth: 1,
            borderColor: Colors.glassyBorder,
            overflow: 'hidden',
          }}
        >
          {item.thumbnailUri && (
            <Image
              source={{ uri: item.thumbnailUri }}
              style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0 }}
              resizeMode="cover"
              onError={(e) => {
                console.warn('[Gallery] thumbnail load failed:', item.thumbnailUri, e?.nativeEvent);
                clearThumbnail(item.id);
              }}
            />
          )}
        </View>
      </Pressable>
    );
  }, [cardWidth, cardHeight, router, clearThumbnail, tick]);

  return (
    <View style={{ flex: 1, backgroundColor: Colors.background }}>
      <Stack.Screen
        options={{
          headerRight: () => (
            <Pressable
              onPress={() => router.push('/settings')}
              hitSlop={12}
              accessibilityLabel="Settings"
              style={{ marginRight: 8 }}
            >
              <Ionicons name="settings-outline" size={22} color={Colors.textPrimary} />
            </Pressable>
          ),
        }}
      />
      <FlatList
        data={jobs}
        keyExtractor={(item) => item.id}
        numColumns={2}
        contentContainerStyle={{ padding: PADDING, paddingBottom: 100 }}
        columnWrapperStyle={{ gap: CARD_GAP, marginBottom: CARD_GAP }}
        renderItem={renderItem}
        ListEmptyComponent={
          <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', paddingTop: 120 }}>
            <Ionicons name="film-outline" size={48} color={Colors.textSecondary} style={{ opacity: 0.5 }} />
            <Text style={{ color: Colors.textSecondary, fontSize: 15, marginTop: 12 }}>
              No videos yet
            </Text>
            <Text style={{ color: Colors.textSecondary, fontSize: 13, marginTop: 4, opacity: 0.7 }}>
              Tap Create on the home screen to make one
            </Text>
          </View>
        }
      />
    </View>
  );
}
