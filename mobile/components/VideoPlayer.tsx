import { useRef, useState, useCallback, useEffect } from 'react';
import { View, Text, ActivityIndicator, Pressable } from 'react-native';
import { Video, ResizeMode, AVPlaybackStatus } from 'expo-av';
import { Ionicons } from '@expo/vector-icons';
import { resolveVideoUrl } from '@/lib/api-client';

interface VideoPlayerProps {
  url: string;
  className?: string;
}

// Safety net for expo-av hangs (after HEAD confirms URL is reachable)
const PLAYBACK_TIMEOUT_MS = 90_000;

export default function VideoPlayer({ url, className }: VideoPlayerProps) {
  const videoRef = useRef<Video>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [showOverlay, setShowOverlay] = useState(true);
  const hideTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const loadTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const resolvedUrl = resolveVideoUrl(url);

  // Verify URL with a 1-byte GET (some CDNs reject HEAD on signed URLs), then let expo-av load
  useEffect(() => {
    let cancelled = false;
    const abort = new AbortController();
    console.log('[VideoPlayer] verifying:', resolvedUrl);

    fetch(resolvedUrl, {
      method: 'GET',
      headers: { Range: 'bytes=0-0' },
      signal: abort.signal,
    })
      .then((res) => {
        if (cancelled) return;
        // 200 or 206 (partial content) both mean reachable
        if (!res.ok && res.status !== 206) {
          setLoading(false);
          setError(`Video unavailable (${res.status})`);
          return;
        }
        // URL is reachable — start safety-net timer for expo-av hang
        loadTimer.current = setTimeout(() => {
          if (!cancelled) {
            setLoading(false);
            setError('Video timed out — CDN too slow');
          }
        }, PLAYBACK_TIMEOUT_MS);
      })
      .catch((err) => {
        if (cancelled || err.name === 'AbortError') return;
        setLoading(false);
        setError('Video unreachable — network error');
      });

    return () => {
      cancelled = true;
      abort.abort();
      if (loadTimer.current) clearTimeout(loadTimer.current);
    };
  }, [resolvedUrl]);

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
          <ActivityIndicator color="#FAF0E6" size="large" />
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
