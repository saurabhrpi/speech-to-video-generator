import Purchases, { LOG_LEVEL } from 'react-native-purchases';

import { apiPost, HttpError } from './api-client';
import {
  PACK_SKUS,
  REVENUECAT_IOS_APP_STORE_KEY,
  REVENUECAT_TEST_STORE_KEY,
  type PackSku,
} from './constants';

let configured = false;

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
  } catch (e) {
    console.warn('[rc] configure failed:', e);
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
