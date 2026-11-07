# VeriWeave — Frontend API Integration Mapping & Contract Specification

> **Project**: VeriWeave — Adaptive Multi-Strategy Retrieval and Grounded Generation Engine  
> **Tagline**: Retrieve intelligently. Reason contextually. Respond reliably.  
> **Date**: 2026-11-07  
> **Backend Version**: 0.4.0 (FastAPI + LangGraph + Qdrant + SQLite)

---

## 1. Overview

This document specifies the exact contract mapping between the VeriWeave FastAPI backend and the React TypeScript frontend. It documents every operational endpoint, schema field, default parameter, error behavior, and explicitly identifies backend limitations to ensure the frontend never relies on simulated or invented functionality.

---

## 2. API Endpoint Matrix

| Method | Endpoint | Description | Request Body / Params | Backend Response Schema |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/` | Backend greeting & version info | None | Root JSON object |
| `GET` | `/api/v1/health` | Comprehensive system & component health | None | `HealthResponse` |
| `GET` | `/api/v1/documents` | List all indexed documents in persistent storage | None | `DocumentListResponse` |
| `POST` | `/api/v1/documents/upload` | Upload & ingest PDF, DOCX, TXT, or MD | `multipart/form-data` (`file`) | `IngestionResponse` |
| `GET` | `/api/v1/documents/{doc_id}` | Retrieve all indexed chunks for a document | Path: `doc_id: str` | `List[DocumentChunk]` |
| `DELETE`| `/api/v1/documents/{doc_id}` | Delete document from vector storage & disk | Path: `doc_id: str` | `DocumentDeleteResponse`|
| `POST` | `/api/v1/chat` | Multi-strategy retrieval & adaptive RAG query | `ChatRequest` (JSON) | `ChatResponse` |

---

## 3. Schema & Type Mapping

### 3.1 Health & Diagnostics (`GET /api/v1/health`)

#### Backend Schema: `HealthResponse`
```typescript
export interface ComponentStatus {
  status: "ok" | "degraded" | "error";
  details: {
    // vector_storage
    engine?: string;
    storage_path?: string;
    collection?: string;
    vectors_count?: number;
    points_count?: number;
    
    // embeddings
    model_name?: string;
    dimension?: number;
    device?: string;
    
    // llm_engine
    model?: string;
    base_url?: string;
    status?: string;
    error?: string;
    [key: string]: any;
  };
}

export interface HealthResponse {
  app_name: string;
  status: "healthy" | "degraded" | "unhealthy";
  version: string;
  components: {
    vector_storage?: ComponentStatus;
    embeddings?: ComponentStatus;
    llm_engine?: ComponentStatus;
    [key: string]: ComponentStatus | undefined;
  };
}
```

---

### 3.2 Document Management (`/api/v1/documents`)

#### List Documents (`GET /api/v1/documents`)
```typescript
export interface DocumentDetail {
  doc_id: string;
  filename: string;
  file_type: string;
  file_size_bytes: number;
  page_count: number;
  chunk_count: number;
  created_at: string; // ISO 8601 string
}

export interface DocumentListResponse {
  total: number;
  documents: DocumentDetail[];
}
```

#### Document Upload (`POST /api/v1/documents/upload`)
- **Content-Type**: `multipart/form-data`
- **Field**: `file: File`
- **Supported File Types**: `.pdf`, `.docx`, `.txt`, `.md`
- **Response**: `IngestionResponse`
```typescript
export interface IngestionResponse {
  doc_id: string;
  filename: string;
  file_type: string;
  file_size_bytes: number;
  page_count: number;
  chunk_count: number;
  status: string; // "indexed"
  message: string;
}
```

#### Document Chunks (`GET /api/v1/documents/{doc_id}`)
```typescript
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
  metadata: Record<string, any>;
}
```

#### Document Deletion (`DELETE /api/v1/documents/{doc_id}`)
```typescript
export interface DocumentDeleteResponse {
  doc_id: string;
  filename: string;
  deleted_chunks: number;
  status: string;
  message: string;
}
```

---

### 3.3 Chat, Retrieval & Adaptive RAG (`POST /api/v1/chat`)

#### Request Schema: `ChatRequest`
```typescript
export type RoutingMode = 
  | "auto"
  | "document_only"
  | "sql_only"
  | "web_only"
  | "multi_source";

export type RetrievalStrategy = 
  | "baseline"
  | "multi_query"
  | "hyde"
  | "decomposition"
  | "fusion"
  | "hybrid"
  | "hybrid_rerank"
  | "rerank";

export interface MetadataFilter {
  doc_id?: string;
  filename?: string;
  page_number?: number;
  custom?: Record<string, any>;
}

export interface ChatRequest {
  query: string; // min_length: 1, max_length: 2000
  routing_mode?: RoutingMode; // default: "auto"
  retrieval_strategy?: RetrievalStrategy; // default: "baseline"
  top_k?: number; // default: 4, ge: 1, le: 20
  score_threshold?: number | null; // ge: 0.0, le: 1.0
  rerank?: boolean; // default: false
  filters?: MetadataFilter;
  doc_id_filter?: string;
  adaptive?: boolean; // default: false (Phase 4 LangGraph pipeline)
}
```

#### Response Schema: `ChatResponse`
```typescript
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
  metadata?: Record<string, any>;
}

export interface RoutingDecision {
  route: "vector_document" | "structured_sql" | "web_search" | "multi_source";
  confidence: number;
  reasoning: string;
  classification_method: "logical_rule" | "semantic_llm" | "user_override" | "fallback";
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
  source_type: "vector_document" | "structured_sql" | "web_search";
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
  metadata: Record<string, any>;
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
```

---

## 4. Backend Capabilities & Explicit Constraints

1. **No Streaming Support**: The backend uses standard synchronous HTTP request/response (`POST /api/v1/chat`). The frontend will use standard async request/response with clear loading states; no artificial simulated token streaming will be used.
2. **No User Authentication**: The backend does not implement JWT/OAuth or user sessions. The workspace remains completely open and accessible without login screens or simulated logins.
3. **No Persistent Chat History in Backend**: The backend is stateless regarding chat history. The frontend stores conversation history locally in client memory and `localStorage` to allow tab switching, history review, and clearing conversations.
4. **Actual Grounding Citations**: All citations rendered in the UI match concrete fields returned in `citations` and `evidence`.

---

## 5. Environment Variables

- **`VITE_API_BASE_URL`**: Base URL pointing to the FastAPI backend (e.g. `http://localhost:8000`).
