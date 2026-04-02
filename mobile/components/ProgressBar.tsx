import { View, Text } from 'react-native';
import Animated, { useAnimatedStyle, withTiming } from 'react-native-reanimated';

interface ProgressBarProps {
  progress: number;
  message: string;
  indeterminate?: boolean;
}

export default function ProgressBar({ progress, message, indeterminate }: ProgressBarProps) {
  const widthStyle = useAnimatedStyle(() => ({
    width: withTiming(`${Math.min(progress, 100)}%`, { duration: 160 }),
  }));

  return (
    <View className="gap-1.5">
      <View className="h-2 rounded-full bg-secondary overflow-hidden">
        {indeterminate ? (
          <View className="h-full w-1/3 rounded-full bg-primary" />
        ) : (
          <Animated.View
            className="h-full rounded-full bg-primary"
            style={widthStyle}
          />
        )}
      </View>
      {message ? (
        <Text className="text-xs text-muted-foreground" numberOfLines={1}>
          {message}
        </Text>
      ) : null}
    </View>
  );
}
