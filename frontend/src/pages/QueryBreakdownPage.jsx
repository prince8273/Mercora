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

// Clean up garbled product names like "Product B0Q1BWOQIR (LAMP-LED-DESK)" → "LAMP-LED-DESK"
function cleanProductName(name) {
  if (!name) return 'Unknown Product';
  const match = name.match(/\(([^)]+)\)$/);
  return match ? match[1] : name;
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
                <div key={i} className={styles.insightCard}>
                  <div className={styles.insightHeader}>
                    <span className={styles.insightTitle}>{insight.title}</span>
                    {insight.value && (
                      <span className={`${styles.badge} ${styles[insight.variant] || ''}`}>
                        {insight.value}
                      </span>
                    )}
                  </div>
                  <p className={styles.insightDesc}>{insight.description}</p>

                  {/* Product/category details if available */}
                  {insight.details && insight.details.length > 0 && (
                    <div className={styles.detailsTable}>
                      <table>
                        <thead>
                          <tr>
                            <th>{insight.details[0]?.metrics ? 'SKU / Category' : 'Item'}</th>
                            <th>Name</th>
                            {insight.details[0]?.metrics?.map((m, mi) => (
                              <th key={mi}>{m.label}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {insight.details.map((d, di) => (
                            <tr key={di}>
                              <td>{d.sku}</td>
                              <td>{cleanProductName(d.name)}</td>
                              {d.metrics?.map((m, mi) => (
                                <td key={mi}>{m.value}</td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
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
