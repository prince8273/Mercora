# Amazon Sellers Mock API - Endpoint Analysis

**Date:** February 25, 2026  
**Mock API URL:** `http://localhost:3001`  
**Purpose:** Testing and development mock data for Amazon Seller Platform

---

## 🎯 MOCK API OVERVIEW

The mock API running on port 3001 provides **realistic Amazon Seller data** for 4 test tenants with complete order, inventory, and dashboard data.

### Available Tenants:
1. **tenant-001** - TechGear Pro (Electronics)
2. **tenant-002** - HomeStyle Living (Home & Kitchen)
3. **tenant-003** - FitLife Sports (Sports & Outdoors)
4. **tenant-004** - BookWorm Treasures (Books)

---

## 📡 AVAILABLE ENDPOINTS

### 1. Root Endpoint
**URL:** `GET http://localhost:3001/`

**Response:**
```json
{
  "message": "Multi-Tenant Amazon Seller Mock API",
  "version": "2.0.0",
  "tenants": [
    {
      "id": "tenant-001",
      "name": "TechGear Pro",
      "type": "Electronics"
    },
    {
      "id": "tenant-002",
      "name": "HomeStyle Living",
      "type": "Home & Kitchen"
    },
    {
      "id": "tenant-003",
      "name": "FitLife Sports",
      "type": "Sports & Outdoors"
    },
    {
      "id": "tenant-004",
      "name": "BookWorm Treasures",
      "type": "Books"
    }
  ],
  "endpoints": {
    "amazon_sp_api": {
      "orders": "GET /orders/v0/orders?tenantId=tenant-001",
      "order_items": "GET /orders/v0/orders/:orderId/orderItems?tenantId=tenant-001",
      "inventory": "GET /fba/inventory/v1/summaries?tenantId=tenant-001"
    },
    "normalized_api": {
      "dashboard": "GET /api/v1/dashboard/stats?tenantId=tenant-001",
      "pricing": "GET /api/v1/pricing/analysis?tenantId=tenant-001",
      "forecast": "GET /api/v1/forecast/alerts?tenantId=tenant-001"
    }
  },
  "setup": {
    "seed_database": "npm run seed"
  }
}
```

---

### 2. Amazon SP-API Orders Endpoint
**URL:** `GET http://localhost:3001/orders/v0/orders?tenantId=tenant-001`

**Response Structure:**
```json
{
  "Orders": [
    {
      "AmazonOrderId": "902-YZXJYO8O0",
      "OrderStatus": "Unshipped",
      "PurchaseDate": "2025-12-15T04:55:58.162Z",
      "MarketplaceId": "ATVPDKIKX0DER",
      "LastUpdateDate": "2025-12-15T13:10:22.557Z",
      "OrderTotal": {
        "CurrencyCode": "USD",
        "Amount": 59.22
      },
      "NumberOfItemsShipped": 0,
      "NumberOfItemsUnshipped": 2,
      "PaymentMethod": "Other",
      "ShipmentServiceLevelCategory": "Standard",
      "OrderType": "StandardOrder",
      "EarliestShipDate": "2025-12-16T04:55:58.162Z",
      "LatestShipDate": "2025-12-18T04:55:58.162Z",
      "EarliestDeliveryDate": "2025-12-20T04:55:58.162Z",
      "LatestDeliveryDate": "2025-12-25T04:55:58.162Z",
      "FulfillmentChannel": "AFN",
      "ShipServiceLevel": "Std US D2D Dom",
      "MarketplaceName": "Amazon.com",
      "MarketplaceCountry": "US"
    }
    // ... more orders (25 total)
  ],
  "NextToken": "mock-next-token",
  "CreatedBefore": "2026-02-24T20:19:26.841Z"
}
```

**Data Includes:**
- ✅ 25 orders per tenant
- ✅ Multiple order statuses: Unshipped, Shipped, PartiallyShipped, Pending, Canceled
- ✅ Multiple marketplaces: Amazon.com (US), Amazon.ca (Canada)
- ✅ Multiple fulfillment channels: AFN (Amazon), MFN (Merchant)
- ✅ Realistic order amounts: $44.58 - $350.77
- ✅ Realistic dates: Last 30 days

---

### 3. Dashboard Stats Endpoint
**URL:** `GET http://localhost:3001/api/v1/dashboard/stats?tenantId=tenant-001`

**Response:**
```json
{
  "payload": {
    "gmv": {
      "value": "14811.31",
      "change": "8.7",
      "trend": "up",
      "currency": "USD"
    },
    "margin": {
      "value": 28.5,
      "change": 2.3,
      "trend": "up"
    },
    "conversion": {
      "value": 3.2,
      "change": -0.5,
      "trend": "down"
    },
    "inventory_health": {
      "value": 65,
      "at_risk_products": 7,
      "out_of_stock": 2,
      "low_stock": 5,
      "change": "5.0",
      "trend": "up"
    },
    "total_orders": 100,
    "total_products": 20,
    "average_order_value": "148.11"
  }
}
```

**Metrics Provided:**
- ✅ **GMV (Gross Merchandise Value):** $14,811.31 (+8.7%)
- ✅ **Margin:** 28.5% (+2.3%)
- ✅ **Conversion Rate:** 3.2% (-0.5%)
- ✅ **Inventory Health:** 65 score
  - 7 at-risk products
  - 2 out of stock
  - 5 low stock
- ✅ **Total Orders:** 100
- ✅ **Total Products:** 20
- ✅ **Average Order Value:** $148.11

---

### 4. Order Items Endpoint
**URL:** `GET http://localhost:3001/orders/v0/orders/:orderId/orderItems?tenantId=tenant-001`
**Status:** ✅ WORKING

**Response Structure:**
```json
{
  "payload": {
    "AmazonOrderId": "902-YZXJYO8O0",
    "OrderItems": [
      {
        "OrderItemId": "tizo2i3mow",
        "ASIN": "B0ZVJDXV53",
        "SellerSKU": "TECHGEAR-0007-G48F",
        "Title": "Laptop Stand Aluminum",
        "QuantityOrdered": 3,
        "QuantityShipped": 2,
        "ItemPrice": {
          "CurrencyCode": "CAD",
          "Amount": 13.25
        },
        "ItemTax": {
          "CurrencyCode": "CAD",
          "Amount": 1.06
        },
        "ShippingPrice": {
          "CurrencyCode": "CAD",
          "Amount": 5.99
        },
        "ShippingTax": {
          "CurrencyCode": "CAD",
          "Amount": 0.48
        },
        "PromotionDiscount": {
          "CurrencyCode": "CAD",
          "Amount": 0
        },
        "IsGift": 0,
        "IsTransparency": 0,
        "ProductInfo": {
          "NumberOfItems": 1
        },
        "TaxCollection": {
          "Model": "MarketplaceFacilitator",
          "ResponsibleParty": "Amazon Services, Inc."
        }
      }
    ],
    "NextToken": null
  }
}
```

**Key Data Points:**
- 3 items per order (typical)
- Complete pricing breakdown (item price, tax, shipping, promotions)
- ASIN and SKU mapping
- Quantity ordered vs shipped tracking
- Product titles and details

---

### 5. Inventory Endpoint
**URL:** `GET http://localhost:3001/fba/inventory/v1/summaries?tenantId=tenant-001`
**Status:** ✅ WORKING

**Response Structure:**
```json
{
  "payload": {
    "granularity": {
      "granularityType": "Marketplace",
      "granularityId": "ATVPDKIKX0DER"
    },
    "inventorySummaries": [
      {
        "asin": "B0NMEUDL22",
        "fnSku": "X003E0X5YC",
        "sellerSku": "TECHGEAR-0000-N827",
        "condition": "NewItem",
        "inventoryDetails": {
          "fulfillableQuantity": 33,
          "inboundWorkingQuantity": 8,
          "inboundShippedQuantity": 10,
          "inboundReceivingQuantity": 0,
          "reservedQuantity": 2
        },
        "lastUpdatedTime": "2026-02-23 20:10:22",
        "totalQuantity": 51
      }
    ]
  }
}
```

**Key Data Points:**
- 20 products per tenant
- Complete inventory breakdown:
  - Fulfillable quantity (available to sell)
  - Inbound working (being prepared)
  - Inbound shipped (in transit to Amazon)
  - Inbound receiving (being received)
  - Reserved quantity (held for orders)
- ASIN, FN-SKU, and Seller SKU mapping
- Last updated timestamps

---

### 6. Pricing Analysis Endpoint
**URL:** `GET http://localhost:3001/api/v1/pricing/analysis?tenantId=tenant-001`
**Status:** ✅ WORKING

**Response Structure:**
```json
{
  "payload": {
    "product_id": "B0ZN4I433O",
    "product_name": "Sample Product B0ZN4I433O",
    "current_price": 19.44,
    "suggested_price": 17.52,
    "price_gap": 1.56,
    "price_gap_percentage": "8.0",
    "competitor_prices": [
      {
        "competitor_id": "COMP-1",
        "name": "Competitor A",
        "price": "18.47"
      },
      {
        "competitor_id": "COMP-2",
        "name": "Competitor B",
        "price": "20.41"
      },
      {
        "competitor_id": "COMP-3",
        "name": "Competitor C",
        "price": "17.88"
      }
    ],
    "confidence_score": 0.87,
    "reasoning": "Based on competitor analysis, reducing price by 2% below lowest competitor will maximize revenue while maintaining margin.",
    "expected_impact": {
      "revenue_change": 8.5,
      "margin_change": -1.2,
      "volume_change": 12.3
    },
    "created_at": "2026-02-24T20:38:29.839Z"
  }
}
```

**Key Data Points:**
- Product pricing recommendations with confidence scores (0.87)
- Competitor price comparison (3 competitors)
- Expected business impact (revenue +8.5%, margin -1.2%, volume +12.3%)
- AI reasoning for price suggestions
- Price gap analysis (8.0% difference)

---

### 7. Forecast Alerts Endpoint
**URL:** `GET http://localhost:3001/api/v1/forecast/alerts?tenantId=tenant-001`
**Status:** ✅ WORKING

**Response Structure:**
```json
{
  "payload": {
    "alerts": [
      {
        "alert_type": "stockout_risk",
        "severity": "critical",
        "product_id": "B0MB1TGCPX",
        "product_name": "Sample Product B0MB1TGCPX",
        "sku": "SKU-9QVTT5RP",
        "current_inventory": 3,
        "recommended_action": "Reorder 181 units",
        "days_until_stockout": 0,
        "created_at": "2026-02-24T20:38:56.470Z"
      }
    ],
    "total_alerts": 14,
    "critical_count": 5,
    "high_count": 9
  }
}
```

**Key Data Points:**
- 14 total stockout risk alerts
- 5 critical alerts (0-2 days until stockout)
- 9 high severity alerts (3-6 days until stockout)
- Specific reorder recommendations per product
- Current inventory levels and SKU tracking

---

## 🔄 COMPARISON: Mock API vs Real Backend

| Feature | Mock API (Port 3001) | Real Backend (Port 8000) |
|---------|---------------------|--------------------------|
| **Purpose** | Testing/Development | Production |
| **Data Source** | Hardcoded mock data | PostgreSQL database |
| **Authentication** | None (query param) | JWT token required |
| **Tenant Isolation** | Query parameter | JWT token + middleware |
| **Data Format** | Amazon SP-API format | Normalized format |
| **Endpoints** | Amazon-specific | Application-specific |
| **Database** | None | PostgreSQL |
| **Updates** | Static | Real-time |

---

## 🎯 HOW TO USE MOCK API DATA

### Option 1: Import Mock Data into Real Database (RECOMMENDED)

Create a script to fetch mock data and insert into your database:

```python
# import_mock_data.py
import requests
import asyncio
from src.database import get_db
from src.models.product import Product
from src.models.sales_record import SalesRecord

async def import_mock_data():
    # Fetch mock orders
    response = requests.get('http://localhost:3001/orders/v0/orders?tenantId=tenant-001')
    orders = response.json()['Orders']
    
    # Fetch mock dashboard stats
    response = requests.get('http://localhost:3001/api/v1/dashboard/stats?tenantId=tenant-001')
    stats = response.json()['payload']
    
    # Insert into database
    async for db in get_db():
        # Create products, sales records, etc.
        # ... (implementation)
        pass

if __name__ == "__main__":
    asyncio.run(import_mock_data())
```

### Option 2: Create Proxy Endpoints

Create endpoints in your real backend that fetch from mock API:

```python
# src/api/mock_proxy.py
@router.get("/mock/orders")
async def get_mock_orders(tenant_id: str):
    response = requests.get(f'http://localhost:3001/orders/v0/orders?tenantId={tenant_id}')
    return response.json()
```

### Option 3: Use Mock API Directly for Testing

Update frontend to call mock API during development:

```javascript
// frontend/.env.development
VITE_API_URL=http://localhost:3001
```

---

## 📊 MOCK DATA STATISTICS

### Per Tenant:
- **Orders:** 25 orders
- **Products:** ~20 products
- **Order Value Range:** $44.58 - $350.77
- **Total GMV:** ~$14,811.31
- **Order Statuses:**
  - Unshipped: ~40%
  - Shipped: ~25%
  - PartiallyShipped: ~20%
  - Pending: ~10%
  - Canceled: ~5%

### Marketplaces:
- Amazon.com (US): ~60%
- Amazon.ca (Canada): ~40%

### Fulfillment:
- MFN (Merchant Fulfilled): ~55%
- AFN (Amazon Fulfilled): ~45%

---

## ✅ VERIFIED ENDPOINTS

| Endpoint | Status | Data Quality |
|----------|--------|--------------|
| `GET /` | ✅ Working | Excellent |
| `GET /orders/v0/orders` | ✅ Working | Excellent - 25 orders |
| `GET /api/v1/dashboard/stats` | ✅ Working | Excellent - Complete metrics |
| `GET /orders/v0/orders/:id/orderItems` | ✅ Working | Excellent - 3 items per order |
| `GET /fba/inventory/v1/summaries` | ✅ Working | Excellent - 20 products |
| `GET /api/v1/pricing/analysis` | ✅ Working | Excellent - AI pricing with confidence |
| `GET /api/v1/forecast/alerts` | ✅ Working | Excellent - 14 stockout alerts |

---

## 🚀 RECOMMENDATION

### For Development:

**DO NOT use mock API directly with frontend.** Instead:

1. **Import mock data into real database:**
   ```bash
   python import_mock_data.py
   ```

2. **Use real backend (port 8000) with imported data:**
   - Frontend calls: `http://localhost:8000/api/v1/...`
   - Backend serves data from database
   - Proper authentication and tenant isolation

3. **Keep mock API running for reference:**
   - Use it to verify data structures
   - Use it to test data import scripts
   - Use it as a fallback during development

### Why Not Use Mock API Directly:

❌ No authentication (security risk)  
❌ Different endpoint structure (incompatible with frontend)  
❌ No database persistence (data lost on restart)  
❌ No tenant isolation middleware  
❌ Amazon-specific format (not normalized)

---

## 💡 NEXT STEPS

1. **Test remaining endpoints:**
   ```bash
   curl "http://localhost:3001/orders/v0/orders/902-YZXJYO8O0/orderItems?tenantId=tenant-001"
   curl "http://localhost:3001/fba/inventory/v1/summaries?tenantId=tenant-001"
   curl "http://localhost:3001/api/v1/pricing/analysis?tenantId=tenant-001"
   curl "http://localhost:3001/api/v1/forecast/alerts?tenantId=tenant-001"
   ```

2. **Create data import script** to load mock data into real database

3. **Use real backend (port 8000)** with imported data

4. **Keep mock API as reference** for data structures

---

**Status:** Mock API Analysis Complete  
**Recommendation:** Import mock data into real database, use real backend  
**Mock API Purpose:** Testing and reference only, not for production use
