import AsyncStorage from '@react-native-async-storage/async-storage';
import Purchases, { LOG_LEVEL, type CustomerInfo } from 'react-native-purchases';

import { apiPost, HttpError } from './api-client';
import {
  PACK_SKUS,
  REVENUECAT_IOS_APP_STORE_KEY,
  REVENUECAT_TEST_STORE_KEY,
  type PackSku,
} from './constants';

let configured = false;
let listenerInstalled = false;

// Locally-tracked set of transactionIdentifiers we've already attempted to grant
// for. AIV-51: the CustomerInfo listener fires repeatedly (every CustomerInfo
// change); without this cache we'd spam /api/credits/grant on every fire.
// Server-side is idempotent, so a stale/empty cache is a perf hit, not a
// correctness issue. Persisted across launches via AsyncStorage.
const GRANTED_TX_STORAGE_KEY = 'rc_granted_tx_ids_v1';
let grantedTxIds: Set<string> | null = null;

async function loadGrantedTxIds(): Promise<Set<string>> {
  if (grantedTxIds) return grantedTxIds;
  try {
    const raw = await AsyncStorage.getItem(GRANTED_TX_STORAGE_KEY);
    const arr = raw ? JSON.parse(raw) : [];
    grantedTxIds = new Set(Array.isArray(arr) ? arr : []);
  } catch {
    grantedTxIds = new Set();
  }
  return grantedTxIds;
}

async function markTxGranted(txId: string): Promise<void> {
  const set = await loadGrantedTxIds();
  if (set.has(txId)) return;
  set.add(txId);
  try {
    await AsyncStorage.setItem(GRANTED_TX_STORAGE_KEY, JSON.stringify([...set]));
  } catch (e) {
    console.warn('[rc] failed to persist granted tx:', e);
  }
}

export function configurePurchases(): void {
  if (configured) return;
  try {
    if (__DEV__) {
      Purchases.setLogLevel(LOG_LEVEL.DEBUG);
    }
    const apiKey = __DEV__
      ? REVENUECAT_TEST_STORE_KEY
      : REVENUECAT_IOS_APP_STORE_KEY;
    Purchases.configure({ apiKey });
    configured = true;

    if (!listenerInstalled) {
      Purchases.addCustomerInfoUpdateListener(handleCustomerInfoUpdate);
      listenerInstalled = true;
    }
  } catch (e) {
    console.warn('[rc] configure failed:', e);
  }
}

// AIV-51: recovery path for offline-replayed transactions + RC REST ingestion lag.
// Fires whenever RC's CustomerInfo updates — including after a delayed receipt
// ingestion that the Paywall's 7s retry window missed. Walks nonSubscriptionTransactions,
// skips ones already granted locally, calls the existing grant endpoint for the rest.
async function handleCustomerInfoUpdate(info: CustomerInfo): Promise<void> {
  const txs = info.nonSubscriptionTransactions ?? [];
  if (txs.length === 0) return;

  // Lazy require: auth-store already imports this file (syncPurchasesUser /
  // resetPurchasesUser), so a top-level import here creates a cycle.
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  const { useAuthStore } =
    require('@/store/auth-store') as typeof import('@/store/auth-store');
  const uid = useAuthStore.getState().uid;
  if (!uid) return; // Not signed in yet; next fire after sign-in will catch up.

  const granted = await loadGrantedTxIds();
  let newGrants = 0;

  for (const tx of txs) {
    const productId = tx.productIdentifier;
    const txId = tx.transactionIdentifier;
    if (!productId || !txId) continue;
    if (!PACK_SKUS.includes(productId as PackSku)) continue;
    if (granted.has(txId)) continue;

    try {
      await grantCreditsForTransaction(productId, txId);
      await markTxGranted(txId);
      newGrants += 1;
    } catch (e) {
      // Leave txId OUT of local set so next listener fire retries.
      console.warn(
        '[rc] listener grant failed (will retry on next CustomerInfo update):',
        e,
      );
    }
  }

  if (newGrants > 0) {
    try {
      await useAuthStore.getState().refreshCredits();
    } catch {
      // Balance will refresh on next /api/auth/session call.
    }
    // Dismiss the Paywall if it's still open showing a stale "Credits should
    // appear shortly" error from the Paywall's inline grant having timed out.
    // No-op when Paywall isn't open; the open-effect resets purchaseError on
    // the next show, so the stale red text won't reappear.
    useAuthStore.getState().closePaywall();
  }
}

export async function syncPurchasesUser(firebaseUid: string): Promise<void> {
  if (!configured) configurePurchases();
  try {
    await Purchases.logIn(firebaseUid);
  } catch (e) {
    console.warn('[rc] logIn failed:', e);
  }
}

export async function resetPurchasesUser(): Promise<void> {
  if (!configured) return;
  try {
    await Purchases.logOut();
  } catch (e) {
    console.warn('[rc] logOut failed:', e);
  }
}

// AIV-51: called from _layout.tsx AppState 'active' to force a CustomerInfo
// re-fetch on foreground. RC SDK auto-refreshes already, but explicitly
// invoking handleCustomerInfoUpdate guarantees the recovery path runs even if
// the SDK's auto-refresh dedupes (cached info unchanged).
export async function refreshPurchasesState(): Promise<void> {
  if (!configured) return;
  try {
    const info = await Purchases.getCustomerInfo();
    await handleCustomerInfoUpdate(info);
  } catch (e) {
    console.warn('[rc] refreshPurchasesState failed:', e);
  }
}

// Call after a purchase or restore to tell the server to credit the user.
// Retries on 404 (RC's backend hasn't ingested the receipt yet).
export async function grantCreditsForTransaction(
  productId: string,
  transactionId: string,
): Promise<void> {
  const delays = [1000, 2000, 4000];
  let lastErr: unknown = null;
  for (let attempt = 0; attempt <= delays.length; attempt++) {
    try {
      await apiPost('/api/credits/grant', {
        product_id: productId,
        transaction_id: transactionId,
      });
      return;
    } catch (e) {
      lastErr = e;
      if (!(e instanceof HttpError) || e.status !== 404) throw e;
      if (attempt < delays.length) {
        await new Promise((r) => setTimeout(r, delays[attempt]));
      }
    }
  }
  throw lastErr;
}

// Restore prior purchases and re-grant credits for any matching non-subscription
// transactions. Server-side grant is idempotent, so replaying a tx is a no-op.
//
// NOTE: no UI surfaces this today — Apple 3.1.1 forbids a Restore button for
// consumable-only apps (memory/reference_no_restore_ui_for_consumables.md).
// Kept as a programmatic recovery option; the CustomerInfo listener above is
// the primary recovery path.
export async function restoreAndGrant(): Promise<void> {
  const info = await Purchases.restorePurchases();
  const txs = info.nonSubscriptionTransactions ?? [];
  for (const tx of txs) {
    if (!PACK_SKUS.includes(tx.productIdentifier as PackSku)) continue;
    try {
      await grantCreditsForTransaction(tx.productIdentifier, tx.transactionIdentifier);
    } catch {
      // Individual grant failures shouldn't abort the batch.
    }
  }
}
