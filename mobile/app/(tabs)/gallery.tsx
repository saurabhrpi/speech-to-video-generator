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
import { useRouter } from 'expo-router';
import { useGalleryStore, type GalleryJob } from '@/store/gallery-store';
import { Colors } from '@/lib/design-tokens';

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

  const renderItem = useCallback(({ item }: { item: GalleryJob }) => {
    if (item.status === 'generating' || item.status === 'paused') {
      const paused = item.status === 'paused';
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
            padding: 12,
          }}
        >
          {paused ? (
            <Ionicons name="cloud-offline-outline" size={28} color={Colors.textSecondary} />
          ) : (
            <ActivityIndicator color={Colors.textPrimary} size="small" />
          )}
          <Text
            style={{ color: Colors.textSecondary, fontSize: 13, marginTop: 10, textAlign: 'center' }}
            numberOfLines={1}
          >
            {paused ? 'Paused' : 'Generating Video'}
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
              onError={() => {
                console.warn('[Gallery] thumbnail load failed, clearing:', item.thumbnailUri);
                clearThumbnail(item.id);
              }}
            />
          )}
        </View>
      </Pressable>
    );
  }, [cardWidth, cardHeight, router, clearThumbnail]);

  return (
    <View style={{ flex: 1, backgroundColor: Colors.background }}>
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
              Generate one from the Speech tab
            </Text>
          </View>
        }
      />
    </View>
  );
}
