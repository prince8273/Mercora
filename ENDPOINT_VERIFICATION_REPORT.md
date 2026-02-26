# Backend Endpoint Verification Report

**Date:** February 25, 2026  
**Purpose:** Verify which API endpoints exist and which need to be created

---

## ✅ EXISTING ENDPOINTS (Verified)

### Authentication (auth.py)
- ✅ `POST /api/v1/auth/register` - Register new user
- ✅ `POST /api/v1/auth/login` - Login and get JWT token
- ✅ `GET /api/v1/auth/me` - Get current user profile

### Dashboard (dashboard.py)
- ✅ `GET /api/v1/dashboard/stats` - Get dashboard statistics
- ✅ `GET /api/v1/dashboard/recent-activity` - Get recent activity

### Products (products.py)
- ✅ `POST /api/v1/products` - Create product
- ✅ `GET /api/v1/products/{product_id}` - Get single product
- ✅ `GET /api/v1/products` - List all products
- ✅ `PUT /api/v1/products/{product_id}` - Update product
- ✅ `DELETE /api/v1/products/{product_id}` - Delete product

### Sentiment (sentiment.py)
- ✅ `GET /api/v1/sentiment/product/{product_id}` - Get product sentiment analysis
- ✅ `POST /api/v1/sentiment/analyze` - Analyze sentiment for multiple products

### Forecast (forecast.py)
- ✅ `POST /api/v1/forecast` - Generate demand forecast
- ✅ `GET /api/v1/forecast/product/{product_id}` - Get product forecast

### Pricing (pricing.py)
- ✅ `GET /api/v1/pricing/analysis` - Get pricing analysis
- ✅ `POST /api/v1/pricing/analysis` - Analyze pricing

### Query (query.py)
- ✅ `POST /api/v1/query` - Execute natural language query

### Insights (insights.py)
- ✅ `GET /api/v1/insights/generate` - Generate insights
- ✅ `GET /api/v1/insights/summary` - Get insights summary

### CSV Upload (csv_upload.py)
- ✅ `POST /api/v1/csv/upload/products` - Upload products CSV
- ✅ `POST /api/v1/csv/upload/reviews` - Upload reviews CSV
- ✅ `POST /api/v1/csv/upload/sales` - Upload sales CSV
- ✅ `POST /api/v1/csv/analyze` - Analyze CSV with custom query

### Ingestion (ingestion.py)
- ✅ `POST /api/v1/ingestion/upload/products` - Upload products
- ✅ `POST /api/v1/ingestion/upload/reviews` - Upload reviews
- ✅ `POST /api/v1/ingestion/upload/json` - Upload JSON data
- ✅ `GET /api/v1/ingestion/status/{job_id}` - Get ingestion status
- ✅ `GET /api/v1/ingestion/jobs` - List ingestion jobs

---

## ❌ MISSING ENDPOINTS (Need to Create)

### Dashboard Endpoints
- ❌ `GET /api/v1/dashboard/kpis` - Get KPI metrics (revenue, margin, conversion)
- ❌ `GET /api/v1/dashboard/insights` - Get AI-generated insights
- ❌ `GET /api/v1/dashboard/alerts` - Get active alerts
- ❌ `GET /api/v1/dashboard/trends` - Get historical trend data
- ❌ `GET /api/v1/dashboard/summary` - Get dashboard summary

**Note:** `/insights/generate` exists but frontend expects `/dashboard/insights`

### Pricing Endpoints
- ❌ `GET /api/v1/pricing/recommendations/{product_id}` - Get pricing recommendations
- ❌ `GET /api/v1/pricing/history/{product_id}` - Get price history
- ❌ `GET /api/v1/pricing/promotions/{product_id}` - Get promotion effectiveness

### Sentiment Endpoints
- ❌ `GET /api/v1/sentiment/reviews/{product_id}` - Get product reviews
- ❌ `GET /api/v1/sentiment/themes/{product_id}` - Get sentiment themes
- ❌ `GET /api/v1/sentiment/complaints/{product_id}` - Get complaint analysis
- ❌ `GET /api/v1/sentiment/features/{product_id}` - Get feature requests
- ❌ `GET /api/v1/sentiment/trends/{product_id}` - Get sentiment trends

### Forecast Endpoints
- ❌ `GET /api/v1/forecast/alerts` - Get inventory alerts
- ❌ `GET /api/v1/forecast/accuracy/{product_id}` - Get forecast accuracy
- ❌ `GET /api/v1/forecast/gap/{product_id}` - Get demand-supply gap
- ❌ `GET /api/v1/forecast/seasonality/{product_id}` - Get seasonality analysis
- ❌ `GET /api/v1/forecast/reorder` - Get reorder recommendations

### Query Endpoints
- ❌ `GET /api/v1/query/{query_id}` - Get query result by ID
- ❌ `GET /api/v1/query/history` - Get query history
- ❌ `GET /api/v1/query/{query_id}/status` - Get query status
- ❌ `GET /api/v1/query/suggestions` - Get query suggestions

---

## 🔄 ENDPOINT MAPPING (Frontend → Backend)

### What Frontend Calls vs What Backend Has:

| Frontend Expects | Backend Has | Status | Action Needed |
|-----------------|-------------|--------|---------------|
| `GET /api/v1/dashboard/stats` | ✅ Exists | ✅ Working | None |
| `GET /api/v1/dashboard/kpis` | ❌ Missing | ❌ Not Working | Create endpoint |
| `GET /api/v1/dashboard/insights` | ⚠️ `/insights/generate` | ⚠️ Different path | Create alias or update frontend |
| `GET /api/v1/dashboard/alerts` | ❌ Missing | ❌ Not Working | Create endpoint |
| `GET /api/v1/dashboard/trends` | ❌ Missing | ❌ Not Working | Create endpoint |
| `GET /api/v1/sentiment/product/{id}` | ✅ Exists | ✅ Working | None |
| `GET /api/v1/sentiment/reviews/{id}` | ❌ Missing | ❌ Not Working | Create endpoint |
| `GET /api/v1/sentiment/themes/{id}` | ❌ Missing | ❌ Not Working | Create endpoint |
| `GET /api/v1/forecast/product/{id}` | ✅ Exists | ✅ Working | None |
| `GET /api/v1/forecast/alerts` | ❌ Missing | ❌ Not Working | Create endpoint |
| `GET /api/v1/pricing/analysis` | ✅ Exists | ✅ Working | None |
| `GET /api/v1/pricing/recommendations/{id}` | ❌ Missing | ❌ Not Working | Create endpoint |

---

## 🎯 PRIORITY ENDPOINTS TO CREATE

### Priority 1: CRITICAL (Dashboard Won't Work Without These)

1. **GET /api/v1/dashboard/kpis**
   ```python
   @router.get("/kpis")
   async def get_dashboard_kpis(
       timeRange: str = "30d",
       db: AsyncSession = Depends(get_db),
       tenant_id: UUID = Depends(get_tenant_id)
   ):
       # Calculate revenue, margin, conversion, inventory
       # Filter by tenant_id
       return {
           "payload": {
               "revenue": {"value": 125000, "change": 12.5},
               "margin": {"value": 35.2, "change": 2.1},
               "conversion": {"value": 3.8, "change": -0.5},
               "inventory": {"value": 45000, "change": 5.0}
           }
       }
   ```

2. **GET /api/v1/dashboard/insights**
   ```python
   @router.get("/insights")
   async def get_dashboard_insights(
       limit: int = 5,
       db: AsyncSession = Depends(get_db),
       tenant_id: UUID = Depends(get_tenant_id)
   ):
       # Get AI insights from insights table
       # Filter by tenant_id
       return {
           "payload": {
               "insights": [
                   {
                       "id": "...",
                       "type": "opportunity",
                       "title": "...",
                       "summary": "...",
                       "confidence": 0.85,
                       "action": {...}
                   }
               ]
           }
       }
   ```

3. **GET /api/v1/dashboard/alerts**
   ```python
   @router.get("/alerts")
   async def get_dashboard_alerts(
       db: AsyncSession = Depends(get_db),
       tenant_id: UUID = Depends(get_tenant_id)
   ):
       # Get active alerts from alerts table
       # Filter by tenant_id
       return {
           "payload": {
               "alerts": [
                   {
                       "id": "...",
                       "title": "Low Stock Alert",
                       "message": "...",
                       "priority": "critical",
                       "timestamp": "..."
                   }
               ]
           }
       }
   ```

4. **GET /api/v1/dashboard/trends**
   ```python
   @router.get("/trends")
   async def get_dashboard_trends(
       timeRange: str = "30d",
       db: AsyncSession = Depends(get_db),
       tenant_id: UUID = Depends(get_tenant_id)
   ):
       # Get historical sales trends
       # Filter by tenant_id
       return {
           "payload": {
               "data": [
                   {"date": "2024-01-26", "revenue": 4200, "orders": 45},
                   {"date": "2024-01-27", "revenue": 4500, "orders": 48}
               ]
           }
       }
   ```

### Priority 2: HIGH (Pricing Page Won't Work)

5. **GET /api/v1/pricing/recommendations/{product_id}**
6. **GET /api/v1/pricing/history/{product_id}**
7. **GET /api/v1/pricing/promotions/{product_id}**

### Priority 3: HIGH (Sentiment Page Won't Work)

8. **GET /api/v1/sentiment/reviews/{product_id}**
9. **GET /api/v1/sentiment/themes/{product_id}**
10. **GET /api/v1/sentiment/complaints/{product_id}**

### Priority 4: HIGH (Forecast Page Won't Work)

11. **GET /api/v1/forecast/alerts**
12. **GET /api/v1/forecast/accuracy/{product_id}**
13. **GET /api/v1/forecast/gap/{product_id}**

### Priority 5: MEDIUM (Intelligence Page Won't Work)

14. **GET /api/v1/query/{query_id}**
15. **GET /api/v1/query/history**
16. **GET /api/v1/query/{query_id}/status**

---

## 🔧 QUICK FIX OPTIONS

### Option 1: Create Missing Endpoints (RECOMMENDED)
- Create all missing endpoints in backend
- Follow existing patterns in `dashboard.py`, `sentiment.py`, etc.
- Ensure all queries filter by `tenant_id`
- Return data in `{ payload: { data } }` format

### Option 2: Update Frontend to Use Existing Endpoints
- Update `dashboardService.js` to call `/insights/generate` instead of `/dashboard/insights`
- Map existing endpoints to frontend expectations
- Less work but inconsistent API structure

### Option 3: Create Endpoint Aliases
- Create simple wrapper endpoints that call existing logic
- Example: `/dashboard/insights` → calls `/insights/generate` internally
- Quick fix but adds complexity

---

## 📋 ENDPOINT CREATION CHECKLIST

For each missing endpoint, ensure:

- [ ] Endpoint path matches frontend expectations
- [ ] Uses `tenant_id` from JWT token (via `Depends(get_tenant_id)`)
- [ ] All database queries filter by `tenant_id`
- [ ] Returns data in `{ payload: { data } }` format
- [ ] Includes proper error handling
- [ ] Has response model defined
- [ ] Documented with docstring
- [ ] Added to router
- [ ] Tested with actual data

---

## 🧪 TESTING COMMANDS

Test each endpoint in browser console:

```javascript
// Test dashboard insights
fetch('/api/v1/dashboard/insights', {
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('token')}`,
    'X-Tenant-ID': localStorage.getItem('tenantId')
  }
})
.then(r => r.json())
.then(data => console.log('Insights:', data))

// Test dashboard KPIs
fetch('/api/v1/dashboard/kpis', {
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('token')}`,
    'X-Tenant-ID': localStorage.getItem('tenantId')
  }
})
.then(r => r.json())
.then(data => console.log('KPIs:', data))

// Test dashboard alerts
fetch('/api/v1/dashboard/alerts', {
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('token')}`,
    'X-Tenant-ID': localStorage.getItem('tenantId')
  }
})
.then(r => r.json())
.then(data => console.log('Alerts:', data))
```

---

## 📊 SUMMARY

### Endpoints Status:
- ✅ **Existing:** 25 endpoints
- ❌ **Missing:** 20+ endpoints
- ⚠️ **Partial:** 2 endpoints (different paths)

### Critical Missing Endpoints:
1. Dashboard KPIs
2. Dashboard Insights
3. Dashboard Alerts
4. Dashboard Trends
5. Pricing Recommendations
6. Sentiment Reviews/Themes/Complaints
7. Forecast Alerts/Accuracy/Gap
8. Query History/Status

### Recommendation:
**Create the 4 Priority 1 dashboard endpoints FIRST** to get the dashboard working, then add others as needed.

---

## 🚀 NEXT STEPS

1. **Immediate:** Create Priority 1 endpoints (dashboard KPIs, insights, alerts, trends)
2. **Short-term:** Create Priority 2-3 endpoints (pricing, sentiment)
3. **Medium-term:** Create Priority 4-5 endpoints (forecast, query)
4. **Test:** Verify each endpoint returns correct data structure
5. **Deploy:** Push to Vercel and test in production

---

**Status:** Verification Complete  
**Critical Blockers:** 4 dashboard endpoints missing  
**Estimated Time to Fix:** 2-4 hours for Priority 1 endpoints
