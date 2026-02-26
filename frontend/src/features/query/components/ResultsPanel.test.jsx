import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '../../../test/utils';
import userEvent from '@testing-library/user-event';
import { ResultsPanel } from './ResultsPanel';

describe('ResultsPanel', () => {
  const mockResults = {
    summary: {
      text: 'Your top products generated $50,000 in revenue this month.',
      keyFindings: [
        'Product A leads with 40% of sales',
        'Revenue increased 15% vs last month',
      ],
    },
    insights: [
      {
        title: 'Top Performer',
        description: 'Product A is your best seller',
        value: '$20,000',
        change: 15,
        trend: 'up',
        variant: 'success',
      },
      {
        title: 'Declining Sales',
        description: 'Product B sales dropped',
        value: '$5,000',
        change: -10,
        trend: 'down',
        variant: 'warning',
      },
    ],
    data: [
      { id: 1, product: 'Product A', revenue: 20000, units: 500 },
      { id: 2, product: 'Product B', revenue: 5000, units: 100 },
    ],
    columns: [
      { key: 'product', label: 'Product' },
      { key: 'revenue', label: 'Revenue' },
      { key: 'units', label: 'Units Sold' },
    ],
    visualization: {
      type: 'line',
      data: [
        { name: 'Jan', value: 10000 },
        { name: 'Feb', value: 15000 },
        { name: 'Mar', value: 20000 },
      ],
    },
    actionItems: [
      {
        title: 'Increase inventory for Product A',
        description: 'Stock levels are running low',
        priority: 'high',
      },
      {
        title: 'Review pricing for Product B',
        description: 'Consider promotional pricing',
        priority: 'medium',
      },
    ],
  };

  it('returns null when no results provided', () => {
    const { container } = render(<ResultsPanel results={null} />);
    
    // ResultsPanel returns null, but ToastContainer is still rendered by providers
    expect(screen.queryByText('Query Results')).not.toBeInTheDocument();
  });

  it('renders results panel header', () => {
    render(<ResultsPanel results={mockResults} />);
    
    expect(screen.getByText('Query Results')).toBeInTheDocument();
  });

  it('renders executive summary section', () => {
    render(<ResultsPanel results={mockResults} />);
    
    // Use getAllByText since "Executive Summary" appears in both section header and component
    const summaryElements = screen.getAllByText('Executive Summary');
    expect(summaryElements.length).toBeGreaterThan(0);
    expect(screen.getByText(/Your top products generated/)).toBeInTheDocument();
  });

  it('renders insights section', () => {
    render(<ResultsPanel results={mockResults} />);
    
    expect(screen.getByText('Key Insights')).toBeInTheDocument();
    expect(screen.getByText('Top Performer')).toBeInTheDocument();
    expect(screen.getByText('Declining Sales')).toBeInTheDocument();
  });

  it('renders data table section', () => {
    render(<ResultsPanel results={mockResults} />);
    
    expect(screen.getByText('Detailed Data')).toBeInTheDocument();
  });

  it('renders visualization section', () => {
    render(<ResultsPanel results={mockResults} />);
    
    expect(screen.getByText('Visualization')).toBeInTheDocument();
  });

  it('renders action items section', () => {
    render(<ResultsPanel results={mockResults} />);
    
    expect(screen.getByText('Recommended Actions')).toBeInTheDocument();
    expect(screen.getByText('Increase inventory for Product A')).toBeInTheDocument();
    expect(screen.getByText('Review pricing for Product B')).toBeInTheDocument();
  });

  it('toggles section expansion', async () => {
    const user = userEvent.setup();
    render(<ResultsPanel results={mockResults} />);
    
    // Find the section header button (not the inner component title)
    const summaryButton = screen.getByRole('button', { name: /Executive Summary/i });
    
    // Summary should be expanded by default
    expect(screen.getByText(/Your top products generated/)).toBeInTheDocument();
    
    // Click to collapse
    await user.click(summaryButton);
    
    // Summary content should be hidden
    expect(screen.queryByText(/Your top products generated/)).not.toBeInTheDocument();
    
    // Click to expand again
    await user.click(summaryButton);
    
    // Summary content should be visible
    expect(screen.getByText(/Your top products generated/)).toBeInTheDocument();
  });

  it('shows export button when onExport provided', () => {
    const mockOnExport = vi.fn();
    render(<ResultsPanel results={mockResults} onExport={mockOnExport} />);
    
    expect(screen.getByText('Export')).toBeInTheDocument();
  });

  it('calls onExport when export button is clicked', async () => {
    const user = userEvent.setup();
    const mockOnExport = vi.fn();
    
    render(<ResultsPanel results={mockResults} onExport={mockOnExport} />);
    
    const exportButton = screen.getByText('Export');
    await user.click(exportButton);
    
    expect(mockOnExport).toHaveBeenCalledWith('pdf', mockResults);
  });

  it('shows share button when onShare provided', () => {
    const mockOnShare = vi.fn();
    render(<ResultsPanel results={mockResults} onShare={mockOnShare} />);
    
    expect(screen.getByText('Share')).toBeInTheDocument();
  });

  it('calls onShare when share button is clicked', async () => {
    const user = userEvent.setup();
    const mockOnShare = vi.fn();
    
    render(<ResultsPanel results={mockResults} onShare={mockOnShare} />);
    
    const shareButton = screen.getByText('Share');
    await user.click(shareButton);
    
    expect(mockOnShare).toHaveBeenCalled();
  });

  it('does not render sections when data is missing', () => {
    const minimalResults = {
      summary: {
        text: 'Summary only',
        keyFindings: [],
      },
    };
    
    render(<ResultsPanel results={minimalResults} />);
    
    // Use getAllByText since "Executive Summary" appears twice
    const summaryElements = screen.getAllByText('Executive Summary');
    expect(summaryElements.length).toBeGreaterThan(0);
    expect(screen.queryByText('Key Insights')).not.toBeInTheDocument();
    expect(screen.queryByText('Detailed Data')).not.toBeInTheDocument();
    expect(screen.queryByText('Visualization')).not.toBeInTheDocument();
    expect(screen.queryByText('Recommended Actions')).not.toBeInTheDocument();
  });

  it('renders all insight cards', () => {
    render(<ResultsPanel results={mockResults} />);
    
    expect(screen.getByText('Top Performer')).toBeInTheDocument();
    expect(screen.getByText('Product A is your best seller')).toBeInTheDocument();
    expect(screen.getByText('Declining Sales')).toBeInTheDocument();
    expect(screen.getByText('Product B sales dropped')).toBeInTheDocument();
  });

  it('displays action item priorities', () => {
    render(<ResultsPanel results={mockResults} />);
    
    expect(screen.getByText('high')).toBeInTheDocument();
    expect(screen.getByText('medium')).toBeInTheDocument();
  });

  it('applies custom className', () => {
    const { container } = render(
      <ResultsPanel results={mockResults} className="custom-class" />
    );
    
    const panel = container.firstChild;
    expect(panel.className).toContain('custom-class');
  });

  it('all sections are expanded by default', () => {
    render(<ResultsPanel results={mockResults} />);
    
    // Check that content from all sections is visible
    expect(screen.getByText(/Your top products generated/)).toBeInTheDocument();
    expect(screen.getByText('Top Performer')).toBeInTheDocument();
    expect(screen.getByText('Increase inventory for Product A')).toBeInTheDocument();
  });
});
