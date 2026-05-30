import { useEffect, useMemo } from 'react';
import { View, Text, Pressable, Linking, StyleSheet, Image } from 'react-native';
import { Video, ResizeMode } from 'expo-av';
import { SafeAreaView } from 'react-native-safe-area-context';
import { PRIVACY_URL, TERMS_URL } from '@/lib/constants';
import { useTemplateStore } from '@/store/template-store';

interface Props {
  onContinue: () => void;
}

export default function OnboardingScreen({ onContinue }: Props) {
  const templates = useTemplateStore((s) => s.templates);
  const hydrate = useTemplateStore((s) => s.hydrate);
  const fetchTemplates = useTemplateStore((s) => s.fetchTemplates);

  // Onboarding gates before the home screen, so we own the first hydrate +
  // fetch here. Mirrors index.tsx — hydrate from AsyncStorage cache first so
  // a returning user sees the hero video instantly, then re-fetch in the
  // background to refresh.
  useEffect(() => {
    (async () => {
      await hydrate();
      fetchTemplates();
    })();
  }, [hydrate, fetchTemplates]);

  const heroVideoUrl = useMemo(() => {
    const heroes = templates
      .filter((t) => t.is_hero && t.published_status === 'published')
      .sort((a, b) => (a.hero_order ?? Infinity) - (b.hero_order ?? Infinity));
    const t = heroes[0] || templates[0];
    return t?.assets?.preview_video_url || t?.assets?.driving_video_url || null;
  }, [templates]);

  return (
    <View style={styles.root}>
      {heroVideoUrl ? (
        <Video
          source={{ uri: heroVideoUrl }}
          style={StyleSheet.absoluteFill}
          resizeMode={ResizeMode.COVER}
          isLooping
          isMuted
          shouldPlay
        />
      ) : (
        <View style={[StyleSheet.absoluteFill, styles.fallback]}>
          <Image source={require('../assets/images/icon.png')} style={styles.fallbackIcon} />
        </View>
      )}

      <View style={styles.bottomOverlay} pointerEvents="none" />

      <SafeAreaView style={styles.bottomArea} edges={['bottom']}>
        <View style={styles.bottomInner}>
          <Text style={styles.legalText}>
            By tapping <Text style={styles.bold}>Continue</Text>, you agree to our{' '}
            <Text style={styles.link} onPress={() => Linking.openURL(TERMS_URL)}>
              Terms of Use
            </Text>
            {' '}and{' '}
            <Text style={styles.link} onPress={() => Linking.openURL(PRIVACY_URL)}>
              Privacy Policy
            </Text>
            .
          </Text>
          <Pressable
            onPress={onContinue}
            style={styles.continueBtn}
            accessibilityLabel="Continue"
            accessibilityRole="button"
          >
            <Text style={styles.continueLabel}>Continue</Text>
          </Pressable>
        </View>
      </SafeAreaView>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: '#000' },
  fallback: { alignItems: 'center', justifyContent: 'center', backgroundColor: '#000' },
  fallbackIcon: { width: 120, height: 120, resizeMode: 'contain' },
  bottomOverlay: {
    position: 'absolute',
    left: 0,
    right: 0,
    bottom: 0,
    height: '38%',
    backgroundColor: 'rgba(0,0,0,0.55)',
  },
  bottomArea: { position: 'absolute', left: 0, right: 0, bottom: 0 },
  bottomInner: { paddingHorizontal: 24, paddingBottom: 16, gap: 16 },
  legalText: {
    color: '#FFFFFF',
    fontSize: 13,
    lineHeight: 18,
    textAlign: 'center',
    opacity: 0.95,
  },
  bold: { fontWeight: '600' },
  link: { textDecorationLine: 'underline', color: '#FFFFFF' },
  continueBtn: {
    backgroundColor: '#007AFF',
    borderRadius: 28,
    paddingVertical: 16,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOpacity: 0.3,
    shadowRadius: 8,
    shadowOffset: { width: 0, height: 4 },
    elevation: 4,
  },
  continueLabel: { color: '#FFFFFF', fontSize: 16, fontWeight: '700' },
});
