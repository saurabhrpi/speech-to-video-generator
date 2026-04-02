import { useState } from 'react';
import { View, Text, TextInput, ScrollView } from 'react-native';
import * as Haptics from 'expo-haptics';
import { Button } from '@/components/Button';
import ProgressBar from '@/components/ProgressBar';
import VideoPlayer from '@/components/VideoPlayer';
import MicVisualizer from '@/components/MicVisualizer';
import ConfirmModal from '@/components/ConfirmModal';
import { useRecording } from '@/hooks/useRecording';
import { apiPost } from '@/lib/api-client';
import { resolveVideoUrl } from '@/lib/api-client';

export default function SpeechScreen() {
  const { isRecording, metering, startRecording, stopRecording } = useRecording();
  const [busy, setBusy] = useState(false);
  const [statusMsg, setStatusMsg] = useState('');
  const [progress, setProgress] = useState(0);
  const [videoUrl, setVideoUrl] = useState<string | null>(null);

  // Confirmation modal state
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [pendingUri, setPendingUri] = useState<string | null>(null);
  const [pendingTranscript, setPendingTranscript] = useState('');

  async function handleStop() {
    const result = await stopRecording();
    if (!result) return;

    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    setPendingUri(result.uri);
    setPendingTranscript('');
    setConfirmOpen(true);

    // Transcribe in background
    try {
      const formData = new FormData();
      formData.append('audio', {
        uri: result.uri,
        type: 'audio/m4a',
        name: 'recording.m4a',
      } as any);
      const data = await apiPost<{ success: boolean; text?: string }>('/api/transcribe', formData, true);
      if (data.success && data.text) {
        setPendingTranscript(data.text);
      }
    } catch {
      // Transcription failure is non-fatal — user can type prompt manually
    }
  }

  async function handleConfirmProceed() {
    setConfirmOpen(false);
    if (!pendingUri) return;

    setBusy(true);
    setStatusMsg('Generating video...');
    setProgress(0);

    try {
      const formData = new FormData();
      if (pendingTranscript.trim()) {
        formData.append('prompt', pendingTranscript.trim());
      } else {
        formData.append('audio', {
          uri: pendingUri,
          type: 'audio/m4a',
          name: 'recording.m4a',
        } as any);
      }

      const data = await apiPost<{ success: boolean; video_url?: string; error?: string }>(
        '/api/ads/superbowl',
        formData,
        true,
      );

      if (data.success && data.video_url) {
        setVideoUrl(resolveVideoUrl(data.video_url));
        setStatusMsg('Done!');
        setProgress(100);
      } else {
        setStatusMsg(`Error: ${data.error || 'Generation failed'}`);
      }
    } catch (err: any) {
      setStatusMsg(err.message || 'Network error');
    } finally {
      setBusy(false);
      setPendingUri(null);
    }
  }

  return (
    <ScrollView className="flex-1 bg-background" contentContainerClassName="p-4 pb-20 gap-5">
      <Text className="text-2xl font-bold text-foreground">Speech to Video</Text>
      <Text className="text-sm text-muted-foreground">
        Record audio and generate a video ad from your speech.
      </Text>

      {/* Record button + visualizer */}
      <View className="gap-3">
        {isRecording && <MicVisualizer metering={metering} isActive={isRecording} />}

        <Button
          size="lg"
          variant={isRecording ? 'destructive' : 'default'}
          onPress={isRecording ? handleStop : startRecording}
          disabled={busy}
          title={isRecording ? 'Stop Recording' : 'Start Recording'}
          className="w-full"
        />
      </View>

      {/* Progress */}
      {(busy || statusMsg) ? (
        <ProgressBar progress={progress} message={statusMsg} indeterminate={busy && progress === 0} />
      ) : null}

      {/* Video result */}
      {videoUrl && !busy && <VideoPlayer url={videoUrl} />}

      {/* Confirmation modal */}
      <ConfirmModal
        visible={confirmOpen}
        title="Review Transcript"
        confirmText="Generate Video"
        cancelText="Cancel"
        onConfirm={handleConfirmProceed}
        onCancel={() => {
          setConfirmOpen(false);
          setPendingUri(null);
        }}
      >
        <View className="gap-2">
          <Text className="text-xs text-muted-foreground">
            Edit the transcript below, then generate your video ad.
          </Text>
          <TextInput
            value={pendingTranscript}
            onChangeText={setPendingTranscript}
            multiline
            numberOfLines={4}
            textAlignVertical="top"
            placeholder={pendingTranscript ? undefined : 'Transcribing...'}
            placeholderTextColor="#9ca3af"
            className="rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground min-h-[80px]"
          />
        </View>
      </ConfirmModal>
    </ScrollView>
  );
}
