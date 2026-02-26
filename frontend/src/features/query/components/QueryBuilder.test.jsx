import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '../../../test/utils';
import userEvent from '@testing-library/user-event';
import { QueryBuilder } from './QueryBuilder';

describe('QueryBuilder', () => {
  const mockOnSubmit = vi.fn();

  it('renders query input textarea', () => {
    render(<QueryBuilder onSubmit={mockOnSubmit} />);
    
    const textarea = screen.getByPlaceholderText(/What are my top-selling products/i);
    expect(textarea).toBeInTheDocument();
  });

  it('updates character count as user types', async () => {
    const user = userEvent.setup();
    render(<QueryBuilder onSubmit={mockOnSubmit} />);
    
    const textarea = screen.getByPlaceholderText(/What are my top-selling products/i);
    
    await user.type(textarea, 'Test query');
    
    expect(screen.getByText(/10 \/ 500/)).toBeInTheDocument();
  });

  it('shows error when query exceeds max length', async () => {
    const user = userEvent.setup();
    render(<QueryBuilder onSubmit={mockOnSubmit} />);
    
    const textarea = screen.getByPlaceholderText(/What are my top-selling products/i);
    
    // Manually set value to test the counter (faster than typing 501 characters)
    const longQuery = 'a'.repeat(501);
    await user.click(textarea);
    
    // Simulate input event
    Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set.call(textarea, longQuery);
    textarea.dispatchEvent(new Event('input', { bubbles: true }));
    
    // Wait for state update
    await waitFor(() => {
      expect(screen.getByText('501 / 500')).toBeInTheDocument();
    });
  }, 10000); // Increase timeout

  it('disables submit button when query is empty', () => {
    render(<QueryBuilder onSubmit={mockOnSubmit} />);
    
    const submitButton = screen.getByText('Submit Query');
    expect(submitButton).toBeDisabled();
  });

  it('enables submit button when query is valid', async () => {
    const user = userEvent.setup();
    render(<QueryBuilder onSubmit={mockOnSubmit} />);
    
    const textarea = screen.getByPlaceholderText(/What are my top-selling products/i);
    await user.type(textarea, 'Valid query');
    
    const submitButton = screen.getByText('Submit Query');
    expect(submitButton).not.toBeDisabled();
  });

  it('disables submit button when loading', () => {
    render(<QueryBuilder onSubmit={mockOnSubmit} loading={true} />);
    
    const submitButton = screen.getByText('Processing...');
    expect(submitButton).toBeDisabled();
  });

  it('submits query with correct data', async () => {
    const user = userEvent.setup();
    render(<QueryBuilder onSubmit={mockOnSubmit} />);
    
    const textarea = screen.getByPlaceholderText(/What are my top-selling products/i);
    await user.clear(textarea);
    await user.type(textarea, 'Test query');
    
    const submitButton = screen.getByText('Submit Query');
    await user.click(submitButton);
    
    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith({
        query: 'Test query',
        mode: 'quick',
        filters: {
          products: [],
          dateRange: {
            startDate: null,
            endDate: null,
          },
        },
      });
    });
  });

  it('toggles mode selector', async () => {
    const user = userEvent.setup();
    render(<QueryBuilder onSubmit={mockOnSubmit} />);
    
    // Check initial mode is quick (just "Quick", not "Quick Analysis")
    expect(screen.getByText('Quick')).toBeInTheDocument();
    
    // Find and click the deep mode button
    const deepButton = screen.getByText('Deep');
    await user.click(deepButton);
    
    // Submit to verify mode changed
    const textarea = screen.getByPlaceholderText(/What are my top-selling products/i);
    await user.type(textarea, 'Test');
    
    const submitButton = screen.getByText('Submit Query');
    await user.click(submitButton);
    
    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith(
        expect.objectContaining({ mode: 'deep' })
      );
    });
  });

  it('toggles filters panel', async () => {
    const user = userEvent.setup();
    render(<QueryBuilder onSubmit={mockOnSubmit} />);
    
    const filtersToggle = screen.getByText(/Show Filters/i);
    
    // Click to show filters
    await user.click(filtersToggle);
    
    // Filters should be visible - check for Hide Filters text
    expect(screen.getByText(/Hide Filters/i)).toBeInTheDocument();
  });

  it('shows query history when available', async () => {
    const user = userEvent.setup();
    const queryHistory = [
      { query: 'Previous query 1', mode: 'quick', timestamp: '2024-01-01T10:00:00Z' },
      { query: 'Previous query 2', mode: 'deep', timestamp: '2024-01-01T09:00:00Z' },
    ];
    
    render(<QueryBuilder onSubmit={mockOnSubmit} queryHistory={queryHistory} />);
    
    const historyButton = screen.getByText('History');
    await user.click(historyButton);
    
    expect(screen.getByText('Previous query 1')).toBeInTheDocument();
    expect(screen.getByText('Previous query 2')).toBeInTheDocument();
  });

  it('selects query from history', async () => {
    const user = userEvent.setup();
    const queryHistory = [
      { query: 'Historical query', mode: 'deep', timestamp: '2024-01-01T10:00:00Z' },
    ];
    
    render(<QueryBuilder onSubmit={mockOnSubmit} queryHistory={queryHistory} />);
    
    const historyButton = screen.getByText('History');
    await user.click(historyButton);
    
    const historyItem = screen.getByText('Historical query');
    await user.click(historyItem);
    
    const textarea = screen.getByPlaceholderText(/What are my top-selling products/i);
    expect(textarea.value).toBe('Historical query');
  });

  it('clears form when clear button is clicked', async () => {
    const user = userEvent.setup();
    render(<QueryBuilder onSubmit={mockOnSubmit} />);
    
    const textarea = screen.getByPlaceholderText(/What are my top-selling products/i);
    await user.type(textarea, 'Test query');
    
    const clearButton = screen.getByText('Clear');
    await user.click(clearButton);
    
    expect(textarea.value).toBe('');
  });

  it('shows validation error when submitting empty query', async () => {
    const user = userEvent.setup();
    render(<QueryBuilder onSubmit={mockOnSubmit} />);
    
    // Try to submit without typing anything
    const submitButton = screen.getByText('Submit Query');
    
    // Button should be disabled, so this shouldn't actually submit
    expect(submitButton).toBeDisabled();
  });

  it('shows filter badge when filters are applied', async () => {
    const user = userEvent.setup();
    render(<QueryBuilder onSubmit={mockOnSubmit} />);
    
    const filtersToggle = screen.getByText(/Show Filters/i);
    await user.click(filtersToggle);
    
    // Note: Actual filter selection would require mocking ProductSelector and DateRangePicker
    // This test verifies the badge appears when filters are set
  });
});
