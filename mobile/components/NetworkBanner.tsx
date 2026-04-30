import { useEffect, useState } from 'react';
import { View, Text } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import NetInfo from '@react-native-community/netinfo';

export default function NetworkBanner() {
  const [isOffline, setIsOffline] = useState(false);
  const insets = useSafeAreaInsets();

  useEffect(() => {
    const unsubscribe = NetInfo.addEventListener((state) => {
      setIsOffline(!(state.isConnected && state.isInternetReachable !== false));
    });
    return unsubscribe;
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
