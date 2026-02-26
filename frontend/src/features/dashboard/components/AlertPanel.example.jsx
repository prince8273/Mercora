import React from 'react';
import { AlertPanel } from './AlertPanel';

// Example data for demonstration
const sampleAlerts = [
  {
    id: '1',
    title: 'Low Stock Alert',
    message: 'Product "Wireless Headphones" is running low on inventory. Only 15 units remaining.',
    details: 'Based on current sales velocity, this product will be out of stock in approximately 3 days. Consider reordering to avoid stockouts.',
    priority: 'critical',
    timestamp: new Date(Date.now() - 1000 * 60 * 30), // 30 minutes ago
    actionUrl: '/inventory/product/123',
    actionLabel: 'View Product',
  },
  {
    id: '2',
    title: 'Price Change Detected',
    message: 'Competitor "TechStore" has reduced price on "Smart Watch Pro" by 15%.',
    details: 'Your current price is $299.99, competitor price is now $254.99. This may impact your competitiveness.',
    priority: 'warning',
    timestamp: new Date(Date.now() - 1000 * 60 * 60 * 2), // 2 hours ago
    actionUrl: '/pricing/product/456',
    actionLabel: 'Review Pricing',
  },
  {
    id: '3',
    title: 'Sales Milestone Reached',
    message: 'Congratulations! You have reached $100,000 in monthly revenue.',
    details: 'This is a 25% increase compared to last month. Your top-performing category is Electronics.',
    priority: 'info',
    timestamp: new Date(Date.now() - 1000 * 60 * 60 * 5), // 5 hours ago
    actionUrl: '/reports/revenue',
    actionLabel: 'View Report',
  },
  {
    id: '4',
    title: 'Review Response Needed',
    message: '3 new customer reviews require your attention.',
    details: 'Responding to customer reviews helps build trust and improve your seller rating.',
    priority: 'medium',
    timestamp: new Date(Date.now() - 1000 * 60 * 60 * 24), // 1 day ago
    actionUrl: '/reviews',
    actionLabel: 'View Reviews',
  },
];

export const AlertPanelExamples = () => {
  const handleDismiss = (alertId) => {
    console.log('Dismiss alert:', alertId);
    // In a real app, this would update state or call an API
  };

  const handleAlertClick = (alert) => {
    console.log('Alert clicked:', alert);
  };

  return (
    <div style={{ padding: '2rem', display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      <h1>AlertPanel Examples</h1>

      {/* Example 1: With Alerts */}
      <div>
        <h2>Alert Panel with Multiple Alerts</h2>
        <div style={{ maxWidth: '600px' }}>
          <AlertPanel
            alerts={sampleAlerts}
            onDismiss={handleDismiss}
            onAlertClick={handleAlertClick}
          />
        </div>
      </div>

      {/* Example 2: Loading State */}
      <div>
        <h2>Loading State</h2>
        <div style={{ maxWidth: '600px' }}>
          <AlertPanel loading={true} />
        </div>
      </div>

      {/* Example 3: Empty State */}
      <div>
        <h2>Empty State (No Alerts)</h2>
        <div style={{ maxWidth: '600px' }}>
          <AlertPanel alerts={[]} />
        </div>
      </div>

      {/* Example 4: Critical Alerts Only */}
      <div>
        <h2>Critical Alerts Only</h2>
        <div style={{ maxWidth: '600px' }}>
          <AlertPanel
            alerts={sampleAlerts.filter((a) => a.priority === 'critical')}
            onDismiss={handleDismiss}
          />
        </div>
      </div>

      {/* Example 5: Single Alert */}
      <div>
        <h2>Single Alert</h2>
        <div style={{ maxWidth: '600px' }}>
          <AlertPanel
            alerts={[sampleAlerts[0]]}
            onDismiss={handleDismiss}
          />
        </div>
      </div>
    </div>
  );
};
