# Vercel API Integration

## Overview

The backend now connects to the deployed Amazon Seller Database API on Vercel instead of localhost.

**API URL**: `https://amazon-seller-db.vercel.app`

---

## Configuration Changes

### 1. `.env`
```bash
# OLD
MOCK_API_URL=http://localhost:8001

# NEW
MOCK_API_URL=https://amazon-seller-db.vercel.app
```

### 2. `src/config.py`
```python
# OLD
mock_api_url: str = "http://localhost:8001"

# NEW
mock_api_url: str = "https://amazon-seller-db.vercel.app"
```

---

## API Endpoints Mapping

### Vercel API Endpoints (from response)

```json
{
  "message": "Amazon Seller Intelligence API",
  "version": "1.0.0",
  "endpoints": {
    "auth_login": "/api/auth/login",
    "auth_me": "/api/auth/me",
    "seller_dashboard": "/api/seller/dashboard",
    "dashboard_kpis": "/api/v1/dashboard/kpis",
    "dashboard_trends": "/api/v1/dashboard/trends",
    "dashboard_alerts": "/api/v1/dashboard/alerts",
    "dashboard_insights": "/api/v1/dashboard/insights",
    "dashboard_stats": "/api/v1/dashboard/stats",
    "pricing_recommendations": "/api/v1/pricing/recommendations",
    "sentiment_analysis": "/api/v1/sentiment/product/{product_id}",
    "forecast": "/api/v1/forecast/product/{product_id}",
    "sync_amazon": "/api/v1/sync/amazon",
    "sync_status": "/api/v1/sync/status",
    "query_execute": "/api/v1/query/execute",
    "query_history": "/api/v1/query/history"
  }
}
```

### Our Backend → Vercel API Mapping

| Our Backend Endpoint | Vercel API Endpoint | Status |
|---------------------|---------------------|--------|
| `/api/v1/dashboard/kpis` | `/api/v1/dashboard/kpis` | ✅ Mapped |
| `/api/v1/dashboard/trends` | `/api/v1/dashboard/trends` | ✅ Mapped |
| `/api/v1/dashboard/alerts` | `/api/v1/dashboard/alerts` | ✅ Mapped |
| `/api/v1/dashboard/insights` | `/api/v1/dashboard/insights` | ✅ Mapped |
| `/api/v1/dashboard/stats` | `/api/v1/dashboard/stats` | ✅ Mapped |
| `/api/v1/dashboard/recent-activity` | ❌ Not available | ⚠️ Needs fallback |
| `/api/v1/pricing/*` | `/api/v1/pricing/recommendations` | ⚠️ Partial |
| `/api/v1/sentiment/*` | `/api/v1/sentiment/product/{id}` | ⚠️ Partial |
| `/api/v1/forecast/*` | `/api/v1/forecast/product/{id}` | ⚠️ Partial |
| `/api/v1/query` | `/api/v1/query/execute` | ⚠️ Different path |

---

## DataService Updates

### Dashboard Endpoints (✅ Working)

```python
# KPIs
await self._fetch_mock("/api/v1/dashboard/kpis", {"tenantId": self.tenant_id})

# Trends
await self._fetch_mock("/api/v1/dashboard/trends", {"tenantId": self.tenant_id, "days": days})

# Alerts
await self._fetch_mock("/api/v1/dashboard/alerts", {"tenantId": self.tenant_id})

# Insights
await self._fetch_mock("/api/v1/dashboard/insights", {"tenantId": self.tenant_id})

# Stats
await self._fetch_mock("/api/v1/dashboard/stats", {"tenantId": self.tenant_id})
```

### Recent Activity (⚠️ Needs Implementation)

The Vercel API doesn't have a `/recent-activity` endpoint. Options:
1. Use database fallback for recent activity
2. Derive from other endpoints
3. Return empty array

**Current Implementation**: Falls back to database

---

## Authentication

### Vercel API Auth Endpoints

```
POST /api/auth/login
GET /api/auth/me
```

Our backend uses its own authentication (JWT tokens), so we don't use Vercel's auth endpoints. We only use the data endpoints.

---

## Tenant Mapping

### Our Tenants → Vercel Tenant IDs

| Our Tenant Name | Our Tenant ID | Vercel Tenant ID |
|----------------|---------------|------------------|
| TechGear Pro | `54d459ab-4ae8-480a-9d1c-d53b218a4fb2` | `tenant-001` |
| HomeStyle Living | (UUID) | `tenant-002` |
| FitLife Sports | (UUID) | `tenant-003` |
| BookWorm Treasures | (UUID) | `tenant-004` |

**Note**: We need to map our UUIDs to Vercel's tenant IDs when making requests.

---

## Request Format

### Our Backend → Vercel API

```javascript
// Request
GET https://amazon-seller-db.vercel.app/api/v1/dashboard/kpis?tenantId=tenant-001

// Headers
{
  "X-Internal-Key": "super-secret-internal-key-change-in-production"
}

// Response
{
  "payload": {
    "gmv": { "value": 4249, "change": 12.5, "trend": "up" },
    "margin": { "value": 23.4, "change": 2.1, "trend": "up" },
    "conversion": { "value": 3.2, "change": -0.5, "trend": "down" },
    "inventory_health": { "value": 87, "change": 5, "trend": "up" }
  }
}
```

---

## Architecture Update

### OLD Architecture
```
Frontend (5173) → Backend (8000) → Mock API (localhost:8001)
```

### NEW Architecture
```
Frontend (5173) → Backend (8000) → Vercel API (https://amazon-seller-db.vercel.app)
                       ↓
                  Redis Cache (WSL: 172.27.52.219:6379)
```

---

## Benefits of Vercel API

1. **No Local Mock API Required**: Don't need to run Mock API on port 8001
2. **Always Available**: Deployed and accessible from anywhere
3. **Production-Like**: Tests against a real deployed API
4. **Multi-Tenant**: Supports multiple tenants (tenant-001 to tenant-004)
5. **Consistent Data**: Same data across all environments

---

## Testing

### Test Vercel API Directly

```bash
# Test root endpoint
curl https://amazon-seller-db.vercel.app/

# Test dashboard KPIs
curl "https://amazon-seller-db.vercel.app/api/v1/dashboard/kpis?tenantId=tenant-001"

# Test dashboard stats
curl "https://amazon-seller-db.vercel.app/api/v1/dashboard/stats?tenantId=tenant-001"
```

### Test Through Backend

```bash
# Start backend
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

# Test dashboard endpoint
curl http://localhost:8000/api/v1/dashboard/kpis
```

---

## Tenant ID Mapping (TODO)

We need to add a mapping function to convert our UUIDs to Vercel tenant IDs:

```python
# src/services/data_service.py

TENANT_ID_MAPPING = {
    "54d459ab-4ae8-480a-9d1c-d53b218a4fb2": "tenant-001",  # TechGear Pro
    # Add other mappings as needed
}

def map_tenant_id(our_tenant_id: str) -> str:
    """Map our UUID tenant ID to Vercel tenant ID"""
    return TENANT_ID_MAPPING.get(our_tenant_id, "tenant-001")  # Default to tenant-001
```

Then use it in `_fetch_mock`:

```python
async def _fetch_mock(self, endpoint: str, params: Dict[str, Any] = None):
    if params is None:
        params = {}
    
    # Map tenant ID
    if "tenantId" in params:
        params["tenantId"] = map_tenant_id(params["tenantId"])
    
    # Continue with request...
```

---

## Next Steps

1. ✅ Update `.env` to use Vercel API URL
2. ✅ Update `src/config.py` default
3. ✅ Update `src/services/data_service.py` endpoints
4. ⚠️ Add tenant ID mapping
5. ⚠️ Handle missing endpoints (recent-activity)
6. ⚠️ Update query endpoint path (`/execute` vs `/`)
7. ✅ Test dashboard endpoints
8. ⚠️ Test pricing, sentiment, forecast endpoints

---

## Summary

The backend now connects to the deployed Vercel API instead of localhost. This provides:
- No need to run local Mock API
- Production-like testing environment
- Consistent multi-tenant data
- Always-available API

The main endpoints (dashboard) are working. Additional endpoints (pricing, sentiment, forecast, query) may need path adjustments to match Vercel's API structure.
