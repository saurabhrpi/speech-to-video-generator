import { Modal, View, Text, Pressable } from 'react-native';
import { Button } from './Button';

interface ConfirmModalProps {
  visible: boolean;
  title: string;
  message?: string;
  confirmText?: string;
  cancelText?: string;
  onConfirm: () => void;
  onCancel: () => void;
  children?: React.ReactNode;
}

export default function ConfirmModal({
  visible,
  title,
  message,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  onConfirm,
  onCancel,
  children,
}: ConfirmModalProps) {
  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      onRequestClose={onCancel}
    >
      <Pressable
        className="flex-1 bg-black/50 items-center justify-center p-6"
        onPress={onCancel}
      >
        <Pressable className="w-full max-w-sm rounded-card bg-elevated p-5 gap-3">
          <Text className="text-subheading font-heading text-foreground">{title}</Text>
          {message && (
            <Text className="text-sm text-muted-foreground">{message}</Text>
          )}
          {children}
          <View className="flex-row gap-2 pt-2">
            <Button
              variant="outline"
              className="flex-1"
              onPress={onCancel}
              title={cancelText}
            />
            <Button
              className="flex-1"
              onPress={onConfirm}
              title={confirmText}
            />
          </View>
        </Pressable>
      </Pressable>
    </Modal>
  );
}
