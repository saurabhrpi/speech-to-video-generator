import { useState } from 'react';
import { View, Text, TextInput, Pressable, ScrollView } from 'react-native';

interface TagInputProps {
  label: string;
  optional?: boolean;
  tags: string[];
  onAddTag: (tag: string) => void;
  onRemoveTag: (tag: string) => void;
  suggestions: string[];
  placeholder?: string;
}

export default function TagInput({
  label,
  optional,
  tags,
  onAddTag,
  onRemoveTag,
  suggestions,
  placeholder = 'Type and press return...',
}: TagInputProps) {
  const [input, setInput] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(false);

  const filtered = suggestions.filter(
    (s) => !tags.includes(s) && s.includes(input.toLowerCase()),
  );

  function addTag(t: string) {
    const trimmed = t.trim().toLowerCase();
    if (trimmed && !tags.includes(trimmed)) {
      onAddTag(trimmed);
    }
    setInput('');
    setShowSuggestions(false);
  }

  return (
    <View className="gap-1.5">
      <Text className="text-sm font-medium text-foreground">
        {label}
        {optional && (
          <Text className="text-muted-foreground font-normal"> (optional)</Text>
        )}
      </Text>

      {tags.length > 0 && (
        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
          <View className="flex-row flex-wrap gap-1.5 mb-1">
            {tags.map((tag) => (
              <View
                key={tag}
                className="flex-row items-center gap-1 rounded-full bg-primary/10 px-2.5 py-1"
              >
                <Text className="text-xs font-medium text-primary">{tag}</Text>
                <Pressable onPress={() => onRemoveTag(tag)}>
                  <Text className="text-xs text-primary">{'\u00d7'}</Text>
                </Pressable>
              </View>
            ))}
          </View>
        </ScrollView>
      )}

      <TextInput
        value={input}
        onChangeText={(t) => {
          setInput(t);
          setShowSuggestions(true);
        }}
        onFocus={() => setShowSuggestions(true)}
        onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
        onSubmitEditing={() => addTag(input)}
        placeholder={placeholder}
        placeholderTextColor="#9ca3af"
        returnKeyType="done"
        className="rounded-md border border-input bg-background px-3 py-2.5 text-sm text-foreground"
      />

      {showSuggestions && input.length > 0 && filtered.length > 0 && (
        <View className="rounded-md border border-input bg-background max-h-40">
          <ScrollView keyboardShouldPersistTaps="handled" nestedScrollEnabled>
            {filtered.map((item) => (
              <Pressable
                key={item}
                onPress={() => addTag(item)}
                className="px-3 py-2 active:bg-accent"
              >
                <Text className="text-sm text-foreground">{item}</Text>
              </Pressable>
            ))}
          </ScrollView>
        </View>
      )}
    </View>
  );
}
