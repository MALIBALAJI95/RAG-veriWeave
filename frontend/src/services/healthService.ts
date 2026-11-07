import { apiClient } from './apiClient';
import { HealthResponse } from '../types/api';

export const healthService = {
  /**
   * Check system health (vector storage, embeddings, Ollama LLM status).
   */
  async checkHealth(): Promise<HealthResponse> {
    const response = await apiClient.get<HealthResponse>('/api/v1/health');
    return response.data;
  },
};
