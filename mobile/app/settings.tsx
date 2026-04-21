import { useState } from 'react';
import { View, Text, Alert } from 'react-native';
import * as AppleAuthentication from 'expo-apple-authentication';
import { Button } from '@/components/Button';
import { useAuthStore } from '@/store/auth-store';
import { restoreAndGrant } from '@/lib/purchases';

export default function SettingsScreen() {
  const isAnonymous = useAuthStore((s) => s.isAnonymous);
  const displayName = useAuthStore((s) => s.displayName);
  const email = useAuthStore((s) => s.email);
  const creditBalance = useAuthStore((s) => s.creditBalance);
  const signInWithApple = useAuthStore((s) => s.signInWithApple);
  const signOut = useAuthStore((s) => s.signOut);
  const openPaywall = useAuthStore((s) => s.openPaywall);
  const refreshCredits = useAuthStore((s) => s.refreshCredits);

  const [restoring, setRestoring] = useState(false);

  async function handleAppleSignIn() {
    try {
      await signInWithApple();
    } catch (e: any) {
      if (e?.code === 'ERR_REQUEST_CANCELED') return;
      Alert.alert('Sign-in failed', e?.message ?? 'Please try again.');
    }
  }

  async function handleRestore() {
    setRestoring(true);
    try {
      await restoreAndGrant();
      await refreshCredits();
    } catch (e: any) {
      Alert.alert('Restore failed', e?.message ?? 'Please try again.');
    } finally {
      setRestoring(false);
    }
  }

  const balanceLabel = creditBalance === null ? '—' : String(creditBalance);

  return (
    <View className="flex-1 bg-background p-4 gap-6">
      <View className="rounded-lg border border-border bg-card p-4 gap-3">
        <Text className="text-sm font-semibold text-foreground">Account</Text>

        <Text className="text-sm text-foreground">Credits: {balanceLabel}</Text>

        {!isAnonymous ? (
          <>
            <View className="gap-1">
              {displayName ? (
                <Text className="text-sm text-foreground">{displayName}</Text>
              ) : null}
              {email ? (
                <Text className="text-xs text-muted-foreground">{email}</Text>
              ) : null}
            </View>
            <Button variant="outline" onPress={signOut} title="Sign Out" />
          </>
        ) : (
          <>
            <Text className="text-sm text-muted-foreground">
              Sign in with Apple to keep your credits safe across devices.
            </Text>
            <AppleAuthentication.AppleAuthenticationButton
              buttonType={AppleAuthentication.AppleAuthenticationButtonType.SIGN_IN}
              buttonStyle={AppleAuthentication.AppleAuthenticationButtonStyle.WHITE}
              cornerRadius={8}
              style={{ width: '100%', height: 48 }}
              onPress={handleAppleSignIn}
            />
          </>
        )}
      </View>

      <View className="rounded-lg border border-border bg-card p-4 gap-3">
        <Text className="text-sm font-semibold text-foreground">Purchases</Text>
        <Button onPress={openPaywall} title="Buy Credits" />
        <Button
          variant="outline"
          onPress={handleRestore}
          disabled={restoring}
          title={restoring ? 'Restoring…' : 'Restore Purchases'}
        />
      </View>

      <View className="rounded-lg border border-border bg-card p-4 gap-2">
        <Text className="text-sm font-semibold text-foreground">About</Text>
        <Text className="text-xs text-muted-foreground">Speech to Video v1.0.0</Text>
        <Text className="text-xs text-muted-foreground">
          Generate AI videos from text or voice prompts.
        </Text>
      </View>
    </View>
  );
}
