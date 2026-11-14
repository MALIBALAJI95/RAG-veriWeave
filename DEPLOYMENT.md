# VeriWeave Cloud Deployment Guide

> **Tagline:** Retrieve intelligently. Reason contextually. Respond reliably.

This guide provides step-by-step instructions for deploying **VeriWeave** as a 100% cloud-hosted application with zero dependence on local development machines, local servers, or network tunnels.

All cloud services utilized operate within generous **free tiers requiring no credit card or paid subscriptions**.

---

## 1. Cloud Architecture Overview

```
                                  +-----------------------------+
                                  |     User Browser Client     |
                                  +--------------+--------------+
                                                 |
                                                 | HTTPS
                                                 v
                       +-------------------------------------------------+
                       |             Vercel Frontend (SPA)              |
                       |          React 18 + Vite + TypeScript           |
                       |       https://veriweave.vercel.app              |
                       +-------------------------+-----------------------+
                                                 |
                                                 | REST API Calls (CORS enabled)
                                                 v
                       +-------------------------------------------------+
                       |             Render Backend API                  |
                       |         FastAPI + LangGraph + Uvicorn           |
                       |       https://veriweave-api.onrender.com        |
                       +-------+--------------------+--------------------+
                               |                    |
             Vector Search &   |                    | Hosted LLM &
             SQL Metadata      |                    | Embeddings
                               v                    v
+---------------------------------------+  +---------------------------------------+
|          Supabase Cloud DB            |  |         Cloudflare Workers AI         |
|  - PostgreSQL 15+ with pgvector       |  |  - @cf/meta/llama-3.2-1b-instruct    |
|  - 384-dim HNSW Vector Cosine Index   |  |  - @cf/baai/bge-small-en-v1.5         |
|  - Document blob & chunk persistence  |  |  - 10,000 free neurons / day          |
+---------------------------------------+  +---------------------------------------+
```

---

## 2. Cloud Service Allocations & Free Tier Limits

| Component | Cloud Platform | Role | Free Tier Allowance |
|---|---|---|---|
| **Frontend** | **Vercel** | React 18 + Vite static single-page application | 100 GB bandwidth/month, unlimited automated git preview deployments |
| **Backend API** | **Render** | FastAPI, LangGraph adaptive workflows, routing orchestrator | 750 free instance hours/month, automatic HTTPS |
| **Vector & SQL DB** | **Supabase** | PostgreSQL with `pgvector` extension and table persistence | 500 MB database storage, 2 free active projects |
| **Hosted LLM & Embeddings** | **Cloudflare Workers AI** | Hosted Llama 3.2 1B text generation and BGE Small embeddings | 10,000 free neurons per day, zero cold start overhead |

---

## 3. Step-by-Step Deployment Instructions

### Step 1: Supabase Database Setup

1. Create a free account at [supabase.com](https://supabase.com).
2. Create a new project named `veriweave-db`.
3. Open the **SQL Editor** tab from the left sidebar.
4. Paste and execute the contents of [`supabase/schema.sql`](file:///Users/balajimali/Developer/DataScience/RAG-veriWeave/supabase/schema.sql):
   - Enables `vector` extension.
   - Creates `veriweave_documents` table with 384-dimensional HNSW cosine index.
   - Creates `documents`, `chunks`, and `document_blobs` tables.
5. In Supabase, navigate to **Project Settings** $\rightarrow$ **Database** $\rightarrow$ **Connection parameters**.
6. Copy the **URI** connection string:
   ```
   postgresql://postgres.[PROJECT-REF]:[YOUR-PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres?sslmode=require
   ```

---

### Step 2: Cloudflare Workers AI Setup (Optional for Hosted LLM)

1. Sign up for a free account at [dash.cloudflare.com](https://dash.cloudflare.com).
2. Go to **AI** $\rightarrow$ **Workers AI**.
3. Under **Overview**, copy your **Account ID**.
4. Go to **My Profile** $\rightarrow$ **API Tokens** $\rightarrow$ **Create Token** $\rightarrow$ choose the **Workers AI Read** template.
5. Copy the generated API token.

*(Note: If Cloudflare credentials are omitted, VeriWeave automatically falls back to its deterministic grounded extractive generator without crashing).*

---

### Step 3: Render Backend Deployment

1. Sign in to [render.com](https://render.com) using your GitHub account (`MALIBALAJI95`).
2. Click **New +** $\rightarrow$ **Blueprint** (or connect repository directly):
   - Select repository: `https://github.com/MALIBALAJI95/RAG-veriWeave`.
   - Render automatically reads the root [`render.yaml`](file:///Users/balajimali/Developer/DataScience/RAG-veriWeave/render.yaml) file.
3. Configure the following environment variables in the Render dashboard:
   - `SUPABASE_DB_URL`: *Your Supabase PostgreSQL URI from Step 1*
   - `VECTOR_STORAGE_BACKEND`: `pgvector`
   - `LLM_PROVIDER`: `cloudflare` (or `fallback`)
   - `CLOUDFLARE_ACCOUNT_ID`: *Your Cloudflare Account ID from Step 2*
   - `CLOUDFLARE_API_TOKEN`: *Your Cloudflare API Token from Step 2*
   - `CORS_ORIGINS`: `*`
4. Click **Apply**. Render will build and deploy the web service.
5. Once deployed, copy your public backend URL (e.g. `https://veriweave-api.onrender.com`).
6. Test your live health endpoint:
   ```bash
   curl https://veriweave-api.onrender.com/api/v1/health
   ```

---

### Step 4: Vercel Frontend Deployment

1. Sign in to [vercel.com](https://vercel.com) using your GitHub account (`MALIBALAJI95`).
2. Click **Add New...** $\rightarrow$ **Project**.
3. Select the `RAG-veriWeave` repository.
4. Configure project settings:
   - **Framework Preset:** `Vite`
   - **Root Directory:** Click `Edit` and select `frontend`
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
5. Under **Environment Variables**, add:
   - `VITE_API_BASE_URL`: *Your Render backend URL from Step 3* (e.g., `https://veriweave-api.onrender.com`)
6. Click **Deploy**. Vercel will build and publish your frontend within 60 seconds.
7. Your app is now live at `https://<your-project>.vercel.app`!

---

## 4. Ephemeral Container Persistence & Data Safety

In free cloud environments like Render, files saved to the local container disk are ephemeral (wiped on server restarts or spin-downs). VeriWeave protects against data loss through two cloud persistence mechanisms:

1. **pgvector Cloud Storage:** All document chunk text and 384-dimensional embeddings are stored directly in Supabase PostgreSQL tables (`veriweave_documents`), surviving indefinitely.
2. **Database Blob Synchronization:** Uploaded file bytes and metadata are persisted in Supabase `document_blobs` and `documents` tables. When Render restarts, all document catalogs, chunk counts, search indexes, and citations remain completely intact.

---

## 5. Verification Checklist

- [x] **Health Check:** `GET /api/v1/health` reports status `ok` for vector storage and embedding engine.
- [x] **Document Ingestion:** `POST /api/v1/documents/upload` accepts PDF, DOCX, TXT, or MD files, extracts pages, chunks text, generates embeddings, and saves to pgvector.
- [x] **Document Listing:** `GET /api/v1/documents` lists documents with exact page counts and chunk statistics even after container restarts.
- [x] **Multi-Strategy Chat:** `POST /api/v1/chat` executes hybrid, BM25, Multi-Query, and HyDE retrieval with citations.
- [x] **Intelligent Routing:** Directs questions to vector documents, structured SQL catalog queries, or web search.
- [x] **LangGraph Adaptive RAG:** Evaluates document relevance, performs query rewrites, and validates grounding.
- [x] **Frontend UI:** All 7 pages (`/`, `/app/chat`, `/app/knowledge`, `/app/inspector`, `/app/dashboard`, `/app/settings`) render with zero console errors and communicate seamlessly with the backend.
