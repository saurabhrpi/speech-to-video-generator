import { create } from 'zustand';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { API_BASE } from '@/lib/constants';

const STORAGE_KEY_TEMPLATES = 'v2_templates_cache';
const STORAGE_KEY_ETAG = 'v2_templates_etag';

export interface Template {
  id: string;
  pipeline_class: 'motion-transfer' | 'scene-insertion';
  outcome: '1' | '2' | 'n/a';
  category: string;
  title: string;
  description: string;
  published_status: 'draft' | 'qa-pending' | 'published';
  assets: {
    driving_video_url: string | null;
    scene_image_url: string | null;
    thumbnail_url: string | null;
    preview_video_url: string | null;
  };
  model: string;
  credit_cost: number;
  prompt_template: string | null;
  created_at?: string;
  updated_at?: string;
}

interface TemplateStore {
  templates: Template[];
  etag: string | null;
  loading: boolean;
  error: string | null;
  lastFetched: number | null;
  hydrated: boolean;

  hydrate: () => Promise<void>;
  fetchTemplates: () => Promise<void>;
}

export const useTemplateStore = create<TemplateStore>((set, get) => ({
  templates: [],
  etag: null,
  loading: false,
  error: null,
  lastFetched: null,
  hydrated: false,

  hydrate: async () => {
    try {
      const [tplRaw, etag] = await Promise.all([
        AsyncStorage.getItem(STORAGE_KEY_TEMPLATES),
        AsyncStorage.getItem(STORAGE_KEY_ETAG),
      ]);
      const templates: Template[] = tplRaw ? JSON.parse(tplRaw) : [];
      set({ templates, etag, hydrated: true });
    } catch (e) {
      // Treat hydration failure as "no cache" rather than a fatal error —
      // the next fetch refills both.
      set({ hydrated: true });
    }
  },

  fetchTemplates: async () => {
    const { etag } = get();
    set({ loading: true, error: null });
    try {
      const headers: Record<string, string> = {};
      if (etag) headers['If-None-Match'] = etag;
      const res = await fetch(`${API_BASE}/api/templates`, { headers });

      if (res.status === 304) {
        // Cache still valid; keep existing templates + etag.
        set({ loading: false, lastFetched: Date.now() });
        return;
      }
      if (!res.ok) {
        throw new Error(`templates fetch failed (${res.status})`);
      }

      const body = await res.json();
      const templates: Template[] = body.templates ?? [];
      const newEtag = res.headers.get('etag') ?? res.headers.get('ETag');

      set({
        templates,
        etag: newEtag,
        loading: false,
        lastFetched: Date.now(),
      });

      await Promise.all([
        AsyncStorage.setItem(STORAGE_KEY_TEMPLATES, JSON.stringify(templates)),
        newEtag ? AsyncStorage.setItem(STORAGE_KEY_ETAG, newEtag) : Promise.resolve(),
      ]);
    } catch (e: any) {
      set({ loading: false, error: e?.message ?? String(e) });
    }
  },
}));

// Convenience selector: group templates by category in stable insertion order.
export function groupByCategory(templates: Template[]): Array<{ category: string; items: Template[] }> {
  const map = new Map<string, Template[]>();
  for (const t of templates) {
    const k = t.category || 'uncategorized';
    if (!map.has(k)) map.set(k, []);
    map.get(k)!.push(t);
  }
  return Array.from(map.entries()).map(([category, items]) => ({ category, items }));
}
