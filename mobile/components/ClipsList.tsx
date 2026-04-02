import { useEffect, useCallback } from 'react';
import { View, Text } from 'react-native';
import DraggableFlatList, {
  type RenderItemParams,
} from 'react-native-draggable-flatlist';
import { useClipsStore } from '@/store/clips-store';
import { usePipelineStore } from '@/store/pipeline-store';
import { Button } from './Button';
import ClipRow from './ClipRow';
import type { Clip } from '@/lib/types';

interface ClipsListProps {
  onPlayClip?: (url: string) => void;
}

export default function ClipsList({ onPlayClip }: ClipsListProps) {
  const { clips, loading, fetchClips, deleteClip, clearClips, reorderClips, stitchSaved } =
    useClipsStore();
  const videoUrl = usePipelineStore((s) => s.videoUrl);

  useEffect(() => {
    fetchClips();
  }, []);

  const renderItem = useCallback(
    ({ item, drag, isActive }: RenderItemParams<Clip>) => (
      <ClipRow
        url={item.url}
        note={item.note}
        ts={item.ts}
        onPress={() => onPlayClip?.(item.url)}
        onDelete={() => deleteClip(item.ts)}
        drag={drag}
        isActive={isActive}
      />
    ),
    [onPlayClip, deleteClip],
  );

  const handleDragEnd = useCallback(
    ({ from, to }: { from: number; to: number }) => {
      if (from !== to) reorderClips(from, to);
    },
    [reorderClips],
  );

  return (
    <View className="flex-1">
      {/* Header actions */}
      <View className="flex-row items-center justify-between px-4 py-2 border-b border-border">
        <Text className="text-sm font-semibold text-foreground">
          Clips ({clips.length})
        </Text>
        <View className="flex-row gap-2">
          {videoUrl && (
            <Button
              variant="ghost"
              size="sm"
              title="Save"
              onPress={() => {
                if (videoUrl) {
                  useClipsStore.getState().saveClip(videoUrl, 'Last generation');
                }
              }}
            />
          )}
          {clips.length >= 2 && (
            <Button
              variant="ghost"
              size="sm"
              title="Stitch"
              onPress={async () => {
                const result = await stitchSaved();
                if (result.stitched_url && onPlayClip) {
                  onPlayClip(result.stitched_url);
                }
              }}
            />
          )}
          {clips.length > 0 && (
            <Button
              variant="ghost"
              size="sm"
              title="Clear"
              onPress={clearClips}
            />
          )}
        </View>
      </View>

      {/* Clip list */}
      {clips.length === 0 ? (
        <View className="flex-1 items-center justify-center p-8">
          <Text className="text-sm text-muted-foreground text-center">
            No saved clips yet. Generate a video and save it here.
          </Text>
        </View>
      ) : (
        <DraggableFlatList
          data={clips}
          keyExtractor={(item) => String(item.ts)}
          renderItem={renderItem}
          onDragEnd={handleDragEnd}
          containerStyle={{ flex: 1 }}
        />
      )}
    </View>
  );
}
