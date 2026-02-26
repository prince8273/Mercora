# Port Configuration Fix - Mock API Port 8001

## Issue
The backend was trying to connect to Mock API on port 3001, but the Mock API is actually running on port 8001.

## Files Updated

### 1. `.env` ✅
```bash
# Changed from:
MOCK_API_URL=http://localhost:3001

# Changed to:
MOCK_API_URL=http://localhost:8001
```

### 2. `src/config.py` ✅
```python
# Changed from:
mock_api_url: str = "http://localhost:3001"  # Default to port 3001

# Changed to:
mock_api_url: str = "http://localhost:8001"  # Default to port 8001
```

### 3. `src/services/data_service.py` ✅
```python
# Updated docstring:
"""
Fetch data from Mock API on port 8001  # Changed from 3001
Uses X-Internal-Key header for service-to-service authentication
tenant_id is ALWAYS added to params for isolation
"""

# Updated error message:
raise Exception(f"Cannot connect to Mock API at {MOCK_API_URL}. Is it running on port 8001?")
# Changed from: "Is it running on port 3001?"
```

### 4. `FRONTEND_BACKEND_WIRING_ANALYSIS.md` ✅
Updated all references from port 3001 to port 8001 throughout the documentation.

## Correct Architecture

```
Frontend (Port 5173) → Backend (Port 8000) → Mock API (Port 8001)
```

## How to Start Servers

### 1. Start Mock API (Port 8001)
```bash
# Already running
# Verify: curl http://localhost:8001
```

### 2. Start Backend (Port 8000)
```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Start Frontend (Port 5173)
```bash
cd frontend
npm run dev
```

## Expected Behavior

When backend starts, you should see:
```
DataService initialized: DATA_SOURCE=mock_api, MOCK_API_URL=http://localhost:8001
```

When dashboard loads, backend logs should show:
```
Cache MISS: dashboard_kpis:tenant-001
Fetching from Mock API at http://localhost:8001/api/v1/dashboard/stats
Cache SET: dashboard_kpis:tenant-001 (TTL: 300s)
```

Second request within 5 minutes:
```
Cache HIT: dashboard_kpis:tenant-001
Response time: <10ms
```

## Verification Steps

1. Check Mock API is running:
   ```bash
   curl http://localhost:8001
   ```
   Should return: `{"message":"Multi-Tenant Amazon Seller Mock API","version":"2.0.0",...}`

2. Start backend and check logs for:
   - `MOCK_API_URL=http://localhost:8001`
   - No connection errors

3. Open frontend and check dashboard loads data

4. Check backend logs for cache hits/misses

## All Configuration Files Now Consistent ✅

- `.env` → Port 8001
- `src/config.py` → Port 8001 (default)
- `src/services/data_service.py` → Port 8001 (comments and errors)
- `FRONTEND_BACKEND_WIRING_ANALYSIS.md` → Port 8001 (documentation)
