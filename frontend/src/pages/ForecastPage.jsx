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
import styles from './ForecastPage.module.css';

export default function ForecastPage() {
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [horizon, setHorizon] = useState('30d');
  const [timeRange, setTimeRange] = useState('30d');

  // Fetch products list
  const { data: productsData, isLoading: productsLoading } = useProducts();
  const products = productsData || [];

  const { data: forecastData, isLoading: forecastLoading } = useDemandForecast(
    selectedProduct,
    { horizon }
  );

  const { data: inventoryData, isLoading: inventoryLoading } = useInventoryRecommendations(
    selectedProduct
  );

  const handleDismissAlert = (alertId) => {
    console.log('Dismiss alert:', alertId);
    // TODO: Implement alert dismissal
  };

  const handleTakeAction = (alertId) => {
    console.log('Take action on alert:', alertId);
    // TODO: Implement action handling
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
            value={selectedProduct}
            onChange={setSelectedProduct}
            placeholder="Select a product..."
            loading={productsLoading}
          />
        </div>
      </div>

      {!selectedProduct ? (
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
    </div>
  );
}
