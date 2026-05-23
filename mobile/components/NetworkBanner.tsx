import { useEffect, useRef, useState } from 'react';
import { View, Text } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import NetInfo from '@react-native-community/netinfo';

// Suppresses the foreground-flash false positive: NetInfo on iOS fires a stale
// "offline" event right after the app returns from background, then corrects
// itself within ~1s once the radio re-attaches.
const OFFLINE_DEBOUNCE_MS = 1500;

export default function NetworkBanner() {
  const [isOffline, setIsOffline] = useState(false);
  const insets = useSafeAreaInsets();
  const offlineTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    const clearTimer = () => {
      if (offlineTimerRef.current) {
        clearTimeout(offlineTimerRef.current);
        offlineTimerRef.current = null;
      }
    };

    const unsubscribe = NetInfo.addEventListener((state) => {
      const offline = !(state.isConnected && state.isInternetReachable !== false);
      if (offline) {
        if (offlineTimerRef.current) return;
        offlineTimerRef.current = setTimeout(() => {
          offlineTimerRef.current = null;
          setIsOffline(true);
        }, OFFLINE_DEBOUNCE_MS);
      } else {
        clearTimer();
        setIsOffline(false);
      }
    });

    return () => {
      clearTimer();
      unsubscribe();
    };
  }, []);

  if (!isOffline) return null;

  // paddingTop pushes the bar below the notch/Dynamic Island instead of bleeding into it.
  return (
    <View
      className="bg-destructive px-4 pb-2"
      style={{ paddingTop: insets.top + 4 }}
    >
      <Text className="text-xs font-medium text-destructive-foreground text-center">
        No internet connection
      </Text>
    </View>
  );
}
