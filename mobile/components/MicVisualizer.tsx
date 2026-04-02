import { useEffect } from 'react';
import { View } from 'react-native';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withTiming,
} from 'react-native-reanimated';

interface MicVisualizerProps {
  metering: number; // dB value from expo-av, typically -160 to 0
  isActive: boolean;
}

export default function MicVisualizer({ metering, isActive }: MicVisualizerProps) {
  const barHeight = useSharedValue(4);

  useEffect(() => {
    if (!isActive) {
      barHeight.value = withTiming(4, { duration: 200 });
      return;
    }
    // Normalize metering from dB range (-160..0) to pixel height (4..60)
    const normalized = Math.max(0, (metering + 160) / 160);
    barHeight.value = withTiming(4 + normalized * 56, { duration: 100 });
  }, [metering, isActive]);

  const animatedStyle = useAnimatedStyle(() => ({
    height: barHeight.value,
  }));

  // Render multiple bars for visual effect
  const bars = Array.from({ length: 20 }, (_, i) => i);

  return (
    <View className="flex-row items-end justify-center gap-1 h-16 rounded-md bg-muted p-2">
      {bars.map((i) => {
        const offset = Math.sin(i * 0.5) * 0.3;
        return (
          <AnimatedBar key={i} metering={metering} isActive={isActive} offset={offset} />
        );
      })}
    </View>
  );
}

function AnimatedBar({
  metering,
  isActive,
  offset,
}: {
  metering: number;
  isActive: boolean;
  offset: number;
}) {
  const height = useSharedValue(4);

  useEffect(() => {
    if (!isActive) {
      height.value = withTiming(4, { duration: 200 });
      return;
    }
    const normalized = Math.max(0, (metering + 160) / 160);
    const barH = 4 + (normalized + offset) * 40;
    height.value = withTiming(Math.max(4, Math.min(barH, 56)), { duration: 100 });
  }, [metering, isActive, offset]);

  const style = useAnimatedStyle(() => ({
    height: height.value,
  }));

  return (
    <Animated.View
      className="w-2 rounded-full bg-primary"
      style={style}
    />
  );
}
