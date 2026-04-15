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
import { File, Directory, Paths } from 'expo-file-system';
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
  const markSaved = useGalleryStore((s) => s.markSaved);

  const selectedJob = jobs.find((j) => j.id === selectedJobId && j.status === 'completed');

  const handleSave = useCallback(async (videoUrl: string, jobId?: string) => {
    try {
      const { status } = await MediaLibrary.requestPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert('Permission needed', 'Allow photo library access to save videos.');
        return;
      }

      const dest = new Directory(Paths.cache, 'saved_videos');
      if (!dest.exists) dest.create();

      const file = await File.downloadFileAsync(videoUrl, dest);
      await MediaLibrary.saveToLibraryAsync(file.uri);
      file.delete();

      if (jobId) markSaved(jobId);
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      Alert.alert('Saved', 'Video saved to Camera Roll.');
    } catch (err: any) {
      Alert.alert('Save failed', err.message || 'Could not save video.');
    }
  }, [markSaved]);

  const renderItem = useCallback(({ item }: { item: GalleryJob }) => {
    if (item.status === 'generating' || item.status === 'paused') {
      const paused = item.status === 'paused';
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
          {paused ? (
            <Ionicons name="cloud-offline-outline" size={28} color={Colors.textSecondary} />
          ) : (
            <ActivityIndicator color={Colors.textPrimary} size="small" />
          )}
          <Text
            style={{ color: Colors.textSecondary, fontSize: 12, marginTop: 8, textAlign: 'center' }}
            numberOfLines={2}
          >
            {item.statusMsg || (paused ? 'Paused' : 'Generating...')}
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

    if (item.status === 'failed') return null;

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
          {/* Remove button — only visible when selected */}
          {isSelected && (
            <Pressable
              onPress={(e) => {
                e.stopPropagation?.();
                removeJob(item.id);
              }}
              style={{
                position: 'absolute',
                top: 6,
                left: 6,
                width: 24,
                height: 24,
                borderRadius: 12,
                backgroundColor: 'rgba(0,0,0,0.4)',
                justifyContent: 'center',
                alignItems: 'center',
                zIndex: 10,
              }}
            >
              <Ionicons name="close" size={14} color="#fff" />
            </Pressable>
          )}
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
          {/* Download button — hidden after save */}
          {!item.saved && (
            <Pressable
              onPress={(e) => {
                e.stopPropagation?.();
                if (item.videoUrl) handleSave(item.videoUrl, item.id);
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
          )}
          {item.saved && (
            <View style={{ position: 'absolute', bottom: 8, right: 8 }}>
              <Ionicons name="checkmark-circle" size={22} color={Colors.textSecondary} />
            </View>
          )}
        </View>
      </Pressable>
    );
  }, [cardWidth, selectedJobId, selectJob, removeJob, handleSave, markSaved]);

  return (
    <Pressable style={{ flex: 1, backgroundColor: Colors.background }} onPress={() => selectJob(null)}>
      {/* Selected video player */}
      {selectedJob?.videoUrl && (
        <View style={{ paddingHorizontal: PADDING, paddingTop: 12, paddingBottom: 4 }}>
          <VideoPlayer url={selectedJob.videoUrl} />
          <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginTop: 8 }}>
            <Text style={{ color: Colors.textSecondary, fontSize: 12, flex: 1 }} numberOfLines={1}>
              {selectedJob.prompt}
            </Text>
            {selectedJob.saved ? (
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: 4 }}>
                <Ionicons name="checkmark-circle" size={16} color={Colors.textSecondary} />
                <Text style={{ color: Colors.textSecondary, fontSize: 13 }}>Saved</Text>
              </View>
            ) : (
              <Pressable
                onPress={() => handleSave(selectedJob.videoUrl!, selectedJob.id)}
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
            )}
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
    </Pressable>
  );
}
