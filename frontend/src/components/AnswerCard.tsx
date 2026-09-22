import React, { useState } from 'react';
import { QueryResponse } from '../types';
import {
  CheckCircle,
  BookOpen,
  ChevronDown,
  ChevronUp,
  FileText,
  Layers,
} from 'lucide-react';

interface AnswerCardProps {
  response: QueryResponse | null;
  error: string | null;
}

export const AnswerCard: React.FC<AnswerCardProps> = ({ response, error }) => {
  const [showEvidence, setShowEvidence] = useState(false);

  if (error) {
    return (
      <section className="card answer-card error-border">
        <div className="alert alert-danger">
          <strong>Analysis Error:</strong> {error}
        </div>
      </section>
    );
  }

  if (!response) {
    return null;
  }

  return (
    <section className="card answer-card">
      <div className="card-header">
        <div className="card-title-group">
          <CheckCircle size={20} className="text-success" />
          <h2 className="card-title">Analysis Answer</h2>
        </div>
      </div>

      <div className="answer-body">
        <p className="answer-text">{response.answer}</p>
      </div>

      {response.sources && response.sources.length > 0 && (
        <div className="sources-container">
          <div className="sources-header">
            <BookOpen size={16} className="text-primary" />
            <span className="sources-title">Cited Source Documents:</span>
          </div>
          <div className="sources-list">
            {response.sources.map((src, index) => (
              <div key={index} className="source-pill">
                <FileText size={14} className="text-muted" />
                <span className="source-doc">{src.document}</span>
                <span className="source-page">Page {src.page}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {response.context && response.context.length > 0 && (
        <div className="evidence-section">
          <button
            type="button"
            className="evidence-toggle-btn"
            onClick={() => setShowEvidence(!showEvidence)}
          >
            <div className="toggle-label">
              <Layers size={16} className="text-muted" />
              <span>
                Retrieved Context & Evidence ({response.context.length} chunks)
              </span>
            </div>
            {showEvidence ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>

          {showEvidence && (
            <div className="evidence-list">
              {response.context.map((ctx, idx) => (
                <div key={idx} className="evidence-chunk">
                  <div className="chunk-header">
                    <span className="chunk-badge">Chunk #{idx + 1}</span>
                    <span className="chunk-meta">
                      {ctx.document} • Page {ctx.page}
                    </span>
                  </div>
                  <pre className="chunk-content">{ctx.content}</pre>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </section>
  );
};
