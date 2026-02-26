import { describe, it, expect } from 'vitest';
import { render, screen } from '../../../test/utils';
import { AgentStatus } from './AgentStatus';

describe('AgentStatus', () => {
  it('renders with idle status', () => {
    render(<AgentStatus status="idle" />);
    
    expect(screen.getByText('Idle')).toBeInTheDocument();
    expect(screen.getByText('Agent is ready to process queries')).toBeInTheDocument();
  });

  it('renders with active status', () => {
    render(<AgentStatus status="active" />);
    
    expect(screen.getByText('Active')).toBeInTheDocument();
    expect(screen.getByText('Agent is processing your query...')).toBeInTheDocument();
  });

  it('renders with error status', () => {
    render(<AgentStatus status="error" />);
    
    expect(screen.getByText('Error')).toBeInTheDocument();
    expect(screen.getByText('Agent encountered an error')).toBeInTheDocument();
  });

  it('displays current activity when provided', () => {
    render(
      <AgentStatus
        status="active"
        currentActivity="Analyzing product data..."
      />
    );
    
    expect(screen.getByText('Analyzing product data...')).toBeInTheDocument();
    expect(screen.queryByText('Agent is processing your query...')).not.toBeInTheDocument();
  });

  it('renders activity log when provided', () => {
    const activityLog = [
      { timestamp: '2024-01-01T10:00:00Z', message: 'Started query execution' },
      { timestamp: '2024-01-01T10:00:05Z', message: 'Fetching product data' },
      { timestamp: '2024-01-01T10:00:10Z', message: 'Analyzing results' },
    ];

    render(<AgentStatus status="active" activityLog={activityLog} />);
    
    expect(screen.getByText('Activity Log')).toBeInTheDocument();
    expect(screen.getByText('Started query execution')).toBeInTheDocument();
    expect(screen.getByText('Fetching product data')).toBeInTheDocument();
    expect(screen.getByText('Analyzing results')).toBeInTheDocument();
  });

  it('does not render activity log when empty', () => {
    render(<AgentStatus status="active" activityLog={[]} />);
    
    expect(screen.queryByText('Activity Log')).not.toBeInTheDocument();
  });

  it('formats timestamps correctly', () => {
    const activityLog = [
      { timestamp: '2024-01-01T10:30:45Z', message: 'Test message' },
    ];

    render(<AgentStatus status="active" activityLog={activityLog} />);
    
    // Check that timestamp is formatted (exact format depends on locale)
    const timestampElement = screen.getByText(/\d{1,2}:\d{2}:\d{2}/);
    expect(timestampElement).toBeInTheDocument();
  });

  it('applies custom className', () => {
    const { container } = render(
      <AgentStatus status="idle" className="custom-class" />
    );
    
    const agentStatus = container.firstChild;
    expect(agentStatus.className).toContain('custom-class');
  });
});
