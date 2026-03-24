import { useState, useRef, useEffect } from 'react';
import styles from './QueryBuilder.module.css';

const MAX = 500;

const CHIPS = [
  'Products with most positive reviews',
  'Top selling items this month',
  'Customer sentiment trends',
  'Revenue by category',
];

export const QueryBuilder = ({
  onSubmit,
  loading = false,
  queryHistory = [],
  onSelectHistory,
  className = '',
  ...props
}) => {
  const [value, setValue] = useState('');
  const textareaRef = useRef(null);

  const MAX_HEIGHT = 160; // ~6 lines

  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = 'auto';
    const next = Math.min(el.scrollHeight, MAX_HEIGHT);
    el.style.height = `${next}px`;
    el.style.overflowY = el.scrollHeight > MAX_HEIGHT ? 'auto' : 'hidden';
  }, [value]);

  const handleSubmit = () => {
    if (!value.trim() || loading) return;
    onSubmit({ query: value.trim(), mode: 'quick', filters: { products: [], dateRange: { startDate: null, endDate: null } } });
  };

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSubmit(); }
  };

  return (
    <div className={`${styles.card} ${className}`} {...props}>
      <p className={styles.prompt}>What would you like to analyse?</p>

      <div className={styles.chips}>
        {CHIPS.map((c) => (
          <button key={c} type="button" className={styles.chip} onClick={() => setValue(c)}>
            {c}
          </button>
        ))}
      </div>

      {/* Pill input */}
      <div className={styles.pill}>
        <textarea
          ref={textareaRef}
          className={styles.textarea}
          placeholder="Ask a question about your data, e.g. 'Which products have the most positive reviews?'"
          value={value}
          onChange={(e) => setValue(e.target.value.slice(0, MAX))}
          onKeyDown={handleKey}
          disabled={loading}
          rows={1}
        />
        <button
          type="button"
          className={`${styles.sendBtn} ${value.trim() && !loading ? styles.sendActive : ''}`}
          onClick={handleSubmit}
          disabled={!value.trim() || loading}
          aria-label="Send"
        >
          {loading ? (
            <svg className={styles.spinner} viewBox="0 0 24 24" fill="none" width="15" height="15">
              <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="2.5" strokeDasharray="28" strokeDashoffset="10" />
            </svg>
          ) : (
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="12" y1="19" x2="12" y2="5" />
              <polyline points="5 12 12 5 19 12" />
            </svg>
          )}
        </button>
        <span className={styles.counter}>{value.length} / {MAX}</span>
      </div>
    </div>
  );
};
