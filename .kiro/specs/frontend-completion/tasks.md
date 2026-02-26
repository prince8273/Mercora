# Frontend Completion Tasks

## Task Status Legend
- ⏳ pending - Not started
- 🔄 in_progress - Currently being worked on
- ✅ completed - Finished and verified
- ❌ blocked - Cannot proceed due to dependency

---

## Phase 1: Molecule Components (CRITICAL)

### Task 1.1: Create MetricCard Component
**Status:** ✅ completed
**Priority:** CRITICAL
**Estimated Time:** 1.5 hours
**Dependencies:** None

**Description:**
Create a reusable MetricCard component for displaying KPI metrics with trend indicators.

**Acceptance Criteria:**
- [x] Component accepts title, value, change, trend props
- [x] Displays metric value with proper formatting
- [x] Shows trend indicator (up/down arrow with color)
- [x] Supports loading state with skeleton
- [x] Supports dark mode
- [x] Has CSS module for styling
- [x] Includes hover effects

**Files Created:**
- frontend/src/components/molecules/MetricCard/MetricCard.jsx
- frontend/src/components/molecules/MetricCard/MetricCard.module.css
- frontend/src/components/molecules/MetricCard/index.js
- frontend/src/components/molecules/MetricCard/MetricCard.example.jsx (bonus)
- frontend/src/components/molecules/index.js

---

### Task 1.2: Create DataTable Component
**Status:** ✅ completed
**Priority:** CRITICAL
**Estimated Time:** 3 hours
**Dependencies:** None

**Description:**
Create a reusable DataTable component with sorting, filtering, and pagination.

**Acceptance Criteria:**
- [ ] Component accepts columns and data props
- [ ] Supports column sorting (asc/desc)
- [ ] Supports pagination with page size options
- [ ] Displays loading state with skeleton rows
- [ ] Supports row selection (optional)
- [ ] Responsive design
- [ ] Dark mode support
- [ ] Empty state handling

**Files to Create:**
- src/components/molecules/DataTable/DataTable.jsx
- src/components/molecules/DataTable/DataTable.module.css
- src/components/molecules/DataTable/index.js

---

### Task 1.3: Create ChartContainer Component
**Status:** ✅ completed
**Priority:** CRITICAL
**Estimated Time:** 2 hours
**Dependencies:** None

**Description:**
Create a responsive wrapper for Recharts with consistent styling and theme support.

**Acceptance Criteria:**
- [ ] Component wraps Recharts components
- [ ] Applies theme colors automatically
- [ ] Responsive sizing
- [ ] Loading state support
- [ ] Error state support
- [ ] Dark mode support
- [ ] Consistent tooltip styling
- [ ] Legend positioning options

**Files to Create:**
- src/components/molecules/ChartContainer/ChartContainer.jsx
- src/components/molecules/ChartContainer/ChartContainer.module.css
- src/components/molecules/ChartContainer/index.js

---

### Task 1.4: Create SearchBar Component
**Status:** ✅ completed
**Priority:** HIGH
**Estimated Time:** 1.5 hours
**Dependencies:** None

**Description:**
Create a debounced search bar with clear button and loading indicator.

**Acceptance Criteria:**
- [ ] Component accepts onSearch callback
- [ ] Implements debouncing using useDebounce hook
- [ ] Shows clear button when input has value
- [ ] Shows loading indicator during search
- [ ] Keyboard shortcuts (Escape to clear)
- [ ] Accessible with proper ARIA labels
- [ ] Dark mode support

**Files to Create:**
- src/components/molecules/SearchBar/SearchBar.jsx
- src/components/molecules/SearchBar/SearchBar.module.css
- src/components/molecules/SearchBar/index.js

---

### Task 1.5: Create FilterGroup Component
**Status:** ✅ completed
**Priority:** HIGH
**Estimated Time:** 2 hours
**Dependencies:** None

**Description:**
Create a multi-select filter component with chips display.

**Acceptance Criteria:**
- [x] Component accepts filter options and onChange callback
- [x] Supports multi-select with checkboxes
- [x] Displays selected filters as chips
- [x] Chips have remove button
- [x] Clear all filters button
- [x] Accessible with keyboard navigation
- [x] Dark mode support

**Files Created:**
- frontend/src/components/molecules/FilterGroup/FilterGroup.jsx
- frontend/src/components/molecules/FilterGroup/FilterGroup.module.css
- frontend/src/components/molecules/FilterGroup/index.js

---

### Task 1.6: Create DateRangePicker Component
**Status:** ✅ completed
**Priority:** HIGH
**Estimated Time:** 2.5 hours
**Dependencies:** None

**Description:**
Create a date range picker with preset options.

**Acceptance Criteria:**
- [x] Component accepts startDate, endDate, onChange props
- [x] Calendar interface for date selection
- [x] Preset options (Last 7 days, Last 30 days, etc.)
- [x] Custom range selection
- [x] Validates date ranges
- [x] Accessible with keyboard navigation
- [x] Dark mode support

**Files Created:**
- frontend/src/components/molecules/DateRangePicker/DateRangePicker.jsx
- frontend/src/components/molecules/DateRangePicker/DateRangePicker.module.css
- frontend/src/components/molecules/DateRangePicker/index.js

---

### Task 1.7: Create ProductSelector Component
**Status:** ✅ completed
**Priority:** HIGH
**Estimated Time:** 2 hours
**Dependencies:** SearchBar

**Description:**
Create a searchable product dropdown with multi-select support.

**Acceptance Criteria:**
- [x] Component accepts products array and onChange callback
- [x] Searchable dropdown with debouncing
- [x] Supports single and multi-select modes
- [x] Displays product image and name
- [x] Shows selected count badge
- [x] Loading state for async product loading
- [x] Dark mode support

**Files Created:**
- frontend/src/components/molecules/ProductSelector/ProductSelector.jsx
- frontend/src/components/molecules/ProductSelector/ProductSelector.module.css
- frontend/src/components/molecules/ProductSelector/index.js

---

### Task 1.8: Create StatusIndicator Component
**Status:** ✅ completed
**Priority:** MEDIUM
**Estimated Time:** 1 hour
**Dependencies:** None

**Description:**
Create a status indicator with color coding and labels.

**Acceptance Criteria:**
- [x] Component accepts status and label props
- [x] Color-coded dot (green, yellow, red, gray)
- [x] Optional pulse animation for active states
- [x] Tooltip with detailed status
- [x] Dark mode support

**Files Created:**
- frontend/src/components/molecules/StatusIndicator/StatusIndicator.jsx
- frontend/src/components/molecules/StatusIndicator/StatusIndicator.module.css
- frontend/src/components/molecules/StatusIndicator/index.js

---

### Task 1.9: Create Toast Component
**Status:** ✅ completed
**Priority:** MEDIUM
**Estimated Time:** 2 hours
**Dependencies:** None

**Description:**
Create a toast notification component with auto-dismiss.

**Acceptance Criteria:**
- [x] Component accepts type, title, message, duration props
- [x] Types: success, error, info, warning
- [x] Auto-dismiss after duration
- [x] Manual dismiss button
- [x] Slide-in animation from right
- [x] Stack multiple toasts
- [x] Dark mode support

**Files Created:**
- frontend/src/components/molecules/Toast/Toast.jsx
- frontend/src/components/molecules/Toast/Toast.module.css
- frontend/src/components/molecules/Toast/ToastContainer.jsx
- frontend/src/components/molecules/Toast/index.js

---

### Task 1.10: Create ProgressBar Component
**Status:** ✅ completed
**Priority:** MEDIUM
**Estimated Time:** 1 hour
**Dependencies:** None

**Description:**
Create a linear progress bar with percentage display.

**Acceptance Criteria:**
- [x] Component accepts value and max props
- [x] Displays progress percentage
- [x] Smooth animation
- [x] Color variants (primary, success, warning, error)
- [x] Optional label
- [x] Dark mode support

**Files Created:**
- frontend/src/components/molecules/ProgressBar/ProgressBar.jsx
- frontend/src/components/molecules/ProgressBar/ProgressBar.module.css
- frontend/src/components/molecules/ProgressBar/index.js

---

### Task 1.11: Create LoadingSkeleton Component
**Status:** ✅ completed
**Priority:** MEDIUM
**Estimated Time:** 1.5 hours
**Dependencies:** None

**Description:**
Create skeleton loader variants for different content types.

**Acceptance Criteria:**
- [x] Variants: card, table, chart, text, avatar, list
- [x] Shimmer animation effect
- [x] Configurable width and height
- [x] Matches actual content structure
- [x] Dark mode support

**Files Created:**
- frontend/src/components/molecules/LoadingSkeleton/LoadingSkeleton.jsx
- frontend/src/components/molecules/LoadingSkeleton/LoadingSkeleton.module.css
- frontend/src/components/molecules/LoadingSkeleton/index.js

---

### Task 1.12: Create PageHeader Component
**Status:** ✅ completed
**Priority:** MEDIUM
**Estimated Time:** 1.5 hours
**Dependencies:** None

**Description:**
Create a consistent page header with title, breadcrumbs, and actions.

**Acceptance Criteria:**
- [x] Component accepts title, breadcrumbs, actions props
- [x] Displays page title
- [x] Breadcrumb navigation
- [x] Action buttons on the right
- [x] Responsive layout
- [x] Dark mode support

**Files Created:**
- frontend/src/components/molecules/PageHeader/PageHeader.jsx
- frontend/src/components/molecules/PageHeader/PageHeader.module.css
- frontend/src/components/molecules/PageHeader/index.js

---

## Phase 2: Organism Components - Dashboard (HIGH PRIORITY)

### Task 2.1: Create KPIDashboard Component
**Status:** ✅ completed
**Priority:** CRITICAL
**Estimated Time:** 2 hours
**Dependencies:** Task 1.1 (MetricCard)

**Description:**
Create a grid of MetricCards displaying real-time KPIs.

**Acceptance Criteria:**
- [x] Component uses useDashboardOverview hook
- [x] Displays 4 KPI cards (GMV, Margin, Conversion, Inventory)
- [x] CSS Grid layout (4 cols desktop, 2 tablet, 1 mobile)
- [x] Loading state with skeletons
- [x] Error state with retry
- [x] Auto-refresh every 5 minutes
- [x] Dark mode support

**Files Created:**
- frontend/src/features/dashboard/components/KPIDashboard.jsx
- frontend/src/features/dashboard/components/KPIDashboard.module.css
- frontend/src/features/dashboard/components/index.js

---

### Task 2.2: Create TrendChart Component
**Status:** ✅ completed
**Priority:** HIGH
**Estimated Time:** 3 hours
**Dependencies:** Task 1.3 (ChartContainer)

**Description:**
Create a line/area chart for displaying trends over time.

**Acceptance Criteria:**
- [x] Component uses Recharts LineChart/AreaChart
- [x] Accepts data, xKey, yKeys props
- [x] Responsive sizing
- [x] Tooltip with formatted values
- [x] Legend with toggle
- [x] Loading state
- [x] Dark mode support with theme colors

**Files Created:**
- frontend/src/features/dashboard/components/TrendChart.jsx
- frontend/src/features/dashboard/components/TrendChart.module.css
- frontend/src/features/dashboard/components/TrendChart.example.jsx (bonus)

---

### Task 2.3: Create AlertPanel Component
**Status:** ✅ completed
**Priority:** HIGH
**Estimated Time:** 2 hours
**Dependencies:** Task 1.8 (StatusIndicator)

**Description:**
Create a panel displaying actionable alerts with priority.

**Acceptance Criteria:**
- [x] Component displays list of alerts
- [x] Priority color coding (critical, warning, info)
- [x] Click to view alert details
- [x] Dismiss alert functionality
- [x] Empty state when no alerts
- [x] Loading state
- [x] Dark mode support

**Files Created:**
- frontend/src/features/dashboard/components/AlertPanel.jsx
- frontend/src/features/dashboard/components/AlertPanel.module.css

---

### Task 2.4: Create QuickInsights Component
**Status:** ✅ completed
**Priority:** MEDIUM
**Estimated Time:** 2 hours
**Dependencies:** None

**Description:**
Create a component displaying AI-generated insights.

**Acceptance Criteria:**
- [x] Component displays list of insights
- [x] Icon for each insight type
- [x] Expandable insight details
- [x] Loading state with skeleton
- [x] Empty state
- [x] Dark mode support

**Files Created:**
- frontend/src/features/dashboard/components/QuickInsights.jsx
- frontend/src/features/dashboard/components/QuickInsights.module.css

---

## Phase 3: Organism Components - Intelligence (HIGH PRIORITY)

### Task 3.1: Create QueryBuilder Component
**Status:** ✅ completed
**Priority:** CRITICAL
**Estimated Time:** 4 hours
**Dependencies:** Task 1.4 (SearchBar), Task 1.5 (FilterGroup)

**Description:**
Create a natural language query input with mode selector and filters.

**Acceptance Criteria:**
- [x] Textarea for query input (max 500 chars)
- [x] Character counter
- [x] Mode selector (Quick/Deep) with visual distinction
- [x] Filter panel (product, date range, categories)
- [x] Submit button (disabled when empty/loading)
- [x] Query history dropdown
- [x] Validation and error messages
- [x] Dark mode support

**Files Created:**
- frontend/src/features/query/components/QueryBuilder.jsx
- frontend/src/features/query/components/QueryBuilder.module.css
- frontend/src/features/query/components/ModeSelector.jsx
- frontend/src/features/query/components/ModeSelector.module.css

---

### Task 3.2: Create ExecutionPanel Component
**Status:** ✅ completed
**Priority:** CRITICAL
**Estimated Time:** 3 hours
**Dependencies:** Task 1.10 (ProgressBar), Task 3.4 (AgentStatus)

**Description:**
Create a panel showing query execution progress with agent status.

**Acceptance Criteria:**
- [x] Displays progress bar (0-100%)
- [x] Shows current agent status
- [x] Estimated time remaining
- [x] Cancel query button
- [x] WebSocket integration placeholder (will be wired in Phase D)
- [x] Error state with retry
- [x] Dark mode support

**Files Created:**
- frontend/src/features/query/components/ExecutionPanel.jsx
- frontend/src/features/query/components/ExecutionPanel.module.css

---

### Task 3.3: Create ResultsPanel Component
**Status:** ✅ completed
**Priority:** CRITICAL
**Estimated Time:** 4 hours
**Dependencies:** Task 1.2 (DataTable), Task 1.3 (ChartContainer)

**Description:**
Create a panel displaying structured query results.

**Acceptance Criteria:**
- [x] Executive summary section
- [x] Insight cards with key findings
- [x] Data visualization (charts/tables)
- [x] Action items list
- [x] Export functionality (CSV, PDF)
- [x] Share results button
- [x] Collapsible sections
- [x] Dark mode support

**Files Created:**
- frontend/src/features/query/components/ResultsPanel.jsx
- frontend/src/features/query/components/ResultsPanel.module.css
- frontend/src/features/query/components/ExecutiveSummary.jsx
- frontend/src/features/query/components/ExecutiveSummary.module.css
- frontend/src/features/query/components/InsightCard.jsx
- frontend/src/features/query/components/InsightCard.module.css

---

### Task 3.4: Create AgentStatus Component
**Status:** ✅ completed
**Priority:** HIGH
**Estimated Time:** 1.5 hours
**Dependencies:** Task 1.8 (StatusIndicator)

**Description:**
Create a real-time agent activity indicator.

**Acceptance Criteria:**
- [x] Displays current agent activity
- [x] Status indicator (active, idle, error)
- [x] Activity log with timestamps
- [x] Animated pulse for active state
- [x] Dark mode support

**Files Created:**
- frontend/src/features/query/components/AgentStatus.jsx
- frontend/src/features/query/components/AgentStatus.module.css

---

## Phase 4: Organism Components - Pricing (HIGH PRIORITY)

### Task 4.1: Create CompetitorMatrix Component
**Status:** ✅ completed
**Priority:** CRITICAL
**Estimated Time:** 4 hours
**Dependencies:** Task 1.2 (DataTable)

**Description:**
Create a virtualized price comparison table with highlighting.

**Acceptance Criteria:**
- [x] Virtualized table for 1000+ products
- [x] Columns: Product, Your Price, Competitor Prices, Gap
- [x] Color-coded price gaps (green=competitive, red=expensive)
- [x] Sortable columns
- [x] Sticky first column
- [x] Export to CSV
- [x] Loading state
- [x] Dark mode support

**Files Created:**
- frontend/src/features/pricing/components/CompetitorMatrix.jsx
- frontend/src/features/pricing/components/CompetitorMatrix.module.css

---

### Task 4.2: Create PriceTrendChart Component
**Status:** ✅ completed
**Priority:** HIGH
**Estimated Time:** 3 hours
**Dependencies:** Task 1.3 (ChartContainer)

**Description:**
Create a multi-line chart for price trends over time.

**Acceptance Criteria:**
- [x] Multi-line chart (your price + competitors)
- [x] Time range selector (7d, 30d, 90d, custom)
- [x] Legend with toggle lines
- [x] Tooltip with all prices
- [x] Responsive design
- [x] Loading state
- [x] Dark mode support

**Files Created:**
- frontend/src/features/pricing/components/PriceTrendChart.jsx
- frontend/src/features/pricing/components/PriceTrendChart.module.css

---

### Task 4.3: Create RecommendationPanel Component
**Status:** ✅ completed
**Priority:** HIGH
**Estimated Time:** 2.5 hours
**Dependencies:** None

**Description:**
Create a panel displaying AI pricing recommendations.

**Acceptance Criteria:**
- [x] List of pricing recommendations
- [x] Confidence score for each recommendation
- [x] Expected impact (revenue, margin)
- [x] Accept/Reject buttons
- [x] Reasoning explanation
- [x] Loading state
- [x] Dark mode support

**Files Created:**
- frontend/src/features/pricing/components/RecommendationPanel.jsx
- frontend/src/features/pricing/components/RecommendationPanel.module.css
- frontend/src/features/pricing/components/RecommendationCard.jsx
- frontend/src/features/pricing/components/RecommendationCard.module.css

---

### Task 4.4: Create PromotionTracker Component
**Status:** ✅ completed
**Priority:** MEDIUM
**Estimated Time:** 2 hours
**Dependencies:** Task 1.1 (MetricCard)

**Description:**
Create a component tracking promotion effectiveness.

**Acceptance Criteria:**
- [x] List of active promotions
- [x] Metrics per promotion (sales lift, ROI)
- [x] Performance comparison
- [x] Status indicators
- [x] Loading state
- [x] Dark mode support

**Files Created:**
- frontend/src/features/pricing/components/PromotionTracker.jsx
- frontend/src/features/pricing/components/PromotionTracker.module.css

---

## Phase 5: Organism Components - Sentiment (MEDIUM PRIORITY)

### Task 5.1: Create SentimentOverview Component
**Status:** ✅ completed
**Priority:** HIGH
**Estimated Time:** 3 hours
**Dependencies:** Task 1.3 (ChartContainer)

**Description:**
Create a sentiment gauge and distribution visualization.

**Acceptance Criteria:**
- [x] Gauge chart for overall sentiment (0-100)
- [x] Bar chart for distribution (positive/neutral/negative)
- [x] Color coding (green, gray, red)
- [x] Trend indicator
- [x] Time range selector
- [x] Loading state
- [x] Dark mode support

**Files Created:**
- frontend/src/features/sentiment/components/SentimentOverview.jsx
- frontend/src/features/sentiment/components/SentimentOverview.module.css
- frontend/src/features/sentiment/components/GaugeChart.jsx
- frontend/src/features/sentiment/components/GaugeChart.module.css

---

### Task 5.2: Create ThemeBreakdown Component
**Status:** ✅ completed
**Priority:** MEDIUM
**Estimated Time:** 3 hours
**Dependencies:** Task 1.3 (ChartContainer)

**Description:**
Create a theme analysis visualization with percentages.

**Acceptance Criteria:**
- [x] TreeMap or bar chart for themes
- [x] Percentage for each theme
- [x] Click to drill down
- [x] Top themes list
- [x] Loading state
- [x] Dark mode support

**Files Created:**
- frontend/src/features/sentiment/components/ThemeBreakdown.jsx
- frontend/src/features/sentiment/components/ThemeBreakdown.module.css

---

### Task 5.3: Create ReviewList Component
**Status:** ✅ completed
**Priority:** MEDIUM
**Estimated Time:** 3 hours
**Dependencies:** Task 1.2 (DataTable), Task 1.5 (FilterGroup)

**Description:**
Create a paginated, filterable review list.

**Acceptance Criteria:**
- [x] List of reviews with rating, text, date
- [x] Filter by sentiment, rating, date
- [x] Sort by date, rating, helpfulness
- [x] Pagination (20 per page)
- [x] Search reviews
- [x] Loading state
- [x] Dark mode support

**Files Created:**
- frontend/src/features/sentiment/components/ReviewList.jsx
- frontend/src/features/sentiment/components/ReviewList.module.css
- frontend/src/features/sentiment/components/ReviewCard.jsx
- frontend/src/features/sentiment/components/ReviewCard.module.css

---

### Task 5.4: Create ComplaintAnalysis Component
**Status:** ✅ completed
**Priority:** MEDIUM
**Estimated Time:** 2 hours
**Dependencies:** Task 1.3 (ChartContainer)

**Description:**
Create a complaint categorization and trend visualization.

**Acceptance Criteria:**
- [x] Bar chart of complaint categories
- [x] Trend over time
- [x] Top complaints list
- [x] Click to view details
- [x] Loading state
- [x] Dark mode support

**Files Created:**
- frontend/src/features/sentiment/components/ComplaintAnalysis.jsx
- frontend/src/features/sentiment/components/ComplaintAnalysis.module.css

---

## Phase 6: Organism Components - Forecast (MEDIUM PRIORITY)

### Task 6.1: Create ForecastChart Component
**Status:** ✅ completed
**Priority:** HIGH
**Estimated Time:** 4 hours
**Dependencies:** Task 1.3 (ChartContainer)

**Description:**
Create a forecast visualization with confidence bands.

**Acceptance Criteria:**
- [x] Line chart for historical data (solid)
- [x] Line chart for forecast (dashed)
- [x] Area chart for confidence bands (shaded)
- [x] Vertical line separating historical/forecast
- [x] Horizon selector (7d, 30d, 90d)
- [x] Tooltip with actual vs predicted
- [x] Loading state
- [x] Dark mode support

**Files Created:**
- frontend/src/features/forecast/components/ForecastChart.jsx
- frontend/src/features/forecast/components/ForecastChart.module.css

---

### Task 6.2: Create InventoryAlerts Component
**Status:** ✅ completed
**Priority:** MEDIUM
**Estimated Time:** 2 hours
**Dependencies:** Task 1.8 (StatusIndicator)

**Description:**
Create a component displaying inventory recommendations and alerts.

**Acceptance Criteria:**
- [x] List of inventory alerts
- [x] Priority indicators (critical, warning, info)
- [x] Recommended action for each alert
- [x] Dismiss alert functionality
- [x] Loading state
- [x] Dark mode support

**Files Created:**
- frontend/src/features/forecast/components/InventoryAlerts.jsx
- frontend/src/features/forecast/components/InventoryAlerts.module.css

---

### Task 6.3: Create DemandSupplyGap Component
**Status:** ✅ completed
**Priority:** MEDIUM
**Estimated Time:** 2.5 hours
**Dependencies:** Task 1.3 (ChartContainer)

**Description:**
Create a gap analysis visualization.

**Acceptance Criteria:**
- [x] Bar chart showing demand vs supply
- [x] Gap highlighting (surplus/shortage)
- [x] Color coding (green=surplus, red=shortage)
- [x] Time range selector
- [x] Loading state
- [x] Dark mode support

**Files Created:**
- frontend/src/features/forecast/components/DemandSupplyGap.jsx
- frontend/src/features/forecast/components/DemandSupplyGap.module.css

---

### Task 6.4: Create AccuracyMetrics Component
**Status:** ✅ completed
**Priority:** LOW
**Estimated Time:** 2 hours
**Dependencies:** Task 1.1 (MetricCard)

**Description:**
Create a component displaying forecast accuracy metrics.

**Acceptance Criteria:**
- [x] Metric cards for MAPE, RMSE, MAE
- [x] Accuracy trend over time
- [x] Comparison to baseline
- [x] Loading state
- [x] Dark mode support

**Files Created:**
- frontend/src/features/forecast/components/AccuracyMetrics.jsx
- frontend/src/features/forecast/components/AccuracyMetrics.module.css
- [ ] Loading state
- [ ] Dark mode support

**Files to Create:**
- src/features/forecast/components/AccuracyMetrics.jsx
- src/features/forecast/components/AccuracyMetrics.module.css

---

## Phase 7: Organism Components - Settings (LOW PRIORITY)

### Task 7.1: Create PreferencesPanel Component
**Status:** ⏳ pending
**Priority:** LOW
**Estimated Time:** 2 hours
**Dependencies:** None

**Description:**
Create a user preferences form.

**Acceptance Criteria:**
- [ ] Theme selector (light/dark/system)
- [ ] Language selector
- [ ] Notification preferences
- [ ] Default date range
- [ ] Save button
- [ ] Loading state
- [ ] Dark mode support

**Files to Create:**
- src/features/settings/components/PreferencesPanel.jsx
- src/features/settings/components/PreferencesPanel.module.css

---

### Task 7.2: Create AmazonIntegration Component
**Status:** ⏳ pending
**Priority:** MEDIUM
**Estimated Time:** 3 hours
**Dependencies:** Task 1.8 (StatusIndicator)

**Description:**
Create Amazon API configuration interface.

**Acceptance Criteria:**
- [ ] API key input fields
- [ ] Connection status indicator
- [ ] Test connection button
- [ ] Sync configuration
- [ ] Last sync timestamp
- [ ] Manual sync button
- [ ] Loading state
- [ ] Dark mode support

**Files to Create:**
- src/features/settings/components/AmazonIntegration.jsx
- src/features/settings/components/AmazonIntegration.module.css

---

### Task 7.3: Create TeamManagement Component
**Status:** ⏳ pending
**Priority:** LOW
**Estimated Time:** 3 hours
**Dependencies:** Task 1.2 (DataTable)

**Description:**
Create team member management interface.

**Acceptance Criteria:**
- [ ] Table of team members
- [ ] Add member button
- [ ] Edit member role
- [ ] Remove member button
- [ ] Role selector (admin, user, viewer)
- [ ] Loading state
- [ ] Dark mode support

**Files to Create:**
- src/features/settings/components/TeamManagement.jsx
- src/features/settings/components/TeamManagement.module.css

---

## Phase 8: Shared Organism Components (MEDIUM PRIORITY)

### Task 8.1: Create NotificationCenter Component
**Status:** ⏳ pending
**Priority:** MEDIUM
**Estimated Time:** 3 hours
**Dependencies:** Task 1.5 (FilterGroup)

**Description:**
Create a notification list with filters.

**Acceptance Criteria:**
- [ ] List of notifications
- [ ] Filter by type, read/unread
- [ ] Mark as read/unread
- [ ] Delete notification
- [ ] Clear all button
- [ ] Pagination
- [ ] Loading state
- [ ] Dark mode support

**Files to Create:**
- src/components/organisms/NotificationCenter/NotificationCenter.jsx
- src/components/organisms/NotificationCenter/NotificationCenter.module.css

---

### Task 8.2: Create CommandPalette Component
**Status:** ⏳ pending
**Priority:** LOW
**Estimated Time:** 4 hours
**Dependencies:** Task 1.4 (SearchBar)

**Description:**
Create a keyboard-driven command interface (⌘K).

**Acceptance Criteria:**
- [ ] Opens with ⌘K / Ctrl+K
- [ ] Searchable command list
- [ ] Keyboard navigation (arrow keys, enter)
- [ ] Recent commands
- [ ] Command categories
- [ ] Close with Escape
- [ ] Dark mode support

**Files to Create:**
- src/components/organisms/CommandPalette/CommandPalette.jsx
- src/components/organisms/CommandPalette/CommandPalette.module.css

---

### Task 8.3: Create ModalDialog Component
**Status:** ⏳ pending
**Priority:** MEDIUM
**Estimated Time:** 2 hours
**Dependencies:** None

**Description:**
Create a reusable modal dialog with variants.

**Acceptance Criteria:**
- [ ] Variants: default, confirm, alert
- [ ] Header, body, footer sections
- [ ] Close button
- [ ] Backdrop click to close
- [ ] Escape key to close
- [ ] Focus trap
- [ ] Accessible with ARIA
- [ ] Dark mode support

**Files to Create:**
- src/components/organisms/ModalDialog/ModalDialog.jsx
- src/components/organisms/ModalDialog/ModalDialog.module.css

---

## Phase 9: Page Integration (CRITICAL)

### Task 9.1: Integrate OverviewPage
**Status:** ✅ completed
**Priority:** CRITICAL
**Estimated Time:** 3 hours
**Dependencies:** Task 2.1, 2.2, 2.3, 2.4

**Description:**
Replace hardcoded data with real data from hooks.

**Acceptance Criteria:**
- [x] Import and use useDashboardOverview hook
- [x] Import and use useKPIMetrics hook
- [x] Replace hardcoded KPI cards with MetricCard components
- [x] Add TrendChart component
- [x] Add AlertPanel component
- [x] Add QuickInsights component
- [x] Implement loading states
- [x] Implement error handling
- [x] Add data refresh logic

**Files Modified:**
- frontend/src/pages/OverviewPage.jsx
- frontend/src/pages/OverviewPage.css

---

### Task 9.2: Integrate IntelligencePage
**Status:** ✅ completed
**Priority:** CRITICAL
**Estimated Time:** 4 hours
**Dependencies:** Task 3.1, 3.2, 3.3, 3.4

**Description:**
Build fully functional query execution interface.

**Acceptance Criteria:**
- [x] Add QueryBuilder component
- [x] Import and use useExecuteQuery hook
- [x] Import and use useQueryHistory hook
- [x] Add ExecutionPanel component
- [x] Add ResultsPanel component
- [x] WebSocket placeholder (will be connected in Phase D)
- [x] Implement query execution flow
- [x] Implement error handling
- [x] Add query history integration
- [x] Empty state with example queries

**Files Modified:**
- frontend/src/pages/IntelligencePage.jsx
- frontend/src/pages/IntelligencePage.module.css (created)

---

### Task 9.3: Integrate PricingPage
**Status:** ✅ completed
**Priority:** HIGH
**Estimated Time:** 3 hours
**Dependencies:** Task 4.1, 4.2, 4.3, 4.4

**Description:**
Build competitor price analysis interface.

**Acceptance Criteria:**
- [x] Add ProductSelector component
- [x] Import and use useCompetitorPricing hook
- [x] Import and use usePriceTrends hook
- [x] Import and use usePricingRecommendations hook
- [x] Import and use usePromotionAnalysis hook
- [x] Add CompetitorMatrix component
- [x] Add PriceTrendChart component
- [x] Add RecommendationPanel component
- [x] Add PromotionTracker component
- [x] Implement loading states
- [x] Implement error handling

**Files Modified:**
- frontend/src/pages/PricingPage.jsx
- frontend/src/pages/PricingPage.module.css (created)
- frontend/src/features/pricing/components/index.js (created)

---

### Task 9.4: Integrate SentimentPage
**Status:** ✅ completed
**Priority:** MEDIUM
**Estimated Time:** 3 hours
**Dependencies:** Task 5.1, 5.2, 5.3, 5.4

**Description:**
Build review sentiment analysis interface.

**Acceptance Criteria:**
- [x] Add ProductSelector component
- [x] Import and use useSentimentOverview hook
- [x] Import and use useThemeBreakdown hook
- [x] Import and use useReviews hook
- [x] Add SentimentOverview component
- [x] Add ThemeBreakdown component
- [x] Add ReviewList component
- [x] Add ComplaintAnalysis component
- [x] Implement filters
- [x] Implement loading states
- [x] Implement error handling

**Files Modified:**
- frontend/src/pages/SentimentPage.jsx
- frontend/src/pages/SentimentPage.module.css (created)

---

### Task 9.5: Integrate ForecastPage
**Status:** ✅ completed
**Priority:** MEDIUM
**Estimated Time:** 3 hours
**Dependencies:** Task 6.1, 6.2, 6.3, 6.4

**Description:**
Build demand forecasting interface.

**Acceptance Criteria:**
- [x] Add ProductSelector component
- [x] Add horizon selector
- [x] Import and use useDemandForecast hook
- [x] Import and use useInventoryRecommendations hook
- [x] Add ForecastChart component
- [x] Add InventoryAlerts component
- [x] Add DemandSupplyGap component
- [x] Add AccuracyMetrics component
- [x] Implement loading states
- [x] Implement error handling

**Files Modified:**
- frontend/src/pages/ForecastPage.jsx
- frontend/src/pages/ForecastPage.module.css (created)

---

### Task 9.6: Integrate SettingsPage
**Status:** ⏳ pending
**Priority:** LOW
**Estimated Time:** 2 hours
**Dependencies:** Task 7.1, 7.2, 7.3

**Description:**
Build settings interface with tabs.

**Acceptance Criteria:**
- [ ] Add tab navigation
- [ ] Add PreferencesPanel component
- [ ] Add AmazonIntegration component
- [ ] Add TeamManagement component
- [ ] Implement form handling
- [ ] Implement settings persistence
- [ ] Implement loading states
- [ ] Implement error handling

**Files to Modify:**
- src/pages/settings/SettingsPage.jsx

---

## Phase 10: Real-Time Features (CRITICAL)

### Task 10.1: Connect WebSocket Manager
**Status:** ⏳ pending
**Priority:** CRITICAL
**Estimated Time:** 2 hours
**Dependencies:** None

**Description:**
Connect WebSocket manager to backend and implement event handlers.

**Acceptance Criteria:**
- [ ] Connect on user login
- [ ] Disconnect on user logout
- [ ] Implement reconnection logic with exponential backoff
- [ ] Handle connection errors
- [ ] Join tenant room
- [ ] Implement event handlers for query:progress, query:complete, query:error
- [ ] Test connection stability

**Files to Modify:**
- src/lib/websocketManager.js
- src/app/providers/AuthProvider.jsx

---

### Task 10.2: Implement Query Progress Tracking
**Status:** ⏳ pending
**Priority:** CRITICAL
**Estimated Time:** 2 hours
**Dependencies:** Task 10.1, Task 3.2

**Description:**
Implement real-time query progress updates via WebSocket.

**Acceptance Criteria:**
- [ ] Subscribe to query events when query starts
- [ ] Update progress bar in real-time
- [ ] Update agent status in real-time
- [ ] Handle query completion
- [ ] Handle query errors
- [ ] Unsubscribe when component unmounts
- [ ] Test with actual backend

**Files to Modify:**
- src/features/query/hooks/useQueryExecution.js
- src/features/query/components/ExecutionPanel.jsx

---

### Task 10.3: Implement Notification System
**Status:** ⏳ pending
**Priority:** HIGH
**Estimated Time:** 3 hours
**Dependencies:** Task 1.9 (Toast)

**Description:**
Implement toast notification system with queue.

**Acceptance Criteria:**
- [ ] Integrate notificationStore with ToastContainer
- [ ] Display toasts in top-right corner
- [ ] Stack multiple toasts (max 3 visible)
- [ ] Auto-dismiss after duration
- [ ] Manual dismiss button
- [ ] Queue toasts when >3 active
- [ ] Test with different notification types

**Files to Create:**
- src/components/organisms/ToastManager/ToastManager.jsx

**Files to Modify:**
- src/app/App.jsx

---

### Task 10.4: Implement Real-Time Data Updates
**Status:** ⏳ pending
**Priority:** MEDIUM
**Estimated Time:** 2 hours
**Dependencies:** Task 10.1

**Description:**
Implement real-time data updates for dashboard KPIs.

**Acceptance Criteria:**
- [ ] Subscribe to data:updated events
- [ ] Invalidate React Query cache on updates
- [ ] Show notification on data update
- [ ] Test with backend data sync

**Files to Modify:**
- src/features/dashboard/hooks/useDashboardOverview.js
- src/lib/websocketManager.js

---

## Phase 11: State Management Cleanup (HIGH PRIORITY)

### Task 11.1: Replace AuthContext with authStore
**Status:** ⏳ pending
**Priority:** HIGH
**Estimated Time:** 2 hours
**Dependencies:** None

**Description:**
Eliminate duplication by using authStore instead of AuthContext.

**Acceptance Criteria:**
- [ ] Remove AuthContext.jsx
- [ ] Update all components using useAuth() to use useAuthStore()
- [ ] Update login/logout logic to use authStore
- [ ] Update tenant switching to use authStore
- [ ] Test authentication flow
- [ ] Test tenant switching

**Files to Modify:**
- src/app/providers/AuthProvider.jsx (remove)
- src/pages/auth/LoginPage.jsx
- src/pages/auth/SignupPage.jsx
- src/components/layout/TopBar/TopBar.jsx
- All components using useAuth()

---

### Task 11.2: Implement UI State Management
**Status:** ⏳ pending
**Priority:** MEDIUM
**Estimated Time:** 1.5 hours
**Dependencies:** None

**Description:**
Use uiStore for sidebar, theme, and modal state.

**Acceptance Criteria:**
- [ ] Use uiStore for sidebar open/close
- [ ] Use uiStore for theme selection
- [ ] Use uiStore for command palette state
- [ ] Use uiStore for modal state
- [ ] Test state persistence

**Files to Modify:**
- src/components/layout/AppShell/AppShell.jsx
- src/components/layout/SideNav/SideNav.jsx
- src/components/layout/TopBar/TopBar.jsx

---

### Task 11.3: Configure React Query Stale Times
**Status:** ⏳ pending
**Priority:** MEDIUM
**Estimated Time:** 1 hour
**Dependencies:** None

**Description:**
Configure appropriate stale times for different data types.

**Acceptance Criteria:**
- [ ] Real-time data (KPIs): 30 seconds
- [ ] Frequent data (pricing): 5 minutes
- [ ] Moderate data (sentiment): 15 minutes
- [ ] Infrequent data (forecasts): 1 hour
- [ ] Static data (preferences): Infinity
- [ ] Test cache behavior

**Files to Modify:**
- src/lib/queryClient.js
- All custom hooks using useQuery

---

## Phase 12: Error Handling (HIGH PRIORITY)

### Task 12.1: Implement Global Error Boundary
**Status:** ⏳ pending
**Priority:** HIGH
**Estimated Time:** 2 hours
**Dependencies:** None

**Description:**
Add global error boundary to catch unhandled errors.

**Acceptance Criteria:**
- [ ] Create GlobalErrorBoundary component
- [ ] Wrap App with error boundary
- [ ] Display user-friendly error page
- [ ] Log errors to Sentry (if configured)
- [ ] Provide "Try Again" button
- [ ] Test with intentional errors

**Files to Create:**
- src/components/feedback/ErrorBoundary/GlobalErrorBoundary.jsx
- src/components/feedback/ErrorBoundary/GlobalErrorFallback.jsx

**Files to Modify:**
- src/main.jsx

---

### Task 12.2: Implement Page-Level Error Boundaries
**Status:** ⏳ pending
**Priority:** HIGH
**Estimated Time:** 1.5 hours
**Dependencies:** Task 12.1

**Description:**
Add error boundaries to each page route.

**Acceptance Criteria:**
- [ ] Create PageErrorBoundary component
- [ ] Wrap each route with error boundary
- [ ] Display page-specific error fallback
- [ ] Provide "Go Back" and "Try Again" buttons
- [ ] Reset page state on retry
- [ ] Test with intentional errors

**Files to Create:**
- src/components/feedback/ErrorBoundary/PageErrorBoundary.jsx
- src/components/feedback/ErrorBoundary/PageErrorFallback.jsx

**Files to Modify:**
- src/app/Router.jsx

---

### Task 12.3: Implement Component Error States
**Status:** ⏳ pending
**Priority:** MEDIUM
**Estimated Time:** 2 hours
**Dependencies:** None

**Description:**
Add error states to all data-fetching components.

**Acceptance Criteria:**
- [ ] Create ErrorState component
- [ ] Add error handling to all organism components
- [ ] Display user-friendly error messages
- [ ] Provide retry functionality
- [ ] Test with API errors

**Files to Create:**
- src/components/feedback/ErrorState/ErrorState.jsx
- src/components/feedback/ErrorState/ErrorState.module.css

**Files to Modify:**
- All organism components

---

### Task 12.4: Implement API Error Handling
**Status:** ⏳ pending
**Priority:** HIGH
**Estimated Time:** 2 hours
**Dependencies:** None

**Description:**
Enhance API client error handling with retry logic.

**Acceptance Criteria:**
- [ ] Implement retry logic with exponential backoff
- [ ] Handle 401 errors (token refresh)
- [ ] Handle 403 errors (permissions)
- [ ] Handle 429 errors (rate limiting)
- [ ] Handle 500 errors (server errors)
- [ ] Display appropriate error messages
- [ ] Test with different error scenarios

**Files to Modify:**
- src/lib/apiClient.js

---

## Phase 13: Loading States (MEDIUM PRIORITY)

### Task 13.1: Implement Skeleton Loaders
**Status:** ⏳ pending
**Priority:** MEDIUM
**Estimated Time:** 3 hours
**Dependencies:** Task 1.11 (LoadingSkeleton)

**Description:**
Add skeleton loaders to all data-loading areas.

**Acceptance Criteria:**
- [ ] Create skeleton variants for each component type
- [ ] Add skeletons to KPIDashboard
- [ ] Add skeletons to DataTable
- [ ] Add skeletons to Charts
- [ ] Add skeletons to Lists
- [ ] Match skeleton structure to actual content
- [ ] Test loading states

**Files to Create:**
- src/components/feedback/Skeleton/KPIDashboardSkeleton.jsx
- src/components/feedback/Skeleton/DataTableSkeleton.jsx
- src/components/feedback/Skeleton/ChartSkeleton.jsx

**Files to Modify:**
- All organism components

---

### Task 13.2: Implement Progress Indicators
**Status:** ⏳ pending
**Priority:** MEDIUM
**Estimated Time:** 1 hour
**Dependencies:** Task 1.10 (ProgressBar)

**Description:**
Add progress indicators for long-running operations.

**Acceptance Criteria:**
- [ ] Add progress bar to query execution
- [ ] Add loading spinners to buttons
- [ ] Add loading spinners to data fetching
- [ ] Test with slow network

**Files to Modify:**
- src/features/query/components/ExecutionPanel.jsx
- All components with async operations

---

### Task 13.3: Implement Suspense Boundaries
**Status:** ⏳ pending
**Priority:** LOW
**Estimated Time:** 1 hour
**Dependencies:** None

**Description:**
Add Suspense boundaries for lazy-loaded components.

**Acceptance Criteria:**
- [ ] Wrap lazy-loaded routes with Suspense
- [ ] Create PageSkeleton fallback
- [ ] Test lazy loading

**Files to Create:**
- src/components/feedback/Skeleton/PageSkeleton.jsx

**Files to Modify:**
- src/app/Router.jsx

---

## Phase 14: Performance Optimization (MEDIUM PRIORITY)

### Task 14.1: Implement Code Splitting
**Status:** ⏳ pending
**Priority:** MEDIUM
**Estimated Time:** 2 hours
**Dependencies:** None

**Description:**
Implement route-based and component-based code splitting.

**Acceptance Criteria:**
- [ ] Lazy load all page components
- [ ] Lazy load heavy components (charts, tables)
- [ ] Configure manual chunks in Vite
- [ ] Test bundle sizes
- [ ] Verify lazy loading works

**Files to Modify:**
- src/app/Router.jsx
- vite.config.js

---

### Task 14.2: Implement Memoization
**Status:** ⏳ pending
**Priority:** MEDIUM
**Estimated Time:** 3 hours
**Dependencies:** None

**Description:**
Add memoization to expensive components and calculations.

**Acceptance Criteria:**
- [ ] Memoize CompetitorMatrix component
- [ ] Memoize chart components
- [ ] Memoize expensive calculations with useMemo
- [ ] Memoize event handlers with useCallback
- [ ] Test performance improvements

**Files to Modify:**
- src/features/pricing/components/CompetitorMatrix.jsx
- All chart components
- Components with expensive calculations

---

### Task 14.3: Implement Virtualization
**Status:** ⏳ pending
**Priority:** HIGH
**Estimated Time:** 3 hours
**Dependencies:** Task 1.2 (DataTable)

**Description:**
Add virtualization to DataTable for large datasets.

**Acceptance Criteria:**
- [ ] Install @tanstack/react-virtual
- [ ] Implement virtualization in DataTable
- [ ] Enable for datasets >100 rows
- [ ] Test with 10,000+ rows
- [ ] Verify smooth scrolling

**Files to Modify:**
- src/components/molecules/DataTable/DataTable.jsx

---

### Task 14.4: Implement Debouncing
**Status:** ⏳ pending
**Priority:** MEDIUM
**Estimated Time:** 1 hour
**Dependencies:** None

**Description:**
Add debouncing to search and filter inputs.

**Acceptance Criteria:**
- [ ] Use useDebounce hook in SearchBar
- [ ] Debounce filter changes (300ms)
- [ ] Debounce API calls on user input
- [ ] Test with rapid input

**Files to Modify:**
- src/components/molecules/SearchBar/SearchBar.jsx
- src/components/molecules/FilterGroup/FilterGroup.jsx

---

## Phase 15: Testing (LOW PRIORITY - Future Phase)

### Task 15.1: Setup Testing Infrastructure
**Status:** ⏳ pending
**Priority:** LOW
**Estimated Time:** 2 hours
**Dependencies:** None

**Description:**
Configure testing framework and utilities.

**Acceptance Criteria:**
- [ ] Install Vitest, React Testing Library
- [ ] Configure test setup file
- [ ] Create test utilities
- [ ] Create mock data
- [ ] Setup MSW for API mocking

**Files to Create:**
- vitest.config.js
- tests/setup.js
- tests/utils/testUtils.jsx
- tests/mocks/handlers.js

---

### Task 15.2: Write Unit Tests for Utilities
**Status:** ⏳ pending
**Priority:** LOW
**Estimated Time:** 3 hours
**Dependencies:** Task 15.1

**Description:**
Write unit tests for utility functions.

**Acceptance Criteria:**
- [ ] Test formatCurrency
- [ ] Test formatDate
- [ ] Test formatNumber
- [ ] Test formatPercentage
- [ ] Achieve 100% coverage for utilities

**Files to Create:**
- src/utils/formatters/currency.test.js
- src/utils/formatters/date.test.js
- src/utils/formatters/number.test.js

---

### Task 15.3: Write Unit Tests for Hooks
**Status:** ⏳ pending
**Priority:** LOW
**Estimated Time:** 4 hours
**Dependencies:** Task 15.1

**Description:**
Write unit tests for custom hooks.

**Acceptance Criteria:**
- [ ] Test useDashboardOverview
- [ ] Test useExecuteQuery
- [ ] Test useCompetitorPricing
- [ ] Test useSentimentOverview
- [ ] Test useDemandForecast
- [ ] Achieve 90% coverage for hooks

**Files to Create:**
- src/features/dashboard/hooks/useDashboardOverview.test.js
- src/features/query/hooks/useExecuteQuery.test.js
- src/features/pricing/hooks/useCompetitorPricing.test.js

---

### Task 15.4: Write Component Tests
**Status:** ⏳ pending
**Priority:** LOW
**Estimated Time:** 6 hours
**Dependencies:** Task 15.1

**Description:**
Write component tests for key components.

**Acceptance Criteria:**
- [ ] Test MetricCard rendering
- [ ] Test DataTable interactions
- [ ] Test QueryBuilder form
- [ ] Test CompetitorMatrix display
- [ ] Achieve 70% coverage for components

**Files to Create:**
- src/components/molecules/MetricCard/MetricCard.test.jsx
- src/components/molecules/DataTable/DataTable.test.jsx
- src/features/query/components/QueryBuilder.test.jsx

---

### Task 15.5: Write Integration Tests
**Status:** ⏳ pending
**Priority:** LOW
**Estimated Time:** 4 hours
**Dependencies:** Task 15.1

**Description:**
Write integration tests for critical flows.

**Acceptance Criteria:**
- [ ] Test login → dashboard flow
- [ ] Test query execution flow
- [ ] Test pricing analysis flow
- [ ] Test sentiment analysis flow

**Files to Create:**
- tests/integration/auth.test.jsx
- tests/integration/query.test.jsx
- tests/integration/pricing.test.jsx

---

### Task 15.6: Write E2E Tests
**Status:** ⏳ pending
**Priority:** LOW
**Estimated Time:** 6 hours
**Dependencies:** None

**Description:**
Write E2E tests for critical user journeys.

**Acceptance Criteria:**
- [ ] Install Playwright
- [ ] Configure Playwright
- [ ] Test user registration and login
- [ ] Test dashboard overview
- [ ] Test query execution (Quick and Deep)
- [ ] Test pricing analysis
- [ ] Test sentiment analysis

**Files to Create:**
- playwright.config.js
- tests/e2e/auth.spec.js
- tests/e2e/dashboard.spec.js
- tests/e2e/query.spec.js

---

## Phase 16: Deployment (CRITICAL)

### Task 16.1: Configure Build Settings
**Status:** ⏳ pending
**Priority:** CRITICAL
**Estimated Time:** 1 hour
**Dependencies:** None

**Description:**
Configure Vite build settings for production.

**Acceptance Criteria:**
- [ ] Configure manual chunks
- [ ] Set chunk size warning limit
- [ ] Disable source maps in production
- [ ] Configure minification
- [ ] Test production build

**Files to Modify:**
- vite.config.js

---

### Task 16.2: Setup Environment Variables
**Status:** ⏳ pending
**Priority:** CRITICAL
**Estimated Time:** 0.5 hours
**Dependencies:** None

**Description:**
Configure environment variables for different environments.

**Acceptance Criteria:**
- [ ] Create .env.development
- [ ] Create .env.staging
- [ ] Create .env.production
- [ ] Document required variables
- [ ] Test with different environments

**Files to Create:**
- .env.development
- .env.staging
- .env.production

---

### Task 16.3: Configure Vercel Deployment
**Status:** ⏳ pending
**Priority:** CRITICAL
**Estimated Time:** 1 hour
**Dependencies:** None

**Description:**
Configure Vercel deployment settings.

**Acceptance Criteria:**
- [ ] Create vercel.json
- [ ] Configure build command
- [ ] Configure output directory
- [ ] Set environment variables
- [ ] Configure headers
- [ ] Configure redirects/rewrites

**Files to Create:**
- vercel.json

---

### Task 16.4: Setup CI/CD Pipeline
**Status:** ⏳ pending
**Priority:** HIGH
**Estimated Time:** 2 hours
**Dependencies:** None

**Description:**
Setup GitHub Actions for CI/CD.

**Acceptance Criteria:**
- [ ] Create workflow file
- [ ] Configure test job
- [ ] Configure build job
- [ ] Configure deploy job (staging)
- [ ] Configure deploy job (production)
- [ ] Test pipeline

**Files to Create:**
- .github/workflows/deploy.yml

---

### Task 16.5: Deploy to Staging
**Status:** ⏳ pending
**Priority:** CRITICAL
**Estimated Time:** 1 hour
**Dependencies:** Task 16.1, 16.2, 16.3, 16.4

**Description:**
Deploy to staging environment and validate.

**Acceptance Criteria:**
- [ ] Deploy to Vercel staging
- [ ] Verify all pages load
- [ ] Verify API integration works
- [ ] Verify WebSocket connection works
- [ ] Run smoke tests
- [ ] Fix any issues

---

### Task 16.6: Deploy to Production
**Status:** ⏳ pending
**Priority:** CRITICAL
**Estimated Time:** 1 hour
**Dependencies:** Task 16.5

**Description:**
Deploy to production environment.

**Acceptance Criteria:**
- [ ] Deploy to Vercel production (canary)
- [ ] Monitor error rates
- [ ] Monitor performance metrics
- [ ] Promote to 100% traffic
- [ ] Verify all functionality
- [ ] Setup monitoring alerts

---

## Phase 17: Monitoring and Observability (HIGH PRIORITY)

### Task 17.1: Setup Performance Monitoring
**Status:** ⏳ pending
**Priority:** HIGH
**Estimated Time:** 2 hours
**Dependencies:** None

**Description:**
Setup performance monitoring with Web Vitals.

**Acceptance Criteria:**
- [ ] Install web-vitals library
- [ ] Create performance monitor
- [ ] Track Core Web Vitals (CLS, FID, FCP, LCP, TTFB)
- [ ] Track custom metrics (route change, API latency)
- [ ] Send metrics to analytics endpoint
- [ ] Test metrics collection

**Files to Create:**
- src/lib/performanceMonitor.js

**Files to Modify:**
- src/main.jsx

---

### Task 17.2: Setup Error Monitoring
**Status:** ⏳ pending
**Priority:** HIGH
**Estimated Time:** 1.5 hours
**Dependencies:** None

**Description:**
Setup error monitoring with Sentry (optional).

**Acceptance Criteria:**
- [ ] Install @sentry/react
- [ ] Configure Sentry
- [ ] Add user context
- [ ] Add breadcrumbs
- [ ] Test error tracking
- [ ] Setup alerts

**Files to Modify:**
- src/main.jsx
- src/lib/apiClient.js

---

### Task 17.3: Setup Analytics
**Status:** ⏳ pending
**Priority:** MEDIUM
**Estimated Time:** 1 hour
**Dependencies:** None

**Description:**
Setup analytics tracking for user behavior.

**Acceptance Criteria:**
- [ ] Create analytics utility
- [ ] Track page views
- [ ] Track user actions (query execution, etc.)
- [ ] Track feature usage
- [ ] Test analytics events

**Files to Create:**
- src/lib/analytics.js

**Files to Modify:**
- src/app/Router.jsx

---

## Summary

**Total Tasks:** 95
**Completed Tasks:** 38
**Remaining Tasks:** 57
**Total Estimated Time:** 180-220 hours (23-28 working days)
**Overall Progress:** 40.0%

**Phase Breakdown:**
- Phase 1: Molecule Components (12 tasks, 20 hours) - ✅ 100% COMPLETE
- Phase 2: Dashboard Organisms (4 tasks, 9 hours) - ✅ 100% COMPLETE
- Phase 3: Intelligence Organisms (4 tasks, 12.5 hours) - ✅ 100% COMPLETE
- Phase 4: Pricing Organisms (4 tasks, 11.5 hours) - ✅ 100% COMPLETE
- Phase 5: Sentiment Organisms (4 tasks, 11 hours) - ✅ 100% COMPLETE
- Phase 6: Forecast Organisms (4 tasks, 10.5 hours) - ✅ 100% COMPLETE
- Phase 7: Settings Organisms (3 tasks, 8 hours) - ⏳ 0% PENDING
- Phase 8: Shared Organisms (3 tasks, 9 hours) - ⏳ 0% PENDING
- Phase 9: Page Integration (6 tasks, 18 hours) - 🔄 83% COMPLETE (5/6)
- Phase 10: Real-Time Features (4 tasks, 9 hours) - ⏳ 0% PENDING
- Phase 11: State Management (3 tasks, 4.5 hours) - ⏳ 0% PENDING
- Phase 12: Error Handling (4 tasks, 7.5 hours) - ⏳ 0% PENDING
- Phase 13: Loading States (3 tasks, 5 hours) - ⏳ 0% PENDING
- Phase 14: Performance (4 tasks, 9 hours) - ⏳ 0% PENDING
- Phase 15: Testing (6 tasks, 25 hours) - ⏳ FUTURE PHASE
- Phase 16: Deployment (6 tasks, 6.5 hours) - ⏳ 0% PENDING
- Phase 17: Monitoring (3 tasks, 4.5 hours) - ⏳ 0% PENDING

**Critical Path:**
1. ✅ Phase 1 (Molecules) - COMPLETE
2. ✅ Phase 2-6 (Dashboard, Intelligence, Pricing, Sentiment, Forecast Organisms) - COMPLETE
3. ⏳ Phase 7-8 (Settings, Shared Organisms) - NEXT
4. ⏳ Complete Phase 9 (Page Integration)
5. ⏳ Phase 10 (Real-Time Features)
6. ⏳ Phase 16 (Deployment)

**Recommended Order:**
1. ✅ Complete all molecule components first (Phase 1) - DONE
2. ✅ Build organism components for Dashboard, Intelligence, Pricing, Sentiment, Forecast (Phases 2-6) - DONE
3. ⏳ Build organism components for Settings and Shared (Phases 7-8) - IN PROGRESS
4. ⏳ Complete remaining page integrations (Phase 9)
5. ⏳ Add real-time features (Phase 10)
6. ⏳ Clean up state management (Phase 11)
7. ⏳ Add error handling (Phase 12)
8. ⏳ Add loading states (Phase 13)
9. ⏳ Optimize performance (Phase 14)
10. ⏳ Deploy to staging and production (Phase 16)
11. ⏳ Setup monitoring (Phase 17)
12. ⏳ Add testing (Phase 15) - Future phase

---

**Document Version:** 1.3
**Last Updated:** February 24, 2026
**Status:** IN PROGRESS - 40.0% COMPLETE 🚀
