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

const CTA_BLUE = '#2563EB';

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
        className="flex-1 bg-black/50 items-center justify-center p-4"
        onPress={onCancel}
      >
        <Pressable className="w-full max-w-lg rounded-card bg-elevated p-6 gap-4">
          <Text className="text-subheading font-body text-foreground">{title}</Text>
          {message && (
            <Text className="text-body font-body text-muted-foreground">{message}</Text>
          )}
          {children}
          <View className="flex-row gap-3 pt-2">
            <Button
              variant="outline"
              className="flex-1 h-12"
              onPress={onCancel}
              title={cancelText}
            />
            {/* Same blue capsule + white text as the home Generate button, slightly smaller. */}
            <Pressable
              onPress={onConfirm}
              accessibilityLabel={confirmText}
              style={{
                flex: 1,
                height: 48,
                borderRadius: 24,
                backgroundColor: CTA_BLUE,
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <Text style={{ color: '#FFFFFF', fontSize: 16, fontWeight: '600' }}>
                {confirmText}
              </Text>
            </Pressable>
          </View>
        </Pressable>
      </Pressable>
    </Modal>
  );
}
