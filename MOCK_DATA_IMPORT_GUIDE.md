# Mock Data Import Guide

**Date:** February 25, 2026  
**Status:** ✅ ALL ENDPOINTS TESTED - READY TO IMPORT

---

## 🎯 OVERVIEW

All 7 mock API endpoints have been tested and verified. The import script is ready to load data from the mock API (port 3001) into the real PostgreSQL database.

---

## ✅ TESTED ENDPOINTS (7/7)

| # | Endpoint | Status | Data Available |
|---|----------|--------|----------------|
| 1 | `GET /` | ✅ Working | API info, 4 tenants |
| 2 | `GET /orders/v0/orders` | ✅ Working | 25 orders per tenant |
| 3 | `GET /api/v1/dashboard/stats` | ✅ Working | Complete dashboard metrics |
| 4 | `GET /orders/v0/orders/:id/orderItems` | ✅ Working | 3 items per order |
| 5 | `GET /fba/inventory/v1/summaries` | ✅ Working | 20 products per tenant |
| 6 | `GET /api/v1/pricing/analysis` | ✅ Working | AI pricing recommendations |
| 7 | `GET /api/v1/forecast/alerts` | ✅ Working | 14 stockout alerts |

---

## 📊 DATA SUMMARY

### Per Tenant (4 tenants total):
- **Orders:** 25 orders
- **Order Items:** ~75 items (3 per order)
- **Products:** 20 products
- **Inventory Records:** 20 inventory summaries
- **Pricing Data:** 1 pricing analysis
- **Forecast Alerts:** 14 stockout alerts

### Total Data to Import:
- **Tenants:** 4
- **Users:** 4 (1 per tenant)
- **Products:** 80 (20 × 4 tenants)
- **Orders:** 100 (25 × 4 tenants)
- **Order Items:** ~300 (75 × 4 tenants)
- **Sales Records:** ~300 (1 per order item)

---

## 🚀 HOW TO IMPORT

### Step 1: Ensure Prerequisites

1. **Mock API is running:**
   ```bash
   # Check if mock API is accessible
   curl http://localhost:3001/
   ```

2. **Backend database is running:**
   ```bash
   # PostgreSQL should be running
   # Check connection in .env file
   ```

3. **Backend dependencies installed:**
   ```bash
   pip install -r requirements.txt
   ```

### Step 2: Run Import Script

```bash
python scripts/import_mock_data.py
```

### Step 3: Verify Import

The script will output:
- ✓ Tenant creation status
- ✓ User creation status
- ✓ Products imported count
- ✓ Sales records imported count
- ✓ Any errors encountered

---

## 📋 WHAT GETS IMPORTED

### 1. Tenants (4 tenants)
```
- tenant-001: TechGear Pro (Electronics)
- tenant-002: HomeStyle Living (Home & Kitchen)
- tenant-003: FitLife Sports (Sports & Outdoors)
- tenant-004: BookWorm Treasures (Books)
```

### 2. Users (1 per tenant)
```
- seller@tenant-001.com (TechGear Pro Seller)
- seller@tenant-002.com (HomeStyle Living Seller)
- seller@tenant-003.com (FitLife Sports Seller)
- seller@tenant-004.com (BookWorm Treasures Seller)
```

### 3. Products (from inventory endpoint)
- ASIN, SKU, FN-SKU mapping
- Stock quantities (fulfillable, inbound, reserved)
- Product names and categories
- Default pricing ($29.99 per product)

### 4. Orders (from orders endpoint)
- Amazon Order IDs
- Order statuses (Unshipped, Shipped, etc.)
- Purchase dates (last 30 days)
- Marketplaces (US, Canada)
- Fulfillment channels (AFN, MFN)

### 5. Sales Records (from order items)
- Product-order relationships
- Quantities and prices
- Item-level details
- Tax and shipping breakdown

---

## 🔄 IMPORT PROCESS FLOW

```
1. Connect to Mock API (port 3001)
   ↓
2. For each tenant (4 tenants):
   ↓
   a. Create/verify tenant in database
   ↓
   b. Create/verify user for tenant
   ↓
   c. Fetch inventory data → Create products
   ↓
   d. Fetch orders data → Get order list
   ↓
   e. For each order:
      - Fetch order items
      - Match items to products (by ASIN)
      - Create sales records
   ↓
3. Commit all changes to database
   ↓
4. Display import summary
```

---

## 🎯 AFTER IMPORT

### 1. Start Backend Server
```bash
python -m uvicorn src.main:app --reload --port 8000
```

### 2. Login with Test Accounts

Use any of these credentials:
- **Email:** `seller@tenant-001.com` (or tenant-002, tenant-003, tenant-004)
- **Password:** Any password (authentication will be updated later)

### 3. Verify Data in Dashboard

After login, you should see:
- **Dashboard:** GMV, margin, conversion, inventory health
- **Products:** 20 products with inventory levels
- **Orders:** Recent orders and sales history
- **Pricing:** Pricing recommendations (if endpoint implemented)
- **Forecast:** Stockout alerts (if endpoint implemented)

---

## 🔍 TROUBLESHOOTING

### Mock API Not Accessible
```bash
# Error: Cannot connect to http://localhost:3001
# Solution: Start the mock API server
npm run dev  # or whatever command starts the mock API
```

### Database Connection Error
```bash
# Error: Could not connect to database
# Solution: Check .env file and PostgreSQL status
cat .env  # Verify DATABASE_URL
pg_isready  # Check if PostgreSQL is running
```

### Import Script Errors
```bash
# Error: Module not found
# Solution: Install dependencies
pip install -r requirements.txt

# Error: Table does not exist
# Solution: Run database migrations
alembic upgrade head
```

### Duplicate Data
```bash
# The script checks for existing data before importing
# It will skip tenants, users, and products that already exist
# Sales records are checked by order_id to avoid duplicates
```

---

## 📝 IMPORT SCRIPT FEATURES

### Smart Duplicate Detection
- Checks if tenant exists before creating
- Checks if user exists before creating
- Checks if product exists (by ASIN + tenant_id)
- Checks if sales record exists (by order_id + tenant_id)

### Error Handling
- Continues on individual item errors
- Rolls back on critical errors
- Displays clear error messages
- Doesn't stop entire import on single failure

### Progress Reporting
- Shows which tenant is being processed
- Displays counts of imported items
- Reports success/failure for each step
- Provides final summary

---

## 🎉 EXPECTED RESULTS

After successful import:

```
============================================================
✅ IMPORT COMPLETE
============================================================

Imported Data:
- 4 tenants created
- 4 users created
- 80 products imported
- 300 sales records imported

You can now:
1. Start the backend: python -m uvicorn src.main:app --reload --port 8000
2. Login with any tenant email:
   - seller@tenant-001.com (password: any)
   - seller@tenant-002.com (password: any)
   - seller@tenant-003.com (password: any)
   - seller@tenant-004.com (password: any)
3. View data in the dashboard
============================================================
```

---

## 🔗 RELATED DOCUMENTS

- `MOCK_API_ENDPOINTS_ANALYSIS.md` - Complete endpoint testing results
- `scripts/import_mock_data.py` - Import script source code
- `COMPLETE_DATA_SCHEMA_ANALYSIS.md` - Database schema documentation
- `LOGIN_FLOW_AND_API_CALLS.md` - Authentication flow details

---

**Status:** Ready to import  
**Next Step:** Run `python scripts/import_mock_data.py`
