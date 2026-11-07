import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { ChatRequest, ChatResponse, RetrievalStrategy, RoutingMode } from '../types/api';
import { ChatMessage } from '../types/chat';
import { chatService } from '../services/chatService';
import { extractErrorMessage } from '../services/apiClient';

interface ChatState {
  messages: ChatMessage[];
  isLoading: boolean;
  error: string | null;
  routingMode: RoutingMode;
  retrievalStrategy: RetrievalStrategy;
  adaptive: boolean;
  topK: number;
  scoreThreshold: number | null;
  rerank: boolean;
  selectedDocIdFilter: string | null;
  inspectedResponse: ChatResponse | null;

  // Actions
  setRoutingMode: (mode: RoutingMode) => void;
  setRetrievalStrategy: (strategy: RetrievalStrategy) => void;
  setAdaptive: (enabled: boolean) => void;
  setTopK: (k: number) => void;
  setScoreThreshold: (threshold: number | null) => void;
  setRerank: (rerank: boolean) => void;
  setSelectedDocIdFilter: (docId: string | null) => void;
  setInspectedResponse: (response: ChatResponse | null) => void;
  sendMessage: (query: string) => Promise<void>;
  clearMessages: () => void;
}

export const useChatStore = create<ChatState>()(
  persist(
    (set, get) => ({
      messages: [],
      isLoading: false,
      error: null,
      routingMode: 'auto',
      retrievalStrategy: 'hybrid',
      adaptive: true, // Default to true so users experience Phase 4 LangGraph by default
      topK: 4,
      scoreThreshold: null,
      rerank: false,
      selectedDocIdFilter: null,
      inspectedResponse: null,

      setRoutingMode: (routingMode) => set({ routingMode }),
      setRetrievalStrategy: (retrievalStrategy) => set({ retrievalStrategy }),
      setAdaptive: (adaptive) => set({ adaptive }),
      setTopK: (topK) => set({ topK }),
      setScoreThreshold: (scoreThreshold) => set({ scoreThreshold }),
      setRerank: (rerank) => set({ rerank }),
      setSelectedDocIdFilter: (selectedDocIdFilter) => set({ selectedDocIdFilter }),
      setInspectedResponse: (inspectedResponse) => set({ inspectedResponse }),

      sendMessage: async (query: string) => {
        const trimmed = query.trim();
        if (!trimmed) return;

        const {
          routingMode,
          retrievalStrategy,
          adaptive,
          topK,
          scoreThreshold,
          rerank,
          selectedDocIdFilter,
        } = get();

        const userMsgId = `user-${Date.now()}`;
        const assistantMsgId = `assistant-${Date.now()}`;

        const userMessage: ChatMessage = {
          id: userMsgId,
          sender: 'user',
          content: trimmed,
          timestamp: new Date().toISOString(),
        };

        const pendingAssistantMessage: ChatMessage = {
          id: assistantMsgId,
          sender: 'assistant',
          content: '',
          timestamp: new Date().toISOString(),
          isPending: true,
        };

        set((state) => ({
          messages: [...state.messages, userMessage, pendingAssistantMessage],
          isLoading: true,
          error: null,
        }));

        try {
          const request: ChatRequest = {
            query: trimmed,
            routing_mode: routingMode,
            retrieval_strategy: retrievalStrategy,
            top_k: topK,
            score_threshold: scoreThreshold,
            rerank,
            doc_id_filter: selectedDocIdFilter || undefined,
            adaptive,
          };

          const response = await chatService.sendMessage(request);

          set((state) => {
            const updated = state.messages.map((msg) => {
              if (msg.id === assistantMsgId) {
                return {
                  ...msg,
                  content: response.answer,
                  isPending: false,
                  responseMetadata: {
                    latency_ms: response.latency_ms,
                    model_used: response.model_used,
                    grounded: response.grounded,
                    fallback_used: response.fallback_used,
                    citations: response.citations,
                    evidence: response.evidence,
                    routing_decision: response.routing_decision,
                    adaptive_metadata: response.adaptive_metadata,
                    rawResponse: response,
                  },
                };
              }
              return msg;
            });
            return {
              messages: updated,
              isLoading: false,
              inspectedResponse: response,
            };
          });
        } catch (err) {
          const errMsg = extractErrorMessage(err);
          set((state) => ({
            messages: state.messages.map((msg) =>
              msg.id === assistantMsgId
                ? {
                    ...msg,
                    content: 'Failed to generate response.',
                    isPending: false,
                    error: errMsg,
                  }
                : msg
            ),
            isLoading: false,
            error: errMsg,
          }));
        }
      },

      clearMessages: () => set({ messages: [], error: null }),
    }),
    {
      name: 'veriweave-chat-storage',
      partialize: (state) => ({
        messages: state.messages,
        routingMode: state.routingMode,
        retrievalStrategy: state.retrievalStrategy,
        adaptive: state.adaptive,
        topK: state.topK,
        rerank: state.rerank,
      }),
    }
  )
);
