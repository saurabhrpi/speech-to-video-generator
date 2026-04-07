import { useEffect, useState } from 'react';
import { View, Text, TextInput, ScrollView, Switch, ActivityIndicator, KeyboardAvoidingView, Platform } from 'react-native';
import { activateKeepAwake, deactivateKeepAwake } from 'expo-keep-awake';
import Picker from '@/components/Picker';
import TagInput from '@/components/TagInput';
import { Button } from '@/components/Button';
import ProgressBar from '@/components/ProgressBar';
import VideoPlayer from '@/components/VideoPlayer';
import PipelineReview from '@/components/PipelineReview';
import { usePipelineStore } from '@/store/pipeline-store';
import { useAuthStore } from '@/store/auth-store';
import { apiGet } from '@/lib/api-client';
import type { TimelapseOptions } from '@/lib/types';

export default function TimelapseScreen() {
  const [options, setOptions] = useState<TimelapseOptions | null>(null);
  const [roomType, setRoomType] = useState('');
  const [style, setStyle] = useState('');
  const [features, setFeatures] = useState<string[]>([]);
  const [materials, setMaterials] = useState<string[]>([]);
  const [lighting, setLighting] = useState('natural');
  const [cameraMotion, setCameraMotion] = useState('slow_pan');
  const [progression, setProgression] = useState('construction');
  const [videoModel, setVideoModel] = useState<'cheap' | 'expensive'>('cheap');
  const [freeform, setFreeform] = useState('');

  const {
    busy, statusMsg, progress, videoUrl, pipelineState, phaseCompleted,
    pipelineError, stepByStep, setStepByStep, runPipeline, runFakeJob,
    handleContinue, handleResume, handleStop, handleStartOver,
    handleGenerateRemainingImages, handleGenerateRemainingVideos,
  } = usePipelineStore();

  const { auth, canGenerate, setLoginRequired, loginRequired } = useAuthStore();

  // Keep screen awake during generation
  useEffect(() => {
    if (busy) activateKeepAwake('pipeline');
    else deactivateKeepAwake('pipeline');
  }, [busy]);

  // Load options on mount
  useEffect(() => {
    apiGet<TimelapseOptions>('/api/timelapse/options')
      .then(setOptions)
      .catch(() => {});
  }, []);

  // Check auth on mount
  useEffect(() => {
    useAuthStore.getState().fetchSession();
  }, []);

  function handleSubmit() {
    if (!roomType || !style) return;
    if (!canGenerate()) {
      setLoginRequired(true);
      return;
    }
    const payload = {
      room_type: roomType,
      style,
      features,
      materials,
      lighting,
      camera_motion: cameraMotion,
      progression,
      video_model: videoModel,
      freeform_description: freeform,
    };
    const stopAfter = stepByStep ? 'plan' : null;
    runPipeline(payload, stopAfter, null);
  }

  if (!options) {
    return (
      <View className="flex-1 items-center justify-center bg-background">
        <ActivityIndicator size="large" color="#3b82f6" />
        <Text className="mt-2 text-sm text-muted-foreground">Loading options...</Text>
      </View>
    );
  }

  return (
    <KeyboardAvoidingView
      className="flex-1"
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      keyboardVerticalOffset={100}
    >
    <ScrollView className="flex-1 bg-background" contentContainerClassName="p-4 pb-20 gap-5">
      {/* Progress bar */}
      {(busy || statusMsg) && (
        <ProgressBar progress={progress} message={statusMsg} indeterminate={busy && progress === 0} />
      )}

      {/* Login required */}
      {loginRequired && (
        <View className="rounded-lg border border-destructive/50 bg-destructive/5 p-3">
          <Text className="text-sm text-destructive">Sign in required to generate videos.</Text>
        </View>
      )}

      {/* Pipeline review (step-by-step) */}
      {phaseCompleted && pipelineState && !busy && (
        <PipelineReview
          phaseCompleted={phaseCompleted}
          pipelineState={pipelineState}
          busy={busy}
          onContinue={handleContinue}
          onGenerateRemainingImages={handleGenerateRemainingImages}
          onGenerateRemainingVideos={handleGenerateRemainingVideos}
          onStop={handleStop}
          onStartOver={handleStartOver}
        />
      )}

      {/* Pipeline error */}
      {pipelineError && pipelineState && !phaseCompleted && !busy && (
        <View className="rounded-lg border border-destructive/50 bg-destructive/5 p-4 gap-2">
          <Text className="text-sm font-semibold text-destructive">Pipeline failed</Text>
          <Text className="text-sm text-muted-foreground">{pipelineError}</Text>
          <View className="flex-row gap-2 pt-1">
            <Button onPress={handleResume} title="Resume" />
            <Button variant="outline" onPress={handleStartOver} title="Start Over" />
          </View>
        </View>
      )}

      {/* Video result */}
      {videoUrl && !busy && (
        <VideoPlayer url={videoUrl} />
      )}

      {/* Form */}
      {!phaseCompleted && !busy && (
        <View className="gap-5">
          {/* Pickers grid — 2 columns */}
          <View className="gap-4">
            <View className="flex-row gap-4">
              <View className="flex-1">
                <Picker
                  label="Room Type"
                  required
                  value={roomType}
                  onValueChange={setRoomType}
                  options={options.room_types}
                  placeholder="Select room..."
                />
              </View>
              <View className="flex-1">
                <Picker
                  label="Style"
                  required
                  value={style}
                  onValueChange={setStyle}
                  options={options.styles}
                  placeholder="Select style..."
                />
              </View>
            </View>

            <View className="flex-row gap-4">
              <View className="flex-1">
                <Picker
                  label="Lighting"
                  value={lighting}
                  onValueChange={setLighting}
                  options={options.lighting_options}
                />
              </View>
              <View className="flex-1">
                <Picker
                  label="Camera Motion"
                  value={cameraMotion}
                  onValueChange={setCameraMotion}
                  options={options.camera_options}
                />
              </View>
            </View>

            <View className="flex-row gap-4">
              <View className="flex-1">
                <Picker
                  label="Progression"
                  value={progression}
                  onValueChange={setProgression}
                  options={options.progression_types}
                />
              </View>
              <View className="flex-1">
                <Picker
                  label="Video Model"
                  value={videoModel}
                  onValueChange={(v) => setVideoModel(v as 'cheap' | 'expensive')}
                  options={[
                    { value: 'cheap', label: 'Cheap (Hailuo)' },
                    { value: 'expensive', label: 'Expensive (Kling Pro)' },
                  ]}
                />
              </View>
            </View>
          </View>

          {/* Tag inputs */}
          <TagInput
            label="Features"
            tags={features}
            onAddTag={(f) => setFeatures((prev) => [...prev, f])}
            onRemoveTag={(f) => setFeatures((prev) => prev.filter((x) => x !== f))}
            suggestions={options.suggested_features}
            placeholder="Type a feature and press return..."
          />

          <TagInput
            label="Materials"
            optional
            tags={materials}
            onAddTag={(m) => setMaterials((prev) => [...prev, m])}
            onRemoveTag={(m) => setMaterials((prev) => prev.filter((x) => x !== m))}
            suggestions={options.suggested_materials}
            placeholder="Type a material and press return..."
          />

          {/* Freeform */}
          <View className="gap-1.5">
            <Text className="text-sm font-medium text-foreground">
              Additional Description <Text className="text-muted-foreground font-normal">(optional)</Text>
            </Text>
            <TextInput
              value={freeform}
              onChangeText={setFreeform}
              placeholder="Any extra creative direction..."
              placeholderTextColor="#9ca3af"
              multiline
              numberOfLines={2}
              textAlignVertical="top"
              className="rounded-md border border-input bg-background px-3 py-2.5 text-sm text-foreground min-h-[60px]"
            />
          </View>

          {/* Step-by-step toggle */}
          <View className="flex-row items-center gap-3">
            <Switch
              value={stepByStep}
              onValueChange={setStepByStep}
              trackColor={{ false: '#d1d5db', true: '#93c5fd' }}
              thumbColor={stepByStep ? '#3b82f6' : '#f4f3f4'}
            />
            <View>
              <Text className="text-sm font-medium text-foreground">Step-by-step mode</Text>
              <Text className="text-xs text-muted-foreground">Review each phase before proceeding</Text>
            </View>
          </View>

          {/* Submit */}
          <Button
            size="lg"
            onPress={handleSubmit}
            disabled={busy || !roomType || !style}
            title={busy ? 'Generating...' : 'Generate Timelapse'}
            className="w-full"
          />

          {/* Debug: Test SSE with fake job (no AI cost) */}
          <Button
            variant="outline"
            onPress={runFakeJob}
            disabled={busy}
            title="🐛 Test SSE (fake job)"
            className="w-full"
          />
        </View>
      )}
    </ScrollView>
    </KeyboardAvoidingView>
  );
}
