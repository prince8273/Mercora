import React, { useState, useEffect } from 'react';
import { PageHeader } from '../components/molecules/PageHeader';
import {
  QueryBuilder,
  ExecutionPanel,
  ResultsPanel,
} from '../features/query/components';
import {
  useExecuteQuery,
  useQueryHistory,
  useCancelQuery,
  useExportResults,
} from '../hooks/useQuery';
import { useQueryExecution } from '../hooks/useQueryExecution';
import { useToast } from '../components/organisms/ToastManager';
import styles from './IntelligencePage.module.css';

export default function IntelligencePage() {
  const [currentQueryId, setCurrentQueryId] = useState(null);
  const [queryResults, setQueryResults] = useState(null);
  const toast = useToast();

  // Hooks
  const { data: queryHistory } = useQueryHistory({ limit: 10 });
  const executeQueryMutation = useExecuteQuery();
  const cancelQueryMutation = useCancelQuery();
  const exportResultsMutation = useExportResults();

  // Real-time query execution tracking
  const {
    progress,
    status,
    currentActivity,
    activityLog,
    estimatedTime,
    error: executionError,
    reset: resetExecution,
    isPollingMode,
  } = useQueryExecution(currentQueryId);

  // Handle query execution completion
  useEffect(() => {
    if (executeQueryMutation.isSuccess && executeQueryMutation.data) {
      // Transform backend StructuredReport to frontend format
      const backendData = executeQueryMutation.data;
      const transformedResults = {
        id: backendData.report_id,
        summary: {
          text: backendData.executive_summary || 'No summary available',
          keyFindings: backendData.insights?.slice(0, 3).map(i => i.title) || []
        },
        insights: backendData.insights?.map(insight => {
          // Extract product details from supporting_evidence
          const details = insight.supporting_evidence?.map(evidence => {
            try {
              const data = JSON.parse(evidence.transformation_applied || '{}');
              return {
                sku: data.sku || 'N/A',
                name: data.name || 'Unknown Product',
                description: data.description,
                badge: data.badge,
                badgeVariant: data.badge_variant,
                metrics: [
                  data.current_price && { label: 'Current', value: `$${data.current_price}` },
                  data.competitor_price && { label: 'Competitor', value: `$${data.competitor_price}` },
                  data.gap_percentage && { label: 'Gap', value: `${data.gap_percentage}%` }
                ].filter(Boolean)
              };
            } catch (e) {
              return null;
            }
          }).filter(Boolean) || [];

          return {
            title: insight.title,
            description: insight.description,
            value: insight.confidence ? `${(insight.confidence * 100).toFixed(0)}%` : null,
            trend: 'stable',
            variant: insight.confidence > 0.7 ? 'success' : insight.confidence > 0.4 ? 'warning' : 'danger',
            icon: 'lightbulb',
            details: details.length > 0 ? details : null
          };
        }) || [],
        actionItems: backendData.action_items || [],
        data: [], // No detailed data table for now
        columns: [],
        visualization: null, // No visualization for now
        confidence: backendData.overall_confidence,
        metrics: backendData.key_metrics || [],
        risks: backendData.risks || []
      };
      
      setQueryResults(transformedResults);
      setCurrentQueryId(backendData.report_id);
      
      if (isPollingMode) {
        toast.info('Query Submitted', 'Using polling mode for progress updates', 3000);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [executeQueryMutation.isSuccess, executeQueryMutation.data, isPollingMode]);

  // Handle query execution error
  useEffect(() => {
    if (executeQueryMutation.isError) {
      toast.error('Query Failed', executeQueryMutation.error?.message || 'Failed to execute query');
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [executeQueryMutation.isError, executeQueryMutation.error]);

  // Handle execution completion
  useEffect(() => {
    if (status === 'completed') {
      toast.success('Query Complete', 'Your query has been processed successfully', 3000);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status]);

  const handleSubmitQuery = (queryData) => {
    resetExecution();
    setQueryResults(null);
    setCurrentQueryId(null);
    executeQueryMutation.mutate(queryData);
  };

  const handleCancelQuery = () => {
    if (currentQueryId) {
      cancelQueryMutation.mutate(currentQueryId);
      toast.info('Query Cancelled', 'Query execution has been cancelled');
    }
    resetExecution();
    setCurrentQueryId(null);
  };

  const handleRetryQuery = () => {
    if (queryResults) {
      handleSubmitQuery(queryResults);
    }
  };

  const handleExport = (format) => {
    if (currentQueryId) {
      exportResultsMutation.mutate({
        queryId: currentQueryId,
        format,
      });
      toast.info('Export Started', `Exporting results as ${format.toUpperCase()}...`);
    }
  };

  const handleShare = () => {
    // Implement share functionality
    toast.info('Share', 'Share functionality coming soon');
  };

  const handleSelectHistory = (historyItem) => {
    // Optionally load previous results
    console.log('Selected history item:', historyItem);
    setCurrentQueryId(historyItem.id);
    setQueryResults(historyItem);
  };

  const isExecuting = executeQueryMutation.isPending || (status === 'active' && progress < 100);

  return (
    <div className={styles.page}>
      <PageHeader
        title="Intelligence Query"
        breadcrumbs={[
          { label: 'Intelligence', path: '/intelligence' },
        ]}
      />

      <div className={styles.content}>
        {/* Query Builder */}
        <div className={styles.querySection}>
          <QueryBuilder
            onSubmit={handleSubmitQuery}
            loading={isExecuting}
            queryHistory={queryHistory?.data || []}
            onSelectHistory={handleSelectHistory}
          />
        </div>

        {/* Execution Panel */}
        {(isExecuting || status === 'completed' || status === 'error' || executeQueryMutation.isError) && (
          <div className={styles.executionSection}>
            <ExecutionPanel
              progress={progress}
              status={status}
              currentActivity={currentActivity}
              activityLog={activityLog}
              estimatedTime={estimatedTime}
              onCancel={isExecuting ? handleCancelQuery : null}
              error={executionError || (executeQueryMutation.isError ? executeQueryMutation.error?.message || 'Query execution failed' : null)}
              onRetry={status === 'error' || executeQueryMutation.isError ? handleRetryQuery : null}
            />
          </div>
        )}

        {/* Results Panel */}
        {queryResults && (status === 'completed' || executeQueryMutation.isSuccess) && (
          <div className={styles.resultsSection}>
            <ResultsPanel
              results={queryResults}
              onExport={handleExport}
              onShare={handleShare}
            />
          </div>
        )}

        {/* Empty State */}
        {!currentQueryId && !queryResults && (
          <div className={styles.emptyState}>
            <svg
              className={styles.emptyIcon}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
              />
            </svg>
            <h3 className={styles.emptyTitle}>Ask a Question</h3>
            <p className={styles.emptyText}>
              Use natural language to query your Amazon seller data and get AI-powered insights.
            </p>
            <div className={styles.exampleQueries}>
              <p className={styles.examplesLabel}>Try asking:</p>
              <ul className={styles.examplesList}>
                <li>"What are my top-selling products this month?"</li>
                <li>"Show me products with declining sales"</li>
                <li>"Which categories have the highest profit margins?"</li>
                <li>"Analyze my inventory turnover rate"</li>
              </ul>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
