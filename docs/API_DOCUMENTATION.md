# E-commerce Intelligence Agent - API Documentation

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

Most endpoints require JWT authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

### Demo Mode

When `DEMO_MODE=True`, authentication is bypassed for testing purposes.

---

## Table of Contents

1. [Authentication](#authentication-endpoints)
2. [Query Execution](#query-execution)
3. [CSV Upload](#csv-upload)
4. [Dashboard](#dashboard)
5. [Products](#products)
6. [Reviews](#reviews)
7. [Pricing](#pricing)
8. [Sentiment](#sentiment)
9. [Forecast](#forecast)
10. [Metrics](#metrics)

---

## Authentication Endpoints

### POST /auth/register

Register a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "full_name": "John Doe"
}
```

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "created_at": "2026-02-21T10:00:00Z"
}
```

### POST /auth/login

Login and receive JWT token.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "full_name": "John Doe"
  }
}
```

### GET /auth/me

Get current user information.

**Headers:**
```
Authorization: Bearer <token>
```

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "tenant_id": "uuid",
  "is_active": true
}
```

---

## Query Execution

### POST /query

Execute an intelligence query.

**Headers:**
```
Authorization: Bearer <token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "query_text": "What are my best-selling products?",
  "execution_mode": "quick",
  "context": {
    "time_period": "last_30_days",
    "category": "Electronics"
  }
}
```

**Parameters:**
- `query_text` (required): Natural language query
- `execution_mode` (optional): "quick" or "deep" (default: "quick")
- `context` (optional): Additional context for the query

**Response:** `200 OK`
```json
{
  "query_id": "uuid",
  "executive_summary": "Your top-selling products are...",
  "key_metrics": {
    "total_revenue": 125000.50,
    "top_product": "Wireless Mouse",
    "units_sold": 1250
  },
  "insights": [
    {
      "title": "Strong Electronics Performance",
      "description": "Electronics category shows 25% growth",
      "confidence": 0.87,
      "supporting_data": ["sales_records", "inventory_data"]
    }
  ],
  "action_items": [
    {
      "priority": "high",
      "title": "Increase inventory for top sellers",
      "description": "Stock levels running low for best-selling items",
      "expected_impact": "Prevent stockouts, increase revenue by 15%"
    }
  ],
  "overall_confidence": 87.5,
  "data_quality_warnings": [],
  "execution_time_ms": 1250,
  "agents_used": ["pricing", "sentiment", "demand_forecast"],
  "created_at": "2026-02-21T10:00:00Z"
}
```

---

## CSV Upload

### POST /csv/upload/products

Upload products CSV file.

**Headers:**
```
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

**Request Body:**
```
file: <products.csv>
```

**CSV Format:**
```csv
sku,name,category,price,currency,marketplace,inventory_level
PROD-001,Wireless Mouse,Electronics,29.99,USD,amazon,150
```

**Response:** `200 OK`
```json
{
  "status": "success",
  "products_uploaded": 150,
  "analysis": {
    "intent": "product_analysis",
    "confidence": 0.92,
    "agents_used": ["pricing"],
    "report": {
      "executive_summary": "Uploaded 150 products across 5 categories...",
      "key_metrics": {
        "total_products": 150,
        "avg_price": 45.99,
        "total_inventory_value": 125000
      }
    }
  },
  "token_usage": {
    "prompt_tokens": 250,
    "response_tokens": 180,
    "total_tokens": 430
  }
}
```

### POST /csv/upload/reviews

Upload reviews CSV file.

**Headers:**
```
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

**Request Body:**
```
file: <reviews.csv>
```

**CSV Format:**
```csv
product_sku,rating,review_text,reviewer_name,review_date
PROD-001,5,Great product!,John Doe,2026-02-15
```

**Response:** `200 OK`
```json
{
  "status": "success",
  "reviews_uploaded": 500,
  "analysis": {
    "intent": "sentiment_analysis",
    "confidence": 0.88,
    "agents_used": ["sentiment"],
    "average_rating": 4.2,
    "report": {
      "executive_summary": "Overall positive sentiment with 4.2/5 average rating...",
      "sentiment_distribution": {
        "positive": 350,
        "neutral": 100,
        "negative": 50
      }
    }
  }
}
```

### POST /csv/upload/sales

Upload sales CSV file.

**Headers:**
```
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

**Request Body:**
```
file: <sales.csv>
```

**CSV Format:**
```csv
product_id,quantity,revenue,date,marketplace
<uuid>,2,59.98,2026-01-15,amazon
```

**Response:** `200 OK`
```json
{
  "status": "success",
  "sales_records_uploaded": 1000,
  "analysis": {
    "intent": "demand_forecast",
    "confidence": 0.85,
    "agents_used": ["demand_forecast"],
    "total_revenue": 125000.50,
    "total_quantity": 2500,
    "report": {
      "executive_summary": "Strong sales performance with $125K revenue...",
      "forecast": {
        "next_30_days": 3000,
        "confidence_interval": [2700, 3300]
      }
    }
  }
}
```

---

## Dashboard

### GET /dashboard/stats

Get dashboard statistics.

**Headers:**
```
Authorization: Bearer <token>
```

**Response:** `200 OK`
```json
{
  "total_queries": 342,
  "avg_confidence": 0.87,
  "active_products": 150,
  "total_products": 200,
  "total_reviews": 500,
  "recent_insights": [
    {
      "title": "Low Inventory Alert",
      "description": "5 products have low inventory levels",
      "type": "warning",
      "timestamp": "2026-02-21T10:00:00Z"
    }
  ]
}
```

### GET /dashboard/recent-activity

Get recent activity feed.

**Headers:**
```
Authorization: Bearer <token>
```

**Query Parameters:**
- `limit` (optional): Number of activities to return (default: 10)

**Response:** `200 OK`
```json
[
  {
    "type": "product_added",
    "title": "New product: Wireless Mouse",
    "description": "SKU: PROD-001",
    "timestamp": "2026-02-21T10:00:00Z"
  },
  {
    "type": "review_added",
    "title": "New review received",
    "description": "Rating: 5/5",
    "timestamp": "2026-02-21T09:55:00Z"
  }
]
```

---

## Products

### GET /products

List all products.

**Headers:**
```
Authorization: Bearer <token>
```

**Query Parameters:**
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Number of records to return (default: 100)
- `category` (optional): Filter by category
- `marketplace` (optional): Filter by marketplace

**Response:** `200 OK`
```json
{
  "total": 200,
  "items": [
    {
      "id": "uuid",
      "sku": "PROD-001",
      "name": "Wireless Mouse",
      "category": "Electronics",
      "price": 29.99,
      "currency": "USD",
      "marketplace": "amazon",
      "inventory_level": 150,
      "created_at": "2026-02-21T10:00:00Z"
    }
  ]
}
```

### GET /products/{product_id}

Get product details.

**Headers:**
```
Authorization: Bearer <token>
```

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "sku": "PROD-001",
  "name": "Wireless Mouse",
  "category": "Electronics",
  "price": 29.99,
  "currency": "USD",
  "marketplace": "amazon",
  "inventory_level": 150,
  "created_at": "2026-02-21T10:00:00Z",
  "updated_at": "2026-02-21T10:00:00Z"
}
```

### POST /products

Create a new product.

**Headers:**
```
Authorization: Bearer <token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "sku": "PROD-001",
  "name": "Wireless Mouse",
  "category": "Electronics",
  "price": 29.99,
  "currency": "USD",
  "marketplace": "amazon",
  "inventory_level": 150
}
```

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "sku": "PROD-001",
  "name": "Wireless Mouse",
  "category": "Electronics",
  "price": 29.99,
  "currency": "USD",
  "marketplace": "amazon",
  "inventory_level": 150,
  "created_at": "2026-02-21T10:00:00Z"
}
```

---

## Pricing

### GET /pricing/analysis

Get pricing analysis for products.

**Headers:**
```
Authorization: Bearer <token>
```

**Query Parameters:**
- `product_ids` (optional): Comma-separated product IDs
- `category` (optional): Filter by category

**Response:** `200 OK`
```json
{
  "analysis": [
    {
      "product_id": "uuid",
      "product_name": "Wireless Mouse",
      "current_price": 29.99,
      "competitor_avg_price": 27.50,
      "price_gap": 2.49,
      "recommendation": "Consider reducing price by 5%",
      "confidence": 0.85,
      "expected_impact": {
        "revenue_change": "+12%",
        "volume_change": "+20%"
      }
    }
  ]
}
```

---

## Sentiment

### GET /sentiment/product/{product_id}

Get sentiment analysis for a product.

**Headers:**
```
Authorization: Bearer <token>
```

**Response:** `200 OK`
```json
{
  "product_id": "uuid",
  "aggregate_sentiment": 0.75,
  "sentiment_distribution": {
    "positive": 350,
    "neutral": 100,
    "negative": 50
  },
  "top_topics": [
    {
      "topic": "Quality",
      "sentiment": 0.85,
      "frequency": 120
    }
  ],
  "feature_requests": [
    {
      "feature": "Wireless charging",
      "frequency": 45,
      "sentiment": 0.70
    }
  ],
  "confidence": 0.88
}
```

---

## Forecast

### GET /forecast/product/{product_id}

Get demand forecast for a product.

**Headers:**
```
Authorization: Bearer <token>
```

**Query Parameters:**
- `horizon_days` (optional): Forecast horizon in days (default: 30)

**Response:** `200 OK`
```json
{
  "product_id": "uuid",
  "forecast_horizon_days": 30,
  "predicted_demand": [45, 48, 52, ...],
  "confidence_intervals": [[40, 50], [43, 53], ...],
  "seasonality_detected": true,
  "inventory_alerts": [
    {
      "type": "stockout_risk",
      "date": "2026-03-15",
      "severity": "high",
      "recommended_action": "Order 200 units"
    }
  ],
  "confidence": 0.82
}
```

---

## Metrics

### GET /metrics

Get Prometheus metrics.

**Response:** `200 OK` (text/plain)
```
# HELP ecommerce_agent_requests_total Total number of requests
# TYPE ecommerce_agent_requests_total counter
ecommerce_agent_requests_total{endpoint="/query",method="POST",status="success"} 342.0

# HELP ecommerce_agent_query_duration_seconds Query execution duration
# TYPE ecommerce_agent_query_duration_seconds histogram
ecommerce_agent_query_duration_seconds_bucket{execution_mode="quick",le="1.0"} 250.0
...
```

---

## Error Responses

### 400 Bad Request

```json
{
  "detail": "Invalid request format",
  "errors": [
    {
      "field": "query_text",
      "message": "Field is required"
    }
  ]
}
```

### 401 Unauthorized

```json
{
  "detail": "Not authenticated"
}
```

### 403 Forbidden

```json
{
  "detail": "Insufficient permissions"
}
```

### 404 Not Found

```json
{
  "detail": "Resource not found"
}
```

### 500 Internal Server Error

```json
{
  "detail": "Internal server error",
  "error_id": "uuid"
}
```

---

## Rate Limiting

- **Default**: 100 requests per minute per user
- **CSV Upload**: 10 uploads per hour per user
- **Query Execution**: 50 queries per hour per user

**Rate Limit Headers:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1645456800
```

---

## Pagination

List endpoints support pagination:

**Query Parameters:**
- `skip`: Number of records to skip (default: 0)
- `limit`: Number of records to return (default: 100, max: 1000)

**Response Headers:**
```
X-Total-Count: 500
X-Page-Size: 100
X-Page-Number: 1
```

---

## Webhooks

Configure webhooks to receive real-time notifications:

### POST /webhooks

Register a webhook endpoint.

**Request Body:**
```json
{
  "url": "https://your-domain.com/webhook",
  "events": ["query.completed", "data.uploaded", "alert.triggered"],
  "secret": "your-webhook-secret"
}
```

### Webhook Payload

```json
{
  "event": "query.completed",
  "timestamp": "2026-02-21T10:00:00Z",
  "data": {
    "query_id": "uuid",
    "status": "success",
    "confidence": 0.87
  },
  "signature": "sha256=..."
}
```

---

## SDK Examples

### Python

```python
import requests

# Login
response = requests.post(
    'http://localhost:8000/api/v1/auth/login',
    json={'email': 'user@example.com', 'password': 'password'}
)
token = response.json()['access_token']

# Execute query
headers = {'Authorization': f'Bearer {token}'}
response = requests.post(
    'http://localhost:8000/api/v1/query',
    headers=headers,
    json={'query_text': 'What are my best-selling products?'}
)
result = response.json()
print(result['executive_summary'])
```

### JavaScript

```javascript
// Login
const loginResponse = await fetch('http://localhost:8000/api/v1/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email: 'user@example.com', password: 'password' })
});
const { access_token } = await loginResponse.json();

// Execute query
const queryResponse = await fetch('http://localhost:8000/api/v1/query', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${access_token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ query_text: 'What are my best-selling products?' })
});
const result = await queryResponse.json();
console.log(result.executive_summary);
```

---

**Version:** 1.0.0  
**Last Updated:** February 21, 2026  
**Interactive Docs:** http://localhost:8000/docs
