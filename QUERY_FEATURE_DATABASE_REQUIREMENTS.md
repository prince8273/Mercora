# Query Feature - Database Requirements

## Overview

The Intelligence Query feature requires the following database tables to function properly. All tables MUST have `tenant_id` for multi-tenant isolation.

---

## Required Tables

### 1. **users** (Authentication)
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id)
);
```

**Used for**: Authentication and tenant identification

---

### 2. **tenants** (Multi-tenancy)
```sql
CREATE TABLE tenants (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    contact_email VARCHAR(255),
    plan VARCHAR(50) DEFAULT 'free',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Used for**: Tenant isolation and identification

---

### 3. **products** ⭐ CRITICAL
```sql
CREATE TABLE products (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    sku VARCHAR(255) NOT NULL,
    name VARCHAR(500) NOT NULL,
    description TEXT,
    category VARCHAR(255),
    price DECIMAL(10, 2) NOT NULL,
    cost DECIMAL(10, 2),
    inventory_level INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id),
    UNIQUE(tenant_id, sku)
);
```

**Used for**:
- Product identification
- Pricing analysis
- Inventory queries
- Product performance analysis

**Query Examples**:
- "What are my top-selling products?"
- "Show me products with low inventory"
- "Which products are most expensive?"

---

### 4. **sales_records** ⭐ CRITICAL
```sql
CREATE TABLE sales_records (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    product_id UUID NOT NULL,
    date DATE NOT NULL,
    quantity INTEGER NOT NULL,
    revenue DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);
```

**Used for**:
- Sales volume analysis
- Revenue calculations
- Top-selling product identification
- Demand forecasting

**Query Examples**:
- "What are my top-selling products?"
- "Show me sales trends"
- "Which products generate most revenue?"

---

### 5. **reviews** ⭐ CRITICAL
```sql
CREATE TABLE reviews (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    product_id UUID NOT NULL,
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    text TEXT,
    sentiment VARCHAR(50),  -- 'positive', 'negative', 'neutral'
    sentiment_confidence DECIMAL(3, 2),
    is_spam BOOLEAN DEFAULT FALSE,
    source VARCHAR(100),  -- 'amazon', 'website', etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);
```

**Used for**:
- Sentiment analysis
- Customer feedback analysis
- Product rating queries
- Complaint detection

**Query Examples**:
- "Show me products with negative reviews"
- "What are customers saying about my products?"
- "Which products have low ratings?"

---

## Optional Tables (For Enhanced Features)

### 6. **price_history** (Optional - for pricing trends)
```sql
CREATE TABLE price_history (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    product_id UUID NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    effective_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);
```

**Used for**: Historical price analysis and trends

---

### 7. **forecast_results** (Optional - for caching forecasts)
```sql
CREATE TABLE forecast_results (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    product_id UUID NOT NULL,
    forecast_date DATE NOT NULL,
    predicted_quantity INTEGER,
    confidence_interval_lower INTEGER,
    confidence_interval_upper INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);
```

**Used for**: Storing and retrieving demand forecasts

---

## Current Database Status

Based on your imported data, you have:

✅ **tenants** - 4 tenants
✅ **users** - 4 users  
✅ **products** - 80 products
✅ **sales_records** - 1204 sales records
✅ **reviews** - (need to verify count)

---

## Sample Data Requirements

For the query feature to work well, you need:

### Minimum Data:
- ✅ At least 1 tenant
- ✅ At least 1 user per tenant
- ✅ At least 10 products per tenant
- ✅ At least 100 sales records per tenant
- ⚠️ At least 50 reviews per tenant (VERIFY THIS)

### Your Current Data:
```
Tenants: 4
Users: 4
Products: 80 (20 per tenant)
Sales Records: 1204 (301 per tenant)
Reviews: ??? (NEED TO CHECK)
```

---

## How Query Feature Uses These Tables

### Query: "most selling product"

**Step 1**: Query understanding (OpenAI GPT-4)
- Intent: `PRODUCT_PERFORMANCE`
- Agents needed: `pricing`, `sentiment`, `demand_forecast`

**Step 2**: Get relevant products
```sql
SELECT 
    sr.product_id,
    SUM(sr.quantity) as total_quantity
FROM sales_records sr
WHERE sr.tenant_id = '54d459ab-4ae8-480a-9d1c-d53b218a4fb2'
GROUP BY sr.product_id
ORDER BY total_quantity DESC
LIMIT 10;
```

**Step 3**: Get product details
```sql
SELECT * FROM products
WHERE id IN (product_ids)
  AND tenant_id = '54d459ab-4ae8-480a-9d1c-d53b218a4fb2';
```

**Step 4**: Get reviews for sentiment analysis
```sql
SELECT * FROM reviews
WHERE product_id IN (product_ids)
  AND tenant_id = '54d459ab-4ae8-480a-9d1c-d53b218a4fb2';
```

**Step 5**: Synthesize results and return report

---

## Tenant Isolation

Every query MUST filter by `tenant_id`:

```sql
-- ✅ CORRECT
SELECT * FROM products 
WHERE tenant_id = '54d459ab-4ae8-480a-9d1c-d53b218a4fb2';

-- ❌ WRONG - Security vulnerability!
SELECT * FROM products;
```

This ensures:
- Seller A can NEVER see Seller B's data
- Each tenant has isolated data
- Multi-tenancy is enforced at database level

---

## Checking Your Database

Run these queries to verify your data:

```sql
-- Check tenants
SELECT id, name, slug FROM tenants;

-- Check products per tenant
SELECT tenant_id, COUNT(*) as product_count 
FROM products 
GROUP BY tenant_id;

-- Check sales records per tenant
SELECT tenant_id, COUNT(*) as sales_count 
FROM sales_records 
GROUP BY tenant_id;

-- Check reviews per tenant (IMPORTANT!)
SELECT tenant_id, COUNT(*) as review_count 
FROM reviews 
GROUP BY tenant_id;

-- Check if TechGear Pro tenant has data
SELECT 
    (SELECT COUNT(*) FROM products WHERE tenant_id = '54d459ab-4ae8-480a-9d1c-d53b218a4fb2') as products,
    (SELECT COUNT(*) FROM sales_records WHERE tenant_id = '54d459ab-4ae8-480a-9d1c-d53b218a4fb2') as sales,
    (SELECT COUNT(*) FROM reviews WHERE tenant_id = '54d459ab-4ae8-480a-9d1c-d53b218a4fb2') as reviews;
```

---

## Summary

**Required for Query Feature to Work:**

1. ✅ **products** table with tenant_id
2. ✅ **sales_records** table with tenant_id  
3. ⚠️ **reviews** table with tenant_id (VERIFY DATA EXISTS)
4. ✅ **tenants** table
5. ✅ **users** table

**Your Status:**
- Database schema: ✅ Correct
- Product data: ✅ 80 products
- Sales data: ✅ 1204 records
- Review data: ⚠️ NEED TO VERIFY

**If reviews table is empty**, the sentiment analysis will be skipped, but pricing and forecast agents will still work.

**Test Query**: "most selling product" should work if you have products and sales_records data for your tenant.
