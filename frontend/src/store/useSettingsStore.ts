import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { RetrievalStrategy, RoutingMode } from '../types/api';

interface SettingsState {
  apiBaseUrl: string;
  defaultRoutingMode: RoutingMode;
  defaultRetrievalStrategy: RetrievalStrategy;
  defaultAdaptive: boolean;
  defaultTopK: number;
  enableDebugInspector: boolean;

  setApiBaseUrl: (url: string) => void;
  setDefaultRoutingMode: (mode: RoutingMode) => void;
  setDefaultRetrievalStrategy: (strategy: RetrievalStrategy) => void;
  setDefaultAdaptive: (adaptive: boolean) => void;
  setDefaultTopK: (topK: number) => void;
  setEnableDebugInspector: (enabled: boolean) => void;
  resetDefaults: () => void;
}

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set) => ({
      apiBaseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
      defaultRoutingMode: 'auto',
      defaultRetrievalStrategy: 'hybrid',
      defaultAdaptive: true,
      defaultTopK: 4,
      enableDebugInspector: true,

      setApiBaseUrl: (apiBaseUrl) => set({ apiBaseUrl }),
      setDefaultRoutingMode: (defaultRoutingMode) => set({ defaultRoutingMode }),
      setDefaultRetrievalStrategy: (defaultRetrievalStrategy) => set({ defaultRetrievalStrategy }),
      setDefaultAdaptive: (defaultAdaptive) => set({ defaultAdaptive }),
      setDefaultTopK: (defaultTopK) => set({ defaultTopK }),
      setEnableDebugInspector: (enableDebugInspector) => set({ enableDebugInspector }),
      resetDefaults: () =>
        set({
          apiBaseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
          defaultRoutingMode: 'auto',
          defaultRetrievalStrategy: 'hybrid',
          defaultAdaptive: true,
          defaultTopK: 4,
          enableDebugInspector: true,
        }),
    }),
    {
      name: 'veriweave-settings-storage',
    }
  )
);
