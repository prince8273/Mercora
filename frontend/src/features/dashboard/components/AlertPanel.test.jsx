import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '../../../test/utils';
import { AlertPanel } from './AlertPanel';

describe('AlertPanel', () => {
  const mockAlerts = [
    {
      id: '1',
      priority: 'critical',
      title: 'Low Stock Alert',
      message: 'Product XYZ is running low on stock',
      timestamp: '2024-01-01T10:00:00Z',
    },
    {
      id: '2',
      priority: 'warning',
      title: 'Price Change',
      message: 'Competitor lowered price',
      timestamp: '2024-01-01T11:00:00Z',
    },
  ];

  it('renders list of alerts', () => {
    render(<AlertPanel alerts={mockAlerts} />);

    expect(screen.getByText('Low Stock Alert')).toBeInTheDocument();
    expect(screen.getByText('Price Change')).toBeInTheDocument();
  });

  it('calls onDismiss when dismiss button is clicked', () => {
    const onDismiss = vi.fn();
    render(<AlertPanel alerts={mockAlerts} onDismiss={onDismiss} />);

    const dismissButtons = screen.getAllByLabelText(/dismiss/i);
    fireEvent.click(dismissButtons[0]);

    expect(onDismiss).toHaveBeenCalledWith('1');
  });

  it('shows loading skeleton when loading prop is true', () => {
    const { container } = render(<AlertPanel alerts={[]} loading={true} />);

    // Check for skeleton elements
    const skeletons = container.querySelectorAll('[class*="skeleton"]');
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it('shows empty state when no alerts', () => {
    render(<AlertPanel alerts={[]} />);

    expect(screen.getByText(/no alerts/i)).toBeInTheDocument();
  });

  it('displays correct priority indicators', () => {
    render(<AlertPanel alerts={mockAlerts} />);

    // Both alerts should render
    expect(screen.getByText('Low Stock Alert')).toBeInTheDocument();
    expect(screen.getByText('Price Change')).toBeInTheDocument();
  });

  it('expands alert details on click', () => {
    const alertsWithDetails = [
      {
        ...mockAlerts[0],
        details: 'Detailed information about low stock',
      },
    ];

    render(<AlertPanel alerts={alertsWithDetails} />);

    const alertItem = screen.getByText('Low Stock Alert').closest('li');
    fireEvent.click(alertItem);

    expect(screen.getByText('Detailed information about low stock')).toBeInTheDocument();
  });
});
