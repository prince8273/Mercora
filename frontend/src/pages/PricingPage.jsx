import React, { useState } from 'react';
import { PageHeader } from '../components/molecules/PageHeader';
import { ProductSelector } from '../components/molecules/ProductSelector';
import { LoadingSkeleton } from '../components/molecules/LoadingSkeleton';
import { Button } from '../components/atoms/Button';
import {
  CompetitorMatrix,
  PriceTrendChart,
  RecommendationPanel,
  PromotionTracker,
} from '../features/pricing/components';
import {
  useCompetitorPricing,
  usePriceTrends,
  usePricingRecommendations,
  usePromotionAnalysis,
} from '../hooks/usePricing';
import { useProducts } from '../hooks/useProducts';
import { usePricingRealtime } from '../hooks/useRealtimeData';
import styles from './PricingPage.module.css';

export default function PricingPage() {
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [timeRange, setTimeRange] = useState('30d');
  const [filters, setFilters] = useState({});

  // Enable real-time updates for pricing
  usePricingRealtime(false); // Set to true to show notifications on updates

  // Fetch products list
  const { data: productsData, isLoading: productsLoading } = useProducts();
  const products = productsData || [];

  // Fetch data using hooks
  const {
    data: competitorData,
    isLoading: competitorLoading,
    error: competitorError,
    refetch: refetchCompetitor,
  } = useCompetitorPricing(selectedProduct?.id, filters);

  const {
    data: trendData,
    isLoading: trendLoading,
    error: trendError,
  } = usePriceTrends(selectedProduct?.id, timeRange);

  const {
    data: recommendations,
    isLoading: recommendationsLoading,
    error: recommendationsError,
    refetch: refetchRecommendations,
  } = usePricingRecommendations(selectedProduct?.id);

  const {
    data: promotions,
    isLoading: promotionsLoading,
    error: promotionsError,
  } = usePromotionAnalysis(filters);

  const handleProductChange = (product) => {
    setSelectedProduct(product);
  };

  const handleRefresh = () => {
    refetchCompetitor();
    refetchRecommendations();
  };

  const handleExportMatrix = (data) => {
    // Export competitor matrix to CSV
    console.log('Export matrix:', data);
  };

  const handleAcceptRecommendation = (recommendation) => {
    console.log('Accept recommendation:', recommendation);
    // In real app, this would call API to apply pricing
  };

  const handleRejectRecommendation = (recommendation) => {
    console.log('Reject recommendation:', recommendation);
    // In real app, this would call API to dismiss recommendation
  };

  return (
    <div className={styles.page}>
      <PageHeader
        title="Pricing Analysis"
        breadcrumbs={[{ label: 'Pricing', path: '/pricing' }]}
        actions={
          <Button onClick={handleRefresh} variant="secondary" size="sm">
            <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
            Refresh
          </Button>
        }
      />

      {/* Product Selector */}
      <div className={styles.filterSection}>
        <ProductSelector
          products={products}
          selected={selectedProduct ? [selectedProduct.id] : []}
          onChange={(selectedIds) => {
            if (selectedIds.length > 0) {
              const product = products.find(p => p.id === selectedIds[0]);
              setSelectedProduct(product);
            } else {
              setSelectedProduct(null);
            }
          }}
          placeholder="Select a product to analyze pricing..."
          multiple={false}
          loading={productsLoading}
        />
      </div>

      {!selectedProduct ? (
        /* Empty State */
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
              d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <h3 className={styles.emptyTitle}>Select a Product</h3>
          <p className={styles.emptyText}>
            Choose a product from the dropdown above to view competitive pricing analysis,
            trends, and AI-powered recommendations.
          </p>
          <div className={styles.featureList}>
            <div className={styles.feature}>
              <svg width="20" height="20" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                  clipRule="evenodd"
                />
              </svg>
              <span>Real-time competitor price tracking</span>
            </div>
            <div className={styles.feature}>
              <svg width="20" height="20" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                  clipRule="evenodd"
                />
              </svg>
              <span>Historical price trends and analysis</span>
            </div>
            <div className={styles.feature}>
              <svg width="20" height="20" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                  clipRule="evenodd"
                />
              </svg>
              <span>AI-powered pricing recommendations</span>
            </div>
            <div className={styles.feature}>
              <svg width="20" height="20" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                  clipRule="evenodd"
                />
              </svg>
              <span>Promotion effectiveness tracking</span>
            </div>
          </div>
        </div>
      ) : (
        /* Main Content */
        <div className={styles.content}>
          {/* Price Trend Chart */}
          <div className={styles.trendSection}>
            {trendLoading ? (
              <LoadingSkeleton variant="chart" />
            ) : trendError ? (
              <div className={styles.errorState}>
                <p>Failed to load price trends</p>
                <Button onClick={() => window.location.reload()} size="sm">
                  Retry
                </Button>
              </div>
            ) : (
              <PriceTrendChart
                data={trendData?.data || []}
                timeRange={timeRange}
                onTimeRangeChange={setTimeRange}
              />
            )}
          </div>

          {/* Two Column Layout */}
          <div className={styles.twoColumnGrid}>
            {/* Recommendations Panel */}
            <div className={styles.recommendationsSection}>
              {recommendationsLoading ? (
                <LoadingSkeleton variant="card" />
              ) : recommendationsError ? (
                <div className={styles.errorState}>
                  <p>Failed to load recommendations</p>
                  <Button onClick={refetchRecommendations} size="sm">
                    Retry
                  </Button>
                </div>
              ) : (
                <RecommendationPanel
                  recommendations={recommendations?.data || []}
                  onAccept={handleAcceptRecommendation}
                  onReject={handleRejectRecommendation}
                />
              )}
            </div>

            {/* Promotion Tracker */}
            <div className={styles.promotionsSection}>
              {promotionsLoading ? (
                <LoadingSkeleton variant="card" />
              ) : promotionsError ? (
                <div className={styles.errorState}>
                  <p>Failed to load promotions</p>
                  <Button onClick={() => window.location.reload()} size="sm">
                    Retry
                  </Button>
                </div>
              ) : (
                <PromotionTracker promotions={promotions?.data || []} />
              )}
            </div>
          </div>

          {/* Competitor Matrix */}
          <div className={styles.matrixSection}>
            {competitorLoading ? (
              <LoadingSkeleton variant="table" />
            ) : competitorError ? (
              <div className={styles.errorState}>
                <p>Failed to load competitor data</p>
                <Button onClick={refetchCompetitor} size="sm">
                  Retry
                </Button>
              </div>
            ) : (
              <CompetitorMatrix
                data={competitorData?.data || []}
                onExport={handleExportMatrix}
              />
            )}
          </div>
        </div>
      )}
    </div>
  );
}
