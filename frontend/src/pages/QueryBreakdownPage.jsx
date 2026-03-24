import { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { PageHeader } from '../components/molecules/PageHeader';
import styles from './QueryBreakdownPage.module.css';

// Parse the backend's newline-separated summary string into structured lines
function SummaryText({ text }) {
  if (!text) return null;
  const lines = text.split('\n').map(l => l.trim()).filter(Boolean);
  return (
    <div className={styles.summaryLines}>
      {lines.map((line, i) => {
        if (line.startsWith('- ')) {
          return <p key={i} className={styles.summaryBullet}>{line.slice(2)}</p>;
        }
        if (line.match(/^(Analysis for|Overall Confidence|Key Findings|Critical Risks|Recommended Actions)/)) {
          return <p key={i} className={styles.summarySection}>{line}</p>;
        }
        return <p key={i} className={styles.summaryText}>{line}</p>;
      })}
    </div>
  );
}

// Clean up garbled product names:
// "Men's Cotton T-Shirt Blue (DUMBBELL-SET-20KG)" → "Men's Cotton T-Shirt Blue"
// "Product B05F7WXX3Q (LAMP-LED-DESK)" → "LAMP-LED-DESK"  (last paren = real SKU)
// "Product B05F7WXX3Q" → use the SKU column instead (handled at call site)
function cleanProductName(name, sku) {
  if (!name) return sku || 'Unknown';

  // If name is just "Product <ASIN>" with no real info, use the SKU
  if (/^Product\s+[A-Z0-9]{8,}$/.test(name.trim())) {
    return sku || name;
  }

  // Strip all trailing (SKU-LIKE) parenthetical groups — they're data corruption
  // SKU pattern: all-caps/digits/hyphens, 4+ chars
  const cleaned = name.replace(/\s*\([A-Z0-9][A-Z0-9\-]{3,}\)/g, '').trim();
  return cleaned || sku || name;
}

// Expandable insight table — rows are clickable to reveal complaints / issues
function InsightTable({ insight }) {
  const [expandedRow, setExpandedRow] = useState(null);
  const isCategory = insight.title?.toLowerCase().includes('category');
  // Time-series insights (trend data) have no product name column
  const firstDetail = insight.details?.[0];
  const isTimeSeries = ['revenue_trend', 'sentiment_trend'].includes(firstDetail?.analysisType);
  const hideNameCol = isCategory || isTimeSeries;
  const firstColLabel = isCategory ? 'Category' : isTimeSeries ? 'Month' : 'SKU / Category';

  const toggle = (idx) => setExpandedRow(prev => prev === idx ? null : idx);

  return (
    <div className={styles.insightCard}>
      <div className={styles.insightHeader}>
        <span className={styles.insightTitle}>{insight.title}</span>
        {insight.value && (
          <span className={`${styles.badge} ${styles[insight.variant] || ''}`}>
            {insight.value}
          </span>
        )}
      </div>
      <p className={styles.insightDesc}>{insight.description}</p>

      {insight.details && insight.details.length > 0 && (
        <div className={styles.detailsTable}>
          <table>
            <thead>
              <tr>
                <th>{firstColLabel}</th>
                {!hideNameCol && <th>Name</th>}
                {insight.details[0]?.metrics?.map((m, mi) => (
                  <th key={mi}>{m.label}</th>
                ))}
                {insight.details.some(d => d.complaints != null || d.issues) && (
                  <th>Details</th>
                )}
              </tr>
            </thead>
            <tbody>
              {insight.details.map((d, di) => {
                const hasExtra = d.complaints != null || (d.issues && d.issues !== 'none detected') || (d.lowReviews && d.lowReviews.length > 0);
                const isOpen = expandedRow === di;
                const colSpan = (hideNameCol ? 1 : 2) + (d.metrics?.length || 0) + (hasExtra ? 1 : 0);
                return (
                  <>
                    <tr
                      key={di}
                      className={hasExtra ? styles.clickableRow : ''}
                      onClick={hasExtra ? () => toggle(di) : undefined}
                      title={hasExtra ? 'Click to see details' : undefined}
                    >
                      <td>{d.sku}</td>
                      {!hideNameCol && (
                        <td>{d.name ? cleanProductName(d.name, d.sku) : '—'}</td>
                      )}
                      {d.metrics?.map((m, mi) => (
                        <td key={mi}>{m.value}</td>
                      ))}
                      {hasExtra && (
                        <td className={styles.expandCell}>
                          <span className={`${styles.expandChevron} ${isOpen ? styles.chevronOpen : ''}`}>▾</span>
                        </td>
                      )}
                    </tr>
                    {isOpen && hasExtra && (
                      <tr key={`${di}-detail`} className={styles.expandedRow}>
                        <td colSpan={colSpan}>
                          <div className={styles.expandedContent}>
                            {d.complaints > 0 && (
                              <div className={styles.expandedItem}>
                                <span className={styles.expandedLabel}>Complaints (1–2★ reviews)</span>
                                <span className={styles.expandedBadgeDanger}>
                                  {d.complaints}
                                  {d.complaintRate != null && d.complaintRate > 0 && (
                                    <span className={styles.complaintRateNote}> ({d.complaintRate.toFixed(1)}% of buyers)</span>
                                  )}
                                </span>
                              </div>
                            )}
                            {d.issues && d.issues !== 'none detected' && (
                              <div className={styles.expandedItem}>
                                <span className={styles.expandedLabel}>Issues detected</span>
                                <span className={styles.expandedIssues}>{d.issues}</span>
                              </div>
                            )}
                            {d.lowReviews && d.lowReviews.length > 0 && (
                              <div className={styles.reviewsList}>
                                <span className={styles.reviewsHeader}>1–2★ Customer Reviews</span>
                                {d.lowReviews.map((rev, ri) => (
                                  <div key={ri} className={styles.reviewItem}>
                                    <span className={styles.reviewStars}>
                                      {'★'.repeat(rev.rating)}{'☆'.repeat(2 - rev.rating)}
                                    </span>
                                    <span className={styles.reviewText}>{rev.text}</span>
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        </td>
                      </tr>
                    )}
                  </>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default function QueryBreakdownPage() {
  const { state } = useLocation();
  const navigate = useNavigate();
  const results = state?.results ?? (() => {
    try {
      const saved = sessionStorage.getItem('breakdownResults');
      return saved ? JSON.parse(saved) : null;
    } catch { return null; }
  })();

  if (!results) {
    return (
      <div className={styles.page}>
        <PageHeader
          title="Detailed Breakdown"
          breadcrumbs={[
            { label: 'Intelligence', path: '/dashboard/intelligence' },
            { label: 'Breakdown' },
          ]}
        />
        <div className={styles.empty}>
          <p>No query data found. Please run a query first.</p>
          <button className={styles.backBtn} onClick={() => navigate('/dashboard/intelligence')}>
            Back to Intelligence
          </button>
        </div>
      </div>
    );
  }

  const confidence = results.confidence != null
    ? Math.round(results.confidence > 1 ? results.confidence : results.confidence * 100)
    : null;

  return (
    <div className={styles.page}>
      <PageHeader
        title="Detailed Breakdown"
        breadcrumbs={[
          { label: 'Intelligence', path: '/dashboard/intelligence' },
          { label: 'Breakdown' },
        ]}
      />

      <div className={styles.content}>

        {/* Summary */}
        {results.summary && (
          <section className={styles.card}>
            <h2 className={styles.cardTitle}>Executive Summary</h2>
            {confidence != null && (
              <div className={styles.confRow}>
                <span className={styles.confLabel}>Confidence</span>
                <div className={styles.barTrack}>
                  <div className={styles.barFill} style={{ width: `${confidence}%` }} />
                </div>
                <span className={styles.confValue}>{confidence}%</span>
              </div>
            )}
            <SummaryText text={results.summary.text} />          </section>
        )}

        {/* Key Metrics */}
        {results.metrics && results.metrics.length > 0 && (
          <section className={styles.card}>
            <h2 className={styles.cardTitle}>Key Metrics</h2>
            <div className={styles.metricsGrid}>
              {results.metrics.map((m, i) => (
                <div key={i} className={styles.metricCard}>
                  <span className={styles.metricValue}>{m.value}{m.unit || ''}</span>
                  <span className={styles.metricLabel}>{m.name || m.key}</span>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Insights */}
        {results.insights && results.insights.length > 0 && (
          <section className={styles.card}>
            <h2 className={styles.cardTitle}>Insights ({results.insights.length})</h2>
            <div className={styles.insightsList}>
              {results.insights.map((insight, i) => (
                <InsightTable key={i} insight={insight} />
              ))}
            </div>
          </section>
        )}

        {/* Action Items */}
        {results.actionItems && results.actionItems.length > 0 && (
          <section className={styles.card}>
            <h2 className={styles.cardTitle}>Recommended Actions</h2>
            <div className={styles.actionsList}>
              {results.actionItems.map((item, i) => (
                <div key={i} className={styles.actionCard}>
                  <div className={styles.actionHeader}>
                    <span className={styles.actionTitle}>{item.title || item.action}</span>
                    {item.priority && (
                      <span className={`${styles.badge} ${styles[item.priority]}`}>
                        {item.priority}
                      </span>
                    )}
                  </div>
                  {item.description && <p className={styles.actionDesc}>{item.description}</p>}
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Risks */}
        {results.risks && results.risks.length > 0 && (
          <section className={styles.card}>
            <h2 className={styles.cardTitle}>Risk Factors</h2>
            <div className={styles.actionsList}>
              {results.risks.map((risk, i) => (
                <div key={i} className={`${styles.actionCard} ${styles.riskCard}`}>
                  <span className={styles.actionTitle}>{risk.title || risk.description || risk}</span>
                </div>
              ))}
            </div>
          </section>
        )}

      </div>
    </div>
  );
}
