import { useCallback } from 'react';
import { View, Text, Pressable, Alert, StyleSheet } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import * as Sharing from 'expo-sharing';
import * as MediaLibrary from 'expo-media-library';
import { File, Directory, Paths } from 'expo-file-system';
import * as Haptics from 'expo-haptics';
import { Stack, useLocalSearchParams, useRouter } from 'expo-router';

import VideoPlayer from '@/components/VideoPlayer';
import { useGalleryStore } from '@/store/gallery-store';
import { Colors } from '@/lib/design-tokens';

export default function ClipScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();

  const job = useGalleryStore((s) => s.jobs.find((j) => j.id === id));
  const removeJob = useGalleryStore((s) => s.removeJob);
  const markSaved = useGalleryStore((s) => s.markSaved);

  const handleClose = useCallback(() => {
    if (router.canGoBack()) router.back();
    else router.replace('/(tabs)/gallery' as any);
  }, [router]);

  const handleSave = useCallback(async () => {
    if (!job?.videoUrl) return;
    try {
      const { status } = await MediaLibrary.requestPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert('Permission needed', 'Allow photo library access to save videos.');
        return;
      }
      const dest = new Directory(Paths.cache, 'saved_videos');
      if (!dest.exists) dest.create();
      const file = await File.downloadFileAsync(job.videoUrl, dest);
      await MediaLibrary.saveToLibraryAsync(file.uri);
      file.delete();
      markSaved(job.id);
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      Alert.alert('Saved', 'Video saved to Camera Roll.');
    } catch (err: any) {
      Alert.alert('Save failed', err.message || 'Could not save video.');
    }
  }, [job, markSaved]);

  const handleShare = useCallback(async () => {
    if (!job?.videoUrl) return;
    try {
      const available = await Sharing.isAvailableAsync();
      if (!available) {
        Alert.alert('Sharing unavailable', 'This device cannot share files.');
        return;
      }
      const dest = new Directory(Paths.cache, 'shared_videos');
      if (!dest.exists) dest.create();
      const file = await File.downloadFileAsync(job.videoUrl, dest);
      await Sharing.shareAsync(file.uri, { mimeType: 'video/mp4', dialogTitle: 'Share clip' });
      // Don't delete the file immediately — the share sheet may still be reading it.
    } catch (err: any) {
      Alert.alert('Share failed', err.message || 'Could not share video.');
    }
  }, [job]);

  const handleCreateNew = useCallback(() => {
    router.dismissTo('/(tabs)');
  }, [router]);

  const handleDelete = useCallback(() => {
    if (!job) return;
    Alert.alert('Delete clip?', 'This cannot be undone.', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Delete',
        style: 'destructive',
        onPress: () => {
          removeJob(job.id);
          router.back();
        },
      },
    ]);
  }, [job, removeJob, router]);

  if (!job || !job.videoUrl) {
    return (
      <SafeAreaView style={styles.safe} edges={['top']}>
        <Stack.Screen options={{ headerShown: false }} />
        <HeaderRow onBack={handleClose} />
        <View style={styles.center}>
          <Text style={styles.dim}>Clip not available.</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <Stack.Screen options={{ headerShown: false }} />
      <HeaderRow onBack={handleClose} onDelete={handleDelete} />

      <VideoPlayer url={job.videoUrl} />

      <View style={styles.spacer} />

      <View style={styles.actionsRow}>
        <ActionButton icon="add" label="Create New" onPress={handleCreateNew} />
        <ActionButton icon="arrow-down" label="Save" onPress={handleSave} />
        <ActionButton icon="share-outline" label="Share" onPress={handleShare} />
      </View>
    </SafeAreaView>
  );
}

function HeaderRow({ onBack, onDelete }: { onBack: () => void; onDelete?: () => void }) {
  return (
    <View style={styles.headerRow}>
      <Pressable onPress={onBack} hitSlop={12} style={styles.headerBtn} accessibilityLabel="Back">
        <Ionicons name="chevron-back" size={26} color={Colors.textPrimary} />
      </Pressable>
      {onDelete ? (
        <Pressable onPress={onDelete} hitSlop={12} style={styles.headerBtn} accessibilityLabel="Delete clip">
          <Ionicons name="trash-outline" size={22} color={Colors.textPrimary} />
        </Pressable>
      ) : (
        <View style={styles.headerBtn} />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: Colors.background },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  dim: { color: Colors.textSecondary, fontSize: 13 },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 8,
    height: 44,
  },
  headerBtn: {
    width: 40,
    height: 40,
    alignItems: 'center',
    justifyContent: 'center',
  },
  spacer: { flex: 1 },
  actionsRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingBottom: 40,
    paddingTop: 16,
  },
});

interface ActionButtonProps {
  icon: keyof typeof Ionicons.glyphMap;
  label: string;
  onPress: () => void;
}

function ActionButton({ icon, label, onPress }: ActionButtonProps) {
  return (
    <Pressable onPress={onPress} hitSlop={6} style={{ alignItems: 'center', gap: 8 }}>
      <View
        style={{
          width: 64,
          height: 64,
          borderRadius: 32,
          backgroundColor: '#FFFFFF',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <Ionicons name={icon} size={28} color="#1C1614" />
      </View>
      <Text style={{ color: Colors.textPrimary, fontSize: 12 }}>{label}</Text>
    </Pressable>
  );
}
