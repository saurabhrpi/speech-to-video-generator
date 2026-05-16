import { useRef, useState, useCallback, useEffect } from 'react';
import { View, Text, ActivityIndicator, Pressable, Dimensions } from 'react-native';
import { Video, ResizeMode, AVPlaybackStatus } from 'expo-av';
import { resolveVideoUrl } from '@/lib/api-client';

const PREVIEW_HEIGHT = Dimensions.get('window').height * 0.42;

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

  // Tap-to-pause / tap-to-resume. Initial play is driven by the Video onLoad
  // hook below, so the gallery card → play flow is single-tap (no separate
  // "tap play icon" step).
  const handleTap = useCallback(async () => {
    if (!videoRef.current) return;
    if (isPlaying) {
      await videoRef.current.pauseAsync();
    } else {
      await videoRef.current.playAsync();
    }
  }, [isPlaying]);

  const onPlaybackStatusUpdate = useCallback(async (status: AVPlaybackStatus) => {
    if (!status.isLoaded) return;
    setIsPlaying(status.isPlaying);
    if (status.didJustFinish) {
      // Reset to first frame and pause; user taps to replay.
      await videoRef.current?.setPositionAsync(0);
      await videoRef.current?.pauseAsync();
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
            resizeMode={ResizeMode.COVER}
            isLooping={false}
            style={{ width: '100%', height: PREVIEW_HEIGHT }}
            onLoad={async () => {
              if (loadTimer.current) clearTimeout(loadTimer.current);
              setLoading(false);
              // Auto-play as soon as the video is decodable so tapping a
              // thumbnail goes straight to playback (no second tap on a play
              // icon). Tap-to-pause/resume is still handled by handleTap.
              try {
                await videoRef.current?.playAsync();
              } catch {
                // Best-effort; if playback fails (e.g., autoplay restrictions),
                // user can still tap to start manually.
              }
            }}
            onPlaybackStatusUpdate={onPlaybackStatusUpdate}
            onError={() => {
              if (loadTimer.current) clearTimeout(loadTimer.current);
              setLoading(false);
              setError('Video failed to load');
            }}
          />
        </Pressable>
      )}
    </View>
  );
}
