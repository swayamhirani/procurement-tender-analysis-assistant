export interface HealthResponse {
  status: string;
  service: string;
  gemini_configured: boolean;
  documents_count: number;
  indexed: boolean;
  chroma_status: string;
}

export interface DocumentInfo {
  filename: string;
  size_bytes: number;
  modified_at: string;
}

export interface DocumentListResponse {
  total: number;
  documents: DocumentInfo[];
}

export interface DocumentUploadResponse {
  message: string;
  uploaded_files: DocumentInfo[];
}

export interface IndexResponse {
  success: boolean;
  message: string;
  documents_indexed: number;
  chunks_indexed: number;
}

export interface SourceItem {
  document: string;
  page: number | string;
}

export interface ContextChunk {
  document: string;
  page: number | string;
  content: string;
}

export interface QueryResponse {
  answer: string;
  sources: SourceItem[];
  context: ContextChunk[];
}
