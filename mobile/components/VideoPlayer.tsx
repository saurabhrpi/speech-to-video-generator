import { useState } from 'react';
import { View, Text, ActivityIndicator } from 'react-native';
import { Video, ResizeMode } from 'expo-av';
import { resolveVideoUrl } from '@/lib/api-client';

interface VideoPlayerProps {
  url: string;
  className?: string;
}

export default function VideoPlayer({ url, className }: VideoPlayerProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const resolvedUrl = resolveVideoUrl(url);

  return (
    <View className={`rounded-lg overflow-hidden bg-black ${className ?? ''}`}>
      {loading && !error && (
        <View className="absolute inset-0 items-center justify-center z-10">
          <ActivityIndicator color="#3b82f6" size="large" />
        </View>
      )}
      {error ? (
        <View className="h-48 items-center justify-center">
          <Text className="text-sm text-destructive">{error}</Text>
        </View>
      ) : (
        <Video
          source={{ uri: resolvedUrl }}
          useNativeControls
          resizeMode={ResizeMode.CONTAIN}
          style={{ width: '100%', aspectRatio: 16 / 9 }}
          onLoad={() => setLoading(false)}
          onError={(e) => {
            setLoading(false);
            setError('Video failed to load');
          }}
        />
      )}
    </View>
  );
}
