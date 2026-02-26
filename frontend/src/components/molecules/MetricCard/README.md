# MetricCard Component

A reusable card component for displaying KPI metrics with trend indicators.

## Features

- ✅ Multiple format types (currency, percentage, number)
- ✅ Trend indicators with color coding (up/down arrows)
- ✅ Loading state with skeleton
- ✅ Dark mode support
- ✅ Hover effects
- ✅ Responsive design
- ✅ Optional icon support

## Usage

```jsx
import { MetricCard } from '@/components/molecules/MetricCard';

function Dashboard() {
  return (
    <MetricCard
      title="Total Revenue"
      value={125432}
      change={5.2}
      trend="up"
      format="currency"
    />
  );
}
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `title` | `string` | required | The metric title/label |
| `value` | `number` | required | The metric value |
| `change` | `number` | `null` | Percentage change from previous period |
| `trend` | `'up' \| 'down' \| 'neutral'` | `'neutral'` | Trend direction |
| `loading` | `boolean` | `false` | Show loading skeleton |
| `format` | `'currency' \| 'percentage' \| 'number'` | `'number'` | Value format type |
| `icon` | `ReactNode` | `null` | Optional icon element |
| `className` | `string` | `''` | Additional CSS classes |

## Examples

### Currency with Positive Change
```jsx
<MetricCard
  title="GMV"
  value={2456789}
  change={8.3}
  trend="up"
  format="currency"
/>
```

### Percentage with Negative Change
```jsx
<MetricCard
  title="Conversion Rate"
  value={3.4}
  change={-1.2}
  trend="down"
  format="percentage"
/>
```

### With Icon
```jsx
<MetricCard
  title="Active Users"
  value={1234}
  change={12.5}
  trend="up"
  format="number"
  icon={<UserIcon />}
/>
```

### Loading State
```jsx
<MetricCard
  title="Loading..."
  loading={true}
/>
```

### No Change Indicator
```jsx
<MetricCard
  title="Inventory Items"
  value={8765}
  format="number"
/>
```

## Styling

The component uses CSS modules and respects the global design tokens:

- Colors: `--primary-color`, `--success-color`, `--error-color`
- Spacing: `--spacing-sm`, `--spacing-md`, `--spacing-lg`
- Border radius: `--radius-lg`
- Shadows: `--shadow-sm`, `--shadow-md`

## Dark Mode

The component automatically adapts to dark mode when `[data-theme='dark']` is applied to the document root.

## Accessibility

- Semantic HTML structure
- Proper heading hierarchy
- Color contrast meets WCAG AA standards
- Hover states for interactive feedback

## Integration with React Query

```jsx
import { MetricCard } from '@/components/molecules/MetricCard';
import { useDashboardOverview } from '@/hooks/useDashboard';

function DashboardPage() {
  const { data, isLoading } = useDashboardOverview();

  return (
    <div className="kpi-grid">
      <MetricCard
        title="GMV"
        value={data?.gmv}
        change={data?.gmvChange}
        trend={data?.gmvChange > 0 ? 'up' : 'down'}
        format="currency"
        loading={isLoading}
      />
    </div>
  );
}
```
