import FontAwesome from '@expo/vector-icons/FontAwesome';
import { DefaultTheme, ThemeProvider, type Theme } from '@react-navigation/native';
import { useFonts } from 'expo-font';
import {
  PlayfairDisplay_400Regular,
} from '@expo-google-fonts/playfair-display';
import { Stack } from 'expo-router';
import * as SplashScreen from 'expo-splash-screen';
import { StatusBar } from 'expo-status-bar';
import { useEffect, useState } from 'react';
import { AppState } from 'react-native';
import NetInfo from '@react-native-community/netinfo';

import { GestureHandlerRootView } from 'react-native-gesture-handler';
import 'react-native-reanimated';

import { Colors } from '@/lib/design-tokens';
import { configurePurchases, refreshPurchasesState } from '@/lib/purchases';
import { useGalleryStore } from '@/store/gallery-store';
import { useAuthStore } from '@/store/auth-store';
import { hasDataSharingConsent, setDataSharingConsent } from '@/lib/consent';
import NetworkBanner from '@/components/NetworkBanner';
import OnboardingScreen from '@/components/OnboardingScreen';
import Paywall from '@/components/Paywall';
import FloatingStatusPill from '@/components/FloatingStatusPill';
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
  initialRouteName: 'index',
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

  // null = unknown (AsyncStorage read in flight); false = first launch, must
  // accept; true = already accepted on a prior launch. Splash hide waits on
  // this resolving so we don't flash the home before the gate renders.
  const [consented, setConsented] = useState<boolean | null>(null);

  useEffect(() => {
    if (error && !isAlreadyRegistered) throw error;
  }, [error, isAlreadyRegistered]);

  useEffect(() => {
    hasDataSharingConsent().then(setConsented);
  }, []);

  useEffect(() => {
    if ((loaded || isAlreadyRegistered) && consented !== null) {
      SplashScreen.hideAsync();
      useGalleryStore.getState().hydrate();
    }
  }, [loaded, isAlreadyRegistered, consented]);

  useEffect(() => {
    configurePurchases();
    const unsub = useAuthStore.getState().initialize();
    return () => unsub();
  }, []);

  useEffect(() => {
    const sub = AppState.addEventListener('change', (state) => {
      if (state === 'active') {
        useGalleryStore.getState().resumePausedJobs();
        // AIV-51: re-poke RC so the CustomerInfo listener catches up any
        // transactions ingested while we were backgrounded.
        refreshPurchasesState();
        // AIV-97: pull a fresh credit balance — covers out-of-band grants
        // (support/promo) that landed while the app was backgrounded.
        useAuthStore.getState().refreshCredits();
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
  if (consented === null) {
    return null;
  }

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <ThemeProvider value={WarmDarkTheme}>
        <StatusBar style="light" />
        {consented ? (
          <>
            <NetworkBanner />
            <Stack>
              <Stack.Screen name="index" options={{ headerShown: false }} />
              <Stack.Screen
                name="gallery"
                options={{ title: 'Gallery', headerBackButtonDisplayMode: 'minimal' }}
              />
              <Stack.Screen name="settings" options={{ presentation: 'modal', title: 'Settings' }} />
              <Stack.Screen name="clip/[id]" options={{ title: 'AIVO', headerBackButtonDisplayMode: 'minimal' }} />
              <Stack.Screen
                name="create-video"
                options={{ title: 'Create Video', headerBackButtonDisplayMode: 'minimal' }}
              />
            </Stack>
            <FloatingStatusPill />
            <Paywall />
          </>
        ) : (
          <OnboardingScreen
            onContinue={async () => {
              await setDataSharingConsent();
              setConsented(true);
            }}
          />
        )}
      </ThemeProvider>
    </GestureHandlerRootView>
  );
}
