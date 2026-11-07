import React, { useState } from 'react';
import {
  FileText,
  Trash2,
  Eye,
  Search,
  RefreshCw,
  FolderOpen,
  Calendar,
  Layers,
} from 'lucide-react';
import { useKnowledgeStore } from '../../store/useKnowledgeStore';
import { DocumentDetail } from '../../types/api';
import { ConfirmDialog } from '../common/ConfirmDialog';
import { LoadingSkeleton } from '../common/LoadingSkeleton';

export const DocumentTable: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [deletingDoc, setDeletingDoc] = useState<DocumentDetail | null>(null);

  const {
    documents,
    isLoading,
    fetchDocuments,
    deleteDoc,
    inspectDocChunks,
  } = useKnowledgeStore();

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
  };

  const formatDate = (dateString: string): string => {
    try {
      const d = new Date(dateString);
      return d.toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
      });
    } catch {
      return dateString;
    }
  };

  const getFormatBadge = (fileType: string) => {
    const ext = fileType.toLowerCase().replace('.', '');
    const colorMap: Record<string, string> = {
      pdf: 'bg-rose-950/60 text-rose-300 border-rose-800/60',
      docx: 'bg-blue-950/60 text-blue-300 border-blue-800/60',
      txt: 'bg-slate-800/80 text-slate-300 border-slate-700/60',
      md: 'bg-emerald-950/60 text-emerald-300 border-emerald-800/60',
    };
    return colorMap[ext] || 'bg-slate-800 text-slate-300 border-slate-700';
  };

  const filteredDocs = documents.filter((doc) =>
    doc.filename.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleConfirmDelete = async () => {
    if (deletingDoc) {
      await deleteDoc(deletingDoc.doc_id);
      setDeletingDoc(null);
    }
  };

  return (
    <div className="space-y-4">
      {/* Search and Action Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Filter indexed documents..."
            className="w-full bg-surface-card border border-surface-border rounded-xl pl-9 pr-4 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
          />
        </div>

        <button
          onClick={() => fetchDocuments()}
          disabled={isLoading}
          className="inline-flex items-center justify-center gap-1.5 px-3 py-2 rounded-xl bg-surface-card hover:bg-surface-hover text-slate-300 text-xs font-medium border border-surface-border transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          <span>Refresh Catalog</span>
        </button>
      </div>

      {/* Table Container */}
      <div className="rounded-2xl border border-surface-border bg-surface-card/60 overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-surface/80 border-b border-surface-border text-slate-400 font-mono uppercase text-[11px]">
              <tr>
                <th className="py-3.5 px-4">Document</th>
                <th className="py-3.5 px-3">Format</th>
                <th className="py-3.5 px-3">Size</th>
                <th className="py-3.5 px-3">Pages</th>
                <th className="py-3.5 px-3">Chunks</th>
                <th className="py-3.5 px-3">Indexed On</th>
                <th className="py-3.5 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-surface-border/60">
              {isLoading && documents.length === 0 ? (
                <tr>
                  <td colSpan={7} className="p-8">
                    <LoadingSkeleton count={4} className="h-10" />
                  </td>
                </tr>
              ) : filteredDocs.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-16 text-center text-slate-400">
                    <FolderOpen className="w-8 h-8 mx-auto mb-2 text-slate-600" />
                    <p className="text-sm font-medium text-slate-300">
                      {documents.length === 0
                        ? 'No reference documents indexed yet'
                        : `No documents match "${searchTerm}"`}
                    </p>
                    <p className="text-xs text-slate-500 mt-1">
                      Upload a PDF, DOCX, TXT, or MD above to start indexing chunks into Qdrant.
                    </p>
                  </td>
                </tr>
              ) : (
                filteredDocs.map((doc) => (
                  <tr
                    key={doc.doc_id}
                    className="hover:bg-surface-hover/50 transition-colors group"
                  >
                    {/* Filename & UUID */}
                    <td className="py-3.5 px-4">
                      <div className="flex items-center gap-2.5">
                        <FileText className="w-4 h-4 text-indigo-400 shrink-0" />
                        <div className="min-w-0 max-w-xs">
                          <span className="font-semibold text-slate-200 truncate block group-hover:text-indigo-300 transition-colors">
                            {doc.filename}
                          </span>
                          <span className="text-[10px] text-slate-500 font-mono truncate block">
                            {doc.doc_id}
                          </span>
                        </div>
                      </div>
                    </td>

                    {/* Format Badge */}
                    <td className="py-3.5 px-3">
                      <span
                        className={`inline-block px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase border ${getFormatBadge(
                          doc.file_type
                        )}`}
                      >
                        {doc.file_type.replace('.', '')}
                      </span>
                    </td>

                    {/* Size */}
                    <td className="py-3.5 px-3 font-mono text-slate-300">
                      {formatFileSize(doc.file_size_bytes)}
                    </td>

                    {/* Pages */}
                    <td className="py-3.5 px-3 font-mono text-slate-300">
                      {doc.page_count}
                    </td>

                    {/* Chunks */}
                    <td className="py-3.5 px-3">
                      <span className="inline-flex items-center gap-1 font-mono text-indigo-300">
                        <Layers className="w-3 h-3 text-indigo-400" />
                        {doc.chunk_count}
                      </span>
                    </td>

                    {/* Ingestion Date */}
                    <td className="py-3.5 px-3 text-slate-400">
                      <div className="flex items-center gap-1.5">
                        <Calendar className="w-3 h-3 text-slate-500" />
                        <span>{formatDate(doc.created_at)}</span>
                      </div>
                    </td>

                    {/* Actions */}
                    <td className="py-3.5 px-4 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        <button
                          onClick={() => inspectDocChunks(doc)}
                          className="p-1.5 rounded-lg text-slate-400 hover:text-indigo-300 hover:bg-surface-hover transition-colors"
                          title="Inspect extracted chunks"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => setDeletingDoc(doc)}
                          className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-rose-950/20 transition-colors"
                          title="Delete document and chunks"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Table Footer */}
        {documents.length > 0 && (
          <div className="p-3 border-t border-surface-border bg-surface/50 text-[11px] text-slate-400 flex items-center justify-between">
            <span>
              Total: {filteredDocs.length} document{filteredDocs.length !== 1 ? 's' : ''} indexed
            </span>
            <span className="font-mono">Persistent Qdrant Vector Storage</span>
          </div>
        )}
      </div>

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={Boolean(deletingDoc)}
        title="Delete Indexed Document"
        message={`Are you sure you want to delete "${deletingDoc?.filename}"? This will remove all ${deletingDoc?.chunk_count} indexed chunks from persistent Qdrant vector storage and delete the stored file from disk.`}
        confirmLabel="Delete Document"
        isDestructive={true}
        onConfirm={handleConfirmDelete}
        onCancel={() => setDeletingDoc(null)}
      />
    </div>
  );
};
