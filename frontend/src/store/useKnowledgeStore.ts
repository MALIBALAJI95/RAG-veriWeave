import { create } from 'zustand';
import { DocumentChunk, DocumentDetail } from '../types/api';
import { documentService } from '../services/documentService';
import { extractErrorMessage } from '../services/apiClient';

interface KnowledgeState {
  documents: DocumentDetail[];
  total: number;
  isLoading: boolean;
  isUploading: boolean;
  uploadProgress: number;
  error: string | null;
  selectedDoc: DocumentDetail | null;
  selectedDocChunks: DocumentChunk[];
  isLoadingChunks: boolean;

  // Actions
  fetchDocuments: () => Promise<void>;
  uploadFile: (file: File) => Promise<boolean>;
  deleteDoc: (docId: string) => Promise<boolean>;
  inspectDocChunks: (doc: DocumentDetail) => Promise<void>;
  closeInspector: () => void;
  clearError: () => void;
}

export const useKnowledgeStore = create<KnowledgeState>((set) => ({
  documents: [],
  total: 0,
  isLoading: false,
  isUploading: false,
  uploadProgress: 0,
  error: null,
  selectedDoc: null,
  selectedDocChunks: [],
  isLoadingChunks: false,

  fetchDocuments: async () => {
    set({ isLoading: true, error: null });
    try {
      const data = await documentService.listDocuments();
      set({ documents: data.documents, total: data.total, isLoading: false });
    } catch (err) {
      set({ error: extractErrorMessage(err), isLoading: false });
    }
  },

  uploadFile: async (file: File) => {
    set({ isUploading: true, uploadProgress: 0, error: null });
    try {
      await documentService.uploadDocument(file, (percent) => {
        set({ uploadProgress: percent });
      });
      set({ isUploading: false, uploadProgress: 100 });
      // Refresh documents
      const data = await documentService.listDocuments();
      set({ documents: data.documents, total: data.total });
      return true;
    } catch (err) {
      set({ error: extractErrorMessage(err), isUploading: false, uploadProgress: 0 });
      return false;
    }
  },

  deleteDoc: async (docId: string) => {
    set({ error: null });
    try {
      await documentService.deleteDocument(docId);
      // Refresh documents
      const data = await documentService.listDocuments();
      set((state) => ({
        documents: data.documents,
        total: data.total,
        selectedDoc: state.selectedDoc?.doc_id === docId ? null : state.selectedDoc,
        selectedDocChunks: state.selectedDoc?.doc_id === docId ? [] : state.selectedDocChunks,
      }));
      return true;
    } catch (err) {
      set({ error: extractErrorMessage(err) });
      return false;
    }
  },

  inspectDocChunks: async (doc: DocumentDetail) => {
    set({ selectedDoc: doc, isLoadingChunks: true, error: null });
    try {
      const chunks = await documentService.getDocumentChunks(doc.doc_id);
      set({ selectedDocChunks: chunks, isLoadingChunks: false });
    } catch (err) {
      set({ error: extractErrorMessage(err), isLoadingChunks: false });
    }
  },

  closeInspector: () => set({ selectedDoc: null, selectedDocChunks: [] }),
  clearError: () => set({ error: null }),
}));
