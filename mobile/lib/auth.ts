import auth, { FirebaseAuthTypes } from '@react-native-firebase/auth';
import * as AppleAuthentication from 'expo-apple-authentication';
import * as Crypto from 'expo-crypto';

export type FirebaseUser = FirebaseAuthTypes.User;

export async function ensureSignedIn(): Promise<void> {
  if (!auth().currentUser) {
    await auth().signInAnonymously();
  }
}

export async function signInWithApple(): Promise<void> {
  const rawNonce = await generateRawNonce();
  const hashedNonce = await Crypto.digestStringAsync(
    Crypto.CryptoDigestAlgorithm.SHA256,
    rawNonce,
  );

  const credential = await AppleAuthentication.signInAsync({
    requestedScopes: [
      AppleAuthentication.AppleAuthenticationScope.FULL_NAME,
      AppleAuthentication.AppleAuthenticationScope.EMAIL,
    ],
    nonce: hashedNonce,
  });

  if (!credential.identityToken) {
    throw new Error('Apple Sign In did not return an identity token');
  }

  const appleCred = auth.AppleAuthProvider.credential(
    credential.identityToken,
    rawNonce,
  );

  const current = auth().currentUser;
  if (current?.isAnonymous) {
    try {
      await current.linkWithCredential(appleCred);
      return;
    } catch (e: any) {
      // Apple account already linked to another Firebase user — fall back
      // to plain sign-in (orphans the anonymous user's data).
      if (e?.code !== 'auth/credential-already-in-use') {
        throw e;
      }
    }
  }

  await auth().signInWithCredential(appleCred);
}

export async function signOut(): Promise<void> {
  await auth().signOut();
}

export async function getIdToken(forceRefresh = false): Promise<string | null> {
  if (!auth().currentUser) {
    await ensureSignedIn().catch(() => {});
  }
  const user = auth().currentUser;
  if (!user) return null;
  return user.getIdToken(forceRefresh);
}

export function onAuthChange(cb: (user: FirebaseUser | null) => void): () => void {
  return auth().onAuthStateChanged(cb);
}

async function generateRawNonce(length: number = 32): Promise<string> {
  const bytes = await Crypto.getRandomBytesAsync(length);
  return Array.from(bytes)
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('');
}
