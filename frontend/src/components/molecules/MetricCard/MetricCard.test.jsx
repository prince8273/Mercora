import { describe, it, expect } from 'vitest';
import { render, screen } from '../../../test/utils';
import { MetricCard } from './MetricCard';

describe('MetricCard', () => {
  it('renders metric title and value', () => {
    render(
      <MetricCard
        title="Total Revenue"
        value={125000}
        change={5.2}
        trend="up"
        format="currency"
      />
    );

    expect(screen.getByText('Total Revenue')).toBeInTheDocument();
    expect(screen.getByText('$125,000')).toBeInTheDocument();
  });

  it('displays positive change with up trend', () => {
    render(
      <MetricCard
        title="Revenue"
        value={100}
        change={10}
        trend="up"
      />
    );

    expect(screen.getByText('+10.0%')).toBeInTheDocument();
    const changeElement = screen.getByText('+10.0%').closest('div');
    // Check for CSS module class containing 'positive'
    expect(changeElement.className).toMatch(/positive/);
  });

  it('displays negative change with down trend', () => {
    render(
      <MetricCard
        title="Revenue"
        value={100}
        change={-5}
        trend="down"
      />
    );

    expect(screen.getByText('-5.0%')).toBeInTheDocument();
    const changeElement = screen.getByText('-5.0%').closest('div');
    // Check for CSS module class containing 'negative'
    expect(changeElement.className).toMatch(/negative/);
  });

  it('shows loading skeleton when loading prop is true', () => {
    const { container } = render(
      <MetricCard
        title="Revenue"
        value={100}
        change={5}
        trend="up"
        loading={true}
      />
    );

    // Check for Skeleton component
    const skeletons = container.querySelectorAll('[class*="skeleton"]');
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it('applies custom className', () => {
    const { container } = render(
      <MetricCard
        title="Revenue"
        value={100}
        change={5}
        trend="up"
        className="custom-class"
      />
    );

    expect(container.firstChild).toHaveClass('custom-class');
  });
});
