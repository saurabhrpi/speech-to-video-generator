import auth, { FirebaseAuthTypes } from '@react-native-firebase/auth';
import * as AppleAuthentication from 'expo-apple-authentication';
import * as Crypto from 'expo-crypto';

export type FirebaseUser = FirebaseAuthTypes.User;

export async function ensureSignedIn(): Promise<void> {
  if (!auth().currentUser) {
    await auth().signInAnonymously();
  }
}

export async function signInWithApple(): Promise<FirebaseUser> {
  const appleCred = await requestAppleCredential();

  const current = auth().currentUser;
  if (current?.isAnonymous) {
    try {
      const result = await current.linkWithCredential(appleCred);
      return result.user;
    } catch (e: any) {
      if (e?.code !== 'auth/credential-already-in-use') {
        throw e;
      }
      // Apple ID is already linked to another Firebase user. The failed link
      // consumed this nonce, so Firebase rejects re-use with
      // [auth/unknown] Duplicate credential received. Request a fresh Apple
      // credential and sign in with it.
      const freshCred = await requestAppleCredential();
      const result = await auth().signInWithCredential(freshCred);
      return result.user;
    }
  }

  const result = await auth().signInWithCredential(appleCred);
  return result.user;
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

async function requestAppleCredential() {
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

  return auth.AppleAuthProvider.credential(
    credential.identityToken,
    rawNonce,
  );
}
