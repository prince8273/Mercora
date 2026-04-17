import { useState } from 'react';
import { useDemandForecast, useInventoryRecommendations } from '../hooks';
import { useProducts } from '../hooks/useProducts';
import { ProductSelector } from '../components/molecules/ProductSelector/ProductSelector';
import {
  ForecastChart,
  InventoryAlerts,
  DemandSupplyGap,
  AccuracyMetrics,
} from '../features/forecast/components';
import ContactSupportModal from '../components/modals/ContactSupportModal';
import styles from './ForecastPage.module.css';

export default function ForecastPage() {
  const [selectedProductId, setSelectedProductId] = useState(null);
  const [horizon, setHorizon] = useState('30d');
  const [timeRange, setTimeRange] = useState('30d');
  const [isContactModalOpen, setIsContactModalOpen] = useState(false);

  // Fetch products list
  const { data: productsData, isLoading: productsLoading } = useProducts();
  const products = productsData || [];

  const { data: forecastData, isLoading: forecastLoading } = useDemandForecast(
    selectedProductId,
    { horizon }
  );

  const { data: inventoryData, isLoading: inventoryLoading } = useInventoryRecommendations(
    selectedProductId
  );

  const handleDismissAlert = (alertId) => {
    console.log('Dismiss alert:', alertId);
    // TODO: Implement alert dismissal
  };

  const handleTakeAction = (alertId) => {
    console.log('Take action on alert:', alertId);
    // TODO: Implement action handling
  };

  const handleContactSupport = () => {
    setIsContactModalOpen(true);
  };

  return (
    <div className={styles.page}>
      <div className={styles.pageHeader}>
        <div>
          <h1 className={styles.title}>Demand Forecast</h1>
          <p className={styles.subtitle}>Sales forecasting and inventory optimization</p>
        </div>
        <div className={styles.productSelector}>
          <ProductSelector
            products={products}
            selected={selectedProductId ? [selectedProductId] : []}
            onChange={(ids) => setSelectedProductId(ids.length > 0 ? ids[0] : null)}
            placeholder="Select a product..."
            loading={productsLoading}
          />
        </div>
      </div>

      {!selectedProductId ? (
        <div className={styles.emptyState}>
          <div className={styles.emptyIcon}>🔮</div>
          <h2>Select a Product</h2>
          <p>Choose a product from the dropdown above to view demand forecasts</p>
        </div>
      ) : (
        <div className={styles.content}>
          {/* Forecast Chart */}
          <div className={styles.section}>
            <ForecastChart
              data={forecastData}
              isLoading={forecastLoading}
              horizon={horizon}
              onHorizonChange={setHorizon}
            />
          </div>

          {/* Inventory Alerts */}
          <div className={styles.section}>
            <InventoryAlerts
              data={inventoryData}
              isLoading={inventoryLoading}
              onDismiss={handleDismissAlert}
              onTakeAction={handleTakeAction}
            />
          </div>

          {/* Two Column Section */}
          <div className={styles.twoColumn}>
            {/* Demand-Supply Gap */}
            <div className={styles.section}>
              <DemandSupplyGap
                data={forecastData?.gapAnalysis}
                isLoading={forecastLoading}
                timeRange={timeRange}
                onTimeRangeChange={setTimeRange}
              />
            </div>

            {/* Accuracy Metrics */}
            <div className={styles.section}>
              <AccuracyMetrics
                data={forecastData?.accuracy}
                isLoading={forecastLoading}
              />
            </div>
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
