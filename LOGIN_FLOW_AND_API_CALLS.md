# Login Flow and API Calls

**Date:** February 25, 2026  
**Purpose:** Document the complete login flow and all API calls made to fetch seller data

---

## 🔐 COMPLETE LOGIN FLOW

### Step-by-Step Process:

```
User enters email + password
         ↓
1. POST /api/v1/auth/login
         ↓
   Backend validates credentials
         ↓
   Returns JWT token with tenant_id
         ↓
2. GET /api/v1/auth/me
         ↓
   Backend returns user profile
         ↓
   Frontend stores user data
         ↓
3. Navigate to Dashboard
         ↓
   Multiple API calls to fetch seller data
```

---

## 📡 API CALLS DURING LOGIN

### 1️⃣ LOGIN API CALL

**Endpoint:** `POST /api/v1/auth/login`

**Request:**
```javascript
{
  email: "seller@example.com",
  password: "password123"
}
```

**Response:**
```javascript
{
  payload: {  // With your backend's wrapper
    access_token: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    token_type: "bearer",
    expires_in: 43200  // 12 hours in seconds
  }
}
```

**JWT Token Contains:**
```javascript
{
  sub: "user-uuid-123",           // user_id
  tenant_id: "tenant-uuid-456",   // CRITICAL: Used to filter all data
  role: "admin",                  // or "superuser"
  exp: 1708876800                 // expiration timestamp
}
```

**What Frontend Does:**
```javascript
// Store token
localStorage.setItem('token', access_token)
localStorage.setItem('tokenType', token_type)
```

---

### 2️⃣ GET USER PROFILE

**Endpoint:** `GET /api/v1/auth/me`

**Headers:**
```javascript
{
  'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
  'X-Tenant-ID': 'tenant-uuid-456'  // Extracted from token
}
```

**Response:**
```javascript
{
  payload: {  // With your backend's wrapper
    id: "user-uuid-123",
    email: "seller@example.com",
    full_name: "John Seller",
    tenant_id: "tenant-uuid-456",
    is_active: true,
    is_superuser: false,
    created_at: "2024-01-15T10:30:00Z",
    last_login: "2024-02-25T08:45:00Z"
  }
}
```

**What Frontend Does:**
```javascript
// Store user data
localStorage.setItem('user', JSON.stringify(userData))
localStorage.setItem('tenantId', userData.tenant_id)

// Set auth state
setUser(userData)
setIsAuthenticated(true)

// Navigate to dashboard
navigate('/dashboard')
```

---

## 📊 API CALLS AFTER LOGIN (Dashboard Load)

Once logged in and navigated to dashboard, frontend makes these API calls:

### 3️⃣ DASHBOARD OVERVIEW

**Endpoint:** `GET /api/v1/dashboard/stats`

**Headers:**
```javascript
{
  'Authorization': 'Bearer {token}',
  'X-Tenant-ID': '{tenant_id}'
}
```

**Backend Query:**
```sql
-- All queries filter by tenant_id from JWT token
SELECT * FROM products WHERE tenant_id = 'tenant-uuid-456';
SELECT * FROM sales_records WHERE tenant_id = 'tenant-uuid-456';
SELECT * FROM reviews WHERE tenant_id = 'tenant-uuid-456';
```

**Response:**
```javascript
{
  payload: {
    total_queries: 342,
    avg_confidence: 0.87,
    active_products: 45,
    total_products: 50,
    total_reviews: 230,
    recent_insights: [
      {
        title: "Low Inventory Alert",
        description: "5 products have low inventory levels",
        type: "warning",
        timestamp: "2024-02-25T10:30:00Z"
      }
    ]
  }
}
```

---

### 4️⃣ DASHBOARD KPIs

**Endpoint:** `GET /api/v1/dashboard/kpis`

**Backend Query:**
```sql
-- Revenue
SELECT SUM(revenue) as total_revenue 
FROM sales_records 
WHERE tenant_id = 'tenant-uuid-456' 
  AND date >= DATE_SUB(NOW(), INTERVAL 30 DAY);

-- Margin
SELECT 
  SUM(revenue - (quantity * cost)) / SUM(revenue) * 100 as margin
FROM sales_records sr
JOIN products p ON sr.product_id = p.id
WHERE sr.tenant_id = 'tenant-uuid-456';

-- Inventory Value
SELECT SUM(inventory_level * price) as inventory_value
FROM products
WHERE tenant_id = 'tenant-uuid-456';
```

**Response:**
```javascript
{
  payload: {
    revenue: {
      value: 125000.00,
      change: 12.5,
      timeframe: "30 days"
    },
    margin: {
      value: 35.2,
      change: 2.1
    },
    conversion: {
      value: 3.8,
      change: -0.5
    },
    inventory: {
      value: 45000.00,
      change: 5.0
    }
  }
}
```

---

### 5️⃣ DASHBOARD INSIGHTS

**Endpoint:** `GET /api/v1/dashboard/insights`

**Backend Query:**
```sql
SELECT * FROM insights 
WHERE tenant_id = 'tenant-uuid-456' 
ORDER BY created_at DESC 
LIMIT 5;
```

**Response:**
```javascript
{
  payload: {
    insights: [
      {
        id: "insight-001",
        type: "opportunity",
        title: "Revenue Opportunity",
        summary: "Increase price on Wireless Mouse",
        details: "Competitors pricing 15% higher, demand is strong",
        confidence: 0.85,  // For ConfidenceScore component
        action: {          // For ActionRecommendation component
          id: "action-001",
          title: "Increase price to $29.99",
          priority: "high",
          effort: "low",
          impact: "high",
          description: "Update price to match market",
          reasoning: "Competitors pricing 15% higher",
          confidence: 0.85
        }
      }
    ]
  }
}
```

---

### 6️⃣ DASHBOARD ALERTS

**Endpoint:** `GET /api/v1/dashboard/alerts`

**Backend Query:**
```sql
SELECT * FROM alerts 
WHERE tenant_id = 'tenant-uuid-456' 
  AND is_dismissed = FALSE 
ORDER BY priority DESC, timestamp DESC 
LIMIT 10;
```

**Response:**
```javascript
{
  payload: {
    alerts: [
      {
        id: "alert-001",
        title: "Low Stock Alert",
        message: "Product XYZ has only 5 units left",
        priority: "critical",
        details: "Current inventory will run out in 3 days",
        timestamp: "2024-02-25T10:30:00Z"
      }
    ]
  }
}
```

---

### 7️⃣ DASHBOARD TRENDS

**Endpoint:** `GET /api/v1/dashboard/trends?timeRange=30d`

**Backend Query:**
```sql
SELECT 
  date,
  SUM(revenue) as revenue,
  COUNT(DISTINCT product_id) as orders
FROM sales_records
WHERE tenant_id = 'tenant-uuid-456'
  AND date >= DATE_SUB(NOW(), INTERVAL 30 DAY)
GROUP BY date
ORDER BY date ASC;
```

**Response:**
```javascript
{
  payload: {
    data: [
      { date: "2024-01-26", revenue: 4200, orders: 45 },
      { date: "2024-01-27", revenue: 4500, orders: 48 },
      { date: "2024-01-28", revenue: 3800, orders: 42 },
      // ... 30 days of data
    ]
  }
}
```

---

## 🗄️ DATABASE TABLES QUERIED

### During Login:
1. **users** - Validate email/password, get user profile
2. **tenants** - Get tenant info (if needed)

### After Login (Dashboard):
3. **products** - Get product count, inventory levels
4. **sales_records** - Calculate revenue, orders, trends
5. **reviews** - Get review count, sentiment data
6. **price_history** - Get price trends
7. **alerts** - Get active alerts
8. **insights** - Get AI-generated insights
9. **pricing_recommendations** - Get pricing suggestions
10. **inventory_alerts** - Get inventory warnings

---

## 🔑 CRITICAL: tenant_id FILTERING

**Every single query MUST filter by tenant_id:**

```sql
-- ✅ CORRECT
SELECT * FROM products WHERE tenant_id = 'tenant-uuid-456';

-- ❌ WRONG - Will return ALL sellers' data!
SELECT * FROM products;
```

**How tenant_id is obtained:**

1. **Login:** User provides email + password
2. **Backend:** Finds user in `users` table, gets their `tenant_id`
3. **JWT Token:** Includes `tenant_id` in payload
4. **All API Calls:** Extract `tenant_id` from JWT token
5. **All Queries:** Filter by `WHERE tenant_id = {extracted_tenant_id}`

---

## 📋 COMPLETE API CALL SEQUENCE

```
1. User Login
   ↓
   POST /api/v1/auth/login
   → Returns: JWT token with tenant_id
   
2. Get User Profile
   ↓
   GET /api/v1/auth/me
   → Returns: User data with tenant_id
   
3. Navigate to Dashboard
   ↓
   GET /api/v1/dashboard/stats
   → Returns: Basic stats (products, reviews count)
   ↓
   GET /api/v1/dashboard/kpis
   → Returns: Revenue, margin, conversion metrics
   ↓
   GET /api/v1/dashboard/insights
   → Returns: AI-generated insights
   ↓
   GET /api/v1/dashboard/alerts
   → Returns: Active alerts
   ↓
   GET /api/v1/dashboard/trends?timeRange=30d
   → Returns: Historical trend data
   
4. User Navigates to Other Pages
   ↓
   GET /api/v1/pricing/recommendations
   → Returns: Pricing suggestions
   ↓
   GET /api/v1/sentiment/product/{id}
   → Returns: Sentiment analysis
   ↓
   GET /api/v1/forecast/product/{id}
   → Returns: Demand forecasts
```

---

## 🔒 SECURITY & DATA ISOLATION

### How Data Isolation Works:

1. **JWT Token Contains tenant_id:**
   ```javascript
   {
     sub: "user-uuid-123",
     tenant_id: "tenant-uuid-456",  // ← This is the key!
     role: "admin"
   }
   ```

2. **Backend Middleware Extracts tenant_id:**
   ```python
   # From JWT token
   tenant_id = token_payload.get("tenant_id")
   ```

3. **All Queries Filter by tenant_id:**
   ```python
   # Example: Get products
   products = await db.execute(
       select(Product).where(Product.tenant_id == tenant_id)
   )
   ```

4. **Seller Can ONLY See Their Own Data:**
   - Seller A (tenant_id: "aaa") sees ONLY their products
   - Seller B (tenant_id: "bbb") sees ONLY their products
   - No cross-tenant data leakage

---

## 🎯 WHAT FRONTEND NEEDS FROM BACKEND

### Minimum Required Endpoints:

**Authentication:**
- ✅ `POST /api/v1/auth/login` - Already exists
- ✅ `GET /api/v1/auth/me` - Already exists

**Dashboard:**
- ✅ `GET /api/v1/dashboard/stats` - Already exists
- ⚠️ `GET /api/v1/dashboard/kpis` - May need to create
- ⚠️ `GET /api/v1/dashboard/insights` - Already exists (tested)
- ⚠️ `GET /api/v1/dashboard/alerts` - May need to create
- ⚠️ `GET /api/v1/dashboard/trends` - May need to create

**Pricing:**
- ⚠️ `GET /api/v1/pricing/recommendations` - May need to create
- ⚠️ `GET /api/v1/pricing/analysis` - May need to create
- ⚠️ `GET /api/v1/pricing/history/{id}` - May need to create

**Sentiment:**
- ⚠️ `GET /api/v1/sentiment/product/{id}` - May need to create
- ⚠️ `GET /api/v1/sentiment/themes/{id}` - May need to create

**Forecast:**
- ⚠️ `GET /api/v1/forecast/product/{id}` - May need to create
- ⚠️ `GET /api/v1/forecast/alerts` - May need to create

---

## 💡 KEY TAKEAWAYS

1. **Login Flow:**
   - POST /api/v1/auth/login → Get JWT token
   - GET /api/v1/auth/me → Get user profile
   - Navigate to dashboard → Multiple API calls

2. **Data Filtering:**
   - Every query MUST filter by `tenant_id`
   - `tenant_id` comes from JWT token
   - Ensures data isolation between sellers

3. **API Response Format:**
   - Backend wraps responses in `{ payload: { data } }`
   - Frontend automatically unwraps via `apiClient.js`
   - All endpoints work consistently

4. **Dashboard Data:**
   - Comes from multiple tables: products, sales_records, reviews, alerts, insights
   - All filtered by seller's `tenant_id`
   - Real-time updates every 2-5 minutes

5. **Security:**
   - JWT token carries `tenant_id`
   - Backend validates token on every request
   - No seller can access another seller's data

---

## 🚀 NEXT STEPS

1. **Verify Endpoints Exist:**
   - Test each endpoint in browser console
   - Check if they return data in correct format

2. **Check Data Structure:**
   - Verify `insights` include `confidence` and `action` fields
   - Verify `alerts` include `priority` and `timestamp` fields

3. **Test Data Isolation:**
   - Login as different sellers
   - Verify each sees only their own data

4. **Monitor API Calls:**
   - Open Network tab in DevTools
   - Watch API calls during login and dashboard load
   - Verify all return 200 status

---

**Status:** Documentation Complete  
**Ready for:** Testing and verification  
**Critical:** All queries MUST filter by `tenant_id` for data isolation
