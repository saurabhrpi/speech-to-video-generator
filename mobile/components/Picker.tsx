import { useState } from 'react';
import { View, Text, Pressable, Modal, FlatList } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

interface PickerOption {
  value: string;
  label: string;
}

interface PickerProps {
  label: string;
  required?: boolean;
  value: string;
  onValueChange: (value: string) => void;
  options: PickerOption[];
  placeholder?: string;
}

export default function Picker({
  label,
  required,
  value,
  onValueChange,
  options,
  placeholder = 'Select...',
}: PickerProps) {
  const [open, setOpen] = useState(false);
  const selectedLabel = options.find((o) => o.value === value)?.label;

  return (
    <View className="gap-1.5">
      <Text className="text-sm font-medium text-foreground">
        {label}{required ? ' *' : ''}
      </Text>
      <Pressable
        onPress={() => setOpen(true)}
        className="flex-row items-center justify-between rounded-md border border-input bg-background px-3 py-3"
      >
        <Text
          className={selectedLabel ? 'text-sm text-foreground' : 'text-sm text-muted-foreground'}
          numberOfLines={1}
        >
          {selectedLabel || placeholder}
        </Text>
        <Text className="text-xs text-muted-foreground">{'\u25BC'}</Text>
      </Pressable>

      <Modal visible={open} animationType="slide" presentationStyle="pageSheet">
        <SafeAreaView style={{ flex: 1, backgroundColor: '#fff' }}>
          <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 16, paddingVertical: 12, borderBottomWidth: 1, borderBottomColor: '#e5e7eb' }}>
            <Pressable onPress={() => setOpen(false)} hitSlop={8}>
              <Text style={{ fontSize: 16, color: '#3b82f6', fontWeight: '500' }}>Cancel</Text>
            </Pressable>
            <Text style={{ fontSize: 16, fontWeight: '600', color: '#111' }}>{label}</Text>
            <View style={{ width: 60 }} />
          </View>

          <FlatList
            data={options}
            keyExtractor={(item) => item.value}
            renderItem={({ item }) => (
              <Pressable
                onPress={() => {
                  onValueChange(item.value);
                  setOpen(false);
                }}
                style={{
                  paddingHorizontal: 16,
                  paddingVertical: 14,
                  borderBottomWidth: 0.5,
                  borderBottomColor: '#e5e7eb',
                  flexDirection: 'row',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                }}
              >
                <Text style={{ fontSize: 16, color: '#111' }}>{item.label}</Text>
                {item.value === value && (
                  <Text style={{ fontSize: 16, color: '#3b82f6' }}>{'\u2713'}</Text>
                )}
              </Pressable>
            )}
          />
        </SafeAreaView>
      </Modal>
    </View>
  );
}
