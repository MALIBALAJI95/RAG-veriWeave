import React, { useState, useRef } from 'react';
import { UploadCloud, AlertCircle, CheckCircle2, RotateCcw } from 'lucide-react';
import { useKnowledgeStore } from '../../store/useKnowledgeStore';

const ACCEPTED_EXTENSIONS = ['.pdf', '.docx', '.txt', '.md'];

export const DocumentUploader: React.FC = () => {
  const [isDragOver, setIsDragOver] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const { uploadFile, isUploading, uploadProgress, error, clearError } = useKnowledgeStore();

  const handleFileProcess = async (file: File) => {
    clearError();
    setSuccessMessage(null);

    const ext = `.${file.name.split('.').pop()?.toLowerCase()}`;
    if (!ACCEPTED_EXTENSIONS.includes(ext)) {
      alert(`Unsupported file format "${ext}". Supported: ${ACCEPTED_EXTENSIONS.join(', ')}`);
      return;
    }

    const success = await uploadFile(file);
    if (success) {
      setSuccessMessage(`Successfully ingested and indexed "${file.name}"`);
      setTimeout(() => setSuccessMessage(null), 4000);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (isUploading) return;

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileProcess(e.dataTransfer.files[0]);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFileProcess(e.target.files[0]);
    }
    // Reset file input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="space-y-3">
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragOver(true);
        }}
        onDragLeave={() => setIsDragOver(false)}
        onDrop={handleDrop}
        onClick={() => !isUploading && fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-2xl p-8 text-center transition-all cursor-pointer relative overflow-hidden ${
          isDragOver
            ? 'border-indigo-500 bg-indigo-950/20 shadow-glow-primary'
            : 'border-surface-border bg-surface-card/60 hover:bg-surface-card hover:border-slate-700'
        } ${isUploading ? 'pointer-events-none opacity-80' : ''}`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.docx,.txt,.md"
          onChange={handleFileInputChange}
          className="hidden"
        />

        <div className="flex flex-col items-center justify-center max-w-sm mx-auto">
          <div className="w-12 h-12 rounded-2xl bg-indigo-950/80 border border-indigo-800/60 flex items-center justify-center text-indigo-400 mb-3 shadow-inner">
            {isUploading ? (
              <RotateCcw className="w-6 h-6 animate-spin text-indigo-400" />
            ) : (
              <UploadCloud className="w-6 h-6" />
            )}
          </div>

          <h3 className="text-base font-semibold text-slate-100 mb-1">
            {isUploading ? 'Chunking and Indexing Document...' : 'Upload Reference Documents'}
          </h3>
          <p className="text-xs text-slate-400 mb-4 leading-relaxed">
            Drag and drop your file here, or click to browse. Text is automatically parsed, recursively chunked, embedded with Sentence-Transformers, and indexed in persistent Qdrant storage.
          </p>

          {/* Supported Format Pills */}
          <div className="flex items-center gap-2">
            {['PDF', 'DOCX', 'TXT', 'MD'].map((fmt) => (
              <span
                key={fmt}
                className="px-2 py-0.5 rounded text-[11px] font-mono font-medium bg-slate-800/90 text-slate-300 border border-slate-700/60"
              >
                .{fmt.toLowerCase()}
              </span>
            ))}
          </div>
        </div>

        {/* Upload Progress Bar */}
        {isUploading && (
          <div className="absolute inset-x-0 bottom-0 p-3 bg-surface/90 border-t border-surface-border">
            <div className="flex justify-between text-xs text-indigo-300 mb-1 font-mono">
              <span>Embedding & Storing Vectors</span>
              <span>{uploadProgress}%</span>
            </div>
            <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-indigo-500 rounded-full transition-all duration-200"
                style={{ width: `${uploadProgress}%` }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Success Notification */}
      {successMessage && (
        <div className="p-3 rounded-xl bg-emerald-950/40 border border-emerald-900/60 text-emerald-300 text-xs flex items-center gap-2 animate-fade-in">
          <CheckCircle2 className="w-4 h-4 shrink-0" />
          <span>{successMessage}</span>
        </div>
      )}

      {/* Error Notification */}
      {error && (
        <div className="p-3 rounded-xl bg-rose-950/40 border border-rose-900/60 text-rose-300 text-xs flex items-center gap-2 animate-fade-in">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
};
