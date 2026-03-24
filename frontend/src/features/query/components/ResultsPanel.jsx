import { useState } from 'react';
import styles from './ResultsPanel.module.css';

// Renders the backend's rule-based summary string (newline-separated) as structured markup
function SummaryText({ text }) {
  if (!text) return null;
  const lines = text.split('\n').map(l => l.trim()).filter(Boolean);
  return (
    <div className={styles.summaryLines}>
      {lines.map((line, i) => {
        if (line.startsWith('- ')) {
          return <p key={i} className={styles.summaryBullet}>{line.slice(2)}</p>;
        }
        if (line.endsWith(':') || line.match(/^(Analysis for|Overall Confidence|Key Findings|Critical Risks|Recommended Actions)/)) {
          return <p key={i} className={styles.summarySection}>{line}</p>;
        }
        return <p key={i} className={styles.summaryCardText}>{line}</p>;
      })}
    </div>
  );
}

export const ResultsPanel = ({ results = null, onExport, onShare, onExplore, className = '' }) => {
  const [summaryOpen, setSummaryOpen] = useState(true);

  if (!results) return null;

  // Backend may send 0.875 (fraction) or 87.5 (already %) — normalise to 0–100
  const confidence = results.confidence != null
    ? Math.round(results.confidence > 1 ? results.confidence : results.confidence * 100)
    : null;

  const productCount = results.insights?.length ?? 0;

  // Pull sentiment threshold from metrics if available, fallback to a readable label
  const sentimentMetric = results.metrics?.find(
    (m) => m.name?.toLowerCase().includes('sentiment') || m.key?.toLowerCase().includes('sentiment')
  );
  const sentimentThreshold = sentimentMetric
    ? `${sentimentMetric.value}${sentimentMetric.unit || ''}`
    : results.summary?.text?.match(/(\d+)%\s*(?:positive\s*)?sentiment/i)?.[1]
      ? `>${results.summary.text.match(/(\d+)%\s*(?:positive\s*)?sentiment/i)[1]}%`
      : null;

  return (
    <div className={`${styles.container} ${className}`}>

      {/* ── Header ── */}
      <div className={styles.header}>
        <h2 className={styles.title}>Query Results</h2>
        <div className={styles.actions}>
          {onShare && (
            <button type="button" className={styles.btnOutline} onClick={onShare}>
              <svg width="15" height="15" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
              </svg>
              Share
            </button>
          )}
          {onExport && (
            <button type="button" className={styles.btnExport} onClick={() => onExport('pdf')}>
              <svg width="15" height="15" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Export
            </button>
          )}
        </div>
      </div>

      {/* ── Metric cards ── */}
      <div className={styles.metrics}>
        {confidence != null && (
          <div className={styles.metricCard}>
            <span className={styles.metricValue}>{confidence}%</span>
            <span className={styles.metricLabel}>Overall confidence</span>
          </div>
        )}
        <div className={styles.metricCard}>
          <span className={styles.metricValue}>{productCount}</span>
          <span className={styles.metricLabel}>Products found</span>
        </div>
        {sentimentThreshold && (
          <div className={styles.metricCard}>
            <span className={styles.metricValue}>{sentimentThreshold}</span>
            <span className={styles.metricLabel}>Sentiment threshold</span>
          </div>
        )}
      </div>

      {/* ── Executive Summary (collapsible) ── */}
      {results.summary && (
        <div className={styles.section}>
          <button
            type="button"
            className={styles.sectionToggle}
            onClick={() => setSummaryOpen((o) => !o)}
            aria-expanded={summaryOpen}
          >
            <span className={styles.sectionTitle}>Executive Summary</span>
            <span className={styles.collapseBtn}>
              <svg
                width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24"
                style={{ transform: summaryOpen ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }}
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
              {summaryOpen ? 'Collapse' : 'Expand'}
            </span>
          </button>

          {summaryOpen && (
            <div className={styles.sectionBody}>
              {/* Confidence bar */}
              {confidence != null && (
                <div className={styles.confRow}>
                  <span className={styles.confLabel}>Confidence level</span>
                  <span className={styles.confValue}>{confidence}%</span>
                  <div className={styles.barTrack}>
                    <div className={styles.barFill} style={{ width: `${confidence}%` }} />
                  </div>
                </div>
              )}

              {/* Summary card with accent border */}
              <div className={styles.summaryCard}>
                <h4 className={styles.summaryCardTitle}>Analysis overview</h4>
                <SummaryText text={results.summary.text} />
              </div>

              {/* Key findings */}
              {results.insights && results.insights.length > 0 && (
                <div className={styles.findings}>
                  <p className={styles.findingsLabel}>KEY FINDINGS</p>
                  {results.insights.map((insight, i) => (
                    <div key={i} className={styles.findingCard}>
                      <span className={styles.checkIcon}>
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                          <circle cx="12" cy="12" r="10" fill="#16a34a" opacity="0.12" />
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} stroke="#16a34a" d="M8 12l3 3 5-5" />
                        </svg>
                      </span>
                      <div className={styles.findingBody}>
                        <p className={styles.findingTitle}>{insight.title}</p>
                        <p className={styles.findingMeta}>{insight.description}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* ── Explore breakdown ── */}
      {onExplore && (
        <div className={styles.exploreRow}>
          <button type="button" className={styles.exploreBtn} onClick={onExplore}>
            Explore detailed breakdown
            <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
          </button>
        </div>
      )}
    </div>
  );
};
