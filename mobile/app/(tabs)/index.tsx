import { useState, useEffect } from 'react';
import { View, Text, TextInput, ScrollView, Pressable } from 'react-native';
import * as Haptics from 'expo-haptics';
import { activateKeepAwake, deactivateKeepAwake } from 'expo-keep-awake';
import { Button } from '@/components/Button';
import ProgressBar from '@/components/ProgressBar';
import VideoPlayer from '@/components/VideoPlayer';
import MicVisualizer from '@/components/MicVisualizer';
import ConfirmModal from '@/components/ConfirmModal';
import { useRecording } from '@/hooks/useRecording';
import { apiPost, resolveVideoUrl } from '@/lib/api-client';
import { streamJob } from '@/lib/streaming';
import { useAuthStore } from '@/store/auth-store';
import { Colors } from '@/lib/design-tokens';

type ModelKey = 'kling' | 'hailuo';

const MODELS: { key: ModelKey; label: string; id: string }[] = [
  { key: 'kling', label: 'Kling', id: 'klingai/video-v3-standard-text-to-video' },
  { key: 'hailuo', label: 'Hailuo', id: 'minimax/hailuo-02' },
];

const DURATIONS: Record<ModelKey, number[]> = {
  kling: [3, 10, 15],
  hailuo: [6, 10],
};

export default function SpeechScreen() {
  const { isRecording, metering, startRecording, stopRecording } = useRecording();
  const [busy, setBusy] = useState(false);
  const [statusMsg, setStatusMsg] = useState('');
  const [progress, setProgress] = useState(0);
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [promptText, setPromptText] = useState('');
  const [selectedModel, setSelectedModel] = useState<ModelKey>('kling');
  const [selectedDuration, setSelectedDuration] = useState(10);

  const { canGenerate, setLoginRequired, loginRequired } = useAuthStore();

  // Keep screen awake during generation
  useEffect(() => {
    if (busy) activateKeepAwake('speech');
    else deactivateKeepAwake('speech');
  }, [busy]);

  // Check auth on mount
  useEffect(() => {
    useAuthStore.getState().fetchSession();
  }, []);

  // Confirmation modal state
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [pendingUri, setPendingUri] = useState<string | null>(null);
  const [pendingTranscript, setPendingTranscript] = useState('');

  function handleModelChange(key: ModelKey) {
    setSelectedModel(key);
    const durations = DURATIONS[key];
    if (!durations.includes(selectedDuration)) {
      setSelectedDuration(durations[durations.length - 1]);
    }
  }

  function appendModelFields(formData: FormData) {
    const model = MODELS.find((m) => m.key === selectedModel)!;
    formData.append('model', model.id);
    formData.append('duration', String(selectedDuration));
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

  async function generateVideo(formData: FormData) {
    if (!canGenerate()) {
      setLoginRequired(true);
      return;
    }
    setBusy(true);
    setStatusMsg('Submitting...');
    setProgress(0);
    try {
      appendModelFields(formData);
      const { job_id } = await apiPost<{ job_id: string }>(
        '/api/generate/speech-to-video',
        formData,
        true,
      );

      const result = await streamJob(job_id, {
        onProgress: (_phase, _step, _total, message) => {
          setStatusMsg(message || 'Generating video...');
        },
        onPartialResult: () => {},
      });

      if (result?.video_url) {
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
        setVideoUrl(resolveVideoUrl(result.video_url));
        setStatusMsg('Done!');
        setProgress(100);
      } else {
        const err = result?.error;
        const errMsg = typeof err === 'string' ? err : JSON.stringify(err);
        setStatusMsg(`Error: ${errMsg || 'Generation failed'}`);
      }
    } catch (err: any) {
      setStatusMsg(err.message || 'Network error');
    } finally {
      setBusy(false);
    }
  }

  async function handleTextToVideo() {
    if (!promptText.trim()) return;
    const formData = new FormData();
    formData.append('prompt', promptText.trim());
    await generateVideo(formData);
  }

  async function handleConfirmProceed() {
    setConfirmOpen(false);
    if (!pendingUri) return;

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
    setPendingUri(null);
    await generateVideo(formData);
  }

  const durations = DURATIONS[selectedModel];

  return (
    <ScrollView className="flex-1 bg-background" contentContainerClassName="p-5 pb-20 gap-8">
      <View className="gap-1">
        <Text className="text-heading font-heading text-foreground">Speech to Video</Text>
        <Text className="text-body font-body text-muted-foreground">
          Type a prompt or record audio to generate a video.
        </Text>
      </View>

      {/* Login required */}
      {loginRequired && (
        <View className="rounded-card border border-destructive/50 bg-destructive/10 p-3">
          <Text className="text-body font-body text-destructive">Sign in required — tap the gear icon above.</Text>
        </View>
      )}

      {/* Model selector */}
      <View className="gap-2">
        <Text className="text-caption font-body-medium text-muted-foreground uppercase tracking-wide">Model</Text>
        <View className="flex-row rounded-input-r bg-card p-1">
          {MODELS.map((m) => {
            const active = selectedModel === m.key;
            return (
              <Pressable key={m.key} onPress={() => handleModelChange(m.key)} disabled={busy} style={{ flex: 1 }}>
                <View
                  className="items-center rounded-input-r py-2.5"
                  style={active ? { backgroundColor: Colors.accent, borderWidth: 1, borderColor: Colors.glassyBorder } : undefined}
                >
                  <Text
                    className="font-body-medium"
                    style={{ fontSize: 14, color: active ? '#F5F0EB' : Colors.textSecondary }}
                  >
                    {m.label}
                  </Text>
                </View>
              </Pressable>
            );
          })}
        </View>
      </View>

      {/* Duration selector */}
      <View className="gap-2">
        <Text className="text-caption font-body-medium text-muted-foreground uppercase tracking-wide">Duration</Text>
        <View className="flex-row rounded-input-r bg-card p-1">
          {durations.map((d) => {
            const active = selectedDuration === d;
            return (
              <Pressable key={d} onPress={() => setSelectedDuration(d)} disabled={busy} style={{ flex: 1 }}>
                <View
                  className="items-center rounded-input-r py-2.5"
                  style={active ? { backgroundColor: Colors.accent, borderWidth: 1, borderColor: Colors.glassyBorder } : undefined}
                >
                  <Text
                    className="font-body-medium"
                    style={{ fontSize: 14, color: active ? '#F5F0EB' : Colors.textSecondary }}
                  >
                    {d}s
                  </Text>
                </View>
              </Pressable>
            );
          })}
        </View>
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
          editable={!busy && !isRecording}
          className="rounded-input-r bg-card px-4 py-3 text-body font-body text-foreground min-h-[96px]"
        />
        <Button
          size="lg"
          onPress={handleTextToVideo}
          disabled={busy || isRecording || !promptText.trim()}
          title="Generate Video"
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
