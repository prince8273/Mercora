import { useState } from 'react';
import { useSentimentOverview, useThemeBreakdown, useReviews, useComplaintAnalysis } from '../hooks';
import { useProducts } from '../hooks/useProducts';
import { ProductSelector } from '../components/molecules/ProductSelector/ProductSelector';
import {
  SentimentOverview,
  ThemeBreakdown,
  ReviewList,
  ComplaintAnalysis,
} from '../features/sentiment/components';
import styles from './SentimentPage.module.css';

export default function SentimentPage() {
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [timeRange, setTimeRange] = useState('30d');

  // Fetch products list
  const { data: productsData, isLoading: productsLoading } = useProducts();
  const products = productsData || [];

  const { data: sentimentData, isLoading: sentimentLoading } = useSentimentOverview(
    selectedProduct,
    { timeRange }
  );

  const { data: themeData, isLoading: themeLoading } = useThemeBreakdown(selectedProduct, {
    timeRange,
  });

  const { data: reviewsData, isLoading: reviewsLoading } = useReviews(selectedProduct, {
    timeRange,
  });

  const { data: complaintData, isLoading: complaintLoading } = useComplaintAnalysis(
    selectedProduct,
    { timeRange }
  );

  return (
    <div className={styles.page}>
      <div className={styles.pageHeader}>
        <div>
          <h1 className={styles.title}>Sentiment Analysis</h1>
          <p className={styles.subtitle}>Customer feedback and review insights</p>
        </div>
        <div className={styles.productSelector}>
          <ProductSelector
            products={products}
            value={selectedProduct}
            onChange={setSelectedProduct}
            placeholder="Select a product..."
            loading={productsLoading}
          />
        </div>
      </div>

      {!selectedProduct ? (
        <div className={styles.emptyState}>
          <div className={styles.emptyIcon}>🔍</div>
          <h2>Select a Product</h2>
          <p>Choose a product from the dropdown above to view sentiment analysis</p>
        </div>
      ) : (
        <div className={styles.content}>
          {/* Sentiment Overview */}
          <div className={styles.section}>
            <SentimentOverview
              data={sentimentData}
              isLoading={sentimentLoading}
              timeRange={timeRange}
              onTimeRangeChange={setTimeRange}
            />
          </div>

          {/* Theme Breakdown */}
          <div className={styles.section}>
            <ThemeBreakdown data={themeData} isLoading={themeLoading} />
          </div>

          {/* Complaint Analysis */}
          <div className={styles.section}>
            <ComplaintAnalysis data={complaintData} isLoading={complaintLoading} />
          </div>

          {/* Reviews List */}
          <div className={styles.section}>
            <ReviewList data={reviewsData} isLoading={reviewsLoading} />
          </div>
        </div>
      )}
    </div>
  );
}
