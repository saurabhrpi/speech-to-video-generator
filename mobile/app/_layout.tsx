import FontAwesome from '@expo/vector-icons/FontAwesome';
import { DefaultTheme, ThemeProvider, type Theme } from '@react-navigation/native';
import { useFonts } from 'expo-font';
import {
  PlayfairDisplay_400Regular,
} from '@expo-google-fonts/playfair-display';
import { Stack } from 'expo-router';
import * as SplashScreen from 'expo-splash-screen';
import { StatusBar } from 'expo-status-bar';
import { useEffect } from 'react';
import { AppState } from 'react-native';
import NetInfo from '@react-native-community/netinfo';

import { GestureHandlerRootView } from 'react-native-gesture-handler';
import 'react-native-reanimated';

import { Colors } from '@/lib/design-tokens';
import { configurePurchases } from '@/lib/purchases';
import { useGalleryStore } from '@/store/gallery-store';
import { useAuthStore } from '@/store/auth-store';
import NetworkBanner from '@/components/NetworkBanner';
import '../global.css';

const WarmDarkTheme: Theme = {
  dark: true,
  fonts: DefaultTheme.fonts,
  colors: {
    primary: Colors.textPrimary,
    background: Colors.background,
    card: Colors.background,
    text: Colors.textPrimary,
    border: Colors.border,
    notification: Colors.textPrimary,
  },
};

export { ErrorBoundary } from 'expo-router';

export const unstable_settings = {
  initialRouteName: '(tabs)',
};

SplashScreen.preventAutoHideAsync();

export default function RootLayout() {
  const [loaded, error] = useFonts({
    SpaceMono: require('../assets/fonts/SpaceMono-Regular.ttf'),
    PlayfairDisplay_400Regular,
    ...FontAwesome.font,
  });

  // CTFontManagerError 104 = font already registered (still usable). Treat as success.
  const isAlreadyRegistered = error?.message?.includes('code: 104');

  useEffect(() => {
    if (error && !isAlreadyRegistered) throw error;
  }, [error, isAlreadyRegistered]);

  useEffect(() => {
    if (loaded || isAlreadyRegistered) {
      SplashScreen.hideAsync();
      useGalleryStore.getState().hydrate();
    }
  }, [loaded, isAlreadyRegistered]);

  useEffect(() => {
    configurePurchases();
    const unsub = useAuthStore.getState().initialize();
    return () => unsub();
  }, []);

  useEffect(() => {
    const sub = AppState.addEventListener('change', (state) => {
      if (state === 'active') {
        useGalleryStore.getState().resumePausedJobs();
      }
    });
    return () => sub.remove();
  }, []);

  useEffect(() => {
    let wasOffline = false;
    const unsub = NetInfo.addEventListener((state) => {
      const online = !!state.isConnected && state.isInternetReachable !== false;
      if (online && wasOffline) {
        useGalleryStore.getState().resumePausedJobs();
      }
      wasOffline = !online;
    });
    return unsub;
  }, []);

  if (!loaded && !isAlreadyRegistered) {
    return null;
  }

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <ThemeProvider value={WarmDarkTheme}>
        <StatusBar style="light" />
        <NetworkBanner />
        <Stack>
          <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
          <Stack.Screen name="settings" options={{ presentation: 'modal', title: 'Settings' }} />
        </Stack>
      </ThemeProvider>
    </GestureHandlerRootView>
  );
}
