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

interface Usage {
  usage_count: number;
  limit: number;
}

interface AuthStore {
  uid: string | null;
  isAnonymous: boolean;
  displayName: string | null;
  email: string | null;
  loading: boolean;
  paywallOpen: boolean;
  usage: Usage | null;

  initialize: () => () => void;
  signInWithApple: () => Promise<void>;
  signOut: () => Promise<void>;
  refreshUsage: () => Promise<void>;
  openPaywall: () => void;
  closePaywall: () => void;
  canGenerate: () => boolean;
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
  usage: null,

  initialize: () => {
    const unsub = onAuthChange(async (user) => {
      if (!user) {
        // No user session — create an anonymous one silently.
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
        await get().refreshUsage();
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
      await get().refreshUsage();
    } catch {
      // ignore
    }
  },

  signOut: async () => {
    await fbSignOut();
    await resetPurchasesUser();
    set({ usage: null });
  },

  refreshUsage: async () => {
    try {
      const j = await apiGet<Record<string, any>>('/api/auth/session');
      set({
        usage: {
          usage_count: Number(j?.usage_count || 0),
          limit: Number(j?.limit || 0),
        },
      });
    } catch {
      // ignore
    }
  },

  openPaywall: () => set({ paywallOpen: true }),
  closePaywall: () => set({ paywallOpen: false }),

  canGenerate: () => {
    const s = get();
    if (!s.isAnonymous) return true;
    if (!s.usage) return true;
    return s.usage.usage_count < s.usage.limit;
  },
}));
