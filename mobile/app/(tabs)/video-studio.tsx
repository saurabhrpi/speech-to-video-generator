import { useState, useRef } from 'react';
import { View, Text, TextInput, ScrollView, Pressable, KeyboardAvoidingView, Platform } from 'react-native';
import { Image } from 'expo-image';
import { Button } from '@/components/Button';
import ProgressBar from '@/components/ProgressBar';
import VideoPlayer from '@/components/VideoPlayer';
import Picker from '@/components/Picker';
import { apiPost } from '@/lib/api-client';
import { pollJob } from '@/lib/polling';
import { resolveVideoUrl } from '@/lib/api-client';

export default function VideoStudioScreen() {
  const [imageUrls, setImageUrls] = useState<string[]>(['', '']);
  const [model, setModel] = useState<'cheap' | 'expensive'>('cheap');
  const [videos, setVideos] = useState<string[]>([]);
  const [prompts, setPrompts] = useState<string[]>([]);
  const [statusMsg, setStatusMsg] = useState('');
  const [progress, setProgress] = useState(0);
  const [busy, setBusy] = useState(false);
  const [allDone, setAllDone] = useState(false);
  const [stitching, setStitching] = useState(false);
  const [stitchedUrl, setStitchedUrl] = useState<string | null>(null);
  const resumeRef = useRef<Record<string, any> | null>(null);

  const validUrls = imageUrls.filter((u) => u.trim().startsWith('http'));
  const totalTransitions = validUrls.length - 1;
  const canStart = validUrls.length >= 2 && !busy;

  function updateUrl(idx: number, val: string) {
    setImageUrls((prev) => {
      const copy = [...prev];
      copy[idx] = val;
      return copy;
    });
  }

  function removeSlot(idx: number) {
    if (imageUrls.length <= 2) return;
    setImageUrls((prev) => prev.filter((_, i) => i !== idx));
  }

  function moveImage(from: number, to: number) {
    if (to < 0 || to >= imageUrls.length) return;
    setImageUrls((prev) => {
      const copy = [...prev];
      const [item] = copy.splice(from, 1);
      copy.splice(to, 0, item);
      return copy;
    });
  }

  async function runGeneration(stopAfter: string | null, resumeState: Record<string, any> | null) {
    setBusy(true);
    setStatusMsg('Starting video generation...');
    setAllDone(false);

    try {
      const { job_id } = await apiPost<{ job_id: string }>('/api/generate/custom-videos', {
        image_urls: validUrls,
        model,
        stop_after: stopAfter,
        resume_state: resumeState,
      });

      const result = await pollJob(job_id, {
        onProgress: (_phase, _step, _total, message) => {
          setStatusMsg(message || 'Processing...');
          const doneVids = resumeRef.current?.transition_videos?.length || 0;
          setProgress(totalTransitions > 0 ? Math.round((doneVids / totalTransitions) * 100) : 0);
        },
        onPartialResult: (partial) => {
          resumeRef.current = partial;
          if (partial.transition_videos) setVideos(partial.transition_videos);
          if (partial.transition_prompts) setPrompts(partial.transition_prompts);
        },
      });

      if (!result) return;

      setVideos(result.transition_videos || []);
      setPrompts(result.transition_prompts || []);
      resumeRef.current = result;

      if (result.phase_completed === 'all_done') {
        setAllDone(true);
        setProgress(100);
        setStatusMsg('All transitions complete!');
      } else {
        const completedCount = (result.transition_videos || []).length;
        setProgress(Math.round((completedCount / totalTransitions) * 100));
        setStatusMsg(`${completedCount} of ${totalTransitions} transitions done.`);
      }
    } catch (err: any) {
      setStatusMsg(err.message || 'Generation failed.');
    } finally {
      setBusy(false);
    }
  }

  function handleStartOver() {
    setVideos([]);
    setPrompts([]);
    setStatusMsg('');
    setProgress(0);
    setAllDone(false);
    setStitching(false);
    setStitchedUrl(null);
    resumeRef.current = null;
  }

  async function handleStitch() {
    if (videos.length < 1) return;
    setStitching(true);
    setBusy(true);
    setStatusMsg('Stitching final video...');

    try {
      const data = await apiPost<{ success: boolean; stitched_url?: string; error?: string }>(
        '/api/generate/stitch-custom',
        { video_urls: videos },
      );
      if (data.success && data.stitched_url) {
        setStitchedUrl(data.stitched_url);
        setStatusMsg('Final video stitched!');
      } else {
        setStatusMsg(`Stitch error: ${data.error || 'Unknown error'}`);
      }
    } catch {
      setStatusMsg('Network error during stitching.');
    } finally {
      setStitching(false);
      setBusy(false);
    }
  }

  const hasStarted = videos.length > 0 || busy;

  return (
    <KeyboardAvoidingView
      className="flex-1"
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      keyboardVerticalOffset={100}
    >
    <ScrollView className="flex-1 bg-background" contentContainerClassName="p-4 pb-20 gap-5">
      {/* Image URLs */}
      <View className="rounded-lg border border-border bg-card p-4 gap-3">
        <Text className="text-sm font-semibold text-foreground">Images</Text>
        <Text className="text-xs text-muted-foreground">
          Paste image URLs in order. Transition videos will be generated between each pair.
        </Text>

        {imageUrls.map((url, idx) => (
          <View key={idx} className="flex-row items-center gap-2">
            <Text className="text-xs text-muted-foreground w-10">#{idx + 1}</Text>
            <TextInput
              value={url}
              onChangeText={(v) => updateUrl(idx, v)}
              placeholder="https://..."
              placeholderTextColor="#9ca3af"
              editable={!busy}
              className="flex-1 rounded border border-input bg-background px-2 py-1.5 text-xs text-foreground"
              autoCapitalize="none"
              keyboardType="url"
            />
            {url.trim().startsWith('http') && (
              <Image
                source={{ uri: url }}
                style={{ width: 40, height: 40, borderRadius: 4 }}
                contentFit="cover"
              />
            )}
            <View className="gap-0.5">
              <Pressable
                onPress={() => moveImage(idx, idx - 1)}
                disabled={idx === 0 || busy}
              >
                <Text className={`text-xs ${idx === 0 ? 'opacity-30' : ''} text-muted-foreground`}>
                  {'\u25b2'}
                </Text>
              </Pressable>
              <Pressable
                onPress={() => moveImage(idx, idx + 1)}
                disabled={idx === imageUrls.length - 1 || busy}
              >
                <Text className={`text-xs ${idx === imageUrls.length - 1 ? 'opacity-30' : ''} text-muted-foreground`}>
                  {'\u25bc'}
                </Text>
              </Pressable>
            </View>
            <Pressable onPress={() => removeSlot(idx)} disabled={imageUrls.length <= 2 || busy}>
              <Text className={`text-xs ${imageUrls.length <= 2 ? 'opacity-30' : ''} text-destructive`}>
                {'\u2715'}
              </Text>
            </Pressable>
          </View>
        ))}

        <Button variant="outline" size="sm" onPress={() => setImageUrls((p) => [...p, ''])} disabled={busy} title="+ Add Image" />

        <View className="pt-2">
          <Picker
            label="Model"
            value={model}
            onValueChange={(v) => setModel(v as 'cheap' | 'expensive')}
            options={[
              { value: 'cheap', label: 'Cheap (Hailuo)' },
              { value: 'expensive', label: 'Expensive (Kling Pro)' },
            ]}
          />
        </View>

        <View className="flex-row gap-2 pt-2">
          {!hasStarted ? (
            <Button onPress={() => runGeneration(`video_1`, null)} disabled={!canStart} title="Generate Next Video" />
          ) : (
            <>
              {!allDone && videos.length < totalTransitions && (
                <>
                  <Button
                    onPress={() => runGeneration(`video_${videos.length + 1}`, resumeRef.current)}
                    disabled={busy}
                    title="Generate Next"
                  />
                  <Button
                    variant="secondary"
                    onPress={() => runGeneration(null, resumeRef.current)}
                    disabled={busy}
                    title="Generate All"
                  />
                </>
              )}
              <Button variant="outline" onPress={handleStartOver} disabled={busy} title="Start Over" />
            </>
          )}
        </View>
      </View>

      {/* Progress */}
      {(busy || statusMsg) ? (
        <ProgressBar progress={progress} message={statusMsg} indeterminate={busy && progress === 0} />
      ) : null}

      {/* Generated videos */}
      {videos.length > 0 && (
        <View className="rounded-lg border border-border bg-card p-4 gap-3">
          <Text className="text-sm font-semibold text-foreground">
            Transition Videos ({videos.length} of {totalTransitions})
          </Text>
          {videos.map((url, i) => (
            <View key={i} className="gap-1">
              <Text className="text-xs text-muted-foreground">
                Transition {i + 1}: Pic {i + 1} {'\u2192'} Pic {i + 2}
              </Text>
              {prompts[i] && (
                <Text className="text-xs text-muted-foreground bg-muted rounded px-2 py-1">
                  Prompt: {prompts[i]}
                </Text>
              )}
              <VideoPlayer url={url} />
            </View>
          ))}
        </View>
      )}

      {/* All done — stitch */}
      {allDone && videos.length > 0 && !stitchedUrl && (
        <View className="rounded-lg border border-green-500/30 bg-green-500/5 p-4 gap-2">
          <Text className="text-sm font-medium text-green-700">
            All {videos.length} transitions generated.
          </Text>
          <Button onPress={handleStitch} disabled={stitching || busy} title={stitching ? 'Stitching...' : 'Stitch Final Video'} />
        </View>
      )}

      {/* Stitched result */}
      {stitchedUrl && (
        <View className="rounded-lg border border-border bg-card p-4 gap-2">
          <Text className="text-sm font-semibold text-foreground">Final Stitched Video</Text>
          <VideoPlayer url={stitchedUrl} />
        </View>
      )}
    </ScrollView>
    </KeyboardAvoidingView>
  );
}
