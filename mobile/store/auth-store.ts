import { create } from 'zustand';
import {
  ensureSignedIn,
  signInWithApple as fbSignInWithApple,
  signOut as fbSignOut,
  onAuthChange,
  type FirebaseUser,
} from '@/lib/auth';
import { apiGet } from '@/lib/api-client';

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
  loginRequired: boolean;
  usage: Usage | null;

  initialize: () => () => void;
  signInWithApple: () => Promise<void>;
  signOut: () => Promise<void>;
  refreshUsage: () => Promise<void>;
  setLoginRequired: (v: boolean) => void;
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
  loginRequired: false,
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
      if (!user.isAnonymous) {
        set({ loginRequired: false });
      }
      try {
        await get().refreshUsage();
      } catch {
        // ignore
      }
    });
    return unsub;
  },

  signInWithApple: async () => {
    await fbSignInWithApple();
  },

  signOut: async () => {
    await fbSignOut();
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

  setLoginRequired: (v) => set({ loginRequired: v }),

  canGenerate: () => {
    const s = get();
    if (!s.isAnonymous) return true;
    if (!s.usage) return true;
    return s.usage.usage_count < s.usage.limit;
  },
}));
