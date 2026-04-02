import { create } from 'zustand';
import type { AuthState } from '@/lib/types';
import * as auth from '@/lib/auth';

interface AuthStore {
  auth: AuthState | null;
  loginRequired: boolean;
  loading: boolean;

  login: () => Promise<void>;
  logout: () => Promise<void>;
  fetchSession: () => Promise<void>;
  setLoginRequired: (v: boolean) => void;

  /** Check if user can generate (authenticated or under usage limit) */
  canGenerate: () => boolean;
}

export const useAuthStore = create<AuthStore>((set, get) => ({
  auth: null,
  loginRequired: false,
  loading: true,

  login: async () => {
    const session = await auth.login();
    if (session) {
      set({ auth: session, loginRequired: false });
    }
  },

  logout: async () => {
    await auth.logout();
    set({ auth: null });
  },

  fetchSession: async () => {
    set({ loading: true });
    const session = await auth.fetchSession();
    set({ auth: session, loading: false });
    if (session?.authenticated) {
      set({ loginRequired: false });
    }
  },

  setLoginRequired: (v) => set({ loginRequired: v }),

  canGenerate: () => {
    const { auth: a } = get();
    if (!a) return false;
    if (a.authenticated) return true;
    return a.usage_count < a.limit;
  },
}));
