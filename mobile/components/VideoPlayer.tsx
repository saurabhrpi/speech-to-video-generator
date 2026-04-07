import { useRef, useState, useCallback, useEffect } from 'react';
import { View, Text, ActivityIndicator, Pressable } from 'react-native';
import { Video, ResizeMode, AVPlaybackStatus } from 'expo-av';
import { Ionicons } from '@expo/vector-icons';
import { resolveVideoUrl } from '@/lib/api-client';

interface VideoPlayerProps {
  url: string;
  className?: string;
}

const LOAD_TIMEOUT_MS = 15_000;

export default function VideoPlayer({ url, className }: VideoPlayerProps) {
  const videoRef = useRef<Video>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [showOverlay, setShowOverlay] = useState(true);
  const hideTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const loadTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const resolvedUrl = resolveVideoUrl(url);

  // Timeout: if video doesn't load within 15s, show error
  useEffect(() => {
    loadTimer.current = setTimeout(() => {
      if (loading) {
        setLoading(false);
        setError('Video timed out — could not load');
      }
    }, LOAD_TIMEOUT_MS);
    return () => {
      if (loadTimer.current) clearTimeout(loadTimer.current);
    };
  }, []);

  const scheduleHide = useCallback(() => {
    if (hideTimer.current) clearTimeout(hideTimer.current);
    hideTimer.current = setTimeout(() => setShowOverlay(false), 1500);
  }, []);

  const handleTap = useCallback(async () => {
    if (!videoRef.current) return;

    if (isPlaying) {
      // If playing and overlay hidden, just show overlay briefly
      if (!showOverlay) {
        setShowOverlay(true);
        scheduleHide();
        return;
      }
      // If playing and overlay visible, pause
      await videoRef.current.pauseAsync();
    } else {
      await videoRef.current.playAsync();
      setShowOverlay(true);
      scheduleHide();
    }
  }, [isPlaying, showOverlay, scheduleHide]);

  const onPlaybackStatusUpdate = useCallback(async (status: AVPlaybackStatus) => {
    if (!status.isLoaded) return;
    setIsPlaying(status.isPlaying);
    if (status.didJustFinish) {
      await videoRef.current?.setPositionAsync(0);
      await videoRef.current?.pauseAsync();
      setShowOverlay(true);
    }
  }, []);

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
        <Pressable onPress={handleTap}>
          <Video
            ref={videoRef}
            source={{ uri: resolvedUrl }}
            resizeMode={ResizeMode.CONTAIN}
            isLooping={false}
            style={{ width: '100%', aspectRatio: 16 / 9 }}
            onLoad={() => {
              if (loadTimer.current) clearTimeout(loadTimer.current);
              setLoading(false);
            }}
            onPlaybackStatusUpdate={onPlaybackStatusUpdate}
            onError={() => {
              if (loadTimer.current) clearTimeout(loadTimer.current);
              setLoading(false);
              setError('Video failed to load');
            }}
          />
          {showOverlay && !loading && (
            <View className="absolute inset-0 items-center justify-center">
              {!isPlaying && (
                <View className="rounded-full bg-black/40 p-4">
                  <Ionicons name="play" size={36} color="white" />
                </View>
              )}
            </View>
          )}
        </Pressable>
      )}
    </View>
  );
}
