import { Modal, View, Text, Pressable, Linking } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Colors } from '@/lib/design-tokens';
import { PRIVACY_URL } from '@/lib/constants';

interface Props {
  visible: boolean;
  onAccept: () => void;
  onDecline: () => void;
}

/**
 * One-time disclosure shown before the first generation. Lists the third-party
 * AI providers your data is sent to and asks for explicit consent. Required
 * by App Store 5.1.1(i) / 5.1.2(i). Once accepted, never shown again on this
 * install (consent stored in AsyncStorage via lib/consent.ts).
 */
export default function DataSharingConsentModal({ visible, onAccept, onDecline }: Props) {
  return (
    <Modal visible={visible} transparent animationType="fade" onRequestClose={onDecline}>
      <View
        style={{
          flex: 1,
          backgroundColor: 'rgba(0,0,0,0.7)',
          justifyContent: 'center',
          paddingHorizontal: 24,
        }}
      >
        <View
          style={{
            backgroundColor: Colors.card,
            borderRadius: 20,
            borderWidth: 1,
            borderColor: Colors.glassyBorder,
            padding: 22,
            gap: 14,
          }}
        >
          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 10 }}>
            <Ionicons name="shield-checkmark-outline" size={22} color={Colors.textPrimary} />
            <Text style={{ color: Colors.textPrimary, fontSize: 18, fontWeight: '600' }}>
              Before we generate
            </Text>
          </View>

          <Text style={{ color: Colors.textPrimary, fontSize: 14, lineHeight: 20, opacity: 0.92 }}>
            To create your video, we send the data below to two AI services. Each request goes out only when you tap Generate.
          </Text>

          <View style={{ gap: 10, paddingVertical: 4 }}>
            <Bullet
              title="OpenAI (Whisper)"
              body="Audio you record, used to transcribe your prompt to text. Audio is not retained after transcription."
            />
            <Bullet
              title="MiniMax (Hailuo)"
              body="Your text prompt, used to generate the video clip. The generated video is hosted on their CDN."
            />
          </View>

          <Text style={{ color: Colors.textSecondary, fontSize: 12, lineHeight: 17 }}>
            These providers handle data under their own privacy policies, which provide equal or better protection.
            See our{' '}
            <Text
              style={{ color: Colors.textPrimary, textDecorationLine: 'underline' }}
              onPress={() => Linking.openURL(PRIVACY_URL)}
            >
              Privacy Policy
            </Text>{' '}
            for full details.
          </Text>

          <View style={{ flexDirection: 'row', gap: 10, marginTop: 6 }}>
            <Pressable
              onPress={onDecline}
              style={{
                flex: 1,
                paddingVertical: 12,
                borderRadius: 12,
                borderWidth: 1,
                borderColor: Colors.glassyBorder,
                backgroundColor: 'transparent',
                alignItems: 'center',
              }}
            >
              <Text style={{ color: Colors.textPrimary, fontSize: 15 }}>Decline</Text>
            </Pressable>
            <Pressable
              onPress={onAccept}
              style={{
                flex: 1,
                paddingVertical: 12,
                borderRadius: 12,
                backgroundColor: '#2563EB',
                alignItems: 'center',
              }}
            >
              <Text style={{ color: '#FFFFFF', fontSize: 15, fontWeight: '600' }}>I understand</Text>
            </Pressable>
          </View>
        </View>
      </View>
    </Modal>
  );
}

function Bullet({ title, body }: { title: string; body: string }) {
  return (
    <View style={{ flexDirection: 'row', gap: 10 }}>
      <View
        style={{
          width: 6,
          height: 6,
          borderRadius: 3,
          backgroundColor: Colors.textPrimary,
          marginTop: 7,
        }}
      />
      <View style={{ flex: 1 }}>
        <Text style={{ color: Colors.textPrimary, fontSize: 13, fontWeight: '600', marginBottom: 2 }}>
          {title}
        </Text>
        <Text style={{ color: Colors.textPrimary, fontSize: 13, lineHeight: 18, opacity: 0.85 }}>
          {body}
        </Text>
      </View>
    </View>
  );
}
