import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
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
import ContactSupportModal from '../components/modals/ContactSupportModal';
import styles from './IntelligencePage.module.css';

export default function IntelligencePage() {
  const [currentQueryId, setCurrentQueryId] = useState(null);
  const [queryResults, setQueryResults] = useState(null);
  const [isContactModalOpen, setIsContactModalOpen] = useState(false);
  const toast = useToast();
  const navigate = useNavigate();

  // Clear previous results on every page load/refresh
  useEffect(() => {
    sessionStorage.removeItem('lastQueryResults');
    sessionStorage.removeItem('lastQueryId');
  }, []);

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
              // analysis_type is embedded in transformation_applied for general agent rows
              const analysisType = data.analysis_type || evidence.data_lineage_path?.[1] || null;
              // Build metrics from explicit metrics array (sales/sentiment) or pricing fields
              const metrics = data.metrics?.length > 0
                ? data.metrics
                : [
                    data.current_price && { label: 'Current', value: `₹${data.current_price}` },
                    data.competitor_price && { label: 'Competitor', value: `₹${data.competitor_price}` },
                    data.gap_percentage && { label: 'Gap', value: `${data.gap_percentage}%` },
                    data.average_sentiment != null && { label: 'Sentiment', value: `${(data.average_sentiment * 100).toFixed(0)}%` },
                    data.review_count && { label: 'Reviews', value: String(data.review_count) },
                  ].filter(Boolean);
              return {
                sku: data.sku || 'N/A',
                name: data.name || null,
                analysisType,
                description: data.description,
                badge: data.badge,
                badgeVariant: data.badge_variant,
                complaints: data.complaints ?? null,
                complaintRate: data.complaint_rate ?? null,
                issues: data.issues ?? null,
                lowReviews: data.low_reviews ?? [],
                metrics
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
      sessionStorage.setItem('lastQueryResults', JSON.stringify(transformedResults));
      setCurrentQueryId(backendData.report_id);
      sessionStorage.setItem('lastQueryId', backendData.report_id || '');
      
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
    sessionStorage.removeItem('lastQueryResults');
    sessionStorage.removeItem('lastQueryId');
    sessionStorage.removeItem('breakdownResults');
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
    const queryId = currentQueryId || queryResults?.id;
    if (!queryId) {
      toast.error('Export Failed', 'No query results to export');
      return;
    }
    toast.info('Export Started', `Exporting results as ${format.toUpperCase()}...`);
    exportResultsMutation.mutate(
      { queryId, format },
      {
        onSuccess: (data) => {
          // If backend returns a download URL, open it
          const url = data?.download_url || data?.url;
          if (url) {
            window.open(url, '_blank');
          } else if (data) {
            // Fallback: treat response as blob/text and download
            const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = `query-results-${queryId}.${format}`;
            link.click();
            URL.revokeObjectURL(link.href);
          }
          toast.success('Export Ready', 'Your export is ready');
        },
        onError: (err) => {
          toast.error('Export Failed', err?.message || 'Failed to export results');
        },
      }
    );
  };

  const handleShare = () => {
    const queryId = currentQueryId || queryResults?.id;
    const shareUrl = queryId
      ? `${window.location.origin}/intelligence?queryId=${queryId}`
      : window.location.href;
    navigator.clipboard.writeText(shareUrl).then(
      () => toast.success('Link Copied', 'Shareable link copied to clipboard'),
      () => toast.error('Copy Failed', 'Could not copy link to clipboard')
    );
  };

  const handleExploreBreakdown = () => {
    sessionStorage.setItem('breakdownResults', JSON.stringify(queryResults));
    window.open('/dashboard/intelligence/breakdown', '_blank');
  };

  const handleSelectHistory = (historyItem) => {
    // Optionally load previous results
    console.log('Selected history item:', historyItem);
    setCurrentQueryId(historyItem.id);
    setQueryResults(historyItem);
  };

  const handleContactSupport = () => {
    setIsContactModalOpen(true);
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
        {queryResults && (
          <div className={styles.resultsSection}>
            <ResultsPanel
              results={queryResults}
              onExport={handleExport}
              onShare={handleShare}
              onExplore={queryResults ? handleExploreBreakdown : undefined}
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

      {/* Contact Support Button */}
      <button
        onClick={handleContactSupport}
        className="fixed bottom-6 right-6 bg-stone-900 text-white px-6 py-3 rounded-full shadow-lg hover:bg-stone-800 transition-all duration-300 flex items-center gap-2 z-40"
      >
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
        </svg>
        Contact Support
      </button>

      {/* Contact Support Modal */}
      <ContactSupportModal
        isOpen={isContactModalOpen}
        onClose={() => setIsContactModalOpen(false)}
      />
    </div>
  );
}
