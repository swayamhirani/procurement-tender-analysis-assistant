import React from 'react';
import { HealthResponse } from '../types';
import { FileText, CheckCircle2, AlertCircle, Database, RefreshCw } from 'lucide-react';

interface DashboardHeaderProps {
  health: HealthResponse | null;
  loading: boolean;
  onRefreshHealth: () => void;
}

export const DashboardHeader: React.FC<DashboardHeaderProps> = ({
  health,
  loading,
  onRefreshHealth,
}) => {
  const isHealthy = health?.status === 'ok';

  return (
    <header className="header-container">
      <div className="header-top">
        <div className="brand-group">
          <div className="brand-icon">
            <FileText size={26} color="#ffffff" />
          </div>
          <div>
            <h1 className="brand-title">Procurement & Tender Analysis Assistant</h1>
            <p className="brand-subtitle">
              Grounded AI analysis for procurement tenders, RFPs, and bid documents
            </p>
          </div>
        </div>

        <div className="status-group">
          <div className={`status-badge ${isHealthy ? 'badge-healthy' : 'badge-error'}`}>
            {isHealthy ? (
              <>
                <CheckCircle2 size={16} />
                <span>API Connected</span>
              </>
            ) : (
              <>
                <AlertCircle size={16} />
                <span>API Disconnected</span>
              </>
            )}
          </div>

          <button
            onClick={onRefreshHealth}
            disabled={loading}
            className="btn-icon"
            title="Refresh System Status"
          >
            <RefreshCw size={15} className={loading ? 'spin' : ''} />
          </button>
        </div>
      </div>

      <div className="metrics-strip">
        <div className="metric-item">
          <span className="metric-label">Stored Documents</span>
          <span className="metric-value">{health?.documents_count ?? 0} PDFs</span>
        </div>
        <div className="metric-divider" />
        <div className="metric-item">
          <span className="metric-label">Vector Store</span>
          <span className="metric-value">
            <Database size={14} style={{ display: 'inline', marginRight: 4 }} />
            {health?.chroma_status === 'ready' ? 'Indexed & Ready' : 'Unindexed'}
          </span>
        </div>
        <div className="metric-divider" />
        <div className="metric-item">
          <span className="metric-label">LLM & Embeddings</span>
          <span className="metric-value">
            {health?.gemini_configured ? 'Google Gemini' : 'Key Missing'}
          </span>
        </div>
      </div>
    </header>
  );
};
