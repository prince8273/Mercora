# E-commerce Intelligence Agent - User Guide

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Features Overview](#features-overview)
4. [Using the Dashboard](#using-the-dashboard)
5. [Uploading Data](#uploading-data)
6. [Running Queries](#running-queries)
7. [Understanding Results](#understanding-results)
8. [Metrics & Monitoring](#metrics--monitoring)
9. [Troubleshooting](#troubleshooting)
10. [Best Practices](#best-practices)

---

## Introduction

The E-commerce Intelligence Agent is an AI-powered system that helps e-commerce businesses make data-driven decisions by analyzing products, reviews, sales data, and market trends. The system uses advanced LLM technology (Google Gemini) to provide actionable insights.

### Key Capabilities

- **Pricing Intelligence**: Analyze competitive pricing and get dynamic pricing recommendations
- **Sentiment Analysis**: Understand customer feedback and identify improvement opportunities
- **Demand Forecasting**: Predict future demand and optimize inventory levels
- **Natural Language Queries**: Ask questions in plain English and get comprehensive answers

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- SQLite (included) or PostgreSQL (for production)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ecommerce-intelligence-agent
   ```

2. **Install backend dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install frontend dependencies**
   ```bash
   cd frontend
   npm install
   cd ..
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize the database**
   ```bash
   python quick_populate_db.py
   ```

### Starting the Application

1. **Start the backend**
   ```bash
   python -m uvicorn src.main:app --reload
   ```
   Backend will run on http://localhost:8000

2. **Start the frontend** (in a new terminal)
   ```bash
   cd frontend
   npm run dev
   ```
   Frontend will run on http://localhost:5173

3. **Access the application**
   - Open your browser to http://localhost:5173
   - Login with demo credentials: `demo@example.com` / `demo123`

---

## Features Overview

### 1. Dashboard

The dashboard provides an at-a-glance view of your e-commerce metrics:

- **Total Queries**: Number of intelligence queries processed
- **Average Confidence**: Quality of AI analysis results
- **Active Products**: Products currently in inventory
- **Total Reviews**: Customer feedback collected
- **Recent Insights**: AI-generated business insights

### 2. Data Upload

Upload your e-commerce data in CSV format:

- **Products**: SKU, name, category, price, inventory
- **Reviews**: Customer ratings and feedback
- **Sales**: Transaction history and revenue data

### 3. Query Interface

Ask natural language questions about your business:

- "What are my best-selling products?"
- "Which products have negative sentiment?"
- "What's my pricing compared to competitors?"
- "Forecast demand for next 30 days"

### 4. Metrics Dashboard

Monitor system performance in real-time:

- Request metrics (throughput, latency, errors)
- Query execution statistics
- Agent performance
- LLM token usage
- Cache effectiveness

---

## Using the Dashboard

### Accessing the Dashboard

1. Login to the application
2. Click "Dashboard" in the navigation menu
3. View your key metrics and insights

### Understanding Dashboard Metrics

**Total Queries**
- Shows how many intelligence queries have been processed
- Trend indicator shows growth over time

**Average Confidence**
- Measures the quality of AI analysis (0-100%)
- Higher scores indicate more reliable insights
- Scores above 70% are considered good

**Active Products**
- Products with inventory > 0
- Click to see total products count

**Total Reviews**
- All customer reviews in the system
- Used for sentiment analysis

**Recent Insights**
- AI-generated business recommendations
- Color-coded by priority:
  - 🔴 Warning: Requires immediate attention
  - 🟡 Info: Informational insights
  - 🟢 Success: Positive trends

---

## Uploading Data

### Preparing Your Data

#### Products CSV Format

```csv
sku,name,category,price,currency,marketplace,inventory_level
PROD-001,Wireless Mouse,Electronics,29.99,USD,amazon,150
PROD-002,USB-C Cable,Electronics,12.99,USD,amazon,300
```

**Required Fields:**
- `sku`: Unique product identifier
- `name`: Product name
- `category`: Product category
- `price`: Selling price (decimal)
- `currency`: Currency code (USD, EUR, etc.)
- `marketplace`: Sales channel (amazon, ebay, etc.)
- `inventory_level`: Current stock quantity (integer)

#### Reviews CSV Format

```csv
product_sku,rating,review_text,reviewer_name,review_date
PROD-001,5,Great product!,John Doe,2026-02-15
PROD-001,4,Good quality,Jane Smith,2026-02-16
```

**Required Fields:**
- `product_sku`: SKU of the product being reviewed
- `rating`: Star rating (1-5)
- `review_text`: Review content
- `reviewer_name`: Customer name (optional)
- `review_date`: Date of review (YYYY-MM-DD)

#### Sales CSV Format

```csv
product_id,quantity,revenue,date,marketplace
<uuid>,2,59.98,2026-01-15,amazon
<uuid>,1,12.99,2026-01-16,amazon
```

**Required Fields:**
- `product_id`: UUID of the product (from products table)
- `quantity`: Units sold
- `revenue`: Total revenue
- `date`: Sale date (YYYY-MM-DD)
- `marketplace`: Sales channel

### Uploading via UI

1. Navigate to "Upload Data" page
2. Select data type (Products, Reviews, or Sales)
3. Choose your CSV file
4. Click "Upload & Analyze"
5. Wait for processing (usually 10-30 seconds)
6. View analysis results

### Uploading via API

```python
import requests

# Upload products
with open('products.csv', 'rb') as f:
    files = {'file': ('products.csv', f, 'text/csv')}
    response = requests.post(
        'http://localhost:8000/api/v1/csv/upload/products',
        files=files
    )
    print(response.json())
```

---

## Running Queries

### Query Interface

1. Navigate to "Query" page
2. Enter your question in natural language
3. Select execution mode:
   - **Quick Mode**: Fast analysis (< 2 minutes)
   - **Deep Mode**: Comprehensive analysis (< 10 minutes)
4. Click "Run Query"
5. View results

### Example Queries

**Pricing Analysis**
- "What are my most expensive products?"
- "Compare my prices to competitors"
- "Which products should I discount?"

**Sentiment Analysis**
- "What do customers think about Product X?"
- "Which products have the most negative reviews?"
- "What are the common complaints?"

**Demand Forecasting**
- "Forecast demand for next 30 days"
- "Which products will run out of stock?"
- "What's the seasonal trend for Category X?"

**General Business Intelligence**
- "What are my best-selling products?"
- "Which categories generate most revenue?"
- "What's my inventory turnover rate?"

### Query Tips

✅ **Do:**
- Be specific about what you want to know
- Mention specific products, categories, or time periods
- Ask one question at a time
- Use business terminology

❌ **Don't:**
- Ask multiple unrelated questions in one query
- Use ambiguous terms
- Expect real-time data (data is refreshed periodically)

---

## Understanding Results

### Structured Report Format

Every query returns a structured report with:

1. **Executive Summary**
   - High-level overview of findings
   - Key takeaways
   - Recommended actions

2. **Key Metrics**
   - Quantitative measurements
   - Trends and changes
   - Comparisons

3. **Insights**
   - Detailed analysis
   - Supporting evidence
   - Data sources

4. **Action Items**
   - Prioritized recommendations
   - Expected impact
   - Implementation steps

5. **Confidence Score**
   - Quality indicator (0-100%)
   - Data completeness
   - Model certainty

### Interpreting Confidence Scores

- **90-100%**: Very high confidence - act on recommendations
- **70-89%**: High confidence - recommendations are reliable
- **50-69%**: Moderate confidence - verify before acting
- **Below 50%**: Low confidence - gather more data

### Data Quality Warnings

Reports may include warnings about:
- Missing data fields
- Insufficient historical data
- Data quality issues
- Outdated information

**Action:** Address data quality issues to improve analysis accuracy.

---

## Metrics & Monitoring

### Accessing Metrics Dashboard

1. Navigate to "Metrics" page
2. View real-time system metrics
3. Metrics auto-refresh every 5 seconds

### Key Metrics to Monitor

**Request Metrics**
- Total requests processed
- Success vs. error rate
- Average response time

**Query Execution**
- Total queries run
- Quick vs. Deep mode usage
- Average execution time

**Intelligence Agents**
- Pricing agent executions
- Sentiment agent executions
- Forecast agent executions

**LLM Usage**
- Total tokens consumed
- API request count
- Average LLM response time

**Cache Performance**
- Cache hit rate (higher is better)
- Cache misses
- Cache effectiveness

### Performance Benchmarks

**Good Performance:**
- Request success rate > 95%
- Average response time < 2s
- Cache hit rate > 60%
- Error rate < 5%

**Needs Attention:**
- Request success rate < 90%
- Average response time > 5s
- Cache hit rate < 40%
- Error rate > 10%

---

## Troubleshooting

### Common Issues

#### 1. Upload Fails

**Symptoms:** CSV upload returns error

**Solutions:**
- Verify CSV format matches template
- Check for missing required fields
- Ensure data types are correct (numbers, dates)
- Remove special characters from text fields
- Check file size (< 10MB recommended)

#### 2. Query Returns Low Confidence

**Symptoms:** Confidence score < 50%

**Solutions:**
- Upload more historical data
- Ensure data completeness
- Check for data quality issues
- Try more specific queries
- Use Deep Mode for complex questions

#### 3. Slow Query Performance

**Symptoms:** Queries take > 5 minutes

**Solutions:**
- Use Quick Mode for faster results
- Reduce query complexity
- Check system metrics for bottlenecks
- Clear cache if stale
- Restart backend service

#### 4. Authentication Issues

**Symptoms:** Cannot login

**Solutions:**
- Verify credentials
- Check if demo mode is enabled
- Clear browser cache
- Check backend logs
- Restart backend service

#### 5. Dashboard Shows No Data

**Symptoms:** Dashboard metrics are zero

**Solutions:**
- Upload data via CSV upload
- Run `python quick_populate_db.py` for demo data
- Check database connection
- Verify data was saved successfully

### Getting Help

**Check Logs:**
```bash
# Backend logs
tail -f logs/app.log

# Frontend console
Open browser DevTools > Console
```

**API Documentation:**
- Visit http://localhost:8000/docs for interactive API docs

**Support:**
- Check GitHub issues
- Contact system administrator
- Review error messages in logs

---

## Best Practices

### Data Management

1. **Regular Updates**
   - Upload new data daily or weekly
   - Keep product information current
   - Update inventory levels regularly

2. **Data Quality**
   - Validate data before upload
   - Remove duplicates
   - Fix missing values
   - Standardize formats

3. **Historical Data**
   - Maintain at least 6 months of history
   - More data = better forecasts
   - Archive old data periodically

### Query Optimization

1. **Start Simple**
   - Begin with Quick Mode
   - Use Deep Mode for complex analysis
   - Break complex questions into parts

2. **Be Specific**
   - Mention specific products/categories
   - Define time periods
   - Clarify what metrics you want

3. **Review Results**
   - Check confidence scores
   - Verify data sources
   - Act on high-confidence insights

### System Maintenance

1. **Monitor Performance**
   - Check metrics dashboard regularly
   - Watch for error rate increases
   - Monitor LLM token usage

2. **Cache Management**
   - Clear cache if data is stale
   - Monitor cache hit rate
   - Adjust cache TTL if needed

3. **Security**
   - Change default passwords
   - Use strong authentication
   - Enable HTTPS in production
   - Regular security updates

### Cost Optimization

1. **LLM Usage**
   - Use Quick Mode when possible
   - Cache frequently asked queries
   - Optimize query complexity
   - Monitor token consumption

2. **Data Storage**
   - Archive old data
   - Clean up unused records
   - Optimize database queries

---

## Appendix

### Keyboard Shortcuts

- `Ctrl/Cmd + K`: Focus search/query input
- `Ctrl/Cmd + /`: Toggle sidebar
- `Esc`: Close modals

### API Endpoints

**Query Execution:**
```
POST /api/v1/query
```

**CSV Upload:**
```
POST /api/v1/csv/upload/products
POST /api/v1/csv/upload/reviews
POST /api/v1/csv/upload/sales
```

**Dashboard:**
```
GET /api/v1/dashboard/stats
```

**Metrics:**
```
GET /api/v1/metrics
```

### Configuration

**Environment Variables:**
- `LLM_PROVIDER`: LLM provider (gemini, openai)
- `GEMINI_API_KEY`: Google Gemini API key
- `DEMO_MODE`: Enable demo mode (true/false)
- `CACHE_ENABLED`: Enable caching (true/false)
- `DATABASE_URL`: Database connection string

### Support Resources

- **Documentation**: `/docs` folder
- **API Docs**: http://localhost:8000/docs
- **GitHub**: <repository-url>
- **Issues**: <repository-url>/issues

---

**Version:** 1.0.0  
**Last Updated:** February 21, 2026  
**License:** MIT
