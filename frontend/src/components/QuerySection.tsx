import React, { useState } from 'react';
import { Search, Sparkles } from 'lucide-react';

interface QuerySectionProps {
  onAsk: (question: string) => Promise<void>;
  loading: boolean;
}

const EXAMPLE_QUESTIONS = [
  'According to GeM bid.pdf, what is the minimum average annual turnover required for the bidder?',
  'What are the eligibility criteria?',
  'What is the contract period?',
  'What is the bid submission deadline?',
  'What is the evaluation method?',
];

export const QuerySection: React.FC<QuerySectionProps> = ({ onAsk, loading }) => {
  const [question, setQuestion] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim() || loading) return;
    onAsk(question.trim());
  };

  const handleSelectExample = (example: string) => {
    setQuestion(example);
    onAsk(example);
  };

  return (
    <section className="card query-section">
      <div className="card-header">
        <div className="card-title-group">
          <Search size={20} className="text-primary" />
          <h2 className="card-title">Ask About Your Tender</h2>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="query-form">
        <div className="input-group">
          <input
            type="text"
            className="query-input"
            placeholder="e.g. What is the minimum annual turnover required?"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            disabled={loading}
          />
          <button
            type="submit"
            className="btn btn-primary"
            disabled={loading || !question.trim()}
          >
            {loading ? (
              <>
                <span className="spin-inline" />
                <span>Analyzing...</span>
              </>
            ) : (
              <>
                <Search size={16} />
                <span>Ask Question</span>
              </>
            )}
          </button>
        </div>
      </form>

      <div className="example-questions-container">
        <div className="example-label">
          <Sparkles size={14} className="text-primary" />
          <span>Quick Analysis Questions:</span>
        </div>
        <div className="example-chips">
          {EXAMPLE_QUESTIONS.map((q, idx) => (
            <button
              key={idx}
              type="button"
              className="chip-btn"
              onClick={() => handleSelectExample(q)}
              disabled={loading}
            >
              {q}
            </button>
          ))}
        </div>
      </div>
    </section>
  );
};
