import { create } from 'zustand';
import {
  ensureSignedIn,
  signInWithApple as fbSignInWithApple,
  signOut as fbSignOut,
  onAuthChange,
  type FirebaseUser,
} from '@/lib/auth';
import { apiGet, apiDelete } from '@/lib/api-client';
import { resetPurchasesUser, syncPurchasesUser } from '@/lib/purchases';
import { creditCostFor, type CostTable } from '@/lib/constants';

interface AuthStore {
  uid: string | null;
  isAnonymous: boolean;
  displayName: string | null;
  email: string | null;
  loading: boolean;
  paywallOpen: boolean;
  creditBalance: number | null;
  costTable: CostTable | null;

  initialize: () => () => void;
  signInWithApple: () => Promise<void>;
  signOut: () => Promise<void>;
  deleteAccount: () => Promise<void>;
  refreshCredits: () => Promise<void>;
  openPaywall: () => void;
  closePaywall: () => void;
  canAfford: (modelKey: string, duration: number) => boolean;
}

function applyUser(user: FirebaseUser | null) {
  if (!user) {
    return {
      uid: null,
      isAnonymous: true,
      displayName: null,
      email: null,
    };
  }
  return {
    uid: user.uid,
    isAnonymous: user.isAnonymous,
    displayName: user.displayName ?? null,
    email: user.email ?? null,
  };
}

export const useAuthStore = create<AuthStore>((set, get) => ({
  uid: null,
  isAnonymous: true,
  displayName: null,
  email: null,
  loading: true,
  paywallOpen: false,
  creditBalance: null,
  costTable: null,

  initialize: () => {
    const unsub = onAuthChange(async (user) => {
      if (!user) {
        try {
          await ensureSignedIn();
        } catch (e) {
          console.warn('[auth] anonymous sign-in failed:', e);
          set({ loading: false });
        }
        return;
      }
      const prevUid = get().uid;
      const next = { ...applyUser(user), loading: false };
      // UID changed (sign-in/out/anon-rotation) → drop stale balance immediately so
      // the projected-balance check in canAfford doesn't gate against a previous user's credits.
      if (prevUid !== user.uid) {
        set({ ...next, creditBalance: null, costTable: null });
      } else {
        set(next);
      }
      syncPurchasesUser(user.uid);
      try {
        await get().refreshCredits();
      } catch {
        // ignore
      }
    });
    return unsub;
  },

  signInWithApple: async () => {
    const user = await fbSignInWithApple();
    set(applyUser(user));
    try {
      await get().refreshCredits();
    } catch {
      // ignore
    }
  },

  signOut: async () => {
    await fbSignOut();
    await resetPurchasesUser();
    set({ creditBalance: null, costTable: null });
  },

  deleteAccount: async () => {
    // Server deletion goes first while the Firebase ID token is still valid.
    // Server wipes credits doc + clip namespace + Firebase user (in that order).
    // Once the Firebase user is gone, further authed calls would 401, so all
    // local cleanup runs after the server call completes.
    await apiDelete('/api/account');

    // Lazy require avoids a circular dependency with gallery-store, which
    // already imports this store for the canAfford check.
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const { useGalleryStore } = require('@/store/gallery-store') as typeof import('@/store/gallery-store');
    await useGalleryStore.getState().wipe();

    await resetPurchasesUser();
    try {
      await fbSignOut();
    } catch {
      // Firebase user already deleted server-side; signOut may throw. The
      // onAuthStateChanged listener will fire with null and re-anon via
      // ensureSignedIn(), so the app stays usable.
    }
    set({ creditBalance: null, costTable: null });
  },

  refreshCredits: async () => {
    try {
      const j = await apiGet<Record<string, any>>('/api/auth/session');
      set({
        creditBalance:
          typeof j?.credit_balance === 'number' ? j.credit_balance : null,
        costTable:
          j?.cost_table && typeof j.cost_table === 'object'
            ? (j.cost_table as CostTable)
            : null,
      });
    } catch {
      // ignore
    }
  },

  openPaywall: () => set({ paywallOpen: true }),
  closePaywall: () => set({ paywallOpen: false }),

  canAfford: (modelKey, duration) => {
    const s = get();
    const cost = creditCostFor(modelKey, duration, s.costTable);
    if (cost === null) return true;
    if (s.creditBalance === null) return true;
    // Lazy require avoids the circular import (gallery-store already imports this store).
    // Subtract in-flight job costs so concurrent submits can't slip past the credit gate
    // — the server still races on submit (TOCTOU), this is the client-side mitigation.
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const { useGalleryStore } = require('@/store/gallery-store') as typeof import('@/store/gallery-store');
    const inFlight = useGalleryStore.getState().jobs
      .filter((j) => j.status === 'generating' || j.status === 'paused')
      .reduce((sum, j) => sum + (j.costAtSubmit ?? 0), 0);
    return s.creditBalance - inFlight >= cost;
  },
}));
