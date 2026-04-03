import { View, Text, ScrollView, Pressable, Alert } from 'react-native';
import { Image } from 'expo-image';
import * as Clipboard from 'expo-clipboard';
import { Button } from './Button';
import VideoPlayer from './VideoPlayer';
import { PHASE_ORDER, PHASE_LABELS, NUM_STAGES } from '@/lib/constants';
import { nextStopAfter } from '@/lib/pipeline';
import type { PipelineState } from '@/lib/types';

interface PipelineReviewProps {
  phaseCompleted: string;
  pipelineState: PipelineState & Record<string, any>;
  busy: boolean;
  onContinue: () => void;
  onGenerateRemainingImages: () => void;
  onGenerateRemainingVideos: () => void;
  onStop: () => void;
  onStartOver: () => void;
}

function PhaseDots({ phaseCompleted }: { phaseCompleted: string }) {
  const completedIdx = (PHASE_ORDER as readonly string[]).indexOf(phaseCompleted);
  return (
    <View className="flex-row items-center gap-0.5">
      {PHASE_ORDER.map((p, i) => (
        <View
          key={p}
          className={`h-2 rounded-full ${
            completedIdx >= i ? 'bg-primary' : 'bg-muted'
          } ${p.startsWith('stage_') || p.startsWith('video_') ? 'w-3' : 'w-5'}`}
        />
      ))}
    </View>
  );
}

export default function PipelineReview({
  phaseCompleted,
  pipelineState,
  busy,
  onContinue,
  onGenerateRemainingImages,
  onGenerateRemainingVideos,
  onStop,
  onStartOver,
}: PipelineReviewProps) {
  const next = nextStopAfter(phaseCompleted);

  return (
    <View className="rounded-lg border border-border bg-card p-4 gap-4">
      {/* Header */}
      <View className="flex-row items-center justify-between">
        <Text className="text-sm font-semibold text-foreground">
          Phase complete: {PHASE_LABELS[phaseCompleted] || phaseCompleted}
        </Text>
        <PhaseDots phaseCompleted={phaseCompleted} />
      </View>

      {/* Plan phase */}
      {phaseCompleted === 'plan' && pipelineState.stages && (
        <View className="gap-3">
          <View>
            <Text className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
              Scene Bible
            </Text>
            <View className="mt-1 rounded bg-muted p-2">
              <Text className="text-sm text-foreground">{pipelineState.scene_bible}</Text>
            </View>
          </View>

          {(pipelineState.elements?.length ?? 0) > 0 && (
            <View>
              <Text className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                Elements to Renovate ({pipelineState.elements!.length})
              </Text>
              <View className="mt-1 flex-row flex-wrap gap-1.5">
                {pipelineState.elements!.map((e, i) => (
                  <View key={i} className="rounded-full bg-muted px-2.5 py-0.5">
                    <Text className="text-xs text-foreground">{e}</Text>
                  </View>
                ))}
              </View>
            </View>
          )}

          <View>
            <Text className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
              Stage 1 Description
            </Text>
            <View className="mt-1 rounded bg-muted p-2">
              <Text className="text-sm text-foreground">
                {(pipelineState.stages as any[])[0]?.description}
              </Text>
            </View>
          </View>
        </View>
      )}

      {/* Stage phase — keyframe images */}
      {phaseCompleted?.startsWith('stage_') && pipelineState.keyframe_images && (
        <View className="gap-3">
          {(pipelineState.elements?.length ?? 0) > 0 && (
            <View>
              <Text className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                Renovation Progress
              </Text>
              <View className="mt-1 flex-row flex-wrap gap-1.5">
                {pipelineState.elements!.map((e, i) => {
                  const done = (pipelineState.renovated_elements || []).includes(e);
                  return (
                    <View
                      key={i}
                      className={`rounded-full px-2.5 py-0.5 ${done ? 'bg-primary' : 'bg-muted'}`}
                    >
                      <Text
                        className={`text-xs ${done ? 'text-primary-foreground' : 'text-foreground'}`}
                      >
                        {done ? '\u2713 ' : ''}{e}
                      </Text>
                    </View>
                  );
                })}
              </View>
            </View>
          )}

          <Text className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
            Keyframe Images ({pipelineState.keyframe_images.length} of {NUM_STAGES})
          </Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false}>
            <View className="flex-row gap-2">
              {pipelineState.keyframe_images.map((kf: any, i: number) => (
                <Pressable
                  key={i}
                  onPress={() => {
                    Clipboard.setStringAsync(kf.image_url);
                    Alert.alert('Copied', `Stage ${kf.stage} image URL copied to clipboard.`);
                  }}
                >
                  <View className="gap-1" style={{ width: 140 }}>
                    <Image
                      source={{ uri: kf.image_url }}
                      style={{ width: 140, height: 79, borderRadius: 6 }}
                      contentFit="cover"
                    />
                    <Text className="text-xs text-center text-muted-foreground">
                      Stage {kf.stage} · tap to copy
                    </Text>
                  </View>
                </Pressable>
              ))}
            </View>
          </ScrollView>
        </View>
      )}

      {/* Video phase — transition videos */}
      {phaseCompleted?.startsWith('video_') && pipelineState.transition_videos && (() => {
        const vidIdx = parseInt(phaseCompleted.replace('video_', ''), 10) - 1;
        const latestUrl = pipelineState.transition_videos[vidIdx];
        return (
          <View className="gap-3">
            <Text className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
              Transition Video {vidIdx + 1} {'\u2192'} {vidIdx + 2}
              {'  '}({pipelineState.transition_videos!.length} of {NUM_STAGES - 1} done)
            </Text>
            {latestUrl && <VideoPlayer url={latestUrl} />}
          </View>
        );
      })()}

      {/* Action buttons */}
      <View className="flex-row flex-wrap gap-2 pt-1">
        <Button onPress={onContinue} disabled={busy} title={
          next
            ? `Continue to ${PHASE_LABELS[next] || 'next phase'}`
            : 'Finish & Stitch'
        } />

        {(phaseCompleted === 'plan' ||
          (phaseCompleted?.startsWith('stage_') &&
            phaseCompleted !== `stage_${NUM_STAGES}`)) && (
          <Button
            variant="secondary"
            disabled={busy}
            onPress={onGenerateRemainingImages}
            title="Generate Remaining Images"
          />
        )}

        {(phaseCompleted === `stage_${NUM_STAGES}` ||
          phaseCompleted?.startsWith('video_')) && (
          <Button
            variant="secondary"
            disabled={busy}
            onPress={onGenerateRemainingVideos}
            title="Generate Remaining Videos"
          />
        )}

        <Button variant="secondary" onPress={onStop} disabled={busy} title="Stop" />
        <Button variant="outline" onPress={onStartOver} disabled={busy} title="Start Over" />
      </View>
    </View>
  );
}
