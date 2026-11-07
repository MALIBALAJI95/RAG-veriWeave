import { apiClient } from './apiClient';
import { ChatRequest, ChatResponse } from '../types/api';

export const chatService = {
  /**
   * Submit a question to the VeriWeave chat endpoint.
   * Supports standard multi-path routing and LangGraph adaptive RAG (`adaptive: true`).
   */
  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    const response = await apiClient.post<ChatResponse>('/api/v1/chat', request);
    return response.data;
  },
};
