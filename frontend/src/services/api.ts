import {
  HealthResponse,
  DocumentListResponse,
  DocumentUploadResponse,
  IndexResponse,
  QueryResponse,
} from '../types';

const API_BASE = ''; // Uses Vite proxy when running dev server, or direct origin

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorDetail = `Request failed with status ${res.status}`;
    try {
      const errorJson = await res.json();
      if (errorJson && errorJson.detail) {
        errorDetail = typeof errorJson.detail === 'string'
          ? errorJson.detail
          : JSON.stringify(errorJson.detail);
      }
    } catch {
      // Fallback to status text
      if (res.statusText) {
        errorDetail = res.statusText;
      }
    }
    throw new Error(errorDetail);
  }
  return res.json() as Promise<T>;
}

export const api = {
  async getHealth(): Promise<HealthResponse> {
    try {
      const res = await fetch(`${API_BASE}/health`);
      return await handleResponse<HealthResponse>(res);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Backend unreachable';
      throw new Error(message);
    }
  },

  async listDocuments(): Promise<DocumentListResponse> {
    const res = await fetch(`${API_BASE}/api/documents`);
    return handleResponse<DocumentListResponse>(res);
  },

  async uploadDocuments(files: File[]): Promise<DocumentUploadResponse> {
    const formData = new FormData();
    for (const file of files) {
      formData.append('files', file);
    }
    const res = await fetch(`${API_BASE}/api/documents/upload`, {
      method: 'POST',
      body: formData,
    });
    return handleResponse<DocumentUploadResponse>(res);
  },

  async indexDocuments(): Promise<IndexResponse> {
    const res = await fetch(`${API_BASE}/api/documents/index`, {
      method: 'POST',
    });
    return handleResponse<IndexResponse>(res);
  },

  async query(question: string): Promise<QueryResponse> {
    const res = await fetch(`${API_BASE}/api/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ question }),
    });
    return handleResponse<QueryResponse>(res);
  },
};
