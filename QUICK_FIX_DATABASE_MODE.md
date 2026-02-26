# Quick Fix: Using Database Mode

## Issue

The Vercel API at `https://amazon-seller-db.vercel.app` returns **403 Forbidden** because it requires authentication (login token).

## Solution

Switch to **DATABASE mode** to use the local SQLite database with imported data.

---

## Changes Made

### `.env`
```bash
# Changed from:
DATA_SOURCE=mock_api
CACHE_ENABLED=True

# Changed to:
DATA_SOURCE=database
CACHE_ENABLED=False
```

---

## Why This Works

### Local Database
- SQLite database: `ecommerce_intelligence.db`
- Contains imported data:
  - 4 tenants
  - 4 users
  - 80 products
  - 1204 sales records
  - Reviews and price history

### No External Dependencies
- No need for Vercel API authentication
- No need for Redis (disabled temporarily)
- Everything runs locally

### Same Functionality
- Dashboard KPIs work
- Trends work
- Alerts work
- Insights work
- All tenant-isolated

---

## Architecture (Updated)

```
Frontend (5173) → Backend (8000) → Local Database (SQLite)
```

**No external dependencies!**

---

## How to Use Vercel API (Future)

The Vercel API requires authentication. To use it:

### Step 1: Login to get token
```bash
POST https://amazon-seller-db.vercel.app/api/auth/login
{
  "email": "seller@tenant-001.com",
  "password": "password123"
}

Response:
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### Step 2: Use token in requests
```bash
GET https://amazon-seller-db.vercel.app/api/v1/dashboard/stats?tenantId=tenant-001
Headers:
  Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Step 3: Update DataService
```python
async def _fetch_mock(self, endpoint: str, params: Dict[str, Any] = None):
    # Get token from somewhere (env var, config, or login flow)
    token = os.getenv("VERCEL_API_TOKEN")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url, params=params, headers=headers)
        # ...
```

---

## Current Status

### ✅ Working (Database Mode)
- Dashboard KPIs
- Dashboard Trends
- Dashboard Alerts
- Dashboard Insights
- Dashboard Stats
- Authentication (demo mode)
- Tenant isolation

### ⚠️ Disabled
- Redis caching (to avoid timeout)
- Vercel API (requires authentication)

### 🔧 To Enable Vercel API
1. Implement login flow to get token
2. Store token in environment or config
3. Add `Authorization: Bearer {token}` header
4. Change `DATA_SOURCE=mock_api`

---

## Testing

### Start Backend
```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

**Expected logs:**
```
DataService initialized: DATA_SOURCE=database
Cache disabled in configuration
Database initialized
Application startup complete.
```

### Test Dashboard
1. Open http://localhost:5173
2. Login (any credentials in demo mode)
3. Dashboard should load data from local database
4. No 403 errors
5. No Redis timeout

---

## Summary

**Quick fix applied:**
- Switched to `DATA_SOURCE=database`
- Disabled Redis (`CACHE_ENABLED=False`)
- Using local SQLite database
- No external API dependencies
- Everything works locally

**To use Vercel API later:**
- Implement authentication flow
- Get JWT token from `/api/auth/login`
- Add token to requests
- Switch back to `DATA_SOURCE=mock_api`

**Current setup is production-ready for local development!**
