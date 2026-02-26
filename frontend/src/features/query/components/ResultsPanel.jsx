import React, { useState } from 'react';
import { ExecutiveSummary } from './ExecutiveSummary';
import { InsightCard } from './InsightCard';
import { DataTable } from '../../../components/molecules/DataTable';
import { ChartContainer } from '../../../components/molecules/ChartContainer';
import { Button } from '../../../components/atoms/Button';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import styles from './ResultsPanel.module.css';

export const ResultsPanel = ({
  results = null,
  onExport,
  onShare,
  className = '',
  ...props
}) => {
  const [expandedSections, setExpandedSections] = useState({
    summary: true,
    insights: true,
    data: true,
    visualization: true,
    actions: true,
  });

  if (!results) {
    return null;
  }

  const toggleSection = (section) => {
    setExpandedSections((prev) => ({
      ...prev,
      [section]: !prev[section],
    }));
  };

  const handleExport = (format) => {
    if (onExport) {
      onExport(format, results);
    }
  };

  const renderVisualization = () => {
    if (!results.visualization) return null;

    const { type, data } = results.visualization;

    if (type === 'line' && data) {
      return (
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
            <XAxis
              dataKey="name"
              stroke="var(--text-tertiary)"
              style={{ fontSize: '0.75rem' }}
            />
            <YAxis
              stroke="var(--text-tertiary)"
              style={{ fontSize: '0.75rem' }}
            />
            <Tooltip />
            <Line
              type="monotone"
              dataKey="value"
              stroke="var(--primary-color)"
              strokeWidth={2}
              dot={{ r: 4 }}
              activeDot={{ r: 6 }}
            />
          </LineChart>
        </ResponsiveContainer>
      );
    }

    return <p className={styles.placeholder}>Visualization not available</p>;
  };

  return (
    <div className={`${styles.container} ${className}`} {...props}>
      <div className={styles.header}>
        <h2 className={styles.title}>Query Results</h2>
        <div className={styles.headerActions}>
          {onShare && (
            <Button variant="secondary" size="sm" onClick={onShare}>
              <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
              </svg>
              Share
            </Button>
          )}
          {onExport && (
            <div className={styles.exportDropdown}>
              <Button variant="primary" size="sm" onClick={() => handleExport('pdf')}>
                <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                Export
              </Button>
            </div>
          )}
        </div>
      </div>

      {/* Executive Summary */}
      {results.summary && (
        <section className={styles.section}>
          <button
            className={styles.sectionHeader}
            onClick={() => toggleSection('summary')}
            aria-expanded={expandedSections.summary}
          >
            <h3 className={styles.sectionTitle}>Executive Summary</h3>
            <svg
              className={`${styles.expandIcon} ${expandedSections.summary ? styles.expanded : ''}`}
              width="20"
              height="20"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          {expandedSections.summary && (
            <div className={styles.sectionContent}>
              <ExecutiveSummary
                summary={results.summary.text}
                keyFindings={results.summary.keyFindings}
              />
            </div>
          )}
        </section>
      )}

      {/* Insights */}
      {results.insights && results.insights.length > 0 && (
        <section className={styles.section}>
          <button
            className={styles.sectionHeader}
            onClick={() => toggleSection('insights')}
            aria-expanded={expandedSections.insights}
          >
            <h3 className={styles.sectionTitle}>Key Insights</h3>
            <svg
              className={`${styles.expandIcon} ${expandedSections.insights ? styles.expanded : ''}`}
              width="20"
              height="20"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          {expandedSections.insights && (
            <div className={styles.sectionContent}>
              <div className={styles.insightsGrid}>
                {results.insights.map((insight, index) => (
                  <InsightCard
                    key={index}
                    title={insight.title}
                    description={insight.description}
                    value={insight.value}
                    change={insight.change}
                    trend={insight.trend}
                    variant={insight.variant}
                    icon={insight.icon}
                  />
                ))}
              </div>
            </div>
          )}
        </section>
      )}

      {/* Data Table */}
      {results.data && results.data.length > 0 && (
        <section className={styles.section}>
          <button
            className={styles.sectionHeader}
            onClick={() => toggleSection('data')}
            aria-expanded={expandedSections.data}
          >
            <h3 className={styles.sectionTitle}>Detailed Data</h3>
            <svg
              className={`${styles.expandIcon} ${expandedSections.data ? styles.expanded : ''}`}
              width="20"
              height="20"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          {expandedSections.data && (
            <div className={styles.sectionContent}>
              <DataTable
                columns={results.columns || []}
                data={results.data}
                pageSize={10}
              />
            </div>
          )}
        </section>
      )}

      {/* Visualization */}
      {results.visualization && (
        <section className={styles.section}>
          <button
            className={styles.sectionHeader}
            onClick={() => toggleSection('visualization')}
            aria-expanded={expandedSections.visualization}
          >
            <h3 className={styles.sectionTitle}>Visualization</h3>
            <svg
              className={`${styles.expandIcon} ${expandedSections.visualization ? styles.expanded : ''}`}
              width="20"
              height="20"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          {expandedSections.visualization && (
            <div className={styles.sectionContent}>
              <ChartContainer height={300}>
                {renderVisualization()}
              </ChartContainer>
            </div>
          )}
        </section>
      )}

      {/* Action Items */}
      {results.actionItems && results.actionItems.length > 0 && (
        <section className={styles.section}>
          <button
            className={styles.sectionHeader}
            onClick={() => toggleSection('actions')}
            aria-expanded={expandedSections.actions}
          >
            <h3 className={styles.sectionTitle}>Recommended Actions</h3>
            <svg
              className={`${styles.expandIcon} ${expandedSections.actions ? styles.expanded : ''}`}
              width="20"
              height="20"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          {expandedSections.actions && (
            <div className={styles.sectionContent}>
              <ul className={styles.actionsList}>
                {results.actionItems.map((action, index) => (
                  <li key={index} className={styles.actionItem}>
                    <div className={styles.actionIcon}>
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    </div>
                    <div className={styles.actionContent}>
                      <h4 className={styles.actionTitle}>{action.title}</h4>
                      <p className={styles.actionDescription}>{action.description}</p>
                      {action.priority && (
                        <span className={`${styles.actionPriority} ${styles[`priority-${action.priority}`]}`}>
                          {action.priority}
                        </span>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </section>
      )}
    </div>
  );
};
