import { apiClient } from './apiClient';
import {
  DocumentChunk,
  DocumentDeleteResponse,
  DocumentListResponse,
  IngestionResponse,
} from '../types/api';

export const documentService = {
  /**
   * List all documents currently indexed in the persistent Qdrant database.
   */
  async listDocuments(): Promise<DocumentListResponse> {
    const response = await apiClient.get<DocumentListResponse>('/api/v1/documents');
    return response.data;
  },

  /**
   * Upload and ingest a file (.pdf, .docx, .txt, .md).
   */
  async uploadDocument(
    file: File,
    onProgress?: (percent: number) => void
  ): Promise<IngestionResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiClient.post<IngestionResponse>(
      '/api/v1/documents/upload',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total && onProgress) {
            const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            onProgress(percent);
          }
        },
      }
    );
    return response.data;
  },

  /**
   * Retrieve all chunks and metadata for a specific document ID.
   */
  async getDocumentChunks(docId: string): Promise<DocumentChunk[]> {
    const response = await apiClient.get<DocumentChunk[]>(`/api/v1/documents/${encodeURIComponent(docId)}`);
    return response.data;
  },

  /**
   * Delete document chunks from vector storage and file from disk.
   */
  async deleteDocument(docId: string): Promise<DocumentDeleteResponse> {
    const response = await apiClient.delete<DocumentDeleteResponse>(`/api/v1/documents/${encodeURIComponent(docId)}`);
    return response.data;
  },
};
