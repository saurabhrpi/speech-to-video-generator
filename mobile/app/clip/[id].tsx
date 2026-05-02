import { useCallback, useState } from 'react';
import { View, Text, ScrollView, Pressable, Alert } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import * as Clipboard from 'expo-clipboard';
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
  const [copied, setCopied] = useState(false);

  const handleCopy = useCallback(async () => {
    if (!job) return;
    await Clipboard.setStringAsync(job.prompt);
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    setCopied(true);
    setTimeout(() => setCopied(false), 1200);
  }, [job]);

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
      <>
        <Stack.Screen options={{ title: 'S2V', headerBackTitle: '' }} />
        <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: Colors.background }}>
          <Text style={{ color: Colors.textSecondary }}>Clip not available.</Text>
        </View>
      </>
    );
  }

  return (
    <>
      <Stack.Screen
        options={{
          title: 'S2V',
          headerBackButtonDisplayMode: 'minimal',
          headerRight: () => (
            <Pressable onPress={handleDelete} hitSlop={10}>
              <Ionicons name="trash-outline" size={22} color={Colors.textPrimary} />
            </Pressable>
          ),
        }}
      />
      {/* Layout split: video ~50% (16:9 letterboxed inside), prompt ~25%,
          actions ~25%. Achieved via flex 2 / 1 / 1 on the three sections. */}
      <View style={{ flex: 1, backgroundColor: Colors.background }}>
        <View style={{ flex: 2, paddingHorizontal: 20, justifyContent: 'center' }}>
          <VideoPlayer url={job.videoUrl} />
        </View>

        <View style={{ flex: 1, paddingHorizontal: 20, paddingBottom: 12 }}>
          <View
            style={{
              flex: 1,
              backgroundColor: Colors.card,
              borderRadius: 16,
              borderWidth: 1,
              borderColor: Colors.glassyBorder,
              padding: 16,
            }}
          >
            <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
              <Text style={{ color: Colors.textPrimary, fontSize: 16, fontWeight: '600' }}>Prompt</Text>
              <Pressable
                onPress={handleCopy}
                style={{
                  paddingHorizontal: 14,
                  paddingVertical: 6,
                  borderRadius: 14,
                  backgroundColor: Colors.elevated,
                  borderWidth: 1,
                  borderColor: Colors.glassyBorder,
                }}
              >
                <Text style={{ color: Colors.textPrimary, fontSize: 13 }}>{copied ? 'Copied' : 'Copy'}</Text>
              </Pressable>
            </View>
            <ScrollView style={{ flex: 1 }} showsVerticalScrollIndicator={false}>
              <Text style={{ color: Colors.textPrimary, fontSize: 14, lineHeight: 20, opacity: 0.9 }}>
                {job.prompt}
              </Text>
            </ScrollView>
          </View>
        </View>

        <View
          style={{
            flex: 1,
            flexDirection: 'row',
            justifyContent: 'space-around',
            alignItems: 'center',
            paddingHorizontal: 20,
            paddingBottom: 40,
          }}
        >
          <ActionButton icon="add" label="Create New" onPress={handleCreateNew} />
          <ActionButton icon="arrow-down" label="Save" onPress={handleSave} />
          <ActionButton icon="share-outline" label="Share" onPress={handleShare} />
        </View>
      </View>
    </>
  );
}

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
