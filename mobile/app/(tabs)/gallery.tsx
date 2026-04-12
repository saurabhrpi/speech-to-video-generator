import { useCallback } from 'react';
import {
  View,
  Text,
  FlatList,
  Pressable,
  ActivityIndicator,
  Alert,
  useWindowDimensions,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { File, Paths } from 'expo-file-system';
import * as MediaLibrary from 'expo-media-library';
import VideoPlayer from '@/components/VideoPlayer';
import { useGalleryStore, type GalleryJob } from '@/store/gallery-store';
import { Colors } from '@/lib/design-tokens';

const CARD_GAP = 12;
const PADDING = 20;

export default function GalleryScreen() {
  const { width } = useWindowDimensions();
  const cardWidth = (width - PADDING * 2 - CARD_GAP) / 2;

  const jobs = useGalleryStore((s) => s.jobs);
  const selectedJobId = useGalleryStore((s) => s.selectedJobId);
  const selectJob = useGalleryStore((s) => s.selectJob);
  const removeJob = useGalleryStore((s) => s.removeJob);

  const selectedJob = jobs.find((j) => j.id === selectedJobId && j.status === 'completed');

  const handleSave = useCallback(async (videoUrl: string) => {
    try {
      const { status } = await MediaLibrary.requestPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert('Permission needed', 'Allow photo library access to save videos.');
        return;
      }

      const filename = `video_${Date.now()}.mp4`;
      const file = new File(Paths.cache, filename);

      // Download video to local cache
      const res = await fetch(videoUrl);
      const blob = await res.blob();
      const buffer = await blob.arrayBuffer();
      file.write(new Uint8Array(buffer));

      await MediaLibrary.saveToLibraryAsync(file.uri);
      file.delete();

      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      Alert.alert('Saved', 'Video saved to Camera Roll.');
    } catch (err: any) {
      Alert.alert('Save failed', err.message || 'Could not save video.');
    }
  }, []);

  const renderItem = useCallback(({ item }: { item: GalleryJob }) => {
    if (item.status === 'generating') {
      return (
        <View
          style={{
            width: cardWidth,
            height: cardWidth * 1.2,
            backgroundColor: Colors.card,
            borderRadius: 16,
            borderWidth: 1,
            borderColor: Colors.glassyBorder,
            justifyContent: 'center',
            alignItems: 'center',
            padding: 12,
          }}
        >
          <ActivityIndicator color={Colors.textPrimary} size="small" />
          <Text
            style={{ color: Colors.textSecondary, fontSize: 12, marginTop: 8, textAlign: 'center' }}
            numberOfLines={2}
          >
            {item.statusMsg || 'Generating...'}
          </Text>
          <Text
            style={{ color: Colors.textSecondary, fontSize: 11, marginTop: 6, textAlign: 'center' }}
            numberOfLines={1}
          >
            {item.model} · {item.duration}s
          </Text>
        </View>
      );
    }

    if (item.status === 'failed') {
      return (
        <View
          style={{
            width: cardWidth,
            height: cardWidth * 1.2,
            backgroundColor: Colors.card,
            borderRadius: 16,
            borderWidth: 1,
            borderColor: 'rgba(217,64,64,0.3)',
            justifyContent: 'center',
            alignItems: 'center',
            padding: 12,
          }}
        >
          <Ionicons name="alert-circle" size={28} color={Colors.destructive} />
          <Text
            style={{ color: Colors.destructive, fontSize: 12, marginTop: 6, textAlign: 'center' }}
            numberOfLines={2}
          >
            {item.error || 'Failed'}
          </Text>
          <Pressable
            onPress={() => removeJob(item.id)}
            style={{ marginTop: 10, paddingHorizontal: 12, paddingVertical: 6, borderRadius: 8, backgroundColor: 'rgba(217,64,64,0.15)' }}
          >
            <Text style={{ color: Colors.destructive, fontSize: 12 }}>Remove</Text>
          </Pressable>
        </View>
      );
    }

    // Completed
    const isSelected = selectedJobId === item.id;
    return (
      <Pressable onPress={() => selectJob(isSelected ? null : item.id)}>
        <View
          style={{
            width: cardWidth,
            height: cardWidth * 1.2,
            backgroundColor: Colors.card,
            borderRadius: 16,
            borderWidth: 1,
            borderColor: isSelected ? Colors.textPrimary : Colors.glassyBorder,
            justifyContent: 'center',
            alignItems: 'center',
            padding: 12,
            overflow: 'hidden',
          }}
        >
          <Ionicons name="play-circle" size={40} color={Colors.textPrimary} style={{ opacity: 0.8 }} />
          <Text
            style={{ color: Colors.textPrimary, fontSize: 12, marginTop: 8, textAlign: 'center' }}
            numberOfLines={2}
          >
            {item.prompt}
          </Text>
          <Text
            style={{ color: Colors.textSecondary, fontSize: 11, marginTop: 4 }}
            numberOfLines={1}
          >
            {item.model} · {item.duration}s
          </Text>
          {/* Download button */}
          <Pressable
            onPress={(e) => {
              e.stopPropagation?.();
              if (item.videoUrl) handleSave(item.videoUrl);
            }}
            style={{
              position: 'absolute',
              bottom: 8,
              right: 8,
              width: 32,
              height: 32,
              borderRadius: 16,
              backgroundColor: 'rgba(255,255,255,0.12)',
              justifyContent: 'center',
              alignItems: 'center',
            }}
          >
            <Ionicons name="download-outline" size={18} color={Colors.textPrimary} />
          </Pressable>
        </View>
      </Pressable>
    );
  }, [cardWidth, selectedJobId, selectJob, removeJob, handleSave]);

  return (
    <View style={{ flex: 1, backgroundColor: Colors.background }}>
      {/* Selected video player */}
      {selectedJob?.videoUrl && (
        <View style={{ paddingHorizontal: PADDING, paddingTop: 12, paddingBottom: 4 }}>
          <VideoPlayer url={selectedJob.videoUrl} />
          <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginTop: 8 }}>
            <Text style={{ color: Colors.textSecondary, fontSize: 12, flex: 1 }} numberOfLines={1}>
              {selectedJob.prompt}
            </Text>
            <Pressable
              onPress={() => handleSave(selectedJob.videoUrl!)}
              style={{
                flexDirection: 'row',
                alignItems: 'center',
                gap: 4,
                paddingHorizontal: 12,
                paddingVertical: 6,
                borderRadius: 8,
                backgroundColor: Colors.accent,
                borderWidth: 1,
                borderColor: Colors.glassyBorder,
              }}
            >
              <Ionicons name="download-outline" size={16} color={Colors.textPrimary} />
              <Text style={{ color: Colors.textPrimary, fontSize: 13 }}>Save</Text>
            </Pressable>
          </View>
        </View>
      )}

      {/* Grid */}
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
