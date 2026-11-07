# VeriWeave Frontend — Production AI SaaS Interface

> **Tagline**: Retrieve intelligently. Reason contextually. Respond reliably.

---

## 1. Overview

This directory contains the production-grade React 18 + TypeScript + Vite frontend for **VeriWeave — Adaptive Multi-Strategy Retrieval and Grounded Generation Engine**.

The frontend provides an interface for interacting with all 4 implemented backend phases:
- **Phase 1**: Ingestion, recursive chunking with page tracking, dense embeddings, persistent Qdrant storage, and grounded inline citations.
- **Phase 2**: Multi-query retrieval, HyDE, query decomposition, BM25 sparse search, Reciprocal Rank Fusion (RRF $k=60$), hybrid search, and cross-encoder reranking (`ms-marco-MiniLM-L-6-v2`).
- **Phase 3**: Intelligent multi-path routing across Vector Documents, Structured SQLite Catalog, External Web Search, and Multi-Source compound synthesis.
- **Phase 4**: Adaptive and corrective RAG with LangGraph, document relevance grading, conversational filler stripping, progressive query rewriting, and claim-by-claim grounding verification.

---

## 2. Architecture & Design Direction

### Visual Identity
- **Palette**: Deep charcoal and midnight navy backgrounds (`#0B0F17`, `#0F172A`, `#111827`) with restrained indigo (`#6366F1`), violet (`#8B5CF6`), and cyan (`#06B6D4`) accents.
- **Typography**: Clean typography using Inter for UI text and JetBrains Mono for citations, code snippets, tokens, and offsets.
- **Borders & Elevation**: Subtle slate/zinc borders (`border-surface-border`), restrained transitions, and glow accents (`shadow-glow-primary`).
- **Responsive**: Fully responsive across mobile, tablet, and desktop viewports with collapsible navigation.

### Page Routes
1. **Public Landing Page (`/`)**: Hero section, core capabilities, architecture workflow, technology stack, and CTA buttons.
2. **Workspace Shell (`/app`)**: Collapsible left sidebar, real-time backend connection status pill, and responsive navigation.
3. **AI Chat (`/app/chat`)**: Main conversational interface with multiline textarea, routing mode controls, vector strategy controls, adaptive RAG toggle, inline citation cards with slide-over source preview, latency & model badges, and copy answer.
4. **Knowledge Base (`/app/knowledge`)**: Drag-and-drop document uploader with progress tracking, searchable indexed document catalog, chunk inspector modal, and document deletion.
5. **Retrieval Inspector (`/app/inspector`)**: Deep diagnostic workbench displaying selected route & confidence, visual LangGraph state machine trace graph, grounding & hallucination audit, query rewrite history, and unified cross-source evidence grid.
6. **System Dashboard (`/app/dashboard`)**: Operational health for persistent Qdrant vector storage, embedding engine, and local Ollama LLM, plus latency distribution charts.
7. **Settings (`/app/settings`)**: Configurable API base URL, default retrieval modes, adaptive RAG toggles, and hardware/model profile specs.

---

## 3. Technology Stack

- **Framework**: React 18 (`react`, `react-dom`)
- **Language**: TypeScript 5.7 (strict typing matching backend Pydantic schemas)
- **Build Tool**: Vite 6 (fast HMR and optimized production bundling)
- **Styling**: Tailwind CSS 3.4 with custom dark mode theme
- **Icons**: Lucide React
- **Routing**: React Router DOM 6
- **State Management**: Zustand 5 with `localStorage` persistence
- **HTTP Client**: Axios with centralized error normalization and request timeout guards
- **Charts**: Recharts 2.15 for latency and candidate distribution
- **Markdown**: `react-markdown` with `remark-gfm` for tables and code blocks

---

## 4. API Integration Mapping

All frontend types strictly map to backend schemas in `backend/app/schemas/`:

| Backend Endpoint | Method | Payload / Params | Frontend Service Method |
| :--- | :--- | :--- | :--- |
| `/api/v1/health` | `GET` | None | `healthService.checkHealth()` |
| `/api/v1/documents` | `GET` | None | `documentService.listDocuments()` |
| `/api/v1/documents/upload` | `POST` | `multipart/form-data` (`file`) | `documentService.uploadDocument(file)` |
| `/api/v1/documents/{doc_id}` | `GET` | Path parameter | `documentService.getDocumentChunks(docId)`|
| `/api/v1/documents/{doc_id}` | `DELETE`| Path parameter | `documentService.deleteDocument(docId)` |
| `/api/v1/chat` | `POST` | `ChatRequest` (JSON) | `chatService.sendMessage(request)` |

See [`../docs/frontend_api_mapping.md`](../docs/frontend_api_mapping.md) for the complete schema contract specification.

---

## 5. Local Development & Build Commands

### Prerequisites
- Node.js >= 18 (Tested on Node v22)
- npm >= 9

### Installation
```bash
cd frontend
npm install
```

### Environment Configuration
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Default configuration:
```env
VITE_API_BASE_URL=http://localhost:8000
```

### Start Development Server
```bash
npm run dev
```
The application will be accessible at: `http://localhost:5173/`

### Build for Production
```bash
npm run build
```
Generates optimized static assets in `dist/`.

### Preview Production Build
```bash
npm run preview
```
Previews the built production bundle at `http://localhost:4173/`.
