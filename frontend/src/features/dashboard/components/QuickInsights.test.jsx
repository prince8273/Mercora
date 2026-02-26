import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '../../../test/utils';
import { QuickInsights } from './QuickInsights';

describe('QuickInsights', () => {
  const mockInsights = [
    {
      id: '1',
      type: 'trend',
      title: 'Sales Increasing',
      summary: 'Sales are up 15% this week',
      details: 'Detailed analysis of sales trend...',
      metrics: [
        { label: 'Growth', value: '+15%' },
        { label: 'Revenue', value: '$50,000' },
      ],
    },
    {
      id: '2',
      type: 'warning',
      title: 'Inventory Low',
      summary: '5 products need restocking',
      details: 'Products running low on inventory...',
    },
  ];

  it('renders list of insights', () => {
    render(<QuickInsights insights={mockInsights} />);

    expect(screen.getByText('Sales Increasing')).toBeInTheDocument();
    expect(screen.getByText('Inventory Low')).toBeInTheDocument();
  });

  it('displays insight summaries', () => {
    render(<QuickInsights insights={mockInsights} />);

    expect(screen.getByText('Sales are up 15% this week')).toBeInTheDocument();
    expect(screen.getByText('5 products need restocking')).toBeInTheDocument();
  });

  it('expands insight details on click', () => {
    render(<QuickInsights insights={mockInsights} />);

    const firstInsightButton = screen.getByText('Sales Increasing').closest('button');
    fireEvent.click(firstInsightButton);

    expect(screen.getByText('Detailed analysis of sales trend...')).toBeInTheDocument();
  });

  it('displays metrics when expanded', () => {
    render(<QuickInsights insights={mockInsights} />);

    const firstInsightButton = screen.getByText('Sales Increasing').closest('button');
    fireEvent.click(firstInsightButton);

    expect(screen.getByText('Growth:')).toBeInTheDocument();
    expect(screen.getByText('+15%')).toBeInTheDocument();
    expect(screen.getByText('Revenue:')).toBeInTheDocument();
    expect(screen.getByText('$50,000')).toBeInTheDocument();
  });

  it('shows loading skeleton when loading prop is true', () => {
    const { container } = render(<QuickInsights insights={[]} loading={true} />);

    // Check for skeleton elements
    const skeletons = container.querySelectorAll('[class*="skeleton"]');
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it('shows empty state when no insights', () => {
    render(<QuickInsights insights={[]} />);

    expect(screen.getByText(/no insights/i)).toBeInTheDocument();
  });

  it('displays correct icons for insight types', () => {
    const { container } = render(<QuickInsights insights={mockInsights} />);

    // Check that SVG icons are rendered
    const icons = container.querySelectorAll('svg');
    expect(icons.length).toBeGreaterThan(0);
  });
});
