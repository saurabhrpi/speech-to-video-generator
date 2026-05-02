import auth, { FirebaseAuthTypes } from '@react-native-firebase/auth';
import * as AppleAuthentication from 'expo-apple-authentication';
import * as Crypto from 'expo-crypto';
import { AppState } from 'react-native';

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

/**
 * Resolves when the app is foregrounded (AppState 'active') OR when the
 * timeout elapses, whichever comes first. If the app is already active when
 * called, resolves immediately. Used to delay an Apple Sign In retry until
 * after the user returns from Settings (iCloud sign-in flow).
 */
function waitForAppActive(timeoutMs: number): Promise<void> {
  return new Promise((resolve) => {
    if (AppState.currentState === 'active') {
      resolve();
      return;
    }
    let done = false;
    const finish = () => {
      if (done) return;
      done = true;
      clearTimeout(timer);
      sub.remove();
      resolve();
    };
    const timer = setTimeout(finish, timeoutMs);
    const sub = AppState.addEventListener('change', (state) => {
      if (state === 'active') finish();
    });
  });
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

  const signInOpts = {
    requestedScopes: [
      AppleAuthentication.AppleAuthenticationScope.FULL_NAME,
      AppleAuthentication.AppleAuthenticationScope.EMAIL,
    ],
    nonce: hashedNonce,
  };

  // First call after a fresh iCloud sign-in (e.g., App Review on iPad with
  // a sandbox account, or any user who taps Buy without iCloud signed in)
  // fails with "The authorization attempt failed for an unknown reason"
  // (error code 1000). Two distinct sub-cases:
  //   (a) iCloud was already signed in but auth daemon is cold → immediate
  //       retry would work, but we still want a tiny settle delay.
  //   (b) iCloud was NOT signed in → iOS pulls user to Settings to sign in.
  //       Immediate retry fires while the app is backgrounded and queues
  //       the second signInAsync in a bad state, so it ALSO fails.
  // To handle both, after the first failure we wait for the app to be
  // foregrounded (in case the user was sent to Settings) and then for a
  // settle delay so the daemon recognizes the new iCloud session before
  // we retry. Reproduced on iPad Air sim 2026-05-02 with full log trace.
  let credential;
  try {
    credential = await AppleAuthentication.signInAsync(signInOpts);
  } catch (e: any) {
    if (e?.code === 'ERR_REQUEST_CANCELED') throw e;
    console.warn('[auth] Apple Sign In first attempt failed, waiting then retrying:', e?.code, e?.message);
    // 5 min ceiling: covers slow iCloud sign-ins (forgot password, 2FA,
    // sandbox account setup). Falls through if exceeded — last-ditch retry
    // will likely fail and surface the original error to the user.
    await waitForAppActive(5 * 60_000);
    // Daemon settle — iOS needs a moment after iCloud sign-in completes
    // before it accepts a new ASAuthorization request.
    await new Promise((r) => setTimeout(r, 1000));
    credential = await AppleAuthentication.signInAsync(signInOpts);
  }

  if (!credential.identityToken) {
    throw new Error('Apple Sign In did not return an identity token');
  }

  return auth.AppleAuthProvider.credential(
    credential.identityToken,
    rawNonce,
  );
}
