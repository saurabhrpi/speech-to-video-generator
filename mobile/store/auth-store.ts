import { create } from 'zustand';
import {
  ensureSignedIn,
  signInWithApple as fbSignInWithApple,
  signOut as fbSignOut,
  onAuthChange,
  type FirebaseUser,
} from '@/lib/auth';
import { apiGet } from '@/lib/api-client';
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
      set({ ...applyUser(user), loading: false });
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
    return s.creditBalance >= cost;
  },
}));
