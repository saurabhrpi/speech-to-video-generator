import AsyncStorage from '@react-native-async-storage/async-storage';

// Versioned key — bump if the disclosure scope changes (e.g., add a new
// third-party processor). Old consent is invalidated and the modal re-prompts.
const CONSENT_KEY = 'data_sharing_consent_v1';

/**
 * One-time disclosure + consent for sending user data (text prompts, audio)
 * to third-party AI providers (OpenAI Whisper, MiniMax Hailuo). Required by
 * App Store guidelines 5.1.1(i) and 5.1.2(i).
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
