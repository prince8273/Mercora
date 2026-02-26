import React, { useState } from 'react';
import { ModeSelector } from './ModeSelector';
import { ProductSelector } from '../../../components/molecules/ProductSelector';
import { DateRangePicker } from '../../../components/molecules/DateRangePicker';
import { Button } from '../../../components/atoms/Button';
import styles from './QueryBuilder.module.css';

const MAX_QUERY_LENGTH = 500;

export const QueryBuilder = ({
  onSubmit,
  loading = false,
  queryHistory = [],
  onSelectHistory,
  className = '',
  ...props
}) => {
  const [query, setQuery] = useState('');
  const [mode, setMode] = useState('quick');
  const [showFilters, setShowFilters] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [selectedProducts, setSelectedProducts] = useState([]);
  const [dateRange, setDateRange] = useState({
    startDate: null,
    endDate: null,
  });
  const [errors, setErrors] = useState({});

  const characterCount = query.length;
  const isOverLimit = characterCount > MAX_QUERY_LENGTH;
  const canSubmit = query.trim().length > 0 && !isOverLimit && !loading;

  const handleQueryChange = (e) => {
    setQuery(e.target.value);
    if (errors.query) {
      setErrors({ ...errors, query: null });
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    // Validation
    const newErrors = {};
    if (!query.trim()) {
      newErrors.query = 'Please enter a query';
    }
    if (isOverLimit) {
      newErrors.query = `Query exceeds maximum length of ${MAX_QUERY_LENGTH} characters`;
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    // Submit query
    onSubmit({
      query: query.trim(),
      mode,
      filters: {
        products: selectedProducts,
        dateRange,
      },
    });
  };

  const handleHistorySelect = (historyItem) => {
    setQuery(historyItem.query);
    setMode(historyItem.mode || 'quick');
    if (historyItem.filters) {
      setSelectedProducts(historyItem.filters.products || []);
      setDateRange(historyItem.filters.dateRange || { startDate: null, endDate: null });
    }
    setShowHistory(false);
    if (onSelectHistory) {
      onSelectHistory(historyItem);
    }
  };

  const handleClear = () => {
    setQuery('');
    setMode('quick');
    setSelectedProducts([]);
    setDateRange({ startDate: null, endDate: null });
    setErrors({});
  };

  return (
    <div className={`${styles.container} ${className}`} {...props}>
      <form onSubmit={handleSubmit} className={styles.form}>
        {/* Query Input */}
        <div className={styles.querySection}>
          <div className={styles.queryHeader}>
            <label htmlFor="query-input" className={styles.label}>
              Ask a Question
            </label>
            {queryHistory && queryHistory.length > 0 && (
              <button
                type="button"
                className={styles.historyButton}
                onClick={() => setShowHistory(!showHistory)}
              >
                <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                History
              </button>
            )}
          </div>

          <div className={styles.textareaWrapper}>
            <textarea
              id="query-input"
              className={`${styles.textarea} ${errors.query ? styles.error : ''}`}
              placeholder="e.g., What are my top-selling products this month?"
              value={query}
              onChange={handleQueryChange}
              disabled={loading}
              rows={4}
              aria-invalid={!!errors.query}
              aria-describedby={errors.query ? 'query-error' : undefined}
            />
            <div className={styles.textareaFooter}>
              <span
                className={`${styles.charCount} ${isOverLimit ? styles.overLimit : ''}`}
              >
                {characterCount} / {MAX_QUERY_LENGTH}
              </span>
            </div>
          </div>

          {errors.query && (
            <p id="query-error" className={styles.errorMessage}>
              {errors.query}
            </p>
          )}

          {/* Query History Dropdown */}
          {showHistory && queryHistory.length > 0 && (
            <div className={styles.historyDropdown}>
              <div className={styles.historyHeader}>
                <span>Recent Queries</span>
                <button
                  type="button"
                  className={styles.closeButton}
                  onClick={() => setShowHistory(false)}
                  aria-label="Close history"
                >
                  <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              <ul className={styles.historyList}>
                {queryHistory.slice(0, 5).map((item, index) => (
                  <li key={index}>
                    <button
                      type="button"
                      className={styles.historyItem}
                      onClick={() => handleHistorySelect(item)}
                    >
                      <span className={styles.historyQuery}>{item.query}</span>
                      <span className={styles.historyMeta}>
                        {item.mode} • {formatDate(item.timestamp)}
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* Mode Selector */}
        <ModeSelector mode={mode} onChange={setMode} disabled={loading} />

        {/* Filters Toggle */}
        <button
          type="button"
          className={styles.filtersToggle}
          onClick={() => setShowFilters(!showFilters)}
        >
          <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
          </svg>
          {showFilters ? 'Hide' : 'Show'} Filters
          {(selectedProducts.length > 0 || dateRange.startDate) && (
            <span className={styles.filterBadge}>
              {selectedProducts.length + (dateRange.startDate ? 1 : 0)}
            </span>
          )}
        </button>

        {/* Filters Panel */}
        {showFilters && (
          <div className={styles.filtersPanel}>
            <div className={styles.filterRow}>
              <ProductSelector
                value={selectedProducts}
                onChange={setSelectedProducts}
                multiSelect
                disabled={loading}
              />
            </div>
            <div className={styles.filterRow}>
              <DateRangePicker
                startDate={dateRange.startDate}
                endDate={dateRange.endDate}
                onChange={setDateRange}
                disabled={loading}
              />
            </div>
          </div>
        )}

        {/* Actions */}
        <div className={styles.actions}>
          <Button
            type="button"
            variant="secondary"
            onClick={handleClear}
            disabled={loading || (!query && selectedProducts.length === 0 && !dateRange.startDate)}
          >
            Clear
          </Button>
          <Button
            type="submit"
            variant="primary"
            disabled={!canSubmit}
            isLoading={loading}
          >
            {loading ? 'Processing...' : 'Submit Query'}
          </Button>
        </div>
      </form>
    </div>
  );
};

// Helper function to format date
const formatDate = (timestamp) => {
  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;

  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
  });
};
