import { useState } from 'react';
import { View, Text, TextInput, ScrollView } from 'react-native';
import * as Haptics from 'expo-haptics';
import { useRouter } from 'expo-router';
import { Button } from '@/components/Button';
import MicVisualizer from '@/components/MicVisualizer';
import ConfirmModal from '@/components/ConfirmModal';
import { useRecording } from '@/hooks/useRecording';
import { apiPost } from '@/lib/api-client';
import { useAuthStore } from '@/store/auth-store';
import { useGalleryStore } from '@/store/gallery-store';
import { Colors } from '@/lib/design-tokens';
import { creditCostFor } from '@/lib/constants';

// V1 ships single model + single duration (Session 52). Picker UIs removed.
const HAILUO_MODEL_ID = 'minimax/hailuo-2.3';
const HAILUO_MODEL_KEY = 'hailuo';
const CLIP_DURATION = 10;

export default function SpeechScreen() {
  const router = useRouter();
  const { isRecording, metering, startRecording, stopRecording } = useRecording();
  const [promptText, setPromptText] = useState('');

  const canAfford = useAuthStore((s) => s.canAfford);
  const openPaywall = useAuthStore((s) => s.openPaywall);
  const costTable = useAuthStore((s) => s.costTable);
  const creditBalance = useAuthStore((s) => s.creditBalance);
  const startGeneration = useGalleryStore((s) => s.startGeneration);
  const inFlightCost = useGalleryStore((s) =>
    s.jobs
      .filter((j) => j.status === 'generating' || j.status === 'paused')
      .reduce((sum, j) => sum + (j.costAtSubmit ?? 0), 0),
  );

  const cost = creditCostFor(HAILUO_MODEL_KEY, CLIP_DURATION, costTable);
  // Disable Generate ONLY when an in-flight job is the blocker — i.e. balance alone is enough
  // but the projected (post-in-flight) balance isn't. If balance alone is already < cost, we
  // leave the button tappable so dispatchGeneration's canAfford fallback opens the paywall.
  const blockedByInFlight =
    cost !== null &&
    creditBalance !== null &&
    inFlightCost > 0 &&
    creditBalance >= cost &&
    creditBalance - inFlightCost < cost;

  // Confirmation modal state
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [pendingUri, setPendingUri] = useState<string | null>(null);
  const [pendingTranscript, setPendingTranscript] = useState('');

  function buildFormData(prompt?: string, audioUri?: string): FormData {
    const formData = new FormData();
    if (prompt) {
      formData.append('prompt', prompt);
    } else if (audioUri) {
      formData.append('audio', {
        uri: audioUri,
        type: 'audio/m4a',
        name: 'recording.m4a',
      } as any);
    }
    formData.append('model', HAILUO_MODEL_ID);
    formData.append('duration', String(CLIP_DURATION));
    return formData;
  }

  function dispatchGeneration(formData: FormData, promptLabel: string) {
    if (!canAfford(HAILUO_MODEL_KEY, CLIP_DURATION)) {
      openPaywall();
      return;
    }
    startGeneration(formData, {
      prompt: promptLabel,
      model: 'Hailuo',
      duration: CLIP_DURATION,
      cost: cost ?? 0,
    });
    router.navigate('/(tabs)/gallery');
  }

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

  function handleTextToVideo() {
    if (!promptText.trim()) return;
    const formData = buildFormData(promptText.trim());
    dispatchGeneration(formData, promptText.trim());
  }

  function handleConfirmProceed() {
    setConfirmOpen(false);
    if (!pendingUri) return;

    const prompt = pendingTranscript.trim();
    const formData = prompt
      ? buildFormData(prompt)
      : buildFormData(undefined, pendingUri);
    dispatchGeneration(formData, prompt || '(voice recording)');
    setPendingUri(null);
  }

  return (
    <ScrollView className="flex-1 bg-background" contentContainerClassName="p-5 pb-20 gap-8">
      <View className="gap-1">
        <Text className="text-heading font-body text-foreground">Speech to Video</Text>
        <Text className="text-body font-body text-muted-foreground">
          Type a prompt or record audio to generate a 10-second video.
        </Text>
      </View>

      {/* Text prompt input */}
      <View className="gap-3">
        <TextInput
          value={promptText}
          onChangeText={setPromptText}
          multiline
          numberOfLines={4}
          textAlignVertical="top"
          placeholder="Type what you want to see in the video..."
          placeholderTextColor={Colors.textSecondary}
          editable={!isRecording}
          className="rounded-input-r bg-card px-4 py-3 text-body font-body text-foreground min-h-[96px]"
        />
        <Button
          size="lg"
          onPress={handleTextToVideo}
          disabled={isRecording || !promptText.trim() || blockedByInFlight}
          title={cost !== null ? `Generate Video · ${cost} credits` : 'Generate Video'}
          className="w-full"
        />
      </View>

      {/* Divider */}
      <View className="flex-row items-center gap-3">
        <View className="flex-1 h-px bg-border" />
        <Text className="text-caption font-body text-muted-foreground">or record your voice</Text>
        <View className="flex-1 h-px bg-border" />
      </View>

      {/* Record button + visualizer */}
      <View className="gap-3">
        {isRecording && <MicVisualizer metering={metering} isActive={isRecording} />}

        <Button
          size="lg"
          variant={isRecording ? 'destructive' : 'outline'}
          onPress={isRecording ? handleStop : startRecording}
          title={isRecording ? 'Stop Recording' : 'Start Recording'}
          className="w-full"
        />
      </View>

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
          <Text className="text-caption font-body text-muted-foreground">
            Edit the transcript below, then generate your video.
          </Text>
          <TextInput
            value={pendingTranscript}
            onChangeText={setPendingTranscript}
            multiline
            numberOfLines={4}
            textAlignVertical="top"
            placeholder={pendingTranscript ? undefined : 'Transcribing...'}
            placeholderTextColor={Colors.textSecondary}
            className="rounded-input-r bg-card px-4 py-3 text-body font-body text-foreground min-h-[80px]"
          />
        </View>
      </ConfirmModal>
    </ScrollView>
  );
}
