import { useState } from 'react';
import { View, Text, TextInput, ScrollView, Pressable } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { useRouter } from 'expo-router';
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

// Primary CTA color — same hex used for ConfirmModal's Generate button.
const CTA_BLUE = '#2563EB';
const RECORDING_RED = '#B91C1C';

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
  const blockedByInFlight =
    cost !== null &&
    creditBalance !== null &&
    inFlightCost > 0 &&
    creditBalance >= cost &&
    creditBalance - inFlightCost < cost;

  const generateDisabled = isRecording || !promptText.trim() || blockedByInFlight;

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

  function handleStartRecording() {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    startRecording();
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
    <ScrollView className="flex-1 bg-background" contentContainerClassName="p-5 pb-20 gap-6">
      {/* Header — voice-first framing */}
      <View className="gap-1">
        <Text className="text-heading font-body text-foreground">Speech to Video</Text>
        <Text className="text-body font-body text-muted-foreground">
          Speak your idea — get a 10-second video.
        </Text>
      </View>

      {/* Primary input: large mic CTA. Idle = blue circle with mic icon. Recording = red capsule with "Stop Recording" text. */}
      <View style={{ alignItems: 'center', gap: 12, paddingTop: 8 }}>
        {isRecording && <MicVisualizer metering={metering} isActive={isRecording} />}
        {isRecording ? (
          <Pressable
            onPress={handleStop}
            accessibilityLabel="Stop Recording"
            style={{
              height: 72,
              paddingHorizontal: 32,
              minWidth: 220,
              borderRadius: 36,
              backgroundColor: RECORDING_RED,
              alignItems: 'center',
              justifyContent: 'center',
              borderWidth: 2,
              borderColor: 'rgba(255,255,255,0.22)',
            }}
          >
            <Text style={{ color: '#FFFFFF', fontSize: 22, fontWeight: '600' }}>
              Stop Recording
            </Text>
          </Pressable>
        ) : (
          <Pressable
            onPress={handleStartRecording}
            accessibilityLabel="Start Recording"
            style={{
              width: 130,
              height: 130,
              borderRadius: 65,
              backgroundColor: CTA_BLUE,
              alignItems: 'center',
              justifyContent: 'center',
              borderWidth: 3,
              borderColor: 'rgba(255,255,255,0.22)',
            }}
          >
            <Ionicons name="mic" size={56} color="#FFFFFF" />
          </Pressable>
        )}
        <Text className="text-caption font-body text-muted-foreground">
          {isRecording ? 'Tap when you’re done' : 'Tap to speak your idea'}
        </Text>
      </View>

      {/* Divider — text is the secondary input mode */}
      <View className="flex-row items-center gap-3">
        <View className="flex-1 h-px bg-border" />
        <Text className="text-caption font-body text-muted-foreground">or type</Text>
        <View className="flex-1 h-px bg-border" />
      </View>

      {/* Text prompt input + Generate */}
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
        {/* Generate Video — blue capsule, 2x font (~28px), white text. Primary CTA. */}
        <Pressable
          onPress={handleTextToVideo}
          disabled={generateDisabled}
          accessibilityLabel="Generate Video"
          style={{
            height: 64,
            borderRadius: 32,
            backgroundColor: CTA_BLUE,
            alignItems: 'center',
            justifyContent: 'center',
            opacity: generateDisabled ? 0.4 : 1,
          }}
        >
          <Text style={{ color: '#FFFFFF', fontSize: 24, fontWeight: '600' }}>
            Generate Video
          </Text>
        </Pressable>
      </View>

      {/* Transcript review modal — fires after voice recording stops */}
      <ConfirmModal
        visible={confirmOpen}
        title="Edit the transcript below if you want. Then, generate the video."
        confirmText="Generate Video"
        cancelText="Cancel"
        onConfirm={handleConfirmProceed}
        onCancel={() => {
          setConfirmOpen(false);
          setPendingUri(null);
        }}
      >
        <TextInput
          value={pendingTranscript}
          onChangeText={setPendingTranscript}
          multiline
          numberOfLines={5}
          textAlignVertical="top"
          placeholder={pendingTranscript ? undefined : 'Transcribing...'}
          placeholderTextColor={Colors.textSecondary}
          className="rounded-input-r bg-card px-4 py-3 text-body font-body text-foreground min-h-[120px]"
        />
      </ConfirmModal>
    </ScrollView>
  );
}
