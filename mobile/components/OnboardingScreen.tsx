import { useEffect, useState } from 'react';
import { View, Text, Pressable, Linking, StyleSheet, Image } from 'react-native';
import { Video, ResizeMode } from 'expo-av';
import { SafeAreaView, useSafeAreaInsets } from 'react-native-safe-area-context';
import { PRIVACY_URL, TERMS_URL } from '@/lib/constants';
import { useTemplateStore } from '@/store/template-store';

interface Props {
  onContinue: () => void;
}

// S86: onboarding redesign (ref: Onboarding.png). Each slide shows a dance
// VIDEO (the "after") full-screen, plus a small circular "Before" headshot —
// an NBP-regenerated solo portrait built from the video's first frame
// (scripts/gen_onboarding_before.py) — with a curved arrow between them to
// read as "your photo → your dance". Three fixed slides cycle on a loop.
// Assets are bundled (work in the dev client with no native deps) and the
// videos stream from R2.
type Slide = { title: string; videoUrl: string; before: number };
const R2 = 'https://assets.speech-2-video.ai/viral-dances';
const SLIDES: Slide[] = [
  { title: 'Bombale', videoUrl: `${R2}/bombale/preview_stream.mp4`, before: require('../assets/onboarding/bombale.jpg') },
  { title: 'Gangsta', videoUrl: `${R2}/gangsta/preview_stream.mp4`, before: require('../assets/onboarding/gangsta.jpg') },
  { title: 'Mapopo', videoUrl: `${R2}/mapopo/preview_stream.mp4`, before: require('../assets/onboarding/mapopo.jpg') },
];
const ARROW = require('../assets/onboarding/arrow.png');
const FADE = require('../assets/onboarding/bottom_fade.png');
const SLIDE_MS = 5000;

export default function OnboardingScreen({ onContinue }: Props) {
  const insets = useSafeAreaInsets();
  const hydrate = useTemplateStore((s) => s.hydrate);
  const fetchTemplates = useTemplateStore((s) => s.fetchTemplates);

  // Onboarding gates before home, so we own the first hydrate + fetch here so
  // the home grid is warm by the time the user taps Continue.
  useEffect(() => {
    (async () => {
      await hydrate();
      fetchTemplates();
    })();
  }, [hydrate, fetchTemplates]);

  // Cycle the showcase slides on a loop.
  const [idx, setIdx] = useState(0);
  useEffect(() => {
    const t = setInterval(() => setIdx((i) => (i + 1) % SLIDES.length), SLIDE_MS);
    return () => clearInterval(t);
  }, []);
  const slide = SLIDES[idx];

  return (
    <View style={styles.root}>
      {/* Full-screen dance video (the "after"). Keyed so it remounts (and
          restarts) on each slide change — only one <Video> is ever mounted. */}
      <Video
        key={slide.videoUrl}
        source={{ uri: slide.videoUrl }}
        style={StyleSheet.absoluteFill}
        resizeMode={ResizeMode.COVER}
        isLooping
        isMuted
        shouldPlay
      />

      {/* Smooth bottom fade for text legibility (replaces the old flat 38%
          black band). */}
      <Image source={FADE} style={styles.bottomFade} resizeMode="stretch" />

      {/* Curved "before → after" arrow, anchored under the Before circle. */}
      <Image source={ARROW} style={[styles.arrow, { top: insets.top + 70 }]} resizeMode="contain" />

      <SafeAreaView style={StyleSheet.absoluteFill} edges={['top', 'bottom']}>
        {/* Before circle + label (top-left). */}
        <View style={styles.beforeWrap}>
          <Image source={slide.before} style={styles.beforeCircle} resizeMode="cover" />
          <View style={styles.beforePill}>
            <Text style={styles.beforePillText}>Before</Text>
          </View>
        </View>

        <View style={styles.spacer} />

        {/* Template caption over the video. */}
        <Text style={styles.caption}>{slide.title}</Text>

        {/* Welcome + tagline + CTA + legal. */}
        <View style={styles.bottomInner}>
          <Text style={styles.welcome}>Welcome to AIVO</Text>
          <Text style={styles.tagline}>Turn your photo into a viral dance</Text>
          <Pressable
            onPress={onContinue}
            style={styles.continueBtn}
            accessibilityLabel="Continue"
            accessibilityRole="button"
          >
            <Text style={styles.continueLabel}>Continue</Text>
          </Pressable>
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
        </View>
      </SafeAreaView>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: '#000' },
  bottomFade: {
    position: 'absolute',
    left: 0,
    right: 0,
    bottom: 0,
    width: '100%',
    height: '55%',
  },
  arrow: {
    position: 'absolute',
    left: 60,
    width: 120,
    height: 150,
    zIndex: 2,
  },
  // Before circle + label
  beforeWrap: {
    marginTop: 8,
    marginLeft: 16,
    width: 96,
    alignItems: 'center',
    zIndex: 3,
  },
  beforeCircle: {
    width: 76,
    height: 76,
    borderRadius: 38,
    borderWidth: 2.5,
    borderColor: '#fff',
    overflow: 'hidden',
    backgroundColor: '#222',
  },
  beforePill: {
    marginTop: 6,
    paddingHorizontal: 12,
    paddingVertical: 3,
    borderRadius: 12,
    backgroundColor: 'rgba(0,0,0,0.55)',
  },
  beforePillText: { color: '#fff', fontSize: 13, fontWeight: '600' },
  spacer: { flex: 1 },
  caption: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
    textAlign: 'center',
    marginBottom: 8,
    opacity: 0.95,
    textShadowColor: 'rgba(0,0,0,0.6)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 4,
  },
  bottomInner: { paddingHorizontal: 24, paddingBottom: 16, gap: 12 },
  welcome: {
    color: '#fff',
    fontSize: 30,
    fontWeight: '800',
    textAlign: 'center',
    letterSpacing: 0.3,
    textShadowColor: 'rgba(0,0,0,0.5)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 6,
  },
  tagline: {
    color: '#fff',
    fontSize: 15,
    textAlign: 'center',
    opacity: 0.92,
    marginTop: -4,
    textShadowColor: 'rgba(0,0,0,0.5)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 4,
  },
  continueBtn: {
    marginTop: 4,
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
  legalText: {
    color: '#FFFFFF',
    fontSize: 13,
    lineHeight: 18,
    textAlign: 'center',
    opacity: 0.95,
  },
  bold: { fontWeight: '600' },
  link: { textDecorationLine: 'underline', color: '#FFFFFF' },
});
