import React from 'react';
import { QuickInsights } from './QuickInsights';

// Example data for demonstration
const sampleInsights = [
  {
    id: '1',
    type: 'trend',
    title: 'Revenue Growth Accelerating',
    summary: 'Your revenue has increased by 28% this month compared to last month.',
    details: 'This growth is primarily driven by increased sales in the Electronics category, particularly in the Smart Home subcategory. The average order value has also increased by 12%.',
    metrics: [
      { label: 'Revenue Growth', value: '+28%' },
      { label: 'Electronics Growth', value: '+45%' },
      { label: 'Avg Order Value', value: '+12%' },
    ],
    recommendation: 'Consider increasing inventory for top-performing products in Electronics to capitalize on this trend.',
  },
  {
    id: '2',
    type: 'opportunity',
    title: 'Pricing Opportunity Detected',
    summary: 'You can increase prices on 15 products without losing competitiveness.',
    details: 'Analysis shows that your prices are significantly lower than competitors for several high-demand products. Increasing prices by 5-10% would still keep you competitive while improving margins.',
    metrics: [
      { label: 'Products Identified', value: '15' },
      { label: 'Potential Revenue Increase', value: '+$8,500/month' },
      { label: 'Margin Improvement', value: '+3.2%' },
    ],
    recommendation: 'Review the pricing recommendations in the Pricing Intelligence section and implement gradual price increases.',
  },
  {
    id: '3',
    type: 'warning',
    title: 'Inventory Imbalance Detected',
    summary: '8 products are overstocked while 5 products are at risk of stockout.',
    details: 'Your inventory distribution is not aligned with current demand patterns. Some slow-moving products have excess stock, while fast-moving products are running low.',
    metrics: [
      { label: 'Overstocked Products', value: '8' },
      { label: 'At-Risk Products', value: '5' },
      { label: 'Excess Inventory Value', value: '$12,400' },
    ],
    recommendation: 'Consider running promotions on overstocked items and expediting reorders for at-risk products.',
  },
  {
    id: '4',
    type: 'alert',
    title: 'Customer Sentiment Declining',
    summary: 'Average review rating has dropped from 4.5 to 4.2 stars this month.',
    details: 'Recent reviews indicate concerns about shipping delays and product quality for certain items. The decline is concentrated in 3 specific products.',
    metrics: [
      { label: 'Rating Change', value: '-0.3 stars' },
      { label: 'Negative Reviews', value: '12' },
      { label: 'Affected Products', value: '3' },
    ],
    recommendation: 'Investigate the quality issues with affected products and improve shipping processes to address customer concerns.',
  },
  {
    id: '5',
    type: 'success',
    title: 'Conversion Rate Improving',
    summary: 'Your conversion rate has increased to 3.8%, up from 3.2% last month.',
    details: 'The improvement is attributed to better product descriptions, improved images, and faster page load times. Mobile conversion rate has seen the most significant improvement.',
    metrics: [
      { label: 'Overall Conversion', value: '3.8%' },
      { label: 'Mobile Conversion', value: '+25%' },
      { label: 'Desktop Conversion', value: '+12%' },
    ],
    recommendation: 'Continue optimizing product pages and consider applying the same improvements to underperforming listings.',
  },
];

export const QuickInsightsExamples = () => {
  return (
    <div style={{ padding: '2rem', display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      <h1>QuickInsights Examples</h1>

      {/* Example 1: Full Insights */}
      <div>
        <h2>Quick Insights with All Types</h2>
        <div style={{ maxWidth: '700px' }}>
          <QuickInsights insights={sampleInsights} />
        </div>
      </div>

      {/* Example 2: Loading State */}
      <div>
        <h2>Loading State</h2>
        <div style={{ maxWidth: '700px' }}>
          <QuickInsights loading={true} />
        </div>
      </div>

      {/* Example 3: Empty State */}
      <div>
        <h2>Empty State (No Insights)</h2>
        <div style={{ maxWidth: '700px' }}>
          <QuickInsights insights={[]} />
        </div>
      </div>

      {/* Example 4: Positive Insights Only */}
      <div>
        <h2>Positive Insights Only</h2>
        <div style={{ maxWidth: '700px' }}>
          <QuickInsights
            insights={sampleInsights.filter((i) => ['trend', 'opportunity', 'success'].includes(i.type))}
          />
        </div>
      </div>

      {/* Example 5: Warnings and Alerts */}
      <div>
        <h2>Warnings and Alerts</h2>
        <div style={{ maxWidth: '700px' }}>
          <QuickInsights
            insights={sampleInsights.filter((i) => ['warning', 'alert'].includes(i.type))}
          />
        </div>
      </div>

      {/* Example 6: Single Insight */}
      <div>
        <h2>Single Insight</h2>
        <div style={{ maxWidth: '700px' }}>
          <QuickInsights insights={[sampleInsights[0]]} />
        </div>
      </div>
    </div>
  );
};
