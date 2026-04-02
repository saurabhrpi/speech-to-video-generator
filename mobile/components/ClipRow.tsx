import { View, Text, Pressable } from 'react-native';
import { Image } from 'expo-image';

interface ClipRowProps {
  url: string;
  note?: string;
  ts: number;
  onPress: () => void;
  onDelete: () => void;
  drag?: () => void;
  isActive?: boolean;
}

export default function ClipRow({
  url,
  note,
  ts,
  onPress,
  onDelete,
  drag,
  isActive,
}: ClipRowProps) {
  return (
    <Pressable
      onPress={onPress}
      onLongPress={drag}
      className={`flex-row items-center gap-3 rounded-lg px-3 py-2 ${
        isActive ? 'bg-primary/10' : 'active:bg-accent'
      }`}
    >
      {/* Thumbnail */}
      <View className="w-20 h-12 rounded bg-muted overflow-hidden">
        <Image
          source={{ uri: url }}
          style={{ width: 80, height: 48 }}
          contentFit="cover"
        />
      </View>

      {/* Info */}
      <View className="flex-1">
        <Text className="text-sm text-foreground" numberOfLines={1}>
          {note || `Clip ${ts}`}
        </Text>
        <Text className="text-xs text-muted-foreground">
          {new Date(ts).toLocaleDateString()}
        </Text>
      </View>

      {/* Delete */}
      <Pressable onPress={onDelete} className="p-2">
        <Text className="text-xs text-destructive">Delete</Text>
      </Pressable>
    </Pressable>
  );
}
