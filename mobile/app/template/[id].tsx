import { useEffect, useMemo, useState } from 'react';
import {
  View,
  Text,
  Image,
  Pressable,
  ScrollView,
  ActivityIndicator,
  StyleSheet,
  Alert,
  Dimensions,
  Linking,
} from 'react-native';

const PREVIEW_HEIGHT = Dimensions.get('window').height * 0.42;
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useLocalSearchParams, useRouter, Stack } from 'expo-router';
import { Video, ResizeMode } from 'expo-av';
import * as ImagePicker from 'expo-image-picker';
import { useTemplateStore, type Template } from '@/store/template-store';
import { useAuthStore } from '@/store/auth-store';
import { useGalleryStore } from '@/store/gallery-store';
import { apiPost } from '@/lib/api-client';
import { Colors } from '@/lib/design-tokens';

// AIV-31 Pipeline Review screen — reached by tapping a template tile on
// the V2 home (mobile/app/index.tsx). Preview + selfie pick + Generate. Uploads to
// /api/upload/selfie (AIV-89), dispatches via /api/generate/template-video
// (AIV-15). Polling reuses gallery-store (AIV-30 shipped startTemplateGeneration).
//
// V1 scope (this PR):
// - photo-library pick only (camera capture deferred)
// - no prompt customization (Pipeline B uses template.prompt_template)
// - in-flight job lands in V1 gallery; gallery V2 card variant separate.

const CTA_BLUE = '#2563EB';

function isUsableMediaUrl(url: string | null | undefined): url is string {
  return !!url && /^https?:\/\//.test(url) && !url.includes('placeholder.example');
}

export default function TemplateReviewScreen() {
  const router = useRouter();
  const { id } = useLocalSearchParams<{ id: string }>();
  const templates = useTemplateStore((s) => s.templates);
  const fetchTemplates = useTemplateStore((s) => s.fetchTemplates);

  const template: Template | undefined = useMemo(
    () => templates.find((t) => t.id === id),
    [templates, id],
  );

  // Deep-link fallback: if we landed here without going through the home tab
  // (e.g. cold start to a shared link), trigger a fetch so the template
  // becomes available. Cheap — uses the same ETag-cached endpoint.
  useEffect(() => {
    if (!template) fetchTemplates();
  }, [template, fetchTemplates]);

  const canAfford = useAuthStore((s) => s.canAfford);
  const openPaywall = useAuthStore((s) => s.openPaywall);
  const creditBalance = useAuthStore((s) => s.creditBalance);
  const startTemplateGeneration = useGalleryStore((s) => s.startTemplateGeneration);
  const inFlightCost = useGalleryStore((s) =>
    s.jobs
      .filter((j) => j.status === 'generating' || j.status === 'paused')
      .reduce((sum, j) => sum + (j.costAtSubmit ?? 0), 0),
  );

  const [selfieUri, setSelfieUri] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  if (!template) {
    return (
      <SafeAreaView style={styles.safe} edges={['top']}>
        <Stack.Screen options={{ headerShown: false }} />
        <HeaderRow onBack={() => (router.canGoBack() ? router.back() : router.replace('/' as any))} />
        <View style={styles.center}>
          <ActivityIndicator color={Colors.textPrimary} />
          <Text style={styles.dim}>Loading template…</Text>
        </View>
      </SafeAreaView>
    );
  }

  const cost = template.credit_cost;
  const blockedByInFlight = inFlightCost > 0;
  const canSubmit = !!selfieUri && !submitting && !blockedByInFlight;

  async function handlePickSelfie() {
    // iOS shows the native permission sheet (Allow Full / Limited / Don't
    // Allow) only on the FIRST call when status='undetermined' — once denied,
    // the sheet never fires again and the only path is Settings. AIV-96:
    // dad's iPhone fell through to the in-app Alert with no escape; surface
    // Open Settings directly so the user isn't dead-ended.
    const perm = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!perm.granted) {
      Alert.alert(
        'Photo access needed',
        'AIVO needs access to your Photos to pick a selfie. Tap Open Settings, then enable Photos for AIVO.',
        [
          { text: 'Cancel', style: 'cancel' },
          { text: 'Open Settings', onPress: () => Linking.openSettings() },
        ],
      );
      return;
    }
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ['images'],
      allowsEditing: true,
      aspect: [1, 1],
      quality: 0.85,
    });
    if (result.canceled) return;
    const asset = result.assets?.[0];
    if (asset?.uri) setSelfieUri(asset.uri);
  }

  async function handleGenerate() {
    if (!selfieUri || !template) return;

    // Credit gate. Template-video uses template.credit_cost — passed via
    // a synthetic "model key" so canAfford's table-lookup doesn't 404.
    // Since canAfford goes through costTable lookups for V1 keys, we bypass
    // for V2 by comparing balance directly to template.credit_cost.
    const projected = (creditBalance ?? 0) - inFlightCost;
    if (projected < cost) {
      openPaywall();
      return;
    }

    setSubmitting(true);
    try {
      // 1) Upload selfie.
      const fd = new FormData();
      const filename = selfieUri.split('/').pop() ?? 'selfie.jpg';
      const ext = (filename.split('.').pop() ?? 'jpg').toLowerCase();
      const mime = ext === 'png' ? 'image/png' : ext === 'webp' ? 'image/webp' : 'image/jpeg';
      fd.append('file', { uri: selfieUri, name: filename, type: mime } as any);

      const upload = await apiPost<{ key: string; expires_at: string; size_bytes: number }>(
        '/api/upload/selfie',
        fd,
        true,
      );

      // 2) Dispatch generation. gallery-store handles temp_id → real_id swap
      // and polling.
      startTemplateGeneration(
        { template_id: template.id, selfie_key: upload.key },
        {
          prompt: template.title,
          model: template.model || 'kling-motion-control',
          cost,
        },
      );

      // 3) Go to gallery to watch the in-flight job.
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      router.replace('/gallery' as any);
    } catch (err: any) {
      Alert.alert('Upload failed', err?.message ?? 'Could not upload your selfie.');
    } finally {
      setSubmitting(false);
    }
  }

  const videoUrl =
    template.assets?.preview_video_url ?? template.assets?.driving_video_url;
  const scene = template.assets?.scene_image_url;
  const isPipelineA = template.pipeline_class === 'motion-transfer';

  const handleClose = () => {
    if (router.canGoBack()) router.back();
    else router.replace('/' as any);
  };

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <Stack.Screen options={{ headerShown: false }} />
      <HeaderRow onBack={handleClose} />

      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
        <View style={styles.previewWrap}>
          {isPipelineA && isUsableMediaUrl(videoUrl) ? (
            <Video
              source={{ uri: videoUrl }}
              style={styles.preview}
              resizeMode={ResizeMode.COVER}
              isLooping
              shouldPlay
            />
          ) : !isPipelineA && isUsableMediaUrl(scene) ? (
            <Image source={{ uri: scene }} style={styles.preview} />
          ) : (
            <View style={[styles.preview, styles.previewPlaceholder]}>
              <Ionicons name="film-outline" size={36} color={Colors.textSecondary} />
              <Text style={styles.dim}>Preview asset pending</Text>
            </View>
          )}
        </View>

        <View style={styles.formContent}>
          {!!template.description && (
            <Text style={styles.description}>{template.description}</Text>
          )}

          <SectionTitle>Add your photo</SectionTitle>
          <View style={styles.selfieRow}>
            {selfieUri ? (
              <>
                <Image source={{ uri: selfieUri }} style={styles.selfieThumb} />
                <Pressable onPress={handlePickSelfie} style={styles.changeBtn}>
                  <Text style={styles.changeLabel}>Change</Text>
                </Pressable>
              </>
            ) : (
              <Pressable onPress={handlePickSelfie} style={styles.pickerBox}>
                <Ionicons name="image-outline" size={28} color={Colors.textSecondary} />
                <Text style={styles.pickerLabel}>Pick a photo</Text>
              </Pressable>
            )}
          </View>

          <View style={styles.costLine}>
            <Text style={styles.costLabel}>Cost</Text>
            <Text style={styles.costValue}>{cost} credits</Text>
          </View>

          <Pressable
            onPress={handleGenerate}
            disabled={!canSubmit}
            style={[styles.generateBtn, { opacity: canSubmit ? 1 : 0.4 }]}
            accessibilityLabel="Generate video"
          >
            {submitting ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <Text style={styles.generateLabel}>
                {blockedByInFlight ? 'Generation in progress' : 'Generate Video'}
              </Text>
            )}
          </Pressable>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

function HeaderRow({ onBack }: { onBack: () => void }) {
  // Flow-layout back chevron. Replaces the prior absolute-positioned overlay
  // X — iOS silently swallowed touches on a Pressable sitting above the
  // expo-av <Video>. Mirrors clip/[id].tsx (S66). See
  // Memory/feedback_absolute_overlay_button_intercept.md.
  return (
    <View style={styles.headerRow}>
      <Pressable onPress={onBack} hitSlop={12} style={styles.headerBtn} accessibilityLabel="Back">
        <Ionicons name="chevron-back" size={26} color={Colors.textPrimary} />
      </Pressable>
      <View style={styles.headerBtn} />
    </View>
  );
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return <Text style={styles.sectionTitle}>{children}</Text>;
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: Colors.background },
  scroll: { paddingBottom: 32 },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: 12 },
  dim: { color: Colors.textSecondary, fontSize: 13 },
  previewWrap: { marginHorizontal: 0 },
  formContent: { paddingHorizontal: 16 },
  preview: {
    width: '100%',
    height: PREVIEW_HEIGHT,
    backgroundColor: Colors.card,
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 8,
    height: 44,
  },
  headerBtn: {
    width: 40,
    height: 40,
    alignItems: 'center',
    justifyContent: 'center',
  },
  previewPlaceholder: {
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: Colors.border,
  },
  description: {
    color: Colors.textSecondary,
    fontSize: 14,
    marginTop: 16,
    lineHeight: 20,
  },
  sectionTitle: {
    color: Colors.textPrimary,
    fontSize: 15,
    fontWeight: '600',
    marginTop: 24,
    marginBottom: 12,
  },
  selfieRow: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  pickerBox: {
    flex: 1,
    height: 96,
    borderRadius: 12,
    borderWidth: 1,
    borderStyle: 'dashed',
    borderColor: Colors.border,
    backgroundColor: Colors.card,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
  },
  pickerLabel: { color: Colors.textSecondary, fontSize: 13 },
  selfieThumb: { width: 96, height: 96, borderRadius: 12, backgroundColor: Colors.card },
  changeBtn: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    backgroundColor: Colors.elevated,
    borderRadius: 8,
  },
  changeLabel: { color: Colors.textPrimary, fontSize: 13 },
  costLine: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 24,
    paddingHorizontal: 4,
  },
  costLabel: { color: Colors.textSecondary, fontSize: 14 },
  costValue: { color: Colors.textPrimary, fontSize: 16, fontWeight: '600' },
  generateBtn: {
    marginTop: 16,
    height: 56,
    borderRadius: 28,
    backgroundColor: CTA_BLUE,
    alignItems: 'center',
    justifyContent: 'center',
  },
  generateLabel: { color: '#FFFFFF', fontSize: 18, fontWeight: '600' },
});
