import FontAwesome from '@expo/vector-icons/FontAwesome';
import { Link, Tabs } from 'expo-router';
import { Pressable, useColorScheme } from 'react-native';

export const unstable_settings = {
  initialRouteName: 'index',
};

function TabBarIcon(props: { name: React.ComponentProps<typeof FontAwesome>['name']; color: string }) {
  return <FontAwesome size={24} style={{ marginBottom: -3 }} {...props} />;
}

export default function TabLayout() {
  const colorScheme = useColorScheme();
  const tint = colorScheme === 'dark' ? '#6ea8fe' : '#3b82f6';

  return (
    <Tabs
      screenOptions={{
        tabBarActiveTintColor: tint,
        headerShown: true,
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: 'Speech',
          tabBarIcon: ({ color }) => <TabBarIcon name="microphone" color={color} />,
          headerRight: () => (
            <Link href="/settings" asChild>
              <Pressable>
                {({ pressed }) => (
                  <FontAwesome
                    name="gear"
                    size={22}
                    color={tint}
                    style={{ marginRight: 15, opacity: pressed ? 0.5 : 1 }}
                  />
                )}
              </Pressable>
            </Link>
          ),
        }}
      />
      <Tabs.Screen
        name="timelapse"
        options={{
          title: 'Timelapse',
          tabBarIcon: ({ color }) => <TabBarIcon name="home" color={color} />,
          headerRight: () => (
            <Link href="/settings" asChild>
              <Pressable>
                {({ pressed }) => (
                  <FontAwesome
                    name="gear"
                    size={22}
                    color={tint}
                    style={{ marginRight: 15, opacity: pressed ? 0.5 : 1 }}
                  />
                )}
              </Pressable>
            </Link>
          ),
        }}
      />
      <Tabs.Screen
        name="video-studio"
        options={{
          title: 'Video Studio',
          tabBarIcon: ({ color }) => <TabBarIcon name="film" color={color} />,
        }}
      />
    </Tabs>
  );
}
