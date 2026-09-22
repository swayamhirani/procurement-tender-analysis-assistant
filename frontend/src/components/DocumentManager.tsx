import React, { useState } from 'react';
import { DocumentInfo } from '../types';
import {
  Upload,
  FileCheck,
  RefreshCw,
  FolderOpen,
  AlertTriangle,
  CheckCircle,
} from 'lucide-react';

interface DocumentManagerProps {
  documents: DocumentInfo[];
  loadingDocs: boolean;
  onUpload: (files: File[]) => Promise<void>;
  onIndex: () => Promise<void>;
  indexing: boolean;
  indexResult: { message: string; success: boolean } | null;
}

export const DocumentManager: React.FC<DocumentManagerProps> = ({
  documents,
  loadingDocs,
  onUpload,
  onIndex,
  indexing,
  indexResult,
}) => {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const validFiles = Array.from(e.target.files).filter((f) =>
        f.name.toLowerCase().endsWith('.pdf')
      );
      if (validFiles.length !== e.target.files.length) {
        setUploadError('Only PDF files are permitted.');
      } else {
        setUploadError(null);
      }
      setSelectedFiles(validFiles);
    }
  };

  const handleUploadClick = async () => {
    if (selectedFiles.length === 0) return;
    setUploading(true);
    setUploadError(null);
    try {
      await onUpload(selectedFiles);
      setSelectedFiles([]);
      const fileInput = document.getElementById('file-upload-input') as HTMLInputElement;
      if (fileInput) fileInput.value = '';
    } catch (err: unknown) {
      setUploadError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <section className="card document-manager">
      <div className="card-header">
        <div className="card-title-group">
          <FolderOpen size={20} className="text-primary" />
          <h2 className="card-title">Tender & RFP Documents</h2>
        </div>
        <button
          onClick={onIndex}
          disabled={indexing || documents.length === 0}
          className="btn btn-primary"
        >
          <RefreshCw size={16} className={indexing ? 'spin' : ''} />
          <span>{indexing ? 'Indexing...' : 'Index Documents'}</span>
        </button>
      </div>

      {indexResult && (
        <div
          className={`alert ${indexResult.success ? 'alert-success' : 'alert-danger'}`}
          style={{ marginBottom: '1rem' }}
        >
          {indexResult.success ? <CheckCircle size={18} /> : <AlertTriangle size={18} />}
          <span>{indexResult.message}</span>
        </div>
      )}

      {uploadError && (
        <div className="alert alert-danger" style={{ marginBottom: '1rem' }}>
          <AlertTriangle size={18} />
          <span>{uploadError}</span>
        </div>
      )}

      <div className="upload-box">
        <input
          id="file-upload-input"
          type="file"
          accept=".pdf,application/pdf"
          multiple
          onChange={handleFileChange}
          style={{ display: 'none' }}
        />
        <label htmlFor="file-upload-input" className="upload-dropzone">
          <Upload size={28} className="upload-icon" />
          <div className="upload-text">
            <strong>Choose PDF tender documents</strong> or browse files
          </div>
          <div className="upload-hint">Supported formats: .pdf (Up to 200+ pages)</div>
        </label>

        {selectedFiles.length > 0 && (
          <div className="selected-files-bar">
            <span>{selectedFiles.length} file(s) selected</span>
            <button
              onClick={handleUploadClick}
              disabled={uploading}
              className="btn btn-secondary"
            >
              {uploading ? 'Uploading...' : 'Confirm Upload'}
            </button>
          </div>
        )}
      </div>

      <div className="documents-list-section">
        <h3 className="section-subtitle">
          Stored Tender Documents ({documents.length})
        </h3>

        {loadingDocs ? (
          <div className="empty-state">Loading document catalog...</div>
        ) : documents.length === 0 ? (
          <div className="empty-state">
            No tender PDFs stored. Use the upload area above to add documents.
          </div>
        ) : (
          <div className="doc-table-wrapper">
            <table className="doc-table">
              <thead>
                <tr>
                  <th>Document Name</th>
                  <th>File Size</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {documents.map((doc) => (
                  <tr key={doc.filename}>
                    <td className="doc-name-cell">
                      <FileCheck size={16} className="text-muted" />
                      <span className="doc-title">{doc.filename}</span>
                    </td>
                    <td className="text-muted">{formatFileSize(doc.size_bytes)}</td>
                    <td>
                      <span className="badge-chip">Stored</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </section>
  );
};
