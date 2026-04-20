import Purchases, { LOG_LEVEL } from 'react-native-purchases';

import {
  REVENUECAT_IOS_APP_STORE_KEY,
  REVENUECAT_TEST_STORE_KEY,
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
