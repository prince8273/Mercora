# Complete Data Schema Analysis for E-commerce Intelligence Platform

**Date:** February 24, 2026  
**Purpose:** Complete breakdown of all data requirements, schemas, and API responses for every feature

---

## 🎯 EXECUTIVE SUMMARY

This document provides the EXACT data requirements, database schemas, and API response formats for every single page and feature in the platform.

**Key Principle:** Every table MUST have `tenant_id` column for data isolation.

**Data Flow:**
1. Seller logs in with email + password
2. Backend finds their `tenant_id` from `users` table
3. JWT token carries `tenant_id`
4. ALL queries filter by: `WHERE tenant_id = seller_tenant_id`

---

## 📊 EXISTING TABLES (Already Implemented)

### ✅ Table 1: users
```
┌──────────────────┬──────────┬─────────────────────────────────┐
│ column_name      │ type     │ description                     │
├──────────────────┼──────────┼─────────────────────────────────┤
│ id               │ UUID     │ primary key                     │
│ tenant_id        │ UUID     │ FK → tenants.id (DATA FILTER)   │
│ email            │ VARCHAR  │ login key (unique)              │
│ hashed_password  │ VARCHAR  │ bcrypt hashed password          │
│ full_name        │ VARCHAR  │ seller's full name              │
│ is_active        │ BOOLEAN  │ account status                  │
│ is_superuser     │ BOOLEAN  │ admin flag                      │
│ created_at       │ DATETIME │ account creation date           │
│ updated_at       │ DATETIME │ last update                     │
│ last_login       │ DATETIME │ last login timestamp            │
└──────────────────┴──────────┴─────────────────────────────────┘
```

### ✅ Table 2: tenants
```
┌──────────────────┬──────────┬─────────────────────────────────┐
│ column_name      │ type     │ description                     │
├──────────────────┼──────────┼─────────────────────────────────┤
│ id               │ UUID     │ primary key (tenant_id)         │
│ name             │ VARCHAR  │ seller/company name             │
│ slug             │ VARCHAR  │ unique identifier               │
│ contact_email    │ VARCHAR  │ contact email                   │
│ plan             │ VARCHAR  │ subscription plan               │
│ max_products     │ INTEGER  │ product limit                   │
│ max_users        │ INTEGER  │ user limit                      │
│ is_active        │ BOOLEAN  │ tenant status                   │
│ created_at       │ DATETIME │ tenant creation date            │
│ updated_at       │ DATETIME │ last update                     │
└──────────────────┴──────────┴─────────────────────────────────┘
```

### ✅ Table 3: products
```
┌──────────────────┬──────────┬─────────────────────────────────┐
│ column_name      │ type     │ description                     │
├──────────────────┼──────────┼─────────────────────────────────┤
│ id               │ UUID     │ primary key                     │
│ tenant_id        │ UUID     │ FK → tenants.id (DATA FILTER)   │
│ sku              │ VARCHAR  │ product SKU                     │
│ normalized_sku   │ VARCHAR  │ normalized SKU for matching     │
│ name             │ VARCHAR  │ product name                    │
│ category         │ VARCHAR  │ product category                │
│ price            │ DECIMAL  │ current price                   │
│ cost             │ DECIMAL  │ cost of goods sold              │
│ currency         │ VARCHAR  │ currency code (USD)             │
│ marketplace      │ VARCHAR  │ marketplace (Amazon, etc)       │
│ inventory_level  │ INTEGER  │ current stock level             │
│ created_at       │ DATETIME │ product creation date           │
│ updated_at       │ DATETIME │ last update                     │
│ extra_metadata   │ JSON     │ additional product data         │
└──────────────────┴──────────┴─────────────────────────────────┘
```

### ✅ Table 4: sales_records
```
┌──────────────────┬──────────┬─────────────────────────────────┐
│ column_name      │ type     │ description                     │
├──────────────────┼──────────┼─────────────────────────────────┤
│ id               │ UUID     │ primary key                     │
│ tenant_id        │ UUID     │ FK → tenants.id (DATA FILTER)   │
│ product_id       │ UUID     │ FK → products.id                │
│ quantity         │ INTEGER  │ units sold                      │
│ revenue          │ DECIMAL  │ total revenue                   │
│ date             │ DATE     │ sale date                       │
│ marketplace      │ VARCHAR  │ marketplace                     │
│ extra_data       │ JSON     │ additional sale data            │
│ created_at       │ DATETIME │ record creation date            │
└──────────────────┴──────────┴─────────────────────────────────┘
```


### ✅ Table 5: reviews
```
┌──────────────────────┬──────────┬─────────────────────────────────┐
│ column_name          │ type     │ description                     │
├──────────────────────┼──────────┼─────────────────────────────────┤
│ id                   │ UUID     │ primary key                     │
│ tenant_id            │ UUID     │ FK → tenants.id (DATA FILTER)   │
│ product_id           │ UUID     │ FK → products.id                │
│ rating               │ INTEGER  │ star rating (1-5)               │
│ text                 │ TEXT     │ review text content             │
│ review_text          │ TEXT     │ alias for text                  │
│ sentiment            │ VARCHAR  │ positive/negative/neutral       │
│ sentiment_label      │ VARCHAR  │ alias for sentiment             │
│ sentiment_confidence │ FLOAT    │ confidence score (0-1)          │
│ sentiment_score      │ FLOAT    │ alias for confidence            │
│ is_spam              │ BOOLEAN  │ spam detection flag             │
│ source               │ VARCHAR  │ review source                   │
│ created_at           │ DATETIME │ review date                     │
│ updated_at           │ DATETIME │ last update                     │
└──────────────────────┴──────────┴─────────────────────────────────┘
```

### ✅ Table 6: price_history
```
┌──────────────────┬──────────┬─────────────────────────────────┐
│ column_name      │ type     │ description                     │
├──────────────────┼──────────┼─────────────────────────────────┤
│ id               │ UUID     │ primary key                     │
│ tenant_id        │ UUID     │ FK → tenants.id (DATA FILTER)   │
│ product_id       │ UUID     │ FK → products.id                │
│ price            │ DECIMAL  │ price at this timestamp         │
│ competitor_id    │ UUID     │ FK → products.id (optional)     │
│ timestamp        │ DATETIME │ price snapshot time             │
│ source           │ VARCHAR  │ data source                     │
└──────────────────┴──────────┴─────────────────────────────────┘
```

---

## ❌ MISSING TABLES (Need to Create)

### ❌ Table 7: sellers (CRITICAL - MISSING!)
**Purpose:** Store seller profile data linked to user account

```
┌──────────────────┬──────────┬─────────────────────────────────┐
│ column_name      │ type     │ description                     │
├──────────────────┼──────────┼─────────────────────────────────┤
│ id               │ UUID     │ primary key                     │
│ user_id          │ UUID     │ FK → users.id                   │
│ tenant_id        │ UUID     │ FK → tenants.id (DATA FILTER)   │
│ email            │ VARCHAR  │ SAME as users.email             │
│ store_name       │ VARCHAR  │ Amazon store name               │
│ rating           │ FLOAT    │ seller rating (0-5)             │
│ total_sales      │ DECIMAL  │ lifetime sales                  │
│ total_products   │ INTEGER  │ product count                   │
│ total_orders     │ INTEGER  │ order count                     │
│ created_at       │ DATETIME │ seller creation date            │
│ updated_at       │ DATETIME │ last update                     │
└──────────────────┴──────────┴─────────────────────────────────┘
```

**Why needed:** Login endpoint returns seller profile data (store_name, rating, etc.)

### ❌ Table 8: alerts (MISSING!)
**Purpose:** Store dashboard alerts and notifications

```
┌──────────────────┬──────────┬─────────────────────────────────┐
│ column_name      │ type     │ description                     │
├──────────────────┼──────────┼─────────────────────────────────┤
│ id               │ UUID     │ primary key                     │
│ tenant_id        │ UUID     │ FK → tenants.id (DATA FILTER)   │
│ title            │ VARCHAR  │ alert title                     │
│ message          │ TEXT     │ alert message                   │
│ priority         │ VARCHAR  │ critical/warning/info           │
│ details          │ TEXT     │ detailed description            │
│ action_url       │ VARCHAR  │ link to action                  │
│ action_label     │ VARCHAR  │ action button text              │
│ is_dismissed     │ BOOLEAN  │ dismissal status                │
│ timestamp        │ DATETIME │ alert creation time             │
└──────────────────┴──────────┴─────────────────────────────────┘
```

**Why needed:** AlertPanel component displays alerts on dashboard

### ❌ Table 9: insights (MISSING!)
**Purpose:** Store AI-generated insights for dashboard

```
┌──────────────────┬──────────┬─────────────────────────────────┐
│ column_name      │ type     │ description                     │
├──────────────────┼──────────┼─────────────────────────────────┤
│ id               │ UUID     │ primary key                     │
│ tenant_id        │ UUID     │ FK → tenants.id (DATA FILTER)   │
│ type             │ VARCHAR  │ trend/warning/opportunity/etc   │
│ title            │ VARCHAR  │ insight title                   │
│ summary          │ TEXT     │ brief summary                   │
│ details          │ TEXT     │ detailed explanation            │
│ metrics          │ JSON     │ related metrics                 │
│ recommendation   │ TEXT     │ recommended action              │
│ created_at       │ DATETIME │ insight generation time         │
└──────────────────┴──────────┴─────────────────────────────────┘
```

**Why needed:** QuickInsights component displays AI insights


### ❌ Table 10: pricing_recommendations (MISSING!)
**Purpose:** Store AI-generated pricing recommendations

```
┌──────────────────────┬──────────┬─────────────────────────────────┐
│ column_name          │ type     │ description                     │
├──────────────────────┼──────────┼─────────────────────────────────┤
│ id                   │ UUID     │ primary key                     │
│ tenant_id            │ UUID     │ FK → tenants.id (DATA FILTER)   │
│ product_id           │ UUID     │ FK → products.id                │
│ current_price        │ DECIMAL  │ current product price           │
│ recommended_price    │ DECIMAL  │ AI recommended price            │
│ confidence           │ FLOAT    │ confidence score (0-1)          │
│ expected_revenue     │ DECIMAL  │ projected revenue impact        │
│ expected_margin      │ DECIMAL  │ projected margin impact         │
│ reasoning            │ TEXT     │ explanation for recommendation  │
│ status               │ VARCHAR  │ pending/accepted/rejected       │
│ created_at           │ DATETIME │ recommendation creation time    │
└──────────────────────┴──────────┴─────────────────────────────────┘
```

**Why needed:** RecommendationPanel displays pricing recommendations

### ❌ Table 11: promotions (MISSING!)
**Purpose:** Track promotional campaigns and their performance

```
┌──────────────────┬──────────┬─────────────────────────────────┐
│ column_name      │ type     │ description                     │
├──────────────────┼──────────┼─────────────────────────────────┤
│ id               │ UUID     │ primary key                     │
│ tenant_id        │ UUID     │ FK → tenants.id (DATA FILTER)   │
│ name             │ VARCHAR  │ promotion name                  │
│ discount         │ FLOAT    │ discount percentage             │
│ start_date       │ DATE     │ promotion start date            │
│ end_date         │ DATE     │ promotion end date              │
│ status           │ VARCHAR  │ active/scheduled/ended          │
│ sales_lift       │ FLOAT    │ sales increase percentage       │
│ revenue          │ DECIMAL  │ revenue generated               │
│ roi              │ FLOAT    │ return on investment            │
│ units_sold       │ INTEGER  │ units sold during promotion     │
│ product_ids      │ JSON     │ array of product IDs            │
│ created_at       │ DATETIME │ promotion creation time         │
└──────────────────┴──────────┴─────────────────────────────────┘
```

**Why needed:** PromotionTracker displays promotion performance

### ❌ Table 12: competitor_prices (MISSING!)
**Purpose:** Store competitor pricing data for comparison

```
┌──────────────────┬──────────┬─────────────────────────────────┐
│ column_name      │ type     │ description                     │
├──────────────────┼──────────┼─────────────────────────────────┤
│ id               │ UUID     │ primary key                     │
│ tenant_id        │ UUID     │ FK → tenants.id (DATA FILTER)   │
│ product_id       │ UUID     │ FK → products.id                │
│ competitor_name  │ VARCHAR  │ competitor name                 │
│ competitor_id    │ VARCHAR  │ competitor identifier           │
│ price            │ DECIMAL  │ competitor's price              │
│ timestamp        │ DATETIME │ price snapshot time             │
│ source           │ VARCHAR  │ data source                     │
└──────────────────┴──────────┴─────────────────────────────────┘
```

**Why needed:** CompetitorMatrix displays competitor price comparison

### ❌ Table 13: forecast_data (MISSING!)
**Purpose:** Store demand forecast predictions

```
┌──────────────────────┬──────────┬─────────────────────────────────┐
│ column_name          │ type     │ description                     │
├──────────────────────┼──────────┼─────────────────────────────────┤
│ id                   │ UUID     │ primary key                     │
│ tenant_id            │ UUID     │ FK → tenants.id (DATA FILTER)   │
│ product_id           │ UUID     │ FK → products.id                │
│ date                 │ DATE     │ forecast date                   │
│ predicted_demand     │ INTEGER  │ predicted units                 │
│ confidence_lower     │ INTEGER  │ lower confidence bound          │
│ confidence_upper     │ INTEGER  │ upper confidence bound          │
│ confidence_level     │ FLOAT    │ confidence percentage           │
│ model_version        │ VARCHAR  │ ML model version                │
│ created_at           │ DATETIME │ forecast generation time        │
└──────────────────────┴──────────┴─────────────────────────────────┘
```

**Why needed:** ForecastChart displays demand predictions

### ❌ Table 14: inventory_alerts (MISSING!)
**Purpose:** Store inventory-related alerts and recommendations

```
┌──────────────────┬──────────┬─────────────────────────────────┐
│ column_name      │ type     │ description                     │
├──────────────────┼──────────┼─────────────────────────────────┤
│ id               │ UUID     │ primary key                     │
│ tenant_id        │ UUID     │ FK → tenants.id (DATA FILTER)   │
│ product_id       │ UUID     │ FK → products.id                │
│ product_name     │ VARCHAR  │ product name                    │
│ priority         │ VARCHAR  │ critical/warning/info           │
│ title            │ VARCHAR  │ alert title                     │
│ message          │ TEXT     │ alert message                   │
│ recommendation   │ TEXT     │ recommended action              │
│ impact           │ VARCHAR  │ business impact description     │
│ actionable       │ BOOLEAN  │ can take action                 │
│ is_dismissed     │ BOOLEAN  │ dismissal status                │
│ created_at       │ DATETIME │ alert creation time             │
└──────────────────┴──────────┴─────────────────────────────────┘
```

**Why needed:** InventoryAlerts component displays inventory warnings


### ❌ Table 15: query_history (MISSING!)
**Purpose:** Store LLM query execution history

```
┌──────────────────┬──────────┬─────────────────────────────────┐
│ column_name      │ type     │ description                     │
├──────────────────┼──────────┼─────────────────────────────────┤
│ id               │ UUID     │ primary key                     │
│ tenant_id        │ UUID     │ FK → tenants.id (DATA FILTER)   │
│ user_id          │ UUID     │ FK → users.id                   │
│ query_text       │ TEXT     │ user's natural language query   │
│ query_mode       │ VARCHAR  │ quick/deep                      │
│ status           │ VARCHAR  │ pending/active/completed/error  │
│ progress         │ INTEGER  │ progress percentage (0-100)     │
│ results          │ JSON     │ query results                   │
│ execution_time   │ INTEGER  │ execution time in seconds       │
│ created_at       │ DATETIME │ query submission time           │
│ completed_at     │ DATETIME │ query completion time           │
└──────────────────┴──────────┴─────────────────────────────────┘
```

**Why needed:** IntelligencePage displays query history and results

### ❌ Table 16: sentiment_themes (MISSING!)
**Purpose:** Store sentiment analysis themes/topics

```
┌──────────────────┬──────────┬─────────────────────────────────┐
│ column_name      │ type     │ description                     │
├──────────────────┼──────────┼─────────────────────────────────┤
│ id               │ UUID     │ primary key                     │
│ tenant_id        │ UUID     │ FK → tenants.id (DATA FILTER)   │
│ product_id       │ UUID     │ FK → products.id                │
│ theme            │ VARCHAR  │ theme name (quality, shipping)  │
│ sentiment        │ VARCHAR  │ positive/negative/neutral       │
│ count            │ INTEGER  │ number of mentions              │
│ percentage       │ FLOAT    │ percentage of total reviews     │
│ sample_reviews   │ JSON     │ array of sample review IDs      │
│ created_at       │ DATETIME │ analysis time                   │
└──────────────────┴──────────┴─────────────────────────────────┘
```

**Why needed:** ThemeBreakdown component displays sentiment themes

### ❌ Table 17: complaints (MISSING!)
**Purpose:** Store categorized customer complaints

```
┌──────────────────┬──────────┬─────────────────────────────────┐
│ column_name      │ type     │ description                     │
├──────────────────┼──────────┼─────────────────────────────────┤
│ id               │ UUID     │ primary key                     │
│ tenant_id        │ UUID     │ FK → tenants.id (DATA FILTER)   │
│ product_id       │ UUID     │ FK → products.id                │
│ review_id        │ UUID     │ FK → reviews.id                 │
│ category         │ VARCHAR  │ complaint category              │
│ severity         │ VARCHAR  │ high/medium/low                 │
│ description      │ TEXT     │ complaint description           │
│ frequency        │ INTEGER  │ occurrence count                │
│ created_at       │ DATETIME │ complaint detection time        │
└──────────────────┴──────────┴─────────────────────────────────┘
```

**Why needed:** ComplaintAnalysis component displays complaint patterns

---

## 📄 PAGE-BY-PAGE DATA REQUIREMENTS

### 1️⃣ DASHBOARD PAGE (OverviewPage.jsx)

#### Metrics Displayed:
1. **Total Revenue** - Sum of all sales revenue
2. **Gross Margin** - (Revenue - Cost) / Revenue * 100
3. **Conversion Rate** - Orders / Views * 100
4. **Inventory Value** - Sum of (inventory_level * price)

#### Components:
1. **KPI Cards** - Display key metrics (revenue, margin, conversion, inventory)
2. **Revenue & Orders Trend Chart** - Line/Area chart showing revenue and orders over time
3. **Alerts Panel** - Display critical alerts
4. **Quick Insights** - AI-generated insights

#### API Endpoints:
```
GET /api/v1/dashboard/kpis          - Get KPI metrics
GET /api/v1/dashboard/trends?days=30 - Get revenue & orders trend data
GET /api/v1/dashboard/alerts        - Get alerts
GET /api/v1/dashboard/insights      - Get AI insights
GET /api/v1/dashboard/stats         - Get dashboard statistics
```

---

## 📈 REVENUE & ORDERS TREND DATA SCHEMA

### API Endpoint:
```
GET /api/v1/dashboard/trends?days=30
Headers: Authorization: Bearer JWT_TOKEN
```

### Request Parameters:
```
┌──────────────┬──────────┬──────────┬─────────────────────────────────┐
│ parameter    │ type     │ required │ description                     │
├──────────────┼──────────┼──────────┼─────────────────────────────────┤
│ days         │ INTEGER  │ optional │ number of days (default: 30)    │
└──────────────┴──────────┴──────────┴─────────────────────────────────┘
```

### Response Schema:
```json
{
  "payload": {
    "trends": [
      {
        "date": "2026-01-27",
        "sales": 53,
        "revenue": "5464.37",
        "orders": 11
      },
      {
        "date": "2026-01-28",
        "sales": 49,
        "revenue": "6416.28",
        "orders": 28
      }
    ],
    "period": "30 days"
  }
}
```

### Data Structure:
```
┌──────────────┬──────────┬─────────────────────────────────────────┐
│ field        │ type     │ description                             │
├──────────────┼──────────┼─────────────────────────────────────────┤
│ payload      │ OBJECT   │ wrapper object                          │
│ ├─ trends    │ ARRAY    │ array of daily trend data points        │
│ │  ├─ date  │ STRING   │ date in YYYY-MM-DD format               │
│ │  ├─ sales │ INTEGER  │ total units sold on this date           │
│ │  ├─ revenue│ STRING  │ total revenue (can be string or number) │
│ │  └─ orders│ INTEGER  │ total orders on this date               │
│ └─ period    │ STRING   │ time period description                 │
└──────────────┴──────────┴─────────────────────────────────────────┘
```

### Frontend Usage:
```javascript
// In OverviewPage.jsx
const { data: trendData, isLoading, error } = useTrendData('revenue', '30d');

// Access the data
const chartData = trendData?.payload?.trends || [];

// TrendChart component expects:
<TrendChart
  data={chartData}           // Array of trend objects
  xKey="date"                // X-axis field name
  yKeys={['revenue', 'orders']} // Y-axis field names (multiple lines)
  title="Revenue & Orders Trend"
  type="area"                // Chart type: line, area, bar
  formatValue={(value) => value.toLocaleString()}
  formatXAxis={(date) => new Date(date).toLocaleDateString()}
  height={350}
/>
```

### Database Query (if using database instead of Mock API):
```sql
-- Get daily trends for last N days
SELECT 
  sr.date,
  COUNT(DISTINCT sr.id) as orders,
  SUM(sr.quantity) as sales,
  SUM(sr.revenue) as revenue
FROM sales_records sr
WHERE sr.tenant_id = :tenant_id
  AND sr.date >= DATE_SUB(CURRENT_DATE, INTERVAL :days DAY)
GROUP BY sr.date
ORDER BY sr.date ASC;
```

### Mock API Implementation:
The Mock API (port 3001) generates random trend data for the specified period:
- Generates one data point per day
- Revenue ranges from $3,000 to $7,000 per day
- Orders range from 10 to 40 per day
- Sales (units) range from 20 to 70 per day

### Caching:
- **Cache Key**: `dashboard_trends:{tenant_id}:days={days}`
- **TTL**: 5 minutes (300 seconds)
- **Cache Strategy**: Cache MISS → Fetch from Mock API → Store in Redis → Return
- **Cache HIT**: Return from Redis (< 10ms response time)

### Error Handling:
```javascript
// Frontend error handling
if (trendError) {
  return <div>Failed to load trend data</div>;
}

// Backend error response
{
  "detail": "Failed to fetch trends: <error message>"
}
```

### Data Validation:
- `date` must be valid ISO date string (YYYY-MM-DD)
- `revenue` can be string or number (frontend converts to number)
- `orders` must be non-negative integer
- `sales` must be non-negative integer
- Array must be sorted by date ascending

---

#### API Response - Dashboard KPIs:
```json
{
  "seller": {
    "store_name": "Prince Electronics Store",
    "email": "prince@gmail.com",
    "rating": 4.7,
    "total_sales": 125000.00
  },
  "metrics": {
    "revenue": {
      "value": 125000.00,
      "change": 12.5
    },
    "margin": {
      "value": 35.2,
      "change": 2.1
    },
    "conversion": {
      "value": 3.8,
      "change": -0.5
    },
    "inventory": {
      "value": 45000.00,
      "change": 5.0
    }
  },
  "trendData": {
    "data": [
      { "date": "2024-01-01", "revenue": 4200, "orders": 45 },
      { "date": "2024-01-02", "revenue": 4500, "orders": 48 }
    ]
  },
  "alerts": {
    "data": [
      {
        "id": "alert-001",
        "title": "Low Stock Alert",
        "message": "Product XYZ has only 5 units left",
        "priority": "warning",
        "timestamp": "2024-01-15T10:30:00Z"
      }
    ]
  },
  "insights": {
    "data": [
      {
        "id": "insight-001",
        "type": "trend",
        "title": "Sales Increasing",
        "summary": "Your sales are up 15% this week",
        "details": "Detailed analysis...",
        "metrics": [
          { "label": "Weekly Growth", "value": "15%" }
        ],
        "recommendation": "Consider increasing inventory"
      }
    ]
  }
}
```

#### Database Queries:
```sql
-- Get seller info
SELECT * FROM sellers WHERE tenant_id = ? AND email = ?;

-- Get revenue metric
SELECT SUM(revenue) as total_revenue 
FROM sales_records 
WHERE tenant_id = ? AND date >= DATE_SUB(NOW(), INTERVAL 30 DAY);

-- Get products count
SELECT COUNT(*) FROM products WHERE tenant_id = ?;

-- Get orders count
SELECT COUNT(DISTINCT date) FROM sales_records WHERE tenant_id = ?;

-- Get alerts
SELECT * FROM alerts WHERE tenant_id = ? AND is_dismissed = FALSE ORDER BY timestamp DESC LIMIT 10;

-- Get insights
SELECT * FROM insights WHERE tenant_id = ? ORDER BY created_at DESC LIMIT 5;
```


### 2️⃣ PRICING PAGE (PricingPage.jsx)

#### Data Displayed:
1. **Competitor Price Matrix** - Your price vs competitors
2. **Price Trend Chart** - Historical price trends
3. **Pricing Recommendations** - AI-powered suggestions
4. **Promotion Tracker** - Active promotions performance

#### API Endpoints:
```
GET /api/pricing/competitor-matrix?product_id={id}
GET /api/pricing/trends?product_id={id}&timeRange=30d
GET /api/pricing/recommendations?product_id={id}
GET /api/pricing/promotions
```

#### API Response - Competitor Matrix:
```json
{
  "data": [
    {
      "productId": "prod-001",
      "productName": "Wireless Mouse",
      "sku": "WM-001",
      "yourPrice": 29.99,
      "competitorPrices": {
        "comp-001": 32.99,
        "comp-002": 27.99,
        "comp-003": 31.50
      }
    }
  ],
  "competitors": [
    { "id": "comp-001", "name": "Competitor A" },
    { "id": "comp-002", "name": "Competitor B" },
    { "id": "comp-003", "name": "Competitor C" }
  ]
}
```

#### API Response - Price Trends:
```json
{
  "data": [
    {
      "date": "2024-01-01",
      "yourPrice": 29.99,
      "competitor1": 32.99,
      "competitor2": 27.99
    }
  ]
}
```

#### API Response - Recommendations:
```json
{
  "data": [
    {
      "id": "rec-001",
      "productId": "prod-001",
      "currentPrice": 29.99,
      "recommendedPrice": 27.99,
      "confidence": 0.85,
      "expectedRevenue": 5200.00,
      "expectedMargin": 32.5,
      "reasoning": "Competitors are pricing lower. Reducing price by $2 could increase sales by 20%"
    }
  ]
}
```

#### API Response - Promotions:
```json
{
  "data": [
    {
      "id": "promo-001",
      "name": "Summer Sale",
      "discount": 15,
      "startDate": "2024-06-01",
      "endDate": "2024-06-30",
      "status": "active",
      "metrics": {
        "salesLift": 25.5,
        "revenue": 15000.00,
        "roi": 180.5,
        "unitsSold": 450
      },
      "products": ["prod-001", "prod-002"]
    }
  ]
}
```

#### Database Queries:
```sql
-- Get competitor prices
SELECT 
  p.id, p.name, p.sku, p.price as your_price,
  cp.competitor_name, cp.price as competitor_price
FROM products p
LEFT JOIN competitor_prices cp ON p.id = cp.product_id
WHERE p.tenant_id = ? AND p.id = ?;

-- Get price trends
SELECT 
  ph.timestamp as date,
  ph.price as your_price,
  cp.price as competitor_price,
  cp.competitor_name
FROM price_history ph
LEFT JOIN competitor_prices cp ON ph.product_id = cp.product_id
WHERE ph.tenant_id = ? AND ph.product_id = ?
ORDER BY ph.timestamp DESC;

-- Get recommendations
SELECT * FROM pricing_recommendations 
WHERE tenant_id = ? AND product_id = ? AND status = 'pending';

-- Get promotions
SELECT * FROM promotions 
WHERE tenant_id = ? AND status = 'active';
```

---

### 3️⃣ SENTIMENT PAGE (SentimentPage.jsx)

#### Data Displayed:
1. **Sentiment Overview** - Overall sentiment score and distribution
2. **Theme Breakdown** - Sentiment by topic/theme
3. **Review List** - Paginated customer reviews
4. **Complaint Analysis** - Common complaint patterns

#### API Endpoints:
```
GET /api/sentiment/overview?product_id={id}&timeRange=30d
GET /api/sentiment/themes?product_id={id}&timeRange=30d
GET /api/sentiment/reviews?product_id={id}&page=1&limit=20
GET /api/sentiment/complaints?product_id={id}&timeRange=30d
```

#### API Response - Sentiment Overview:
```json
{
  "overallScore": 75.5,
  "trend": 5.2,
  "distribution": {
    "positive": 65,
    "neutral": 20,
    "negative": 15
  },
  "totalReviews": 230
}
```

#### API Response - Theme Breakdown:
```json
{
  "themes": [
    {
      "theme": "Quality",
      "sentiment": "positive",
      "count": 145,
      "percentage": 63.0,
      "sampleReviews": ["rev-001", "rev-002"]
    },
    {
      "theme": "Shipping",
      "sentiment": "negative",
      "count": 35,
      "percentage": 15.2,
      "sampleReviews": ["rev-003", "rev-004"]
    }
  ]
}
```

#### API Response - Reviews:
```json
{
  "reviews": [
    {
      "id": "rev-001",
      "productId": "prod-001",
      "rating": 5,
      "text": "Great product! Highly recommend.",
      "title": "Excellent quality",
      "sentiment": "positive",
      "date": "2024-01-15T10:30:00Z",
      "helpfulVotes": 12
    }
  ],
  "total": 230,
  "page": 1,
  "totalPages": 12
}
```

#### API Response - Complaints:
```json
{
  "complaints": [
    {
      "category": "Shipping Delay",
      "severity": "high",
      "frequency": 25,
      "percentage": 10.9,
      "description": "Customers reporting late deliveries",
      "sampleReviews": ["rev-005", "rev-006"]
    }
  ]
}
```

#### Database Queries:
```sql
-- Get sentiment overview
SELECT 
  AVG(sentiment_score) as overall_score,
  COUNT(*) as total_reviews,
  SUM(CASE WHEN sentiment = 'positive' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as positive_pct,
  SUM(CASE WHEN sentiment = 'neutral' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as neutral_pct,
  SUM(CASE WHEN sentiment = 'negative' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as negative_pct
FROM reviews
WHERE tenant_id = ? AND product_id = ?;

-- Get themes
SELECT * FROM sentiment_themes 
WHERE tenant_id = ? AND product_id = ?
ORDER BY count DESC;

-- Get reviews
SELECT * FROM reviews 
WHERE tenant_id = ? AND product_id = ?
ORDER BY created_at DESC
LIMIT ? OFFSET ?;

-- Get complaints
SELECT * FROM complaints 
WHERE tenant_id = ? AND product_id = ?
ORDER BY frequency DESC;
```


### 4️⃣ FORECAST PAGE (ForecastPage.jsx)

#### Data Displayed:
1. **Forecast Chart** - Historical vs predicted demand
2. **Inventory Alerts** - Stock warnings and recommendations
3. **Demand-Supply Gap** - Gap analysis
4. **Accuracy Metrics** - Forecast accuracy stats

#### API Endpoints:
```
GET /api/forecast/demand?product_id={id}&horizon=30d
GET /api/forecast/inventory-alerts?product_id={id}
GET /api/forecast/gap-analysis?product_id={id}&timeRange=30d
GET /api/forecast/accuracy?product_id={id}
```

#### API Response - Demand Forecast:
```json
{
  "historical": [
    {
      "date": "2024-01-01",
      "actual": 45,
      "type": "historical"
    }
  ],
  "forecast": [
    {
      "date": "2024-02-01",
      "predicted": 52,
      "confidenceLower": 45,
      "confidenceUpper": 60,
      "type": "forecast"
    }
  ],
  "stats": {
    "avgHistorical": 48.5,
    "avgForecast": 52.3,
    "change": 7.8,
    "peakDemand": 65,
    "confidence": 95
  },
  "accuracy": {
    "mape": 8.5,
    "rmse": 4.2,
    "accuracy": 91.5
  },
  "gapAnalysis": {
    "currentInventory": 120,
    "forecastedDemand": 156,
    "gap": -36,
    "daysOfStock": 23
  }
}
```

#### API Response - Inventory Alerts:
```json
{
  "alerts": [
    {
      "id": "alert-001",
      "productId": "prod-001",
      "productName": "Wireless Mouse",
      "priority": "critical",
      "title": "Stock Out Risk",
      "message": "Current inventory will run out in 5 days",
      "recommendation": "Order 200 units immediately",
      "impact": "Potential revenue loss: $5,000",
      "actionable": true,
      "createdAt": "2024-01-15T10:30:00Z"
    }
  ]
}
```

#### Database Queries:
```sql
-- Get historical sales
SELECT date, SUM(quantity) as actual
FROM sales_records
WHERE tenant_id = ? AND product_id = ?
GROUP BY date
ORDER BY date DESC
LIMIT 90;

-- Get forecast data
SELECT date, predicted_demand, confidence_lower, confidence_upper
FROM forecast_data
WHERE tenant_id = ? AND product_id = ?
ORDER BY date ASC;

-- Get inventory alerts
SELECT * FROM inventory_alerts
WHERE tenant_id = ? AND product_id = ? AND is_dismissed = FALSE
ORDER BY priority DESC, created_at DESC;

-- Get current inventory
SELECT inventory_level FROM products
WHERE tenant_id = ? AND id = ?;
```

---

### 5️⃣ INTELLIGENCE PAGE (IntelligencePage.jsx)

#### Data Displayed:
1. **Query Builder** - Natural language query input
2. **Execution Panel** - Real-time query progress
3. **Results Panel** - Query results with insights
4. **Query History** - Previous queries

#### API Endpoints:
```
POST /api/query/execute
GET /api/query/history?limit=10
GET /api/query/status/{query_id}
POST /api/query/cancel/{query_id}
POST /api/query/export/{query_id}
```

#### API Request - Execute Query:
```json
{
  "query": "What are my top-selling products this month?",
  "mode": "quick",
  "filters": {
    "dateRange": "30d",
    "category": "Electronics"
  }
}
```

#### API Response - Execute Query:
```json
{
  "id": "query-001",
  "status": "active",
  "progress": 0,
  "estimatedTime": 15
}
```

#### API Response - Query Status (WebSocket or Polling):
```json
{
  "id": "query-001",
  "status": "active",
  "progress": 45,
  "currentActivity": "Analyzing sales data",
  "activityLog": [
    "Fetching product data...",
    "Analyzing sales trends...",
    "Generating insights..."
  ],
  "estimatedTime": 8
}
```

#### API Response - Query Complete:
```json
{
  "id": "query-001",
  "status": "completed",
  "progress": 100,
  "results": {
    "summary": "Your top 5 products generated $45,000 in revenue this month",
    "insights": [
      {
        "type": "finding",
        "title": "Top Performer",
        "description": "Wireless Mouse is your best seller with 450 units sold"
      }
    ],
    "data": {
      "products": [
        {
          "name": "Wireless Mouse",
          "revenue": 13500,
          "units": 450,
          "growth": 15.5
        }
      ]
    },
    "visualizations": [
      {
        "type": "bar",
        "data": [...]
      }
    ],
    "actionItems": [
      {
        "priority": "high",
        "action": "Increase inventory for Wireless Mouse",
        "reason": "High demand and low stock"
      }
    ]
  },
  "executionTime": 12
}
```

#### API Response - Query History:
```json
{
  "data": [
    {
      "id": "query-001",
      "query": "What are my top-selling products?",
      "mode": "quick",
      "status": "completed",
      "createdAt": "2024-01-15T10:30:00Z",
      "executionTime": 12
    }
  ]
}
```

#### Database Queries:
```sql
-- Save query
INSERT INTO query_history (id, tenant_id, user_id, query_text, query_mode, status, created_at)
VALUES (?, ?, ?, ?, ?, 'pending', NOW());

-- Update query progress
UPDATE query_history 
SET status = ?, progress = ?, results = ?
WHERE id = ? AND tenant_id = ?;

-- Get query history
SELECT * FROM query_history
WHERE tenant_id = ? AND user_id = ?
ORDER BY created_at DESC
LIMIT ?;
```


### 6️⃣ SETTINGS PAGE (SettingsPage.jsx)

#### Data Displayed:
1. **Preferences Panel** - User preferences and settings
2. **Amazon Integration** - API key configuration

#### API Endpoints:
```
GET /api/settings/preferences
PUT /api/settings/preferences
GET /api/settings/amazon-integration
PUT /api/settings/amazon-integration
POST /api/settings/amazon-integration/test
```

#### API Response - Preferences:
```json
{
  "notifications": {
    "email": true,
    "push": false,
    "alerts": true
  },
  "display": {
    "theme": "dark",
    "language": "en",
    "timezone": "America/New_York"
  },
  "dataRefresh": {
    "interval": 300,
    "autoRefresh": true
  }
}
```

#### API Response - Amazon Integration:
```json
{
  "isConnected": true,
  "apiKey": "AKIAIOSFODNN7EXAMPLE",
  "secretKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
  "region": "us-east-1",
  "lastSync": "2024-01-15T10:30:00Z",
  "status": "active"
}
```

#### Database Queries:
```sql
-- Get preferences
SELECT * FROM user_preferences
WHERE user_id = ? AND tenant_id = ?;

-- Update preferences
UPDATE user_preferences
SET preferences = ?
WHERE user_id = ? AND tenant_id = ?;
```

---

## 🔑 AUTHENTICATION FLOW

### Login Endpoint
```
POST /api/auth/login
```

#### Request:
```json
{
  "email": "prince@gmail.com",
  "password": "password123"
}
```

#### Response:
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user_id": "user-001",
  "tenant_id": "tenant-001",
  "seller": {
    "store_name": "Prince Electronics Store",
    "email": "prince@gmail.com",
    "rating": 4.7,
    "total_sales": 125000.00,
    "total_products": 45,
    "total_orders": 890
  }
}
```

#### Backend Logic:
```python
def login(email: str, password: str):
    # 1. Find user by email
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(404, "User not found")
    
    # 2. Verify password
    if not verify_password(password, user.hashed_password):
        raise HTTPException(401, "Invalid credentials")
    
    # 3. Get tenant_id
    tenant_id = user.tenant_id
    
    # 4. Get seller data
    seller = db.query(Seller).filter(
        Seller.email == email,
        Seller.tenant_id == tenant_id
    ).first()
    
    # 5. Generate JWT token with tenant_id
    token = create_jwt_token({
        "user_id": str(user.id),
        "email": user.email,
        "tenant_id": str(tenant_id)
    })
    
    # 6. Return everything
    return {
        "token": token,
        "user_id": str(user.id),
        "tenant_id": str(tenant_id),
        "seller": {
            "store_name": seller.store_name,
            "email": seller.email,
            "rating": seller.rating,
            "total_sales": seller.total_sales,
            "total_products": seller.total_products,
            "total_orders": seller.total_orders
        }
    }
```

---

## 📝 MOCK DATA REQUIREMENTS

### Mock Sellers (10 sellers to create):

```python
MOCK_SELLERS = [
    {
        "email": "prince@gmail.com",
        "password": "password123",
        "store_name": "Prince Electronics Store",
        "rating": 4.7,
        "total_sales": 125000.00,
        "total_products": 45,
        "total_orders": 890
    },
    {
        "email": "john@gmail.com",
        "password": "password123",
        "store_name": "John Fashion Hub",
        "rating": 4.3,
        "total_sales": 89000.00,
        "total_products": 30,
        "total_orders": 654
    },
    {
        "email": "mary@gmail.com",
        "password": "password123",
        "store_name": "Mary Home Decor",
        "rating": 4.8,
        "total_sales": 210000.00,
        "total_products": 60,
        "total_orders": 1200
    },
    {
        "email": "alex@gmail.com",
        "password": "password123",
        "store_name": "Alex Sports World",
        "rating": 4.1,
        "total_sales": 67000.00,
        "total_products": 25,
        "total_orders": 430
    },
    {
        "email": "sara@gmail.com",
        "password": "password123",
        "store_name": "Sara Beauty Shop",
        "rating": 4.6,
        "total_sales": 175000.00,
        "total_products": 80,
        "total_orders": 980
    },
    {
        "email": "rahul@gmail.com",
        "password": "password123",
        "store_name": "Rahul Tech Gadgets",
        "rating": 4.9,
        "total_sales": 290000.00,
        "total_products": 55,
        "total_orders": 1500
    },
    {
        "email": "priya@gmail.com",
        "password": "password123",
        "store_name": "Priya Clothing Co",
        "rating": 4.4,
        "total_sales": 95000.00,
        "total_products": 40,
        "total_orders": 720
    },
    {
        "email": "david@gmail.com",
        "password": "password123",
        "store_name": "David Books Store",
        "rating": 4.2,
        "total_sales": 45000.00,
        "total_products": 200,
        "total_orders": 2100
    },
    {
        "email": "lisa@gmail.com",
        "password": "password123",
        "store_name": "Lisa Kitchen World",
        "rating": 4.5,
        "total_sales": 140000.00,
        "total_products": 70,
        "total_orders": 860
    },
    {
        "email": "demo@example.com",
        "password": "demo123",
        "store_name": "Demo Test Store",
        "rating": 4.0,
        "total_sales": 50000.00,
        "total_products": 30,
        "total_orders": 300
    }
]
```

### Mock Data Per Seller:

For EACH seller, create:

1. **Products** (10-20 products per seller)
   - Random SKUs, names, prices
   - Categories: Electronics, Fashion, Home, Sports, Beauty
   - Inventory levels: 10-500 units

2. **Sales Records** (100-200 records per seller)
   - Last 90 days of sales data
   - Random quantities: 1-10 units per sale
   - Revenue = quantity * price

3. **Reviews** (50-100 reviews per seller)
   - Random ratings: 1-5 stars
   - Random sentiment: 60% positive, 25% neutral, 15% negative
   - Random review text

4. **Price History** (30 days of price data)
   - Daily price snapshots for each product
   - Small price variations (±5%)

5. **Competitor Prices** (3-5 competitors per product)
   - Competitor names: "Competitor A", "Competitor B", etc.
   - Prices: ±10% of seller's price

6. **Alerts** (3-5 alerts per seller)
   - Mix of critical, warning, info priorities
   - Low stock, price changes, review alerts

7. **Insights** (3-5 insights per seller)
   - AI-generated insights about trends, opportunities

8. **Promotions** (1-2 active promotions per seller)
   - 10-20% discounts
   - Performance metrics

9. **Forecast Data** (30 days ahead)
   - Predicted demand for each product
   - Confidence intervals

10. **Inventory Alerts** (2-3 alerts per seller)
    - Stock warnings, reorder recommendations


---

## 📊 SUMMARY TABLE: EXISTING vs MISSING

| Table Name | Status | Purpose | Priority |
|------------|--------|---------|----------|
| users | ✅ EXISTS | Authentication | CRITICAL |
| tenants | ✅ EXISTS | Multi-tenancy | CRITICAL |
| products | ✅ EXISTS | Product catalog | CRITICAL |
| sales_records | ✅ EXISTS | Sales history | CRITICAL |
| reviews | ✅ EXISTS | Customer reviews | CRITICAL |
| price_history | ✅ EXISTS | Price tracking | HIGH |
| **sellers** | ❌ MISSING | Seller profiles | **CRITICAL** |
| **alerts** | ❌ MISSING | Dashboard alerts | **HIGH** |
| **insights** | ❌ MISSING | AI insights | **HIGH** |
| **pricing_recommendations** | ❌ MISSING | Pricing AI | **HIGH** |
| **promotions** | ❌ MISSING | Promotion tracking | **MEDIUM** |
| **competitor_prices** | ❌ MISSING | Competitor data | **HIGH** |
| **forecast_data** | ❌ MISSING | Demand forecasts | **HIGH** |
| **inventory_alerts** | ❌ MISSING | Inventory warnings | **HIGH** |
| **query_history** | ❌ MISSING | LLM query logs | **HIGH** |
| **sentiment_themes** | ❌ MISSING | Sentiment topics | **MEDIUM** |
| **complaints** | ❌ MISSING | Complaint analysis | **MEDIUM** |

---

## 🚀 IMPLEMENTATION PRIORITY

### Phase 1: CRITICAL (Must have for login to work)
1. **Create `sellers` table** - Required for login response
2. **Populate 10 mock sellers** - Test data
3. **Update login endpoint** - Return seller data

### Phase 2: HIGH (Dashboard must work)
4. **Create `alerts` table** - Dashboard alerts
5. **Create `insights` table** - Dashboard insights
6. **Create `competitor_prices` table** - Pricing page
7. **Create `pricing_recommendations` table** - Pricing page
8. **Create `forecast_data` table** - Forecast page
9. **Create `inventory_alerts` table** - Forecast page
10. **Create `query_history` table** - Intelligence page

### Phase 3: MEDIUM (Nice to have)
11. **Create `promotions` table** - Pricing page
12. **Create `sentiment_themes` table** - Sentiment page
13. **Create `complaints` table** - Sentiment page

---

## 🔍 DATA FILTERING EXAMPLES

### Example 1: Dashboard Metrics
```python
# Get seller's total revenue
revenue = db.query(func.sum(SalesRecord.revenue))\
    .filter(SalesRecord.tenant_id == tenant_id)\
    .scalar()

# Get seller's product count
product_count = db.query(func.count(Product.id))\
    .filter(Product.tenant_id == tenant_id)\
    .scalar()
```

### Example 2: Pricing Page
```python
# Get competitor prices for seller's product
competitor_prices = db.query(CompetitorPrice)\
    .join(Product, CompetitorPrice.product_id == Product.id)\
    .filter(Product.tenant_id == tenant_id)\
    .filter(Product.id == product_id)\
    .all()
```

### Example 3: Sentiment Page
```python
# Get reviews for seller's product
reviews = db.query(Review)\
    .filter(Review.tenant_id == tenant_id)\
    .filter(Review.product_id == product_id)\
    .order_by(Review.created_at.desc())\
    .limit(20)\
    .all()
```

### Example 4: Forecast Page
```python
# Get forecast for seller's product
forecast = db.query(ForecastData)\
    .filter(ForecastData.tenant_id == tenant_id)\
    .filter(ForecastData.product_id == product_id)\
    .order_by(ForecastData.date.asc())\
    .all()
```

---

## 🎯 KEY TAKEAWAYS

1. **Every table MUST have `tenant_id`** - This is the data filter
2. **7 tables already exist** - users, tenants, products, sales_records, reviews, price_history, user_preferences
3. **10 tables are MISSING** - sellers, alerts, insights, pricing_recommendations, promotions, competitor_prices, forecast_data, inventory_alerts, query_history, sentiment_themes, complaints
4. **Login flow requires `sellers` table** - CRITICAL priority
5. **Dashboard requires `alerts` and `insights` tables** - HIGH priority
6. **All API responses filter by `tenant_id` from JWT token**
7. **Mock data needed for 10 sellers** - Each with products, sales, reviews, etc.

---

## 📝 NEXT STEPS

### Step 1: Create Missing Tables
```bash
# Create migration for missing tables
alembic revision --autogenerate -m "Add missing tables for seller data"
alembic upgrade head
```

### Step 2: Create Sellers Table Model
```python
# src/models/seller.py
class Seller(Base):
    __tablename__ = "sellers"
    
    id = Column(GUID(), primary_key=True, default=uuid4)
    user_id = Column(GUID(), ForeignKey('users.id'), nullable=False)
    tenant_id = Column(GUID(), ForeignKey('tenants.id'), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    store_name = Column(String(255), nullable=False)
    rating = Column(Float, nullable=True)
    total_sales = Column(Numeric(10, 2), default=0)
    total_products = Column(Integer, default=0)
    total_orders = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### Step 3: Update Login Endpoint
```python
# src/api/auth.py
@router.post("/login")
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    # ... existing validation ...
    
    # Get seller data
    seller = db.query(Seller).filter(
        Seller.email == credentials.email,
        Seller.tenant_id == user.tenant_id
    ).first()
    
    return {
        "token": token,
        "user_id": str(user.id),
        "tenant_id": str(user.tenant_id),
        "seller": {
            "store_name": seller.store_name,
            "email": seller.email,
            "rating": seller.rating,
            "total_sales": float(seller.total_sales),
            "total_products": seller.total_products,
            "total_orders": seller.total_orders
        }
    }
```

### Step 4: Create Mock Data Script
```python
# scripts/create_mock_sellers.py
def create_mock_sellers():
    for seller_data in MOCK_SELLERS:
        # Create tenant
        tenant = Tenant(name=seller_data["store_name"], ...)
        
        # Create user
        user = User(email=seller_data["email"], tenant_id=tenant.id, ...)
        
        # Create seller
        seller = Seller(
            user_id=user.id,
            tenant_id=tenant.id,
            email=seller_data["email"],
            store_name=seller_data["store_name"],
            ...
        )
        
        # Create products, sales, reviews, etc.
        create_mock_products(tenant.id, seller.id)
        create_mock_sales(tenant.id)
        create_mock_reviews(tenant.id)
```

### Step 5: Test Login Flow
```bash
# Test login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"prince@gmail.com","password":"password123"}'

# Expected response:
{
  "token": "eyJ...",
  "tenant_id": "tenant-001",
  "seller": {
    "store_name": "Prince Electronics Store",
    "rating": 4.7,
    ...
  }
}
```

---

**Last Updated:** February 24, 2026  
**Status:** Complete analysis - Ready for implementation  
**Next Action:** Create missing database tables and populate mock data

