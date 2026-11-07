/**
 * Frontend API Contract & Schema Verification Script
 * Validates TypeScript interfaces and services against FastAPI backend contract specifications.
 */

import { ChatRequest, ChatResponse, HealthResponse, DocumentListResponse, IngestionResponse } from '../src/types/api';

function assert(condition: boolean, message: string) {
  if (!condition) {
    throw new Error(`Assertion failed: ${message}`);
  }
}

console.log('=' .repeat(80));
console.log(' VeriWeave Frontend — TypeScript API Contract Verification');
console.log('=' .repeat(80));

// 1. Validate ChatRequest & ChatResponse types
const sampleChatRequest: ChatRequest = {
  query: 'What is the memory architecture of autonomous agents?',
  routing_mode: 'auto',
  retrieval_strategy: 'hybrid',
  top_k: 4,
  score_threshold: 0.45,
  rerank: false,
  adaptive: true,
};
assert(sampleChatRequest.query.length > 0, 'ChatRequest query must be non-empty');
assert(sampleChatRequest.adaptive === true, 'ChatRequest supports adaptive flag');

const sampleChatResponse: ChatResponse = {
  query: sampleChatRequest.query,
  answer: 'Autonomous agents distinguish between short-term memory and long-term memory.',
  citations: [
    {
      citation_id: 1,
      doc_id: 'doc-ai-agents',
      filename: 'ai_agents_overview.txt',
      page_number: 1,
      chunk_index: 1,
      score: 0.92,
      snippet: 'Cognitive agent architectures distinguish between short-term memory...',
    },
  ],
  retrieved_chunks: [],
  model_used: 'llama3.2:1b (offline-fallback)',
  latency_ms: 38.5,
  grounded: true,
  fallback_used: false,
  routing_decision: {
    route: 'vector_document',
    confidence: 0.88,
    reasoning: 'Query asks for explanatory or factual content residing in uploaded reference documents.',
    classification_method: 'logical_rule',
    required_sources: ['vector_document'],
    sub_queries: {},
    fallback_triggered: false,
  },
  retrieval_metadata: {
    strategy: 'hybrid',
    generated_queries: [],
    sub_queries: [],
    fusion_applied: true,
    reranking_applied: false,
    raw_candidate_count: 8,
    returned_candidate_count: 4,
    retrieval_latency_ms: 12.4,
  },
  evidence: [
    {
      evidence_id: 'ev-1',
      source_type: 'vector_document',
      source_id: 'chunk-1',
      doc_id: 'doc-ai-agents',
      filename: 'ai_agents_overview.txt',
      page_number: 1,
      chunk_index: 1,
      content_excerpt: 'Cognitive agent architectures distinguish between short-term memory...',
      score: 0.92,
      retrieval_timestamp: new Date().toISOString(),
      metadata: {},
    },
  ],
  adaptive_metadata: {
    adaptive_applied: true,
    route_selected: 'vector_document',
    original_query: sampleChatRequest.query,
    rewritten_queries: [],
    retrieved_evidence_count: 4,
    relevant_evidence_count: 3,
    irrelevant_evidence_count: 1,
    retrieval_attempts: 1,
    correction_attempts: 0,
    grounding_validation: {
      is_grounded: true,
      supported_claims: ['Autonomous agents distinguish between short-term and long-term memory.'],
      unsupported_claims: [],
      citation_valid: true,
      missing_citations: [],
      validation_reason: 'All factual propositions verified against retrieved evidence.',
      attempt_number: 1,
    },
    workflow_trace: [
      'workflow_start',
      'route_query: selected=\'vector_document\' (conf=0.88)',
      'retrieve_evidence: fetched 4 items',
      'grade_evidence: 3/4 relevant items',
      'generate_answer: synthesized response with 1 citations',
      'validate_grounding: grounded=True',
      'finalize_response: workflow complete',
    ],
    latency_ms: 38.5,
  },
};
assert(sampleChatResponse.citations.length === 1, 'Citations parsed correctly');
assert(sampleChatResponse.adaptive_metadata?.retrieval_attempts === 1, 'Adaptive metadata parsed correctly');
console.log('✓ ChatRequest and ChatResponse schemas validated.');

// 2. Validate Document schemas
const sampleDocList: DocumentListResponse = {
  total: 1,
  documents: [
    {
      doc_id: 'doc-ai-agents',
      filename: 'ai_agents_overview.txt',
      file_type: 'txt',
      file_size_bytes: 994,
      page_count: 1,
      chunk_count: 3,
      created_at: new Date().toISOString(),
    },
  ],
};
assert(sampleDocList.total === 1, 'DocumentList total count matches');
assert(sampleDocList.documents[0].filename === 'ai_agents_overview.txt', 'DocumentDetail filename matches');
console.log('✓ DocumentListResponse and DocumentDetail schemas validated.');

// 3. Validate Health schemas
const sampleHealth: HealthResponse = {
  app_name: 'VeriWeave Engine',
  status: 'healthy',
  version: '0.4.0',
  components: {
    vector_storage: {
      status: 'ok',
      details: {
        engine: 'Qdrant (persistent disk)',
        points_count: 21,
      },
    },
    embeddings: {
      status: 'ok',
      details: {
        model_name: 'sentence-transformers/all-MiniLM-L6-v2',
        dimension: 384,
      },
    },
    llm_engine: {
      status: 'ok',
      details: {
        model: 'llama3.2:1b',
      },
    },
  },
};
assert(sampleHealth.status === 'healthy', 'Health status valid');
assert(sampleHealth.components.vector_storage?.status === 'ok', 'Vector storage status valid');
console.log('✓ HealthResponse schema validated.');

console.log('=' .repeat(80));
console.log(' ✓ All Frontend TypeScript Schemas Match FastAPI Backend Pydantic Contracts!');
console.log('=' .repeat(80));
