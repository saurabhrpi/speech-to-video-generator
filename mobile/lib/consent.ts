import AsyncStorage from '@react-native-async-storage/async-storage';

// Versioned key — bump if the disclosure scope changes (e.g., add a new
// third-party processor). Old consent is invalidated and the modal re-prompts.
// v2 (V2.0.0): adds Kling AI + photo upload to the disclosure scope; also
// folds in the "rights to use the photo" affirmation that used to live as a
// per-template checkbox.
const CONSENT_KEY = 'data_sharing_consent_v2';

/**
 * One-time disclosure + consent for sending user data (text prompts, audio,
 * photos) to third-party AI providers (OpenAI Whisper, MiniMax Hailuo,
 * Kling AI). Required by App Store guidelines 5.1.1(i) and 5.1.2(i).
 */
export async function hasDataSharingConsent(): Promise<boolean> {
  try {
    return (await AsyncStorage.getItem(CONSENT_KEY)) === 'true';
  } catch {
    // AsyncStorage unavailable — treat as not consented; user will see modal.
    return false;
  }
}

export async function setDataSharingConsent(): Promise<void> {
  try {
    await AsyncStorage.setItem(CONSENT_KEY, 'true');
  } catch {
    // Best-effort. If storage fails we'll re-prompt next time, which is fine.
  }
}
