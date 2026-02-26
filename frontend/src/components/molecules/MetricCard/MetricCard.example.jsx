import React from 'react';
import { MetricCard } from './MetricCard';

/**
 * MetricCard Component Examples
 * 
 * This file demonstrates various use cases of the MetricCard component.
 * Copy these examples to use in your pages.
 */

export const MetricCardExamples = () => {
  return (
    <div style={{ 
      display: 'grid', 
      gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
      gap: '1rem',
      padding: '2rem'
    }}>
      {/* Example 1: Currency with positive change */}
      <MetricCard
        title="Total Revenue"
        value={125432}
        change={5.2}
        trend="up"
        format="currency"
      />

      {/* Example 2: Percentage with negative change */}
      <MetricCard
        title="Conversion Rate"
        value={3.4}
        change={-1.2}
        trend="down"
        format="percentage"
      />

      {/* Example 3: Number with icon */}
      <MetricCard
        title="Active Users"
        value={1234}
        change={12.5}
        trend="up"
        format="number"
        icon={
          <svg viewBox="0 0 20 20" fill="currentColor">
            <path d="M9 6a3 3 0 11-6 0 3 3 0 016 0zM17 6a3 3 0 11-6 0 3 3 0 016 0zM12.93 17c.046-.327.07-.66.07-1a6.97 6.97 0 00-1.5-4.33A5 5 0 0119 16v1h-6.07zM6 11a5 5 0 015 5v1H1v-1a5 5 0 015-5z" />
          </svg>
        }
      />

      {/* Example 4: No change indicator */}
      <MetricCard
        title="Inventory Items"
        value={8765}
        format="number"
      />

      {/* Example 5: Loading state */}
      <MetricCard
        title="Loading..."
        loading={true}
      />

      {/* Example 6: Neutral change */}
      <MetricCard
        title="Margin"
        value={23.5}
        change={0}
        trend="neutral"
        format="percentage"
      />

      {/* Example 7: Large currency value */}
      <MetricCard
        title="GMV"
        value={2456789}
        change={8.3}
        trend="up"
        format="currency"
        icon={
          <svg viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M4 4a2 2 0 00-2 2v4a2 2 0 002 2V6h10a2 2 0 00-2-2H4zm2 6a2 2 0 012-2h8a2 2 0 012 2v4a2 2 0 01-2 2H8a2 2 0 01-2-2v-4zm6 4a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd" />
          </svg>
        }
      />

      {/* Example 8: Small percentage */}
      <MetricCard
        title="Bounce Rate"
        value={42.3}
        change={-3.1}
        trend="down"
        format="percentage"
      />
    </div>
  );
};

/**
 * Usage in a real page:
 * 
 * import { MetricCard } from '@/components/molecules/MetricCard';
 * import { useDashboardOverview } from '@/hooks/useDashboard';
 * 
 * function DashboardPage() {
 *   const { data, isLoading } = useDashboardOverview();
 * 
 *   return (
 *     <div className="kpi-grid">
 *       <MetricCard
 *         title="GMV"
 *         value={data?.gmv}
 *         change={data?.gmvChange}
 *         trend={data?.gmvChange > 0 ? 'up' : 'down'}
 *         format="currency"
 *         loading={isLoading}
 *       />
 *       <MetricCard
 *         title="Margin"
 *         value={data?.margin}
 *         change={data?.marginChange}
 *         trend={data?.marginChange > 0 ? 'up' : 'down'}
 *         format="percentage"
 *         loading={isLoading}
 *       />
 *     </div>
 *   );
 * }
 */
