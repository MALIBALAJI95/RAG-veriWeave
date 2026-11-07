/**
 * VeriWeave TypeScript API Contract Definitions
 * Matched strictly to FastAPI Backend Pydantic Schemas
 */

export type RoutingMode =
  | 'auto'
  | 'document_only'
  | 'sql_only'
  | 'web_only'
  | 'multi_source';

export type RetrievalStrategy =
  | 'baseline'
  | 'multi_query'
  | 'hyde'
  | 'decomposition'
  | 'fusion'
  | 'hybrid'
  | 'hybrid_rerank'
  | 'rerank';

export type RouteCategory =
  | 'vector_document'
  | 'structured_sql'
  | 'web_search'
  | 'multi_source';

export interface MetadataFilter {
  doc_id?: string;
  filename?: string;
  page_number?: number;
  custom?: Record<string, unknown>;
}

export interface ChatRequest {
  query: string;
  routing_mode?: RoutingMode;
  retrieval_strategy?: RetrievalStrategy;
  top_k?: number;
  score_threshold?: number | null;
  rerank?: boolean;
  filters?: MetadataFilter;
  doc_id_filter?: string;
  adaptive?: boolean;
}

export interface Citation {
  citation_id: number;
  doc_id: string;
  filename: string;
  page_number: number;
  chunk_index: number;
  score: number;
  snippet: string;
}

export interface RetrievedChunk {
  chunk_id: string;
  doc_id: string;
  filename: string;
  page_number: number;
  chunk_index: number;
  text: string;
  score: number;
  original_rank?: number | null;
  rerank_score?: number | null;
  retrieval_method?: string;
  metadata?: Record<string, unknown>;
}

export interface RoutingDecision {
  route: RouteCategory;
  confidence: number;
  reasoning: string;
  classification_method: 'logical_rule' | 'semantic_llm' | 'user_override' | 'fallback' | string;
  selected_strategy?: string;
  required_sources: string[];
  sub_queries: Record<string, string>;
  fallback_triggered: boolean;
}

export interface RetrievalMetadata {
  strategy: RetrievalStrategy;
  generated_queries: string[];
  hypothetical_document?: string | null;
  sub_queries: string[];
  fusion_applied: boolean;
  reranking_applied: boolean;
  raw_candidate_count: number;
  returned_candidate_count: number;
  retrieval_latency_ms: number;
}

export interface EvidenceItem {
  evidence_id: string;
  source_type: 'vector_document' | 'structured_sql' | 'web_search' | string;
  source_id: string;
  doc_id?: string | null;
  filename?: string | null;
  page_number?: number | null;
  chunk_index?: number | null;
  record_id?: string | null;
  url?: string | null;
  title?: string | null;
  content_excerpt: string;
  score: number;
  retrieval_timestamp: string;
  metadata: Record<string, unknown>;
}

export interface GroundingValidationResult {
  is_grounded: boolean;
  supported_claims: string[];
  unsupported_claims: string[];
  citation_valid: boolean;
  missing_citations: string[];
  validation_reason: string;
  attempt_number: number;
}

export interface AdaptiveWorkflowMetadata {
  adaptive_applied: boolean;
  route_selected: string;
  original_query: string;
  rewritten_queries: string[];
  retrieved_evidence_count: number;
  relevant_evidence_count: number;
  irrelevant_evidence_count: number;
  retrieval_attempts: number;
  correction_attempts: number;
  grounding_validation?: GroundingValidationResult | null;
  workflow_trace: string[];
  latency_ms: number;
}

export interface ChatResponse {
  query: string;
  answer: string;
  citations: Citation[];
  retrieved_chunks: RetrievedChunk[];
  model_used: string;
  latency_ms: number;
  grounded: boolean;
  fallback_used: boolean;
  routing_decision?: RoutingDecision | null;
  retrieval_metadata?: RetrievalMetadata | null;
  evidence: EvidenceItem[];
  adaptive_metadata?: AdaptiveWorkflowMetadata | null;
}

export interface DocumentDetail {
  doc_id: string;
  filename: string;
  file_type: string;
  file_size_bytes: number;
  page_count: number;
  chunk_count: number;
  created_at: string;
}

export interface DocumentListResponse {
  total: number;
  documents: DocumentDetail[];
}

export interface IngestionResponse {
  doc_id: string;
  filename: string;
  file_type: string;
  file_size_bytes: number;
  page_count: number;
  chunk_count: number;
  status: string;
  message: string;
}

export interface DocumentChunk {
  chunk_id: string;
  doc_id: string;
  filename: string;
  page_number: number;
  chunk_index: number;
  text: string;
  char_start: number;
  char_end: number;
  token_count_estimate: number;
  metadata: Record<string, unknown>;
}

export interface DocumentDeleteResponse {
  doc_id: string;
  filename: string;
  deleted_chunks: number;
  status: string;
  message: string;
}

export interface ComponentStatus {
  status: 'ok' | 'degraded' | 'error' | string;
  details: Record<string, unknown>;
}

export interface HealthResponse {
  app_name: string;
  status: 'healthy' | 'degraded' | 'unhealthy' | string;
  version: string;
  components: {
    vector_storage?: ComponentStatus;
    embeddings?: ComponentStatus;
    llm_engine?: ComponentStatus;
    [key: string]: ComponentStatus | undefined;
  };
}
