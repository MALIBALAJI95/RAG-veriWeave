import React, { useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import { Header } from '../components/common/Header';
import { DocumentUploader } from '../components/knowledge/DocumentUploader';
import { DocumentTable } from '../components/knowledge/DocumentTable';
import { ChunkInspectorModal } from '../components/knowledge/ChunkInspectorModal';
import { useKnowledgeStore } from '../store/useKnowledgeStore';
import { Database, FolderGit2, Layers } from 'lucide-react';

interface OutletContextType {
  onMobileMenuOpen: () => void;
}

export const KnowledgeBasePage: React.FC = () => {
  const { onMobileMenuOpen } = useOutletContext<OutletContextType>();
  const { fetchDocuments, total, documents } = useKnowledgeStore();

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  const totalChunks = documents.reduce((acc, doc) => acc + (doc.chunk_count || 0), 0);

  return (
    <div className="flex-1 flex flex-col h-full min-w-0 bg-background overflow-hidden">
      <Header
        title="Knowledge Base"
        subtitle="Manage uploaded reference files, extracted chunks, and Qdrant vector indexing"
        onMobileMenuOpen={onMobileMenuOpen}
      />

      <div className="flex-1 overflow-y-auto p-4 md:p-8 space-y-6">
        <div className="max-w-6xl mx-auto space-y-6">
          {/* Quick Metrics Banner */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="p-4 rounded-2xl bg-surface-card border border-surface-border flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-indigo-950/80 border border-indigo-800/60 flex items-center justify-center text-indigo-400 shrink-0">
                <FolderGit2 className="w-5 h-5" />
              </div>
              <div>
                <span className="text-[11px] uppercase font-mono text-slate-400">
                  Indexed Documents
                </span>
                <p className="text-xl font-bold font-mono text-slate-100">{total}</p>
              </div>
            </div>

            <div className="p-4 rounded-2xl bg-surface-card border border-surface-border flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-violet-950/80 border border-violet-800/60 flex items-center justify-center text-violet-400 shrink-0">
                <Layers className="w-5 h-5" />
              </div>
              <div>
                <span className="text-[11px] uppercase font-mono text-slate-400">
                  Total Extracted Chunks
                </span>
                <p className="text-xl font-bold font-mono text-slate-100">{totalChunks}</p>
              </div>
            </div>

            <div className="p-4 rounded-2xl bg-surface-card border border-surface-border flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-emerald-950/80 border border-emerald-800/60 flex items-center justify-center text-emerald-400 shrink-0">
                <Database className="w-5 h-5" />
              </div>
              <div>
                <span className="text-[11px] uppercase font-mono text-slate-400">
                  Persistent Storage
                </span>
                <p className="text-xl font-bold font-mono text-emerald-400">Qdrant Disk</p>
              </div>
            </div>
          </div>

          {/* Document Ingestion Zone */}
          <DocumentUploader />

          {/* Document Catalog Table */}
          <DocumentTable />
        </div>
      </div>

      {/* Chunk Inspector Modal */}
      <ChunkInspectorModal />
    </div>
  );
};
