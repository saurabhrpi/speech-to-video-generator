import { View, Text } from 'react-native';
import { Button } from '@/components/Button';
import { useAuthStore } from '@/store/auth-store';

export default function SettingsScreen() {
  const { auth, login, logout, loading } = useAuthStore();

  return (
    <View className="flex-1 bg-background p-4 gap-6">
      <View className="rounded-lg border border-border bg-card p-4 gap-3">
        <Text className="text-sm font-semibold text-foreground">Account</Text>

        {auth?.authenticated ? (
          <>
            <View className="gap-1">
              <Text className="text-sm text-foreground">{auth.user?.name}</Text>
              <Text className="text-xs text-muted-foreground">{auth.user?.email}</Text>
            </View>
            <Text className="text-xs text-muted-foreground">
              Generations: {auth.usage_count}
            </Text>
            <Button variant="outline" onPress={logout} title="Sign Out" />
          </>
        ) : (
          <>
            <Text className="text-sm text-muted-foreground">
              Sign in with Google to unlock unlimited generations.
            </Text>
            {auth && (
              <Text className="text-xs text-muted-foreground">
                Free generations used: {auth.usage_count} / {auth.limit}
              </Text>
            )}
            <Button onPress={login} disabled={loading} title="Sign in with Google" />
          </>
        )}
      </View>

      <View className="rounded-lg border border-border bg-card p-4 gap-2">
        <Text className="text-sm font-semibold text-foreground">About</Text>
        <Text className="text-xs text-muted-foreground">Interior Timelapse v1.0.0</Text>
        <Text className="text-xs text-muted-foreground">
          Generate hyper-realistic renovation timelapse videos with AI.
        </Text>
      </View>
    </View>
  );
}
