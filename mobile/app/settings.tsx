import { View, Text, Alert } from 'react-native';
import * as AppleAuthentication from 'expo-apple-authentication';
import { Button } from '@/components/Button';
import { useAuthStore } from '@/store/auth-store';

export default function SettingsScreen() {
  const {
    isAnonymous,
    displayName,
    email,
    usage,
    loading,
    signInWithApple,
    signOut,
  } = useAuthStore();

  async function handleAppleSignIn() {
    try {
      await signInWithApple();
    } catch (e: any) {
      if (e?.code === 'ERR_REQUEST_CANCELED') return; // user dismissed
      Alert.alert('Sign-in failed', e?.message ?? 'Please try again.');
    }
  }

  return (
    <View className="flex-1 bg-background p-4 gap-6">
      <View className="rounded-lg border border-border bg-card p-4 gap-3">
        <Text className="text-sm font-semibold text-foreground">Account</Text>

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
            {usage ? (
              <Text className="text-xs text-muted-foreground">
                Generations: {usage.usage_count}
              </Text>
            ) : null}
            <Button variant="outline" onPress={signOut} title="Sign Out" />
          </>
        ) : (
          <>
            <Text className="text-sm text-muted-foreground">
              Sign in with Apple to unlock unlimited generations.
            </Text>
            {usage ? (
              <Text className="text-xs text-muted-foreground">
                Free generations used: {usage.usage_count} / {usage.limit}
              </Text>
            ) : null}
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
