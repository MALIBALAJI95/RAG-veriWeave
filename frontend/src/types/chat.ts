import { ChatResponse, Citation, EvidenceItem, RoutingDecision, AdaptiveWorkflowMetadata } from './api';

export interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  content: string;
  timestamp: string;
  responseMetadata?: {
    latency_ms: number;
    model_used: string;
    grounded: boolean;
    fallback_used: boolean;
    citations: Citation[];
    evidence: EvidenceItem[];
    routing_decision?: RoutingDecision | null;
    adaptive_metadata?: AdaptiveWorkflowMetadata | null;
    rawResponse: ChatResponse;
  };
  error?: string;
  isPending?: boolean;
}

export interface ConversationSession {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
  messages: ChatMessage[];
}
