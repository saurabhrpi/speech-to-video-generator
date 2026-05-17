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
import { useTemplateStore, findTemplateById } from '@/store/template-store';
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
  // Subscribed for V2 card variant — undefined templates fall through to V1 styling,
  // so an unhydrated store doesn't break rendering.
  const templates = useTemplateStore((s) => s.templates);

  const renderItem = useCallback(({ item }: { item: GalleryJob }) => {
    const template = findTemplateById(templates, item.templateId);

    if (item.status === 'generating' || item.status === 'paused') {
      const paused = item.status === 'paused';
      const inflightCopy = paused
        ? 'Paused'
        : template
          ? `Generating ${template.title}…`
          : 'Generating Video';
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
            numberOfLines={2}
          >
            {inflightCopy}
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
  }, [cardWidth, cardHeight, router, clearThumbnail, templates]);

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
