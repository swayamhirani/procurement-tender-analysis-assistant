import React, { useEffect, useState, useCallback } from 'react';
import { api } from './services/api';
import { HealthResponse, DocumentInfo, QueryResponse } from './types';
import { DashboardHeader } from './components/DashboardHeader';
import { DocumentManager } from './components/DocumentManager';
import { QuerySection } from './components/QuerySection';
import { AnswerCard } from './components/AnswerCard';

export const App: React.FC = () => {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loadingHealth, setLoadingHealth] = useState<boolean>(true);
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [loadingDocs, setLoadingDocs] = useState<boolean>(true);
  const [indexing, setIndexing] = useState<boolean>(false);
  const [indexResult, setIndexResult] = useState<{ message: string; success: boolean } | null>(null);

  const [queryResponse, setQueryResponse] = useState<QueryResponse | null>(null);
  const [queryLoading, setQueryLoading] = useState<boolean>(false);
  const [queryError, setQueryError] = useState<string | null>(null);

  const fetchHealth = useCallback(async () => {
    setLoadingHealth(true);
    try {
      const data = await api.getHealth();
      setHealth(data);
    } catch {
      setHealth(null);
    } finally {
      setLoadingHealth(false);
    }
  }, []);

  const fetchDocuments = useCallback(async () => {
    setLoadingDocs(true);
    try {
      const data = await api.listDocuments();
      setDocuments(data.documents);
    } catch (err: unknown) {
      console.error('Failed to fetch documents:', err);
    } finally {
      setLoadingDocs(false);
    }
  }, []);

  useEffect(() => {
    fetchHealth();
    fetchDocuments();
  }, [fetchHealth, fetchDocuments]);

  const handleUpload = async (files: File[]) => {
    await api.uploadDocuments(files);
    await fetchDocuments();
    await fetchHealth();
  };

  const handleIndex = async () => {
    setIndexing(true);
    setIndexResult(null);
    try {
      const res = await api.indexDocuments();
      setIndexResult({
        message: `${res.message} (${res.documents_indexed} documents, ${res.chunks_indexed} chunks)`,
        success: true,
      });
      await fetchHealth();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Indexing failed';
      setIndexResult({
        message: msg,
        success: false,
      });
    } finally {
      setIndexing(false);
    }
  };

  const handleAsk = async (question: string) => {
    setQueryLoading(true);
    setQueryError(null);
    setQueryResponse(null);
    try {
      const res = await api.query(question);
      setQueryResponse(res);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error querying tender assistant';
      setQueryError(msg);
    } finally {
      setQueryLoading(false);
    }
  };

  return (
    <div className="app-container">
      <div className="app-wrapper">
        <DashboardHeader
          health={health}
          loading={loadingHealth}
          onRefreshHealth={fetchHealth}
        />

        <main className="main-content">
          <DocumentManager
            documents={documents}
            loadingDocs={loadingDocs}
            onUpload={handleUpload}
            onIndex={handleIndex}
            indexing={indexing}
            indexResult={indexResult}
          />

          <QuerySection
            onAsk={handleAsk}
            loading={queryLoading}
          />

          <AnswerCard
            response={queryResponse}
            error={queryError}
          />
        </main>

        <footer className="app-footer">
          <p>
            Procurement & Tender Analysis Assistant • Powered by LangChain, Google Gemini & ChromaDB
          </p>
        </footer>
      </div>
    </div>
  );
};

export default App;
