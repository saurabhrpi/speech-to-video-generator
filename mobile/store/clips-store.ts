import { create } from 'zustand';
import * as clipsApi from '@/lib/clips';
import type { Clip } from '@/lib/types';

interface ClipsStore {
  clips: Clip[];
  loading: boolean;

  fetchClips: () => Promise<void>;
  saveClip: (url: string, note?: string, jsonResponse?: string) => Promise<void>;
  deleteClip: (ts: number) => Promise<void>;
  clearClips: () => Promise<void>;
  reorderClips: (fromIndex: number, toIndex: number) => void;
  stitchSaved: () => Promise<{ success: boolean; stitched_url?: string }>;
}

export const useClipsStore = create<ClipsStore>((set, get) => ({
  clips: [],
  loading: false,

  fetchClips: async () => {
    set({ loading: true });
    try {
      const clips = await clipsApi.fetchClips();
      set({ clips });
    } catch {
      // Silently fail — clips are non-critical
    }
    set({ loading: false });
  },

  saveClip: async (url, note, jsonResponse) => {
    await clipsApi.saveClip(url, note, jsonResponse);
    await get().fetchClips();
  },

  deleteClip: async (ts) => {
    // Optimistic: remove immediately
    set({ clips: get().clips.filter((c) => c.ts !== ts) });
    try {
      await clipsApi.deleteClip(ts);
    } catch {
      // Refetch on failure
      await get().fetchClips();
    }
  },

  clearClips: async () => {
    set({ clips: [] });
    try {
      await clipsApi.clearClips();
    } catch {
      await get().fetchClips();
    }
  },

  reorderClips: (fromIndex, toIndex) => {
    const newClips = [...get().clips];
    const [moved] = newClips.splice(fromIndex, 1);
    newClips.splice(toIndex, 0, moved);
    set({ clips: newClips });
    // Sync to server in background
    clipsApi.reorderClips(newClips.map((c) => c.ts)).catch(() => {});
  },

  stitchSaved: async () => {
    return clipsApi.stitchSavedClips();
  },
}));
