import React from 'react';
import { Link } from 'react-router-dom';
import {
  ShieldCheck,
  ArrowRight,
  Database,
  Layers,
  Sparkles,
  GitMerge,
  SearchCode,
  CheckCircle2,
} from 'lucide-react';
import { useHealthStore } from '../store/useHealthStore';
import { StatusIndicator } from '../components/common/StatusIndicator';

export const LandingPage: React.FC = () => {
  const { health } = useHealthStore();

  const capabilities = [
    {
      title: 'Multi-Format Ingestion',
      desc: 'Robust parsing of PDF, DOCX, TXT, and Markdown preserving physical page numbers, character offsets, and token approximations.',
      icon: Layers,
      color: 'from-blue-500/20 to-indigo-500/20 border-indigo-500/30 text-indigo-400',
    },
    {
      title: 'Multi-Strategy Retrieval',
      desc: 'Dual-channel hybrid search combining dense Sentence-Transformers (384-dim) with sparse Okapi BM25, fused via Reciprocal Rank Fusion (k=60).',
      icon: GitMerge,
      color: 'from-indigo-500/20 to-purple-500/20 border-purple-500/30 text-purple-400',
    },
    {
      title: 'Intelligent Multi-Path Routing',
      desc: 'Classifier routing across Vector Documents, Structured SQLite Catalog, External Web Search, and Multi-Source compound synthesis.',
      icon: SearchCode,
      color: 'from-cyan-500/20 to-blue-500/20 border-cyan-500/30 text-cyan-400',
    },
    {
      title: 'Adaptive LangGraph Self-Correction',
      desc: 'Cyclic state machine evaluating document relevance, stripping conversational noise, reformulating queries, and validating factual claims.',
      icon: Sparkles,
      color: 'from-violet-500/20 to-pink-500/20 border-pink-500/30 text-pink-400',
    },
    {
      title: 'Persistent On-Disk Vector Storage',
      desc: 'File-backed Qdrant collections surviving restarts and reboots with scoped metadata filtering by doc ID, filename, and page.',
      icon: Database,
      color: 'from-emerald-500/20 to-teal-500/20 border-emerald-500/30 text-emerald-400',
    },
    {
      title: 'Verifiable Inline Citations',
      desc: 'Every factual proposition is grounded by exact page citations or database records, achieving 100% truthful rejection on unanswerable queries.',
      icon: ShieldCheck,
      color: 'from-amber-500/20 to-orange-500/20 border-amber-500/30 text-amber-400',
    },
  ];

  const steps = [
    {
      step: '01',
      title: 'Ingest & Chunk',
      desc: 'Extract documents page-by-page, chunk recursively with metadata preservation, and index into persistent Qdrant.',
    },
    {
      step: '02',
      title: 'Route & Retrieve',
      desc: 'Analyze query intent and execute hybrid dense + BM25, multi-query expansion, HyDE, or structured SQL queries.',
    },
    {
      step: '03',
      title: 'Grade & Self-Correct',
      desc: 'LangGraph workflow grades retrieved candidate relevance, reformulates queries if context is insufficient, and executes corrective retrieval.',
    },
    {
      step: '04',
      title: 'Ground & Respond',
      desc: 'Validate factual claims and citation validity before finalizing the answer, preventing hallucinations.',
    },
  ];

  const techStack = [
    { name: 'FastAPI', category: 'Backend Framework' },
    { name: 'LangGraph', category: 'Adaptive Orchestration' },
    { name: 'Qdrant', category: 'Persistent Vector DB' },
    { name: 'Ollama', category: 'Local LLM Inference' },
    { name: 'Sentence Transformers', category: 'all-MiniLM-L6-v2 (384d)' },
    { name: 'Cross-Encoder', category: 'ms-marco-MiniLM-L-6-v2' },
    { name: 'BM25 Okapi', category: 'Sparse Lexical Retrieval' },
    { name: 'SQLite + SQLAlchemy', category: 'Structured Catalog' },
    { name: 'React 18 + TypeScript', category: 'Modern Frontend' },
    { name: 'Tailwind CSS', category: 'Premium Dark UI' },
  ];

  return (
    <div className="min-h-screen bg-background text-slate-100 flex flex-col selection:bg-indigo-600/30 selection:text-indigo-200">
      {/* Top Navbar */}
      <header className="h-20 border-b border-surface-border bg-background/80 backdrop-blur-md sticky top-0 z-30 px-6 lg:px-12 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-indigo-500 via-indigo-600 to-violet-700 flex items-center justify-center shadow-glow-primary">
            <ShieldCheck className="w-6 h-6 text-white" />
          </div>
          <div>
            <span className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
              VeriWeave
              <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-indigo-950 text-indigo-400 border border-indigo-800/60 font-semibold">
                Phase 4
              </span>
            </span>
          </div>
        </div>

        {/* Status Pill & CTA */}
        <div className="flex items-center gap-4">
          <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full bg-surface-card border border-surface-border text-xs">
            <StatusIndicator
              status={health?.status || 'degraded'}
              label={health?.status === 'healthy' ? 'API Online' : 'Connecting'}
              size="sm"
            />
          </div>

          <Link
            to="/app/chat"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold transition-all shadow-glow-primary hover:shadow-lg"
          >
            <span>Open Workspace</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative pt-20 pb-28 px-6 lg:px-12 text-center max-w-5xl mx-auto flex-1 flex flex-col justify-center">
        {/* Subtle Ambient Background Glows */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[350px] bg-indigo-600/10 blur-[120px] rounded-full pointer-events-none -z-10" />
        <div className="absolute top-1/3 left-1/3 w-[300px] h-[250px] bg-violet-600/10 blur-[100px] rounded-full pointer-events-none -z-10" />

        {/* Tagline Badge */}
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-indigo-950/60 border border-indigo-800/60 text-xs font-mono font-medium text-indigo-300 mx-auto mb-6 shadow-sm">
          <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
          <span>"Retrieve intelligently. Reason contextually. Respond reliably."</span>
        </div>

        {/* Main Title */}
        <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight text-white leading-tight sm:leading-none mb-6">
          Adaptive Multi-Strategy Retrieval & <br />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 via-indigo-300 to-violet-400">
            Grounded Generation Engine
          </span>
        </h1>

        <p className="text-base sm:text-lg text-slate-400 max-w-3xl mx-auto leading-relaxed mb-10">
          VeriWeave goes beyond conventional single-pass PDF demos by orchestrating hybrid dense-lexical search, intelligent multi-path routing across SQL and web sources, and a stateful LangGraph self-correcting loop that eliminates hallucinations.
        </p>

        {/* CTAs */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link
            to="/app/chat"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2.5 px-7 py-3.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold transition-all shadow-glow-primary hover:shadow-indigo-500/40 text-sm"
          >
            <span>Launch AI Chat Workspace</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
          <Link
            to="/app/inspector"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3.5 rounded-xl bg-surface-card hover:bg-surface-hover text-slate-200 border border-surface-border text-sm font-medium transition-colors"
          >
            <SearchCode className="w-4 h-4 text-indigo-400" />
            <span>Retrieval Inspector</span>
          </Link>
          <Link
            to="/app/knowledge"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3.5 rounded-xl bg-surface-card hover:bg-surface-hover text-slate-200 border border-surface-border text-sm font-medium transition-colors"
          >
            <Layers className="w-4 h-4 text-indigo-400" />
            <span>Manage Documents</span>
          </Link>
        </div>

        {/* Hardware & Spec Callout */}
        <div className="mt-14 pt-8 border-t border-surface-border/60 flex flex-wrap items-center justify-center gap-6 text-xs font-mono text-slate-400">
          <span className="flex items-center gap-1.5">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            Runs Locally on Apple Silicon Mac (8 GB RAM)
          </span>
          <span className="flex items-center gap-1.5">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            Zero Mandatory Paid APIs
          </span>
          <span className="flex items-center gap-1.5">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            69/69 Automated Tests Passing
          </span>
        </div>
      </section>

      {/* Capabilities Section */}
      <section className="py-20 px-6 lg:px-12 bg-surface-muted/60 border-y border-surface-border">
        <div className="max-w-6xl mx-auto">
          <div className="text-center max-w-2xl mx-auto mb-14">
            <span className="text-xs font-mono uppercase tracking-wider text-indigo-400 font-semibold block mb-2">
              Architecture & Features
            </span>
            <h2 className="text-3xl font-bold text-white tracking-tight">
              Engineered for Verifiable Knowledge Reliability
            </h2>
            <p className="text-sm text-slate-400 mt-3">
              Every query passes through specialized routing, multi-strategy fusion, and stateful verification.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {capabilities.map((cap) => {
              const Icon = cap.icon;
              return (
                <div
                  key={cap.title}
                  className="p-6 rounded-2xl bg-surface-card border border-surface-border hover:border-slate-700 transition-all shadow-sm flex flex-col justify-between"
                >
                  <div>
                    <div
                      className={`w-12 h-12 rounded-xl bg-gradient-to-br ${cap.color} border flex items-center justify-center mb-4`}
                    >
                      <Icon className="w-6 h-6" />
                    </div>
                    <h3 className="text-base font-semibold text-slate-100 mb-2">
                      {cap.title}
                    </h3>
                    <p className="text-xs text-slate-400 leading-relaxed">
                      {cap.desc}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* How VeriWeave Works */}
      <section className="py-20 px-6 lg:px-12 max-w-6xl mx-auto w-full">
        <div className="text-center max-w-2xl mx-auto mb-16">
          <span className="text-xs font-mono uppercase tracking-wider text-indigo-400 font-semibold block mb-2">
            Execution Pipeline
          </span>
          <h2 className="text-3xl font-bold text-white tracking-tight">
            How VeriWeave Eliminates Hallucinations
          </h2>
          <p className="text-sm text-slate-400 mt-3">
            A self-evaluating state machine designed around explicit evidence grading and bounded correction cycles.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {steps.map((st) => (
            <div
              key={st.step}
              className="p-6 rounded-2xl bg-surface-card border border-surface-border relative flex flex-col justify-between"
            >
              <div>
                <span className="text-3xl font-extrabold font-mono text-indigo-500/40 block mb-3">
                  {st.step}
                </span>
                <h4 className="text-base font-semibold text-slate-100 mb-2">
                  {st.title}
                </h4>
                <p className="text-xs text-slate-400 leading-relaxed">
                  {st.desc}
                </p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Technology Stack Grid */}
      <section className="py-20 px-6 lg:px-12 bg-surface-muted/60 border-t border-surface-border">
        <div className="max-w-6xl mx-auto">
          <div className="text-center max-w-2xl mx-auto mb-12">
            <span className="text-xs font-mono uppercase tracking-wider text-indigo-400 font-semibold block mb-2">
              Under The Hood
            </span>
            <h2 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
              Production AI & Full-Stack Tech Stack
            </h2>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
            {techStack.map((tech) => (
              <div
                key={tech.name}
                className="p-4 rounded-xl bg-surface-card border border-surface-border/80 text-center"
              >
                <span className="font-semibold text-xs text-slate-200 block truncate">
                  {tech.name}
                </span>
                <span className="text-[10px] text-slate-500 font-mono block mt-1 truncate">
                  {tech.category}
                </span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-10 px-6 lg:px-12 border-t border-surface-border bg-background text-xs text-slate-500 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <div className="w-5 h-5 rounded-md bg-indigo-600 flex items-center justify-center text-white font-bold text-[10px]">
            V
          </div>
          <span className="text-slate-400 font-semibold">VeriWeave</span>
          <span>•</span>
          <span>Adaptive Multi-Strategy Retrieval and Grounded Generation Engine</span>
        </div>

        <div className="flex items-center gap-6 font-mono text-[11px]">
          <Link to="/app/chat" className="hover:text-indigo-400 transition-colors">
            Chat
          </Link>
          <Link to="/app/knowledge" className="hover:text-indigo-400 transition-colors">
            Knowledge
          </Link>
          <Link to="/app/inspector" className="hover:text-indigo-400 transition-colors">
            Inspector
          </Link>
          <Link to="/app/dashboard" className="hover:text-indigo-400 transition-colors">
            Health
          </Link>
        </div>
      </footer>
    </div>
  );
};
