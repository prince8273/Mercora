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
import ContactSupportModal from '../components/modals/ContactSupportModal';
import styles from './SentimentPage.module.css';

export default function SentimentPage() {
  const [selectedProductId, setSelectedProductId] = useState(null);
  const [timeRange, setTimeRange] = useState('30d');
  const [isContactModalOpen, setIsContactModalOpen] = useState(false);

  // Fetch products list
  const { data: productsData, isLoading: productsLoading } = useProducts();
  const products = productsData || [];

  const { data: sentimentData, isLoading: sentimentLoading } = useSentimentOverview(
    selectedProductId,
    { timeRange }
  );

  const { data: themeData, isLoading: themeLoading } = useThemeBreakdown(selectedProductId, {
    timeRange,
  });

  const { data: reviewsData, isLoading: reviewsLoading } = useReviews(selectedProductId, {
    timeRange,
  });

  const { data: complaintData, isLoading: complaintLoading } = useComplaintAnalysis(
    selectedProductId,
    { timeRange }
  );

  const handleProductChange = (selectedIds) => {
    // ProductSelector returns array, we take first item
    setSelectedProductId(selectedIds.length > 0 ? selectedIds[0] : null);
  };

  const handleContactSupport = () => {
    setIsContactModalOpen(true);
  };

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
            selected={selectedProductId ? [selectedProductId] : []}
            onChange={handleProductChange}
            placeholder="Select a product..."
            loading={productsLoading}
          />
        </div>
      </div>

      {!selectedProductId ? (
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
