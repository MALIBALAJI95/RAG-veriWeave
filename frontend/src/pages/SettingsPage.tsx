import React, { useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { Header } from '../components/common/Header';
import { useSettingsStore } from '../store/useSettingsStore';
import { useHealthStore } from '../store/useHealthStore';
import { RetrievalStrategy, RoutingMode } from '../types/api';
import {
  Save,
  RotateCcw,
  CheckCircle2,
  Server,
  Sparkles,
  HardDrive,
} from 'lucide-react';

interface OutletContextType {
  onMobileMenuOpen: () => void;
}

export const SettingsPage: React.FC = () => {
  const { onMobileMenuOpen } = useOutletContext<OutletContextType>();
  const settings = useSettingsStore();
  const { fetchHealth } = useHealthStore();

  const [apiBaseUrl, setApiBaseUrl] = useState(settings.apiBaseUrl);
  const [defaultRoutingMode, setDefaultRoutingMode] = useState<RoutingMode>(settings.defaultRoutingMode);
  const [defaultRetrievalStrategy, setDefaultRetrievalStrategy] = useState<RetrievalStrategy>(settings.defaultRetrievalStrategy);
  const [defaultAdaptive, setDefaultAdaptive] = useState(settings.defaultAdaptive);
  const [defaultTopK, setDefaultTopK] = useState(settings.defaultTopK);
  const [savedToast, setSavedToast] = useState(false);
  const [testingConnection, setTestingConnection] = useState(false);

  const handleSave = () => {
    settings.setApiBaseUrl(apiBaseUrl);
    settings.setDefaultRoutingMode(defaultRoutingMode);
    settings.setDefaultRetrievalStrategy(defaultRetrievalStrategy);
    settings.setDefaultAdaptive(defaultAdaptive);
    settings.setDefaultTopK(defaultTopK);

    setSavedToast(true);
    setTimeout(() => setSavedToast(false), 3000);
  };

  const handleTestConnection = async () => {
    setTestingConnection(true);
    await fetchHealth();
    setTestingConnection(false);
  };

  const handleReset = () => {
    settings.resetDefaults();
    setApiBaseUrl('http://localhost:8000');
    setDefaultRoutingMode('auto');
    setDefaultRetrievalStrategy('hybrid');
    setDefaultAdaptive(true);
    setDefaultTopK(4);
    setSavedToast(true);
    setTimeout(() => setSavedToast(false), 3000);
  };

  return (
    <div className="flex-1 flex flex-col h-full min-w-0 bg-background overflow-hidden">
      <Header
        title="Settings & Configuration"
        subtitle="Configure backend connection, default retrieval strategies, and local model runtime"
        onMobileMenuOpen={onMobileMenuOpen}
      />

      <div className="flex-1 overflow-y-auto p-4 md:p-8 space-y-6">
        <div className="max-w-4xl mx-auto space-y-6">
          {/* Toast Notification */}
          {savedToast && (
            <div className="p-4 rounded-xl bg-emerald-950/80 border border-emerald-800 text-emerald-300 text-xs flex items-center gap-2 animate-fade-in shadow-lg">
              <CheckCircle2 className="w-4 h-4 shrink-0" />
              <span>Settings successfully saved and persisted to local storage.</span>
            </div>
          )}

          {/* Section 1: Backend Connection */}
          <div className="p-6 rounded-2xl bg-surface-card border border-surface-border shadow-sm space-y-4">
            <div className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-xl bg-indigo-950/80 border border-indigo-800/60 flex items-center justify-center text-indigo-400">
                <Server className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-semibold text-slate-100">
                  Backend API Connection
                </h3>
                <p className="text-xs text-slate-400">
                  Configure the FastAPI endpoint URL for chat and document ingestion
                </p>
              </div>
            </div>

            <div className="space-y-3 pt-2">
              <div>
                <label className="text-xs font-mono text-slate-400 block mb-1">
                  API Base URL (VITE_API_BASE_URL)
                </label>
                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    value={apiBaseUrl}
                    onChange={(e) => setApiBaseUrl(e.target.value)}
                    placeholder="http://localhost:8000"
                    className="flex-1 bg-surface border border-surface-border rounded-xl px-4 py-2.5 text-xs text-slate-200 font-mono focus:outline-none focus:border-indigo-500"
                  />
                  <button
                    onClick={handleTestConnection}
                    disabled={testingConnection}
                    className="px-4 py-2.5 bg-surface hover:bg-surface-hover text-slate-300 text-xs font-semibold rounded-xl border border-surface-border transition-colors disabled:opacity-50 shrink-0"
                  >
                    {testingConnection ? 'Testing...' : 'Test Connection'}
                  </button>
                </div>
                <span className="text-[11px] text-slate-500 mt-1 block">
                  Default: http://localhost:8000 (standard local FastAPI port)
                </span>
              </div>
            </div>
          </div>

          {/* Section 2: Retrieval Defaults */}
          <div className="p-6 rounded-2xl bg-surface-card border border-surface-border shadow-sm space-y-4">
            <div className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-xl bg-violet-950/80 border border-violet-800/60 flex items-center justify-center text-violet-400">
                <Sparkles className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-semibold text-slate-100">
                  Retrieval & Adaptive RAG Defaults
                </h3>
                <p className="text-xs text-slate-400">
                  Default parameters automatically populated in AI Chat
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2 text-xs">
              <div>
                <label className="text-slate-400 block mb-1 font-medium">
                  Default Routing Mode
                </label>
                <select
                  value={defaultRoutingMode}
                  onChange={(e) => setDefaultRoutingMode(e.target.value as RoutingMode)}
                  className="w-full bg-surface border border-surface-border rounded-xl px-3 py-2 text-slate-200 text-xs focus:outline-none focus:border-indigo-500"
                >
                  <option value="auto">Auto (Intelligent Classifier)</option>
                  <option value="document_only">Vector Documents Only</option>
                  <option value="sql_only">Structured SQL Catalog Only</option>
                  <option value="web_only">External Web Search Only</option>
                  <option value="multi_source">Multi-Source Synthesis</option>
                </select>
              </div>

              <div>
                <label className="text-slate-400 block mb-1 font-medium">
                  Default Vector Strategy
                </label>
                <select
                  value={defaultRetrievalStrategy}
                  onChange={(e) => setDefaultRetrievalStrategy(e.target.value as RetrievalStrategy)}
                  className="w-full bg-surface border border-surface-border rounded-xl px-3 py-2 text-slate-200 text-xs focus:outline-none focus:border-indigo-500"
                >
                  <option value="hybrid">Hybrid (Dense + BM25)</option>
                  <option value="hybrid_rerank">Hybrid + Cross-Encoder</option>
                  <option value="baseline">Baseline Dense Similarity</option>
                  <option value="multi_query">Multi-Query RRF</option>
                  <option value="hyde">HyDE Synthesis</option>
                  <option value="decomposition">Query Decomposition</option>
                  <option value="fusion">RAG Fusion</option>
                  <option value="rerank">Cross-Encoder Rerank</option>
                </select>
              </div>

              <div className="sm:col-span-2 flex items-center justify-between p-3.5 rounded-xl bg-surface/50 border border-surface-border">
                <div>
                  <span className="font-semibold text-slate-200 block">
                    Enable Adaptive RAG (LangGraph) by Default
                  </span>
                  <span className="text-[11px] text-slate-400">
                    Activates document relevance grading, query rewriting, and grounding validation
                  </span>
                </div>
                <input
                  type="checkbox"
                  checked={defaultAdaptive}
                  onChange={(e) => setDefaultAdaptive(e.target.checked)}
                  className="rounded accent-indigo-500 cursor-pointer w-4 h-4"
                />
              </div>

              <div className="sm:col-span-2">
                <div className="flex justify-between text-slate-400 mb-1">
                  <span>Default Top-K Candidates</span>
                  <span className="font-mono text-indigo-300 font-semibold">{defaultTopK}</span>
                </div>
                <input
                  type="range"
                  min={1}
                  max={10}
                  value={defaultTopK}
                  onChange={(e) => setDefaultTopK(Number(e.target.value))}
                  className="w-full accent-indigo-500 cursor-pointer"
                />
              </div>
            </div>
          </div>

          {/* Section 3: Model & Hardware Specs (Read-Only) */}
          <div className="p-6 rounded-2xl bg-surface-card border border-surface-border shadow-sm space-y-4">
            <div className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-xl bg-cyan-950/80 border border-cyan-800/60 flex items-center justify-center text-cyan-400">
                <HardDrive className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-semibold text-slate-100">
                  Hardware Profile & Model Specifications
                </h3>
                <p className="text-xs text-slate-400">
                  Local system configuration adhering to the 8 GB Apple Silicon Mac profile
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs font-mono pt-2">
              <div className="p-3 rounded-xl bg-surface/50 border border-surface-border">
                <span className="text-[10px] text-slate-500 uppercase block">Embedding Model</span>
                <span className="text-slate-200 font-semibold">sentence-transformers/all-MiniLM-L6-v2</span>
                <span className="text-[10px] text-indigo-400 block mt-0.5">384 Dimensions (CPU/MPS)</span>
              </div>

              <div className="p-3 rounded-xl bg-surface/50 border border-surface-border">
                <span className="text-[10px] text-slate-500 uppercase block">Cross-Encoder Reranker</span>
                <span className="text-slate-200 font-semibold">cross-encoder/ms-marco-MiniLM-L-6-v2</span>
                <span className="text-[10px] text-indigo-400 block mt-0.5">Joint Attention Scoring</span>
              </div>

              <div className="p-3 rounded-xl bg-surface/50 border border-surface-border">
                <span className="text-[10px] text-slate-500 uppercase block">Vector Database</span>
                <span className="text-slate-200 font-semibold">Qdrant (Persistent Disk)</span>
                <span className="text-[10px] text-indigo-400 block mt-0.5">./data/qdrant_storage</span>
              </div>

              <div className="p-3 rounded-xl bg-surface/50 border border-surface-border">
                <span className="text-[10px] text-slate-500 uppercase block">Structured Database</span>
                <span className="text-slate-200 font-semibold">SQLite + SQLAlchemy Catalog</span>
                <span className="text-[10px] text-indigo-400 block mt-0.5">./data/veriweave.db</span>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center justify-between pt-4">
            <button
              onClick={handleReset}
              className="inline-flex items-center gap-1.5 px-4 py-2.5 rounded-xl text-xs font-semibold text-slate-400 hover:text-slate-200 hover:bg-surface-hover border border-surface-border transition-colors"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Reset to Defaults</span>
            </button>

            <button
              onClick={handleSave}
              className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition-all shadow-sm"
            >
              <Save className="w-4 h-4" />
              <span>Save Changes</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
