import { create } from 'zustand';
import { HealthResponse } from '../types/api';
import { healthService } from '../services/healthService';
import { extractErrorMessage } from '../services/apiClient';

interface HealthState {
  health: HealthResponse | null;
  isLoading: boolean;
  error: string | null;
  lastChecked: string | null;

  // Actions
  fetchHealth: () => Promise<void>;
}

export const useHealthStore = create<HealthState>((set) => ({
  health: null,
  isLoading: false,
  error: null,
  lastChecked: null,

  fetchHealth: async () => {
    set({ isLoading: true, error: null });
    try {
      const data = await healthService.checkHealth();
      set({
        health: data,
        isLoading: false,
        lastChecked: new Date().toLocaleTimeString(),
      });
    } catch (err) {
      set({
        error: extractErrorMessage(err),
        isLoading: false,
        lastChecked: new Date().toLocaleTimeString(),
      });
    }
  },
}));
