# Frontend to Backend Wiring Analysis

## Architecture Overview

```
Frontend (Port 5173) → Backend (Port 8000) → Mock API (Port 8001)
```

## ✅ PROPERLY WIRED COMPONENTS

### 1. Dashboard / Overview Page
**Status**: ✅ FULLY WIRED

**Data Flow**:
```
OverviewPage.jsx
  ↓ uses hooks
useDashboard.js (useKPIMetrics, useTrendData, useAlerts, useQuickInsights)
  ↓ calls
dashboardService.js (getKPIMetrics, getTrendData, getAlerts, getQuickInsights)
  ↓ uses
apiClient.js (GET /api/v1/dashboard/*)
  ↓ proxied by
vite.config.js (proxy /api → http://127.0.0.1:8000)
  ↓ handled by
src/api/dashboard.py (with Redis caching)
  ↓ uses
src/services/data_service.py (DataService)
  ↓ fetches from
Mock API on port 8001 (http://localhost:8001/api/v1/dashboard/*)
```

**Endpoints Used**:
- `/api/v1/dashboard/stats` - Overview statistics
- `/api/v1/dashboard/kpis` - KPI metrics (gmv, margin, conversion, inventory_health)
- `/api/v1/dashboard/trends` - Sales trends over time
- `/api/v1/dashboard/alerts` - Critical alerts
- `/api/v1/dashboard/insights` - AI-generated insights
- `/api/v1/dashboard/recent-activity` - Recent activity feed

**Redis Caching**: ✅ Enabled with 5-minute TTL

---

### 2. Pricing Page
**Status**: ⚠️ PARTIALLY WIRED (hooks exist, but backend endpoints missing)

**Frontend Components**:
- `PricingPage.jsx` - Main page
- Hooks: `useCompetitorPricing`, `usePriceTrends`, `usePricingRecommendations`, `usePromotionAnalysis`

**Missing Backend**:
- ❌ `/api/v1/pricing/competitor` - Competitor pricing data
- ❌ `/api/v1/pricing/trends` - Price trends
- ❌ `/api/v1/pricing/recommendations` - AI pricing recommendations
- ❌ `/api/v1/pricing/promotions` - Promotion analysis

**Action Required**: Create `src/api/pricing.py` with endpoints that use DataService to fetch from Mock API

---

### 3. Sentiment Page
**Status**: ⚠️ PARTIALLY WIRED (hooks exist, but backend endpoints missing)

**Frontend Components**:
- `SentimentPage.jsx` - Main page
- Hooks: `useSentimentOverview`, `useThemeBreakdown`, `useReviews`, `useComplaintAnalysis`

**Missing Backend**:
- ❌ `/api/v1/sentiment/overview` - Sentiment overview
- ❌ `/api/v1/sentiment/themes` - Theme breakdown
- ❌ `/api/v1/sentiment/reviews` - Reviews list
- ❌ `/api/v1/sentiment/complaints` - Complaint analysis

**Action Required**: Create `src/api/sentiment.py` with endpoints that use DataService to fetch from Mock API

---

### 4. Forecast Page
**Status**: ⚠️ PARTIALLY WIRED (hooks exist, but backend endpoints missing)

**Frontend Components**:
- `ForecastPage.jsx` - Main page
- Hooks: `useDemandForecast`, `useInventoryRecommendations`

**Missing Backend**:
- ❌ `/api/v1/forecast/demand` - Demand forecast
- ❌ `/api/v1/forecast/inventory` - Inventory recommendations
- ❌ `/api/v1/forecast/gap-analysis` - Demand-supply gap
- ❌ `/api/v1/forecast/accuracy` - Forecast accuracy metrics

**Action Required**: Create `src/api/forecast.py` with endpoints that use DataService to fetch from Mock API

---

### 5. Intelligence / Query Page
**Status**: ⚠️ PARTIALLY WIRED (hooks exist, but backend endpoints missing)

**Frontend Components**:
- `IntelligencePage.jsx` - Main page
- Hooks: `useExecuteQuery`, `useQueryHistory`, `useCancelQuery`, `useExportResults`

**Missing Backend**:
- ❌ `/api/v1/query/execute` - Execute natural language query
- ❌ `/api/v1/query/history` - Query history
- ❌ `/api/v1/query/cancel` - Cancel running query
- ❌ `/api/v1/query/export` - Export results

**Action Required**: Create `src/api/query.py` with endpoints that use DataService and LLM service

---

## Configuration Files

### ✅ Frontend Configuration

**vite.config.js**:
```javascript
server: {
  port: 5173,
  proxy: {
    '/api': {
      target: 'http://127.0.0.1:8000',  // Backend proxy
      changeOrigin: true,
      secure: false,
    },
  },
}
```

**apiClient.js**:
- Uses relative URLs in development (proxied by Vite)
- Automatically adds `Authorization` header with JWT token
- Automatically adds `X-Tenant-ID` header for tenant isolation
- Handles `{ payload: {...} }` wrapper from backend

---

### ✅ Backend Configuration

**.env**:
```bash
DATA_SOURCE=mock_api
MOCK_API_URL=http://localhost:8001
REDIS_URL=redis://172.27.52.219:6379/0
CACHE_ENABLED=True
```

**src/config.py**:
- Loads settings from `.env` using pydantic-settings
- Provides `settings.data_source`, `settings.mock_api_url`, `settings.redis_url`

**src/services/data_service.py**:
- Switches between Mock API and Database based on `DATA_SOURCE`
- Automatically filters all data by `tenant_id`
- Uses `httpx` to fetch from Mock API with `X-Internal-Key` header

**src/services/cache_service.py**:
- Redis caching with tenant isolation
- Cache keys format: `{endpoint}:{tenant_id}:{params}`
- TTL: 5-30 minutes depending on endpoint
- Graceful fallback if Redis unavailable

---

## Mock API Endpoints (Port 3001)

Based on the Mock API response, available endpoints:

### Amazon SP API Format:
- `GET /orders/v0/orders?tenantId=tenant-001`
- `GET /orders/v0/orders/:orderId/orderItems?tenantId=tenant-001`
- `GET /fba/inventory/v1/summaries?tenantId=tenant-001`

### Normalized API Format:
- `GET /api/v1/dashboard/stats?tenantId=tenant-001` ✅ USED
- `GET /api/v1/pricing/analysis?tenantId=tenant-001` ❌ NOT USED YET
- `GET /api/v1/forecast/alerts?tenantId=tenant-001` ❌ NOT USED YET

---

## Port Configuration

- **Backend**: Port 8000 (FastAPI server with DataService proxy and Redis caching)
- **Frontend**: Port 5173 (Vite dev server)
- **Mock API**: Port 8001 (Amazon Seller mock data - Multi-Tenant Amazon Seller Mock API v2.0.0)

---

## Summary

### ✅ Working (Dashboard Only):
1. Frontend fetches from backend on port 8000
2. Backend proxies to Mock API on port 3001
3. Redis caching is enabled with tenant isolation
4. All data is filtered by tenant_id from JWT token

### ⚠️ Needs Implementation:
1. **Pricing endpoints** - Create `src/api/pricing.py`
2. **Sentiment endpoints** - Create `src/api/sentiment.py`
3. **Forecast endpoints** - Create `src/api/forecast.py`
4. **Query/Intelligence endpoints** - Create `src/api/query.py`

### 🔧 Next Steps:
1. Verify Mock API has endpoints for pricing, sentiment, forecast
2. Create backend API routers for each feature
3. Use DataService pattern (same as dashboard)
4. Add Redis caching (same as dashboard)
5. Test each page end-to-end

---

## Tenant Isolation

All components properly implement tenant isolation:

1. **Frontend**: Sends `X-Tenant-ID` header from localStorage
2. **Backend Middleware**: Extracts tenant_id from JWT token
3. **DataService**: Adds `tenantId` parameter to all Mock API requests
4. **Cache Keys**: Include tenant_id for isolation
5. **Database Queries**: Filter by `WHERE tenant_id = ?`

This ensures sellers can ONLY see their own data.
