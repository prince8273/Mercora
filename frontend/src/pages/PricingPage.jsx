import React, { useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { ProductSelector } from '../components/molecules/ProductSelector';
import { Button } from '../components/atoms/Button';
import { formatPrice } from '../utils/currency';
import { pricingService } from '../services/pricingService';
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
import ContactSupportModal from '../components/modals/ContactSupportModal';
import styles from './PricingPage.module.css';

export default function PricingPage() {
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [timeRange, setTimeRange] = useState('30d');
  const [filters, setFilters] = useState({});
  const [appliedRecommendationId, setAppliedRecommendationId] = useState(null);
  const [appliedRecommendations, setAppliedRecommendations] = useState(new Set());
  const [isContactModalOpen, setIsContactModalOpen] = useState(false);

  // Get query client for cache invalidation
  const queryClient = useQueryClient();

  // Enable real-time updates for pricing
  usePricingRealtime(false); // Set to true to show notifications on updates

  // Fetch products list
  const { data: productsData, isLoading: productsLoading } = useProducts();
  const products = productsData || [];

  // Auto-select first product when products load
  React.useEffect(() => {
    if (products.length > 0 && !selectedProduct) {
      // Convert price to number and ensure proper data structure
      const firstProduct = {
        ...products[0],
        price: parseFloat(products[0].price) || 0
      };
      console.log('Auto-selecting product:', firstProduct.id, firstProduct.name);
      console.log('Product price:', firstProduct.price);
      setSelectedProduct(firstProduct);
      // Reset applied recommendations when switching products
      setAppliedRecommendations(new Set());
    }
  }, [products, selectedProduct]);

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

  // Debug: Log price mismatches
  React.useEffect(() => {
    if (selectedProduct && recommendations?.recommendations && trendData) {
      console.log('=== PRICE DEBUG ===');
      console.log('Selected Product Price:', selectedProduct.price);
      console.log('Selected Product Object:', selectedProduct);
      console.log('Recommendations API Current Price:', recommendations.recommendations[0]?.current_price);
      console.log('Recommendations Debug Info:', recommendations.debug_info);
      console.log('Market Analysis Current Price:', recommendations.market_analysis?.current_price);
      
      // Check trend data
      const chartData = trendData?.data || trendData?.trends || [];
      const latestChartPoint = chartData[chartData.length - 1];
      console.log('Latest Chart Data Point:', latestChartPoint);
      console.log('Chart Latest Price:', latestChartPoint?.yourPrice || latestChartPoint?.price);
      
      console.log('Chart should show:', selectedProduct.price);
      console.log('Recommendations should use:', selectedProduct.price);
      
      // Check if there's a significant price difference
      const apiPrice = recommendations.recommendations[0]?.current_price;
      const frontendPrice = selectedProduct.price;
      const chartPrice = latestChartPoint?.yourPrice || latestChartPoint?.price;
      
      if (apiPrice && Math.abs(apiPrice - frontendPrice) > 1) {
        console.warn('⚠️ API vs FRONTEND PRICE MISMATCH:');
        console.warn('Frontend price:', frontendPrice);
        console.warn('API price:', apiPrice);
        console.warn('Difference:', Math.abs(apiPrice - frontendPrice));
      }
      
      if (chartPrice && Math.abs(chartPrice - frontendPrice) > 1) {
        console.warn('⚠️ CHART vs FRONTEND PRICE MISMATCH:');
        console.warn('Frontend price:', frontendPrice);
        console.warn('Chart price:', chartPrice);
        console.warn('Difference:', Math.abs(chartPrice - frontendPrice));
      }
    }
  }, [selectedProduct, recommendations, trendData]);

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

  const handleAcceptRecommendation = async (recommendation) => {
    console.log('Accept recommendation:', recommendation);
    
    if (selectedProduct && recommendation.suggested_price) {
      try {
        // Real API call to apply pricing
        const result = await pricingService.applyPricing(
          selectedProduct.id, 
          recommendation.suggested_price
        );
        
        if (result.success) {
          // Update the selected product price locally
          const updatedProduct = {
            ...selectedProduct,
            price: recommendation.suggested_price
          };
          setSelectedProduct(updatedProduct);
          
          // Manually update the trend data to show the new price immediately
          const today = new Date().toISOString().split('T')[0];
          
          // Update the trend data in the query cache with proper structure
          queryClient.setQueryData(
            ['pricing', 'trends', selectedProduct.id, timeRange],
            (oldData) => {
              if (!oldData) return oldData;
              
              const trendsArray = oldData.trends || oldData.data || [];
              const lastDataPoint = trendsArray[trendsArray.length - 1];
              
              // Create new data point for today with the updated price
              const newDataPoint = {
                date: today,
                yourPrice: recommendation.suggested_price,
                competitor1: lastDataPoint?.competitor1 || lastDataPoint?.competitor_avg || 0,
                marketDemand: lastDataPoint?.marketDemand || lastDataPoint?.market_demand || 0.8,
                reason: `Applied ${recommendation.title} recommendation`
              };
              
              // Remove any existing data point for today and add the new one
              const filteredTrends = trendsArray.filter(item => item.date !== today);
              const updatedTrends = [...filteredTrends, newDataPoint];
              
              return {
                ...oldData,
                trends: updatedTrends,
                data: updatedTrends,
                current_price: recommendation.suggested_price
              };
            }
          );
          
          // Update recommendations data to use the new current price and filter intelligently
          queryClient.setQueryData(
            ['pricing', 'recommendations', selectedProduct.id],
            (oldRecommendations) => {
              if (!oldRecommendations?.recommendations) return oldRecommendations;
              
              // Filter recommendations based on the new current price
              const filteredRecommendations = oldRecommendations.recommendations
                .filter(rec => {
                  // Remove the applied recommendation
                  if (rec.id === recommendation.id) return false;
                  
                  // Remove any recommendation where suggested price is close to or lower than new current price
                  const priceDifference = Math.abs(rec.suggested_price - recommendation.suggested_price);
                  const isAlreadyApplied = priceDifference < 1; // Within ₹1 difference
                  
                  if (isAlreadyApplied) return false;
                  
                  // Only keep recommendations that suggest meaningfully higher prices (at least 2% more)
                  const minimumIncrease = recommendation.suggested_price * 1.02;
                  return rec.suggested_price > minimumIncrease;
                })
                .map(rec => {
                  // Recalculate remaining recommendations with new current price
                  const newPriceChange = rec.suggested_price - recommendation.suggested_price;
                  const newPriceChangePercent = ((rec.suggested_price - recommendation.suggested_price) / recommendation.suggested_price) * 100;
                  
                  return {
                    ...rec,
                    current_price: recommendation.suggested_price, // Update current price
                    price_change: newPriceChange,
                    price_change_percent: newPriceChangePercent,
                    // Update reasoning to reflect new baseline
                    reasoning: rec.reasoning.replace(
                      /Your price \(\$[\d,]+\.?\d*\)/g, 
                      `Your price (${formatPrice(recommendation.suggested_price)})`
                    )
                  };
                });
              
              return {
                ...oldRecommendations,
                recommendations: filteredRecommendations,
                market_analysis: {
                  ...oldRecommendations.market_analysis,
                  current_price: recommendation.suggested_price
                }
              };
            }
          );
          
          // Also invalidate queries to ensure fresh data on next load
          await Promise.all([
            queryClient.invalidateQueries({ 
              queryKey: ['pricing', 'competitors', selectedProduct.id] 
            }),
            queryClient.invalidateQueries({ 
              queryKey: ['products'] 
            }),
          ]);
          
          // Don't refetch recommendations immediately - let our manual update persist
          // The next time the user navigates or refreshes, it will get fresh data from API
          
          // Get current recommendations data for the success message
          const currentRecommendations = queryClient.getQueryData(['pricing', 'recommendations', selectedProduct.id]);
          const remainingRecommendations = currentRecommendations?.recommendations?.filter(rec => 
            rec.id !== recommendation.id && rec.suggested_price > recommendation.suggested_price
          ).length || 0;
          
          let successMessage = `✅ Pricing updated successfully!\nOld Price: ${formatPrice(result.old_price)}\nNew Price: ${formatPrice(result.new_price)}\nChange: ${result.price_change_percent > 0 ? '+' : ''}${result.price_change_percent.toFixed(1)}%`;
          
          if (remainingRecommendations === 0) {
            successMessage += `\n\n🎯 No further price increases recommended at this time.`;
          } else {
            successMessage += `\n\n📈 ${remainingRecommendations} higher-price recommendation${remainingRecommendations > 1 ? 's' : ''} still available.`;
          }
          
          // Track this recommendation as applied
          setAppliedRecommendations(prev => new Set([...prev, recommendation.id]));
          
          // Mark this recommendation as applied for visual feedback
          setAppliedRecommendationId(recommendation.id);
          
          alert(successMessage);
          
          // Clear the applied recommendation after 3 seconds
          setTimeout(() => {
            setAppliedRecommendationId(null);
          }, 3000);
          
        } else {
          throw new Error('Failed to update price');
        }
        
      } catch (error) {
        console.error('Failed to apply pricing:', error);
        alert('❌ Failed to update pricing. Please try again.');
      }
    }
  };

  const handleRejectRecommendation = (recommendationId) => {
    console.log('Dismiss recommendation:', recommendationId);
    
    if (!recommendationId) {
      console.error('No recommendation ID provided');
      return;
    }
    
    // Update the cache to remove the dismissed recommendation immediately
    queryClient.setQueryData(
      ['pricing', 'recommendations', selectedProduct?.id],
      (oldRecommendations) => {
        if (!oldRecommendations?.recommendations) return oldRecommendations;
        
        console.log('Filtering out recommendation:', recommendationId);
        const filteredRecommendations = oldRecommendations.recommendations.filter(
          rec => rec.id !== recommendationId
        );
        
        console.log('Remaining recommendations:', filteredRecommendations.length);
        
        return {
          ...oldRecommendations,
          recommendations: filteredRecommendations
        };
      }
    );
    
    // Also add to the dismissed set for additional filtering
    setAppliedRecommendations(prev => {
      const newSet = new Set([...prev, recommendationId]);
      console.log('Updated dismissed recommendations:', newSet);
      return newSet;
    });
    
    // Show feedback message
    console.log('✅ Recommendation dismissed successfully!');
  };

  const handleContactSupport = () => {
    setIsContactModalOpen(true);
  };

  return (
    <div className={styles.page}>
      <div className={styles.container}>
        {/* Header Section */}
        <div className={styles.header}>
          <div className={styles.headerTop}>
            <div>
              <h1 className={styles.title}>Pricing Intelligence</h1>
              <p className={styles.subtitle}>
                AI-powered pricing analysis and recommendations for optimal revenue
              </p>
            </div>
            <button onClick={handleRefresh} className={styles.refreshButton}>
              <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                />
              </svg>
              Refresh Data
            </button>
          </div>

          {/* Product Selector */}
          <div className={styles.productSelectorWrapper}>
            <label className={styles.selectorLabel}>Select Product to Analyze</label>
            <ProductSelector
              products={products}
              selected={selectedProduct ? [selectedProduct.id] : []}
              onChange={(selectedIds) => {
                if (selectedIds.length > 0) {
                  const product = products.find(p => p.id === selectedIds[0]);
                  if (product) {
                    const normalizedProduct = {
                      ...product,
                      price: parseFloat(product.price) || 0
                    };
                    setSelectedProduct(normalizedProduct);
                    setAppliedRecommendations(new Set());
                  }
                } else {
                  setSelectedProduct(null);
                  setAppliedRecommendations(new Set());
                }
              }}
              placeholder="Choose a product to view pricing insights..."
              multiple={false}
              loading={productsLoading}
            />
          </div>
        </div>

        {!selectedProduct ? (
          /* Enhanced Empty State */
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
                strokeWidth={1.5}
                d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
              />
            </svg>
            <h2 className={styles.emptyTitle}>Welcome to Pricing Intelligence</h2>
            <p className={styles.emptyText}>
              Select a product above to unlock powerful AI-driven pricing insights, competitive analysis, 
              and revenue optimization recommendations tailored to your market position.
            </p>
            <div className={styles.featureList}>
              <div className={styles.feature}>
                <svg width="24" height="24" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                <span>Real-time competitor tracking</span>
              </div>
              <div className={styles.feature}>
                <svg width="24" height="24" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                <span>Historical trend analysis</span>
              </div>
              <div className={styles.feature}>
                <svg width="24" height="24" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                <span>AI-powered recommendations</span>
              </div>
              <div className={styles.feature}>
                <svg width="24" height="24" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                <span>Promotion effectiveness</span>
              </div>
            </div>
          </div>
        ) : (
          /* Main Dashboard Content */
          <div className={styles.mainContent}>
            {/* Top Section: Chart + Recommendations */}
            <div className={styles.topSection}>
              {/* Price Trend Chart */}
              <div className={styles.chartCard}>
                <div className={styles.chartHeader}>
                  <h2 className={styles.chartTitle}>Price Trends</h2>
                  <div className={styles.priceIndicator}>
                    Current: {formatPrice(selectedProduct.price)}
                  </div>
                </div>
                {trendLoading ? (
                  <div className={styles.loadingCard}>
                    <div className={styles.loadingSpinner}></div>
                  </div>
                ) : trendError ? (
                  <div className={styles.errorState}>
                    <p>Failed to load price trends</p>
                    <Button onClick={() => window.location.reload()} size="sm">
                      Retry
                    </Button>
                  </div>
                ) : (
                  <PriceTrendChart
                    data={(() => {
                      const chartData = trendData?.data || trendData?.trends || [];
                      const today = new Date().toISOString().split('T')[0];
                      
                      if (selectedProduct?.price) {
                        if (chartData.length > 0) {
                          const latestPoint = chartData[chartData.length - 1];
                          
                          if (latestPoint.date === today) {
                            return chartData.map((point, index) => 
                              index === chartData.length - 1 
                                ? { ...point, yourPrice: selectedProduct.price }
                                : point
                            );
                          } else {
                            return [...chartData, {
                              date: today,
                              yourPrice: selectedProduct.price,
                              competitor1: latestPoint?.competitor1 || latestPoint?.competitor_avg || 0,
                              marketDemand: latestPoint?.marketDemand || latestPoint?.market_demand || 0.8,
                              reason: 'Current price'
                            }];
                          }
                        } else {
                          return [{
                            date: today,
                            yourPrice: selectedProduct.price,
                            competitor1: 0,
                            marketDemand: 0.8,
                            reason: 'Current price'
                          }];
                        }
                      }
                      
                      return chartData;
                    })()}
                    yourPriceKey="yourPrice"
                    competitorKeys={['competitor1']}
                    timeRange={timeRange}
                    onTimeRangeChange={setTimeRange}
                    loading={trendLoading}
                    error={trendError}
                    key={`${selectedProduct?.id}-${selectedProduct?.price}`}
                  />
                )}
              </div>

              {/* Recommendations Panel */}
              <div className={styles.recommendationsCard}>
                <div className={styles.recommendationsHeader}>
                  <h2 className={styles.recommendationsTitle}>
                    Recommendations
                    {recommendations?.recommendations && (
                      <span style={{ fontSize: '0.7em', color: '#718096', fontWeight: 'normal', marginLeft: '0.5rem' }}>
                        ({recommendations.recommendations.filter(rec => !appliedRecommendations.has(rec.id)).length})
                      </span>
                    )}
                  </h2>
                  <p className={styles.recommendationsSubtitle}>
                    AI-powered pricing suggestions based on market analysis
                  </p>
                </div>
                {recommendationsLoading ? (
                  <div className={styles.loadingCard}>
                    <div className={styles.loadingSpinner}></div>
                  </div>
                ) : recommendationsError ? (
                  <div className={styles.errorState}>
                    <p>Failed to load recommendations</p>
                    <Button onClick={refetchRecommendations} size="sm">
                      Retry
                    </Button>
                  </div>
                ) : (
                  <RecommendationPanel
                    recommendations={(recommendations?.recommendations || [])
                      .filter(rec => !appliedRecommendations.has(rec.id))
                      .map(rec => {
                        const actualCurrentPrice = selectedProduct?.price || rec.current_price;
                        const priceChange = rec.suggested_price - actualCurrentPrice;
                        const priceChangePercent = ((rec.suggested_price - actualCurrentPrice) / actualCurrentPrice) * 100;
                        
                        return {
                          ...rec,
                          current_price: actualCurrentPrice,
                          price_change: priceChange,
                          price_change_percent: priceChangePercent,
                          reasoning: rec.reasoning.replace(
                            /Your price \(\$?[\d,]+\.?\d*\)/g,
                            `Your price (${formatPrice(actualCurrentPrice)})`
                          )
                        };
                      })
                    }
                    onAccept={handleAcceptRecommendation}
                    onReject={handleRejectRecommendation}
                  />
                )}
              </div>
            </div>

            {/* Bottom Section: Competitor Matrix + Promotions */}
            <div className={styles.bottomSection}>
              {/* Competitor Matrix */}
              <div className={styles.competitorCard}>
                <h2 className={styles.cardTitle}>Competitive Analysis</h2>
                {competitorLoading ? (
                  <div className={styles.loadingCard}>
                    <div className={styles.loadingSpinner}></div>
                  </div>
                ) : competitorError ? (
                  <div className={styles.errorState}>
                    <p>Failed to load competitor data</p>
                    <Button onClick={refetchCompetitor} size="sm">
                      Retry
                    </Button>
                  </div>
                ) : recommendations?.competitors ? (
                  <CompetitorMatrix
                    data={[{
                      productName: selectedProduct?.name || 'Selected Product',
                      sku: selectedProduct?.sku || '',
                      yourPrice: selectedProduct?.price || 0,
                      competitorPrices: recommendations.competitors.reduce((acc, comp, index) => {
                        acc[`comp_${index + 1}`] = comp.price;
                        return acc;
                      }, {})
                    }]}
                    competitors={recommendations.competitors.map((comp, index) => ({
                      id: `comp_${index + 1}`,
                      name: comp.name || `Competitor ${index + 1}`,
                      rating: comp.rating,
                      market_share: comp.market_share
                    }))}
                    loading={recommendationsLoading}
                    error={recommendationsError}
                    onExport={handleExportMatrix}
                  />
                ) : (
                  <div className={styles.errorState}>
                    <p>No competitor data available</p>
                  </div>
                )}
              </div>

              {/* Promotion Tracker */}
              <div className={styles.promotionsCard}>
                <h2 className={styles.cardTitle}>Promotion Performance</h2>
                {promotionsLoading ? (
                  <div className={styles.loadingCard}>
                    <div className={styles.loadingSpinner}></div>
                  </div>
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
