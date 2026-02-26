# Frontend Completion Design Document

## Executive Summary

This design document outlines the implementation strategy for completing the E-commerce Intelligence SaaS frontend from 22% to 100% completion. The design follows the production-grade architecture defined in FRONTEND_ARCHITECTURE.md and addresses the gaps identified in FRONTEND_DEEP_TECHNICAL_AUDIT.md.

**Current State:** 22% complete - Foundation solid, but 70% of components missing and zero integration
**Target State:** 100% complete - Fully functional, production-ready frontend with real data integration
**Timeline:** 10-13 working days (74-100 hours)
**Approach:** Component-first, then integration, following existing architecture patterns

---

## I. DESIGN PHILOSOPHY

### 1.1 Core Principles

**1. Data-First Architecture**
- All components consume real data from backend APIs
- No hardcoded data or mock values in production code
- React Query for server state management
- WebSocket for real-time updates

**2. Component Hierarchy**
- Atomic components (primitives) → Molecules (composites) → Organisms (features) → Pages
- Each layer builds on the previous
- Clear separation of concerns
- Reusability at every level

**3. Progressive Enhancement**
- Start with basic functionality
- Add loading states
- Add error handling
- Add optimizations
- Add polish

**4. Performance-First**
- Virtualization for large datasets
- Code splitting for routes
- Memoization for expensive operations
- Lazy loading for heavy components

---

## II. COMPONENT LIBRARY DESIGN

### 2.1 Molecule Components Architecture

#### MetricCard Component
**Purpose:** Display KPI metrics with trend indicators
**Complexity:** Low
**Dependencies:** Badge, Skeleton

```typescript
interface MetricCardProps {
  title: string;
  value: string | number;
  change?: number;
  trend?: 'up' | 'down' | 'neutral';
  loading?: boolean;
  format?: 'currency' | 'percentage' | 'number';
  icon?: React.ReactNode;
}
```

**Design Decisions:**
- Use CSS Grid for layout flexibility
- Support multiple format types (currency, percentage, number)
- Trend indicator with color coding (green=up, red=down, gray=neutral)
- Skeleton loader matches card structure
- Responsive: stacks on mobile, grid on desktop

**Visual Hierarchy:**
```
┌─────────────────────────────┐
│ Icon  Title            ↑ 5% │
│                             │
│ $125,432                    │
│ vs last period              │
└─────────────────────────────┘
```

---

#### DataTable Component
**Purpose:** Display tabular data with sorting, filtering, pagination
**Complexity:** High
**Dependencies:** Button, Select, Input, Skeleton

```typescript
interface DataTableProps<T> {
  data: T[];
  columns: Column<T>[];
  loading?: boolean;
  pagination?: PaginationConfig;
  sorting?: SortingConfig;
  onRowClick?: (row: T) => void;
  virtualized?: boolean;
}
```

**Design Decisions:**
- Use TanStack Table for table logic
- Use TanStack Virtual for virtualization (10,000+ rows)
- Sticky header for scrolling
- Column resizing and reordering
- Multi-column sorting
- Built-in empty state

**Performance Strategy:**
- Virtualization enabled for >100 rows
- Memoize column definitions
- Debounce filter inputs
- Paginate on server-side for large datasets

---

#### ChartContainer Component
**Purpose:** Responsive wrapper for Recharts with theme support
**Complexity:** Medium
**Dependencies:** Recharts, Skeleton

```typescript
interface ChartContainerProps {
  children: React.ReactNode;
  title?: string;
  loading?: boolean;
  error?: string;
  height?: number;
  showLegend?: boolean;
}
```

**Design Decisions:**
- ResponsiveContainer from Recharts for auto-sizing
- Apply theme colors automatically via context
- Consistent tooltip styling across all charts
- Loading skeleton matches chart dimensions
- Error state with retry button

---

### 2.2 Organism Components Architecture

#### KPIDashboard Component
**Purpose:** Grid of MetricCards with real-time data
**Complexity:** Medium
**Dependencies:** MetricCard, useDashboardOverview hook

```typescript
interface KPIDashboardProps {
  tenantId: string;
  dateRange: DateRange;
  refreshInterval?: number;
}
```

**Design Decisions:**
- CSS Grid layout: 4 columns on desktop, 2 on tablet, 1 on mobile
- Auto-refresh every 5 minutes (configurable)
- React Query for data fetching with stale-while-revalidate
- Skeleton loaders for each card during initial load
- Error boundary for graceful failure

**Data Flow:**
```
KPIDashboard → useDashboardOverview() → React Query → API
                     ↓
              MetricCard[] (GMV, Margin, Conversion, Inventory)
```

---

#### QueryBuilder Component
**Purpose:** Natural language query input with filters
**Complexity:** High
**Dependencies:** Input, Select, Button, FilterGroup

```typescript
interface QueryBuilderProps {
  onSubmit: (query: QueryParams) => void;
  loading?: boolean;
  defaultMode?: 'quick' | 'deep';
}
```

**Design Decisions:**
- Textarea for natural language input
- Mode selector (Quick/Deep) with visual distinction
- Filter panel with product selector, date range, categories
- Character counter (max 500 chars)
- Submit button disabled when empty or loading
- Save query history to local storage

**User Flow:**
```
1. User types query in natural language
2. User selects mode (Quick/Deep)
3. User applies filters (optional)
4. User clicks "Execute Query"
5. ExecutionPanel shows progress
6. ResultsPanel displays structured report
```

---

#### CompetitorMatrix Component
**Purpose:** Price comparison table with highlighting
**Complexity:** High
**Dependencies:** DataTable, Badge, StatusIndicator

```typescript
interface CompetitorMatrixProps {
  productIds: string[];
  competitors: Competitor[];
  priceGaps: PriceGap[];
}
```

**Design Decisions:**
- Virtualized table for 1000+ products
- Color-coded price gaps (green=competitive, red=expensive)
- Sortable by price, gap, competitor
- Sticky first column (product name)
- Export to CSV functionality
- Real-time updates via WebSocket

**Visual Design:**
```
┌──────────────┬──────────┬──────────┬──────────┬──────────┐
│ Product      │ Your $   │ Comp A   │ Comp B   │ Gap      │
├──────────────┼──────────┼──────────┼──────────┼──────────┤
│ Product 1    │ $29.99   │ $32.99   │ $28.99   │ +3.3%    │
│ Product 2    │ $49.99   │ $45.99   │ $47.99   │ -8.0%    │
└──────────────┴──────────┴──────────┴──────────┴──────────┘
```

---

#### SentimentOverview Component
**Purpose:** Sentiment gauge and distribution
**Complexity:** Medium
**Dependencies:** GaugeChart, BarChart, ChartContainer

```typescript
interface SentimentOverviewProps {
  productId: string;
  timeRange: TimeRange;
}
```

**Design Decisions:**
- Gauge chart for overall sentiment score (0-100)
- Bar chart for distribution (positive/neutral/negative)
- Color coding: green (positive), gray (neutral), red (negative)
- Trend indicator showing change over time
- Drill-down to review details

---

#### ForecastChart Component
**Purpose:** Forecast visualization with confidence bands
**Complexity:** High
**Dependencies:** LineChart, AreaChart, ChartContainer

```typescript
interface ForecastChartProps {
  productId: string;
  horizon: number; // days
  historicalData: DataPoint[];
  forecastData: ForecastPoint[];
}
```

**Design Decisions:**
- Line chart for historical data (solid line)
- Line chart for forecast (dashed line)
- Area chart for confidence bands (shaded region)
- Vertical line separating historical from forecast
- Tooltip shows actual vs predicted values
- Seasonality overlay (optional)

**Visual Design:**
```
Sales
  │     Historical    │    Forecast
  │                   │   ╱╲
  │    ╱╲            │  ╱  ╲  ← Upper bound
  │   ╱  ╲           │ ╱    ╲
  │  ╱    ╲          │╱      ╲ ← Prediction
  │ ╱      ╲        ╱│        ╲
  │╱        ╲      ╱ │         ╲ ← Lower bound
  └─────────────────┼──────────────→ Time
                    Today
```

---

## III. PAGE INTEGRATION DESIGN

### 3.1 OverviewPage Integration

**Current State:** Hardcoded KPI cards, no real data
**Target State:** Real-time dashboard with live data

**Integration Steps:**

1. **Replace hardcoded data with hooks**
```typescript
// Before
const kpis = [
  { title: 'GMV', value: '$125,432', change: 5.2 },
  // ... hardcoded
];

// After
const { data: kpis, isLoading, error } = useDashboardOverview({
  tenantId: tenant.id,
  dateRange: selectedDateRange,
});
```

2. **Add loading states**
```typescript
if (isLoading) {
  return <KPIDashboardSkeleton />;
}
```

3. **Add error handling**
```typescript
if (error) {
  return <ErrorState error={error} onRetry={refetch} />;
}
```

4. **Add data refresh**
```typescript
const { refetch } = useDashboardOverview({
  // ... config
  refetchInterval: 5 * 60 * 1000, // 5 minutes
});
```

**Component Tree:**
```
OverviewPage
├── PageHeader (title, date range selector, refresh button)
├── KPIDashboard
│   ├── MetricCard (GMV)
│   ├── MetricCard (Margin)
│   ├── MetricCard (Conversion)
│   └── MetricCard (Inventory)
├── TrendChart (Sales over time)
├── AlertPanel (Critical alerts)
└── QuickInsights (AI-generated insights)
```

---

### 3.2 IntelligencePage Integration

**Current State:** Placeholder text only
**Target State:** Fully functional query execution with real-time progress

**Integration Steps:**

1. **Add QueryBuilder component**
```typescript
const [queryParams, setQueryParams] = useState<QueryParams | null>(null);

<QueryBuilder
  onSubmit={setQueryParams}
  loading={isExecuting}
/>
```

2. **Execute query with hook**
```typescript
const { mutate: executeQuery, data: queryResult, isLoading } = useExecuteQuery();

useEffect(() => {
  if (queryParams) {
    executeQuery(queryParams);
  }
}, [queryParams]);
```

3. **Connect WebSocket for progress**
```typescript
const { progress, result, error } = useQueryWebSocket(queryResult?.queryId);
```

4. **Display results**
```typescript
{result && <ResultsPanel report={result} />}
```

**User Flow:**
```
1. User enters query: "What are my top 10 products by revenue?"
2. User selects "Quick Mode"
3. User clicks "Execute Query"
4. ExecutionPanel shows:
   - Agent status: "Analyzing query..."
   - Progress: 25%
5. WebSocket updates progress in real-time
6. After 30 seconds, ResultsPanel shows:
   - Executive summary
   - Data table with top 10 products
   - Revenue chart
   - Action items
```

---

### 3.3 PricingPage Integration

**Current State:** Placeholder text only
**Target State:** Competitor price analysis with trends

**Integration Steps:**

1. **Add product selector**
```typescript
const [selectedProducts, setSelectedProducts] = useState<string[]>([]);

<ProductSelector
  value={selectedProducts}
  onChange={setSelectedProducts}
  multi
/>
```

2. **Fetch pricing data**
```typescript
const { data: pricingData } = useCompetitorPricing({
  productIds: selectedProducts,
});

const { data: priceHistory } = usePriceHistory({
  productId: selectedProducts[0],
  days: 30,
});
```

3. **Display components**
```typescript
<CompetitorMatrix
  products={pricingData.products}
  competitors={pricingData.competitors}
  priceGaps={pricingData.gaps}
/>

<PriceTrendChart
  data={priceHistory}
  productId={selectedProducts[0]}
/>
```

**Component Tree:**
```
PricingPage
├── PageHeader (title, product selector)
├── CompetitorMatrix (virtualized table)
├── PriceTrendChart (multi-line chart)
├── RecommendationPanel (AI pricing suggestions)
└── PromotionTracker (promotion effectiveness)
```

---

### 3.4 SentimentPage Integration

**Current State:** Placeholder text only
**Target State:** Review sentiment analysis with theme breakdown

**Integration Steps:**

1. **Add product selector and filters**
```typescript
const [selectedProduct, setSelectedProduct] = useState<string | null>(null);
const [filters, setFilters] = useState<ReviewFilters>({
  sentiment: 'all',
  dateRange: 'last30days',
});
```

2. **Fetch sentiment data**
```typescript
const { data: sentimentData } = useSentimentOverview({
  productId: selectedProduct,
});

const { data: themes } = useThemeBreakdown({
  productId: selectedProduct,
});

const { data: reviews } = useReviews({
  productId: selectedProduct,
  filters,
});
```

3. **Display components**
```typescript
<SentimentOverview data={sentimentData} />
<ThemeBreakdown themes={themes} />
<ReviewList reviews={reviews} filters={filters} />
```

**Component Tree:**
```
SentimentPage
├── PageHeader (title, product selector)
├── SentimentOverview
│   ├── GaugeChart (overall score)
│   └── DistributionChart (pos/neu/neg)
├── ThemeBreakdown
│   ├── TreeMap (theme visualization)
│   └── TopicList (top themes)
├── ReviewList (paginated reviews)
└── ComplaintAnalysis (complaint categories)
```

---

### 3.5 ForecastPage Integration

**Current State:** Placeholder text only
**Target State:** Demand forecasting with inventory recommendations

**Integration Steps:**

1. **Add product and horizon selectors**
```typescript
const [selectedProduct, setSelectedProduct] = useState<string | null>(null);
const [horizon, setHorizon] = useState<number>(30); // days
```

2. **Fetch forecast data**
```typescript
const { data: forecastData } = useDemandForecast({
  productId: selectedProduct,
  horizon,
});

const { data: inventoryAlerts } = useInventoryRecommendations({
  tenantId: tenant.id,
});
```

3. **Display components**
```typescript
<ForecastChart
  productId={selectedProduct}
  horizon={horizon}
  historicalData={forecastData.historical}
  forecastData={forecastData.forecast}
/>

<InventoryAlerts alerts={inventoryAlerts} />
```

**Component Tree:**
```
ForecastPage
├── PageHeader (title, product selector, horizon selector)
├── ForecastChart (line chart with confidence bands)
├── InventoryAlerts (critical alerts)
├── DemandSupplyGap (gap analysis)
└── AccuracyMetrics (forecast accuracy)
```

---

## IV. REAL-TIME FEATURES DESIGN

### 4.1 WebSocket Integration Architecture

**Purpose:** Real-time updates for query execution progress

**Connection Flow:**
```
1. User logs in
2. WebSocketManager.connect() called
3. Socket connects with auth token
4. Socket joins tenant room
5. Backend sends events to room
6. Frontend updates UI in real-time
```

**Event Types:**
```typescript
// Query execution events
'query:progress' - Progress updates (0-100%)
'query:complete' - Query finished
'query:error' - Query failed

// Data sync events
'data:updated' - New data available
'data:sync:complete' - Sync finished

// System events
'notification' - New notification
'alert' - Critical alert
```

**Implementation:**
```typescript
// In IntelligencePage
const { progress, result, error } = useQueryWebSocket(queryId);

// Hook implementation
export function useQueryWebSocket(queryId: string | null) {
  const [progress, setProgress] = useState<number>(0);
  const [result, setResult] = useState<StructuredReport | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!queryId) return;

    const unsubscribe = wsManager.subscribeToQuery(queryId, {
      onProgress: (data) => setProgress(data.progress),
      onComplete: (data) => setResult(data),
      onError: (err) => setError(err),
    });

    return unsubscribe;
  }, [queryId]);

  return { progress, result, error };
}
```

**Reconnection Strategy:**
```typescript
// Exponential backoff
const reconnectDelays = [1000, 2000, 5000, 10000, 30000];

// Fallback to polling after 5 failed attempts
if (reconnectAttempts >= 5) {
  console.warn('WebSocket failed, falling back to polling');
  startPolling();
}
```

---

### 4.2 Notification System Design

**Purpose:** Toast notifications for user feedback

**Notification Types:**
- Success: Green, auto-dismiss after 3s
- Error: Red, manual dismiss
- Info: Blue, auto-dismiss after 5s
- Warning: Yellow, auto-dismiss after 5s

**Implementation:**
```typescript
// Using notificationStore
const addNotification = useNotificationStore(state => state.addNotification);

// Trigger notification
addNotification({
  id: crypto.randomUUID(),
  type: 'success',
  title: 'Query executed successfully',
  message: 'Your report is ready',
  duration: 3000,
});
```

**Toast Component:**
```typescript
interface ToastProps {
  notification: Notification;
  onDismiss: (id: string) => void;
}

// Position: top-right
// Animation: slide-in from right
// Stack: max 3 visible, queue others
```

---

## V. STATE MANAGEMENT DESIGN

### 5.1 React Query Configuration

**Query Key Strategy:**
```typescript
// Hierarchical query keys
queryKeys = {
  overview: ['overview'],
  kpis: (tenantId, dateRange) => ['kpis', tenantId, dateRange],
  query: (queryId) => ['query', queryId],
  pricing: (productId) => ['pricing', productId],
  // ...
}
```

**Stale Time Configuration:**
```typescript
// Real-time data: 30 seconds
useQuery({
  queryKey: queryKeys.kpis(tenantId, dateRange),
  staleTime: 30 * 1000,
});

// Frequent updates: 5 minutes
useQuery({
  queryKey: queryKeys.pricing(productId),
  staleTime: 5 * 60 * 1000,
});

// Infrequent updates: 1 hour
useQuery({
  queryKey: queryKeys.forecast(productId, horizon),
  staleTime: 60 * 60 * 1000,
});
```

**Cache Invalidation:**
```typescript
// After mutation
const { mutate } = useMutation({
  mutationFn: updatePricing,
  onSuccess: () => {
    // Invalidate related queries
    queryClient.invalidateQueries({ queryKey: ['pricing'] });
  },
});

// After tenant switch
const switchTenant = async (tenantId: string) => {
  await api.switchTenant(tenantId);
  // Invalidate all queries
  queryClient.invalidateQueries();
};
```

---

### 5.2 Zustand Store Usage

**Replace AuthContext with authStore:**
```typescript
// Before (AuthContext)
const { user, tenant } = useAuth();

// After (authStore)
const { user, tenant } = useAuthStore();
```

**UI State Management:**
```typescript
// Sidebar state
const { sidebarOpen, toggleSidebar } = useUIStore();

// Theme state
const { theme, setTheme } = useUIStore();

// Modal state
const { modalOpen, openModal, closeModal } = useUIStore();
```

**Notification State:**
```typescript
const { notifications, addNotification, removeNotification } = useNotificationStore();
```

---

## VI. ERROR HANDLING DESIGN

### 6.1 Error Boundary Strategy

**Global Error Boundary:**
```typescript
// Wraps entire app
<ErrorBoundary
  fallback={<GlobalErrorFallback />}
  onError={(error, errorInfo) => {
    // Log to Sentry
    Sentry.captureException(error, { extra: errorInfo });
  }}
>
  <App />
</ErrorBoundary>
```

**Page-Level Error Boundaries:**
```typescript
// Wraps each page
<ErrorBoundary
  fallback={<PageErrorFallback />}
  onReset={() => {
    // Reset page state
    queryClient.invalidateQueries();
  }}
>
  <OverviewPage />
</ErrorBoundary>
```

**Component-Level Error States:**
```typescript
// In components
if (error) {
  return (
    <ErrorState
      title="Failed to load data"
      message={error.message}
      onRetry={refetch}
    />
  );
}
```

---

### 6.2 Error Types and Handling

**Network Errors:**
```typescript
// Retry with exponential backoff
retry: (failureCount, error) => {
  if (error.response?.status === 404) return false;
  if (error.response?.status === 401) return false;
  return failureCount < 2;
}
```

**Authentication Errors:**
```typescript
// 401: Token expired → Refresh token
// 403: Insufficient permissions → Show permission error
// Redirect to login if refresh fails
```

**Validation Errors:**
```typescript
// 400: Bad request → Show field-level errors
// Display error messages next to form fields
```

**Server Errors:**
```typescript
// 500: Internal server error → Show retry option
// 503: Service unavailable → Show maintenance message
```

---

## VII. LOADING STATES DESIGN

### 7.1 Skeleton Loader Strategy

**Principles:**
- Match skeleton structure to actual content
- Use subtle animation (shimmer effect)
- Show skeleton during initial load only
- Use spinners for subsequent loads

**Skeleton Components:**
```typescript
// MetricCard skeleton
<div className="metric-card-skeleton">
  <div className="skeleton-title" />
  <div className="skeleton-value" />
  <div className="skeleton-change" />
</div>

// DataTable skeleton
<div className="table-skeleton">
  <div className="skeleton-header" />
  {Array.from({ length: 5 }).map((_, i) => (
    <div key={i} className="skeleton-row" />
  ))}
</div>

// Chart skeleton
<div className="chart-skeleton">
  <div className="skeleton-title" />
  <div className="skeleton-chart" />
</div>
```

---

### 7.2 Progress Indicators

**Query Execution Progress:**
```typescript
<ExecutionPanel>
  <ProgressBar value={progress} max={100} />
  <AgentStatus status={agentStatus} />
  <p>{progress}% complete</p>
</ExecutionPanel>
```

**Data Loading Spinner:**
```typescript
// For quick operations (<1s)
<Spinner size="sm" />

// For longer operations
<Spinner size="md" />
<p>Loading data...</p>
```

---

## VIII. PERFORMANCE OPTIMIZATION DESIGN

### 8.1 Code Splitting Strategy

**Route-Based Splitting:**
```typescript
// Lazy load pages
const IntelligencePage = lazy(() => import('@/pages/intelligence/IntelligencePage'));
const PricingPage = lazy(() => import('@/pages/pricing/PricingPage'));
const SentimentPage = lazy(() => import('@/pages/sentiment/SentimentPage'));
const ForecastPage = lazy(() => import('@/pages/forecast/ForecastPage'));

// Wrap in Suspense
<Suspense fallback={<PageSkeleton />}>
  <Routes>
    <Route path="/intelligence" element={<IntelligencePage />} />
    {/* ... */}
  </Routes>
</Suspense>
```

**Component-Based Splitting:**
```typescript
// Lazy load heavy components
const CompetitorMatrix = lazy(() => import('@/features/pricing/components/CompetitorMatrix'));
const ForecastChart = lazy(() => import('@/features/forecast/components/ForecastChart'));
```

---

### 8.2 Memoization Strategy

**Component Memoization:**
```typescript
// Memoize expensive components
export const CompetitorMatrix = memo(function CompetitorMatrix(props) {
  // ...
}, (prevProps, nextProps) => {
  // Custom comparison
  return prevProps.data === nextProps.data;
});
```

**Value Memoization:**
```typescript
// Memoize expensive calculations
const sortedData = useMemo(() => {
  return data.sort((a, b) => b.value - a.value);
}, [data]);
```

**Callback Memoization:**
```typescript
// Memoize event handlers
const handleRowClick = useCallback((row) => {
  console.log('Row clicked:', row);
}, []);
```

---

### 8.3 Virtualization Strategy

**DataTable Virtualization:**
```typescript
// Enable for >100 rows
<DataTable
  data={largeDataset}
  columns={columns}
  virtualized={largeDataset.length > 100}
/>

// Uses TanStack Virtual internally
const virtualizer = useVirtualizer({
  count: data.length,
  getScrollElement: () => parentRef.current,
  estimateSize: () => 48, // row height
  overscan: 5,
});
```

**List Virtualization:**
```typescript
// For review lists, notification lists
<VirtualList
  items={reviews}
  itemHeight={120}
  overscan={3}
  renderItem={(review) => <ReviewCard review={review} />}
/>
```

---

## IX. TESTING STRATEGY DESIGN

### 9.1 Unit Testing

**Test Coverage Goals:**
- Utility functions: 100%
- Custom hooks: 90%
- Components: 70%
- Overall: 70%

**Testing Framework:**
- Vitest for unit tests
- React Testing Library for component tests
- MSW for API mocking

**Example Tests:**
```typescript
// Utility function test
describe('formatCurrency', () => {
  it('formats USD correctly', () => {
    expect(formatCurrency(1234.56, 'USD')).toBe('$1,234.56');
  });
});

// Hook test
describe('useDashboardOverview', () => {
  it('fetches KPI data', async () => {
    const { result } = renderHook(() => useDashboardOverview({
      tenantId: 'test',
      dateRange: { start: '2024-01-01', end: '2024-01-31' },
    }));

    await waitFor(() => {
      expect(result.current.data).toBeDefined();
    });
  });
});

// Component test
describe('MetricCard', () => {
  it('displays metric value', () => {
    render(<MetricCard title="GMV" value="$125,432" />);
    expect(screen.getByText('$125,432')).toBeInTheDocument();
  });
});
```

---

### 9.2 Integration Testing

**Test Critical Flows:**
- Login → Dashboard → View KPIs
- Execute query → View results
- View pricing → Compare competitors
- View sentiment → Filter reviews

**Example Test:**
```typescript
describe('Query Execution Flow', () => {
  it('executes query and displays results', async () => {
    render(<IntelligencePage />);

    // Enter query
    const input = screen.getByPlaceholderText('Enter your query...');
    await userEvent.type(input, 'What are my top products?');

    // Submit
    const button = screen.getByRole('button', { name: /execute/i });
    await userEvent.click(button);

    // Wait for results
    await waitFor(() => {
      expect(screen.getByText(/top products/i)).toBeInTheDocument();
    });
  });
});
```

---

### 9.3 E2E Testing

**Test Critical User Journeys:**
- User registration and login
- Dashboard overview
- Query execution (Quick and Deep modes)
- Pricing analysis
- Sentiment analysis
- Forecast viewing

**Testing Framework:**
- Playwright for E2E tests

**Example Test:**
```typescript
test('user can execute query', async ({ page }) => {
  // Login
  await page.goto('/login');
  await page.fill('[name="email"]', 'test@example.com');
  await page.fill('[name="password"]', 'password');
  await page.click('button[type="submit"]');

  // Navigate to Intelligence
  await page.click('text=Intelligence');

  // Execute query
  await page.fill('textarea', 'What are my top 10 products?');
  await page.click('button:has-text("Execute Query")');

  // Wait for results
  await page.waitForSelector('text=Top 10 Products');
});
```

---

## X. DEPLOYMENT DESIGN

### 10.1 Build Configuration

**Vite Configuration:**
```typescript
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'query-vendor': ['@tanstack/react-query'],
          'chart-vendor': ['recharts'],
        },
      },
    },
    chunkSizeWarningLimit: 500,
    sourcemap: false,
    minify: 'terser',
  },
});
```

**Environment Variables:**
```bash
# .env.production
VITE_API_BASE_URL=https://api.yourdomain.com
VITE_WS_BASE_URL=wss://api.yourdomain.com
VITE_SENTRY_DSN=https://...
```

---

### 10.2 Deployment Strategy

**Vercel Deployment:**
1. Connect GitHub repository
2. Configure build settings
3. Set environment variables
4. Deploy to staging
5. Run E2E tests on staging
6. Deploy to production (canary)
7. Monitor metrics
8. Promote to 100% traffic

**Rollback Strategy:**
- Keep previous 5 deployments
- One-click rollback in Vercel dashboard
- Automatic rollback on error rate spike

---

## XI. MONITORING AND OBSERVABILITY

### 11.1 Performance Monitoring

**Metrics to Track:**
- Page load time (p50, p95, p99)
- Time to interactive
- First contentful paint
- Largest contentful paint
- Cumulative layout shift
- First input delay

**Tools:**
- Web Vitals library
- Vercel Analytics
- Custom RUM implementation

---

### 11.2 Error Monitoring

**Error Tracking:**
- Sentry for error tracking
- Source maps for stack traces
- User context (tenant, user ID)
- Breadcrumbs for debugging

**Alerts:**
- Error rate > 1%
- Page load time > 3s
- API latency > 2s
- WebSocket disconnections > 10%

---

## XII. ACCESSIBILITY DESIGN

### 12.1 Keyboard Navigation

**Requirements:**
- All interactive elements focusable
- Logical tab order
- Visible focus indicators
- Keyboard shortcuts (⌘K for command palette)

**Implementation:**
```typescript
// Focus management
const firstInputRef = useRef<HTMLInputElement>(null);

useEffect(() => {
  firstInputRef.current?.focus();
}, []);

// Keyboard shortcuts
useEffect(() => {
  const handleKeyDown = (e: KeyboardEvent) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
      e.preventDefault();
      openCommandPalette();
    }
  };

  window.addEventListener('keydown', handleKeyDown);
  return () => window.removeEventListener('keydown', handleKeyDown);
}, []);
```

---

### 12.2 Screen Reader Support

**Requirements:**
- ARIA labels on all interactive elements
- ARIA live regions for dynamic content
- Semantic HTML (headings, lists, tables)
- Alt text for images

**Implementation:**
```typescript
// ARIA labels
<button aria-label="Execute query">
  <PlayIcon />
</button>

// ARIA live regions
<div aria-live="polite" aria-atomic="true">
  {progress}% complete
</div>

// Semantic HTML
<nav aria-label="Main navigation">
  <ul>
    <li><a href="/overview">Overview</a></li>
    {/* ... */}
  </ul>
</nav>
```

---

## XIII. DESIGN SYSTEM TOKENS

### 13.1 Color Tokens

**Brand Colors:**
```css
--color-brand-primary: #0066FF;
--color-brand-secondary: #6366F1;
--color-brand-accent: #8B5CF6;
```

**Semantic Colors:**
```css
--color-success: #10B981;
--color-warning: #F59E0B;
--color-error: #EF4444;
--color-info: #3B82F6;
```

**Chart Colors:**
```css
--color-chart-1: #0066FF;
--color-chart-2: #10B981;
--color-chart-3: #F59E0B;
--color-chart-4: #EF4444;
```

---

### 13.2 Typography Tokens

**Font Families:**
```css
--font-sans: 'Inter', sans-serif;
--font-mono: 'JetBrains Mono', monospace;
```

**Font Sizes:**
```css
--text-xs: 0.75rem;   /* 12px */
--text-sm: 0.875rem;  /* 14px */
--text-base: 1rem;    /* 16px */
--text-lg: 1.125rem;  /* 18px */
--text-xl: 1.25rem;   /* 20px */
--text-2xl: 1.5rem;   /* 24px */
```

---

### 13.3 Spacing Tokens

**Spacing Scale:**
```css
--space-1: 0.25rem;  /* 4px */
--space-2: 0.5rem;   /* 8px */
--space-3: 0.75rem;  /* 12px */
--space-4: 1rem;     /* 16px */
--space-6: 1.5rem;   /* 24px */
--space-8: 2rem;     /* 32px */
--space-12: 3rem;    /* 48px */
```

---

## XIV. IMPLEMENTATION CHECKLIST

### Phase 1: Molecule Components
- [ ] MetricCard
- [ ] DataTable
- [ ] ChartContainer
- [ ] SearchBar
- [ ] FilterGroup
- [ ] DateRangePicker
- [ ] ProductSelector
- [ ] StatusIndicator
- [ ] Toast
- [ ] ProgressBar
- [ ] LoadingSkeleton
- [ ] PageHeader

### Phase 2: Organism Components
- [ ] KPIDashboard
- [ ] TrendChart
- [ ] AlertPanel
- [ ] QuickInsights
- [ ] QueryBuilder
- [ ] ExecutionPanel
- [ ] ResultsPanel
- [ ] AgentStatus
- [ ] CompetitorMatrix
- [ ] PriceTrendChart
- [ ] RecommendationPanel
- [ ] PromotionTracker
- [ ] SentimentOverview
- [ ] ThemeBreakdown
- [ ] ReviewList
- [ ] ComplaintAnalysis
- [ ] ForecastChart
- [ ] InventoryAlerts
- [ ] DemandSupplyGap
- [ ] AccuracyMetrics

### Phase 3: Page Integration
- [ ] OverviewPage integration
- [ ] IntelligencePage integration
- [ ] PricingPage integration
- [ ] SentimentPage integration
- [ ] ForecastPage integration
- [ ] SettingsPage integration

### Phase 4: Real-time Features
- [ ] WebSocket connection
- [ ] Query progress tracking
- [ ] Notification system
- [ ] Real-time data updates

### Phase 5: Error Handling
- [ ] Global error boundary
- [ ] Page-level error boundaries
- [ ] Error states in components
- [ ] Retry logic

### Phase 6: Loading States
- [ ] Skeleton loaders
- [ ] Progress indicators
- [ ] Suspense boundaries

### Phase 7: Performance
- [ ] Code splitting
- [ ] Lazy loading
- [ ] Memoization
- [ ] Virtualization

### Phase 8: Testing
- [ ] Unit tests
- [ ] Integration tests
- [ ] E2E tests

### Phase 9: Deployment
- [ ] Build configuration
- [ ] Environment setup
- [ ] Staging deployment
- [ ] Production deployment

---

## XV. SUCCESS CRITERIA

### Technical Metrics
- [ ] Page load time < 2 seconds
- [ ] Time to interactive < 3 seconds
- [ ] Bundle size < 500KB (gzipped)
- [ ] Test coverage > 70%
- [ ] Zero critical bugs

### Functional Metrics
- [ ] All pages display real data
- [ ] All hooks are used
- [ ] WebSocket connected
- [ ] Error handling works
- [ ] Loading states work

### User Experience Metrics
- [ ] Smooth interactions (60fps)
- [ ] Responsive design works
- [ ] Dark mode works
- [ ] Keyboard navigation works
- [ ] Screen reader compatible

---

**Document Version:** 1.0
**Last Updated:** February 23, 2026
**Status:** READY FOR IMPLEMENTATION 🚀
