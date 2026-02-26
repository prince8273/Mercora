import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '../../../test/utils';
import userEvent from '@testing-library/user-event';
import { ExecutionPanel } from './ExecutionPanel';

describe('ExecutionPanel', () => {
  it('renders with initial progress', () => {
    render(<ExecutionPanel progress={0} status="active" />);
    
    expect(screen.getByText('Query Execution')).toBeInTheDocument();
    expect(screen.getByText('Starting...')).toBeInTheDocument();
  });

  it('displays progress percentage', () => {
    render(<ExecutionPanel progress={45} status="active" />);
    
    // "45%" appears in both label and percentage display
    const percentageElements = screen.getAllByText(/45/);
    expect(percentageElements.length).toBeGreaterThan(0);
  });

  it('shows completion status at 100%', () => {
    render(<ExecutionPanel progress={100} status="active" />);
    
    expect(screen.getByText('Complete')).toBeInTheDocument();
    expect(screen.getByText('Query completed successfully')).toBeInTheDocument();
  });

  it('displays estimated time remaining', () => {
    render(<ExecutionPanel progress={30} status="active" estimatedTime={120} />);
    
    expect(screen.getByText(/2m 0s remaining/)).toBeInTheDocument();
  });

  it('formats time correctly for seconds', () => {
    render(<ExecutionPanel progress={50} status="active" estimatedTime={45} />);
    
    expect(screen.getByText(/45s remaining/)).toBeInTheDocument();
  });

  it('renders AgentStatus component', () => {
    render(
      <ExecutionPanel
        progress={25}
        status="active"
        currentActivity="Analyzing data..."
      />
    );
    
    expect(screen.getByText('Analyzing data...')).toBeInTheDocument();
  });

  it('shows cancel button when in progress', () => {
    const mockOnCancel = vi.fn();
    render(
      <ExecutionPanel
        progress={50}
        status="active"
        onCancel={mockOnCancel}
      />
    );
    
    expect(screen.getByText('Cancel Query')).toBeInTheDocument();
  });

  it('calls onCancel when cancel button is clicked', async () => {
    const user = userEvent.setup();
    const mockOnCancel = vi.fn();
    
    render(
      <ExecutionPanel
        progress={50}
        status="active"
        onCancel={mockOnCancel}
      />
    );
    
    const cancelButton = screen.getByText('Cancel Query');
    await user.click(cancelButton);
    
    expect(mockOnCancel).toHaveBeenCalled();
  });

  it('hides cancel button when complete', () => {
    const mockOnCancel = vi.fn();
    render(
      <ExecutionPanel
        progress={100}
        status="active"
        onCancel={mockOnCancel}
      />
    );
    
    expect(screen.queryByText('Cancel Query')).not.toBeInTheDocument();
  });

  it('displays error state', () => {
    render(
      <ExecutionPanel
        progress={50}
        status="error"
        error="Failed to execute query"
      />
    );
    
    // "Error" appears in both progress label and status indicator
    const errorElements = screen.getAllByText('Error');
    expect(errorElements.length).toBeGreaterThan(0);
    expect(screen.getByText('Failed to execute query')).toBeInTheDocument();
  });

  it('shows retry button on error', () => {
    const mockOnRetry = vi.fn();
    render(
      <ExecutionPanel
        progress={50}
        status="error"
        error="Query failed"
        onRetry={mockOnRetry}
      />
    );
    
    expect(screen.getByText('Retry Query')).toBeInTheDocument();
  });

  it('calls onRetry when retry button is clicked', async () => {
    const user = userEvent.setup();
    const mockOnRetry = vi.fn();
    
    render(
      <ExecutionPanel
        progress={50}
        status="error"
        error="Query failed"
        onRetry={mockOnRetry}
      />
    );
    
    const retryButton = screen.getByText('Retry Query');
    await user.click(retryButton);
    
    expect(mockOnRetry).toHaveBeenCalled();
  });

  it('passes activity log to AgentStatus', () => {
    const activityLog = [
      { timestamp: '2024-01-01T10:00:00Z', message: 'Started execution' },
      { timestamp: '2024-01-01T10:00:05Z', message: 'Processing data' },
    ];
    
    render(
      <ExecutionPanel
        progress={30}
        status="active"
        activityLog={activityLog}
      />
    );
    
    expect(screen.getByText('Started execution')).toBeInTheDocument();
    expect(screen.getByText('Processing data')).toBeInTheDocument();
  });

  it('does not show estimated time when complete', () => {
    render(
      <ExecutionPanel
        progress={100}
        status="active"
        estimatedTime={60}
      />
    );
    
    expect(screen.queryByText(/remaining/)).not.toBeInTheDocument();
  });

  it('does not show estimated time on error', () => {
    render(
      <ExecutionPanel
        progress={50}
        status="error"
        error="Failed"
        estimatedTime={60}
      />
    );
    
    expect(screen.queryByText(/remaining/)).not.toBeInTheDocument();
  });

  it('applies custom className', () => {
    const { container } = render(
      <ExecutionPanel progress={50} status="active" className="custom-class" />
    );
    
    const panel = container.firstChild;
    expect(panel.className).toContain('custom-class');
  });
});
