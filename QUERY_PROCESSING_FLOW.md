# Complete Query Processing Flow: From Input to Output

## Overview
Your intelligence query system processes natural language queries through a sophisticated multi-stage pipeline. Here's the COMPLETE flow from when a user submits a query to when they see the final result.

---

## 🔄 COMPLETE FLOW DIAGRAM

```
User Query Input
    ↓
[1] API Endpoint (src/api/query.py)
    ↓
[2] Query Router (Pattern Matching)
    ↓
[3] LLM Reasoning Engine (Intent Understanding)
    ↓
[4] Execution Plan Generation
    ↓
[5] Execution Service (Agent Orchestration)
    ↓
[6] Individual Agents (Pricing/Sentiment/Forecast)
    ↓
[7] Result Synthesizer (Aggregation)
    ↓
[8] Executive Summary Generation
    ↓
Final StructuredReport → User
```

---

## 📋 DETAILED STEP-BY-STEP BREAKDOWN

### **STEP 1: API Entry Point**
**File:** `src/api/query.py` → `execute_query()`

**What happens:**
- User submits query via POST `/query`
- Request contains:
  - `query_text`: "best rated product by customers"
  - `analysis_type`: "quick" or "deep" (optional)
  - `product_ids`: [] (optional)
- Authentication & tenant isolation applied
- Logging starts: `[ORCHESTRATION] Processing query: best rated product...`

**Output:** Validated QueryRequest object

---

### **STEP 2: Query Router (Deterministic Pattern Matching)**
**File:** `src/orchestration/query_router.py` → `QueryRouter.route_query()`

**What happens:**
1. **Pattern Matching**: Checks query against predefined patterns
   ```python
   patterns = [
       "customer.*review", "sentiment.*analysis", "what.*customer.*think"
   ]
   ```
   
2. **Execution Mode Determination**:
   - **Quick Mode**: Single agent, 2-min SLA, uses cache
   - **Deep Mode**: Multi-agent, 10-min SLA, comprehensive

3. **Cache Key Generation**: Creates hash for potential cache lookup

**For your query "best rated product by customers":**
- Matches: `sentiment_analysis` pattern (keywords: "rated", "customers")
- Mode: QUICK (single agent)
- Agents: [SENTIMENT]
- Cache: Enabled

**Output:** `RoutingDecision` object
```python
{
    "execution_mode": ExecutionMode.QUICK,
    "required_agents": [AgentType.SENTIMENT],
    "use_cache": True,
    "cache_key": "abc123...",
    "estimated_duration": timedelta(seconds=45)
}
```

---

### **STEP 3: LLM Reasoning Engine (Smart Intent Understanding)**
**File:** `src/orchestration/llm_reasoning_engine.py` → `LLMReasoningEngine.understand_query()`

**What happens:**
1. **LLM Call** (if configured):
   - Sends query to OpenAI/Gemini
   - System prompt: "You are an intelligent query analyzer..."
   - Extracts intent and parameters

2. **Fallback** (if LLM unavailable):
   - Keyword-based scoring:
     ```python
     sentiment_keywords = {'review': 3, 'rating': 3, 'customer': 2, 'best': 1}
     sentiment_score = 9  # High score!
     ```
   - Determines intent from highest score

**For your query:**
- Intent: `SENTIMENT_ANALYSIS`
- Parameters: `{'keywords': ['rated', 'customers', 'best']}`
- Confidence: 0.95

**Agent Selection:**
- Maps intent → agents
- `SENTIMENT_ANALYSIS` → `[AgentType.SENTIMENT]`

**Output:** `(QueryIntent.SENTIMENT_ANALYSIS, parameters_dict)`

---

### **STEP 4: Execution Plan Generation**
**File:** `src/orchestration/llm_reasoning_engine.py` → `generate_execution_plan()`

**What happens:**
1. Creates `AgentTask` objects for each agent:
   ```python
   AgentTask(
       agent_type=AgentType.SENTIMENT,
       parameters={'keywords': ['rated', 'customers']},
       dependencies=[],
       timeout_seconds=120  # Quick mode
   )
   ```

2. Determines parallelization:
   - Single agent → Sequential
   - Multiple agents with no dependencies → Parallel

3. Estimates duration:
   - Sentiment agent: ~20 seconds base
   - Quick mode: Cap at 120 seconds

**Output:** `ExecutionPlan` object
```python
{
    "tasks": [AgentTask(SENTIMENT)],
    "execution_mode": ExecutionMode.QUICK,
    "parallel_groups": [[AgentType.SENTIMENT]],
    "estimated_duration": timedelta(seconds=20)
}
```

---

### **STEP 5: Execution Service (Agent Orchestration)**
**File:** `src/orchestration/execution_service.py` → `ExecutionService.execute_plan()`

**What happens:**
1. **Product Resolution**:
   - No product_ids provided → Calls `_get_relevant_products_for_query()`
   - Looks for keywords: "best rated", "top rated", "highest rated"
   - Queries database for products with high ratings
   - Returns top 10-20 product IDs

2. **Agent Execution**:
   - Calls `_execute_single_agent()` with timeout
   - Routes to `_execute_sentiment_agent()`

3. **Timeout & Error Handling**:
   - Wraps in `asyncio.wait_for(timeout=120)`
   - On timeout: Returns fallback strategy
   - On error: Logs and returns error result

**Output:** `List[AgentResult]`

---

### **STEP 6: Sentiment Agent Execution**
**File:** `src/orchestration/execution_service.py` → `_execute_sentiment_agent()`

**What happens:**
1. **Data Fetching**:
   ```python
   # Fetch reviews for products
   SELECT * FROM reviews 
   WHERE product_id IN (product_ids) 
   AND tenant_id = tenant_id
   ```

2. **Agent Initialization**:
   ```python
   sentiment_agent = EnhancedSentimentAgent(tenant_id)
   qa_agent = DataQAAgent(tenant_id)
   ```

3. **Data Quality Assessment**:
   ```python
   qa_report = qa_agent.assess_review_data_quality(reviews)
   # Checks: completeness, validity, freshness, spam detection
   ```

4. **Sentiment Calculation**:
   ```python
   sentiment_result = sentiment_agent.calculate_aggregate_sentiment_with_qa(
       reviews, qa_report
   )
   ```
   - Calculates per-product sentiment scores
   - Groups reviews by product
   - Computes: average_sentiment, positive_percentage, review_count

5. **Product Ranking**:
   ```python
   product_sentiments.sort(key=lambda x: x['average_sentiment'], reverse=True)
   ```
   - Sorts products by sentiment (highest first)
   - **THIS IS WHERE "BEST RATED" IS DETERMINED!**

**Output:** `AgentResult` with data:
```python
{
    'agent': 'sentiment',
    'status': 'completed',
    'confidence': 0.85,
    'data': {
        'review_count': 150,
        'aggregate_sentiment_score': 0.78,
        'product_sentiments': [
            {
                'product_id': 'uuid-1',
                'sku': 'PROD-001',
                'product_name': 'Premium Widget',
                'average_sentiment': 0.92,  # HIGHEST!
                'review_count': 45,
                'positive_percentage': 91.1
            },
            {
                'product_id': 'uuid-2',
                'sku': 'PROD-002',
                'product_name': 'Standard Widget',
                'average_sentiment': 0.75,
                'review_count': 30,
                'positive_percentage': 73.3
            },
            // ... more products sorted by sentiment
        ]
    }
}
```

---

### **STEP 7: Result Synthesizer (Aggregation & Insight Extraction)**
**File:** `src/orchestration/result_synthesizer.py` → `ResultSynthesizer.synthesize_results()`

**What happens:**
1. **Extract Insights** (`_extract_insights()`):
   ```python
   # For sentiment agent:
   - Finds products with >60% positive sentiment
   - Creates insight: "Products with Most Positive Reviews"
   - Stores product details in supporting_evidence
   ```

2. **Extract Metrics** (`_extract_metrics()`):
   ```python
   MetricWithTrend(
       name="Customer Sentiment Score",
       value=0.78,
       unit="score",
       trend=TrendDirection.STABLE,
       confidence=0.85
   )
   ```

3. **Identify Risks** (`_identify_risks()`):
   ```python
   # If sentiment < 0.4:
   RiskAssessment(
       title="Customer Satisfaction Risk",
       severity=SeverityLevel.HIGH,
       impact="Customer churn"
   )
   ```

4. **Generate Action Items** (`_generate_action_items()`):
   ```python
   ActionItem(
       title="Address negative feedback",
       description="Found 15 negative reviews",
       priority="high",
       impact="high",
       urgency="high"
   )
   ```

5. **Prioritize Actions** (`_prioritize_action_items()`):
   ```python
   # Priority score = (impact * 2) + urgency + priority
   # Sorts by score (descending)
   ```

6. **Calculate Overall Confidence** (`_calculate_overall_confidence()`):
   ```python
   # Weighted average of agent confidences
   overall_confidence = 0.85  # From sentiment agent
   ```

**Output:** Structured data ready for summary

---

### **STEP 8: Executive Summary Generation**
**File:** `src/orchestration/result_synthesizer.py` → `_generate_executive_summary()`

**What happens:**

**Mode 1: Rule-Based (Default)**
```python
def _generate_rule_based_summary():
    summary = []
    summary.append(f"Analysis for: {query}")
    summary.append(f"Overall Confidence: {0.85:.1%}")  # 85.0%
    
    # Key findings
    summary.append("Key Findings (2):")
    summary.append("- Products with Most Positive Reviews: Found 5 products with highly positive reviews")
    summary.append("- Overall Customer Sentiment: Positive (score: 0.78)")
    
    # Top actions
    summary.append("Recommended Actions (1):")
    summary.append("- [HIGH] Address negative feedback")
    
    return "\n".join(summary)
```

**Mode 2: LLM-Enhanced** (if enabled)
```python
def _generate_llm_summary():
    # Formats results for LLM
    results_text = """
    Insights:
    - Products with Most Positive Reviews: Found 5 products...
    
    Metrics:
    - Customer Sentiment Score: 0.78 (trend: stable)
    
    Actions:
    - [HIGH] Address negative feedback
    """
    
    # Calls LLM
    summary = llm_engine.generate_summary(
        content=results_text,
        system_prompt="You are a business intelligence analyst..."
    )
    
    return summary  # Natural language summary
```

**For your query, the summary would be:**
```
Analysis for: best rated product by customers

Overall Confidence: 0.9%

Analysis for best rated product by customers Overall Confidence: 0.9

Key Findings (1):
- Products with Most Positive Reviews: Found 5 products with highly positive reviews (>60% sentiment score)

Recommended Actions (0):
```

**Output:** Executive summary string

---

### **STEP 9: Final Report Assembly**
**File:** `src/orchestration/result_synthesizer.py` → `synthesize_results()`

**What happens:**
Creates final `StructuredReport`:
```python
StructuredReport(
    report_id="uuid-report-123",
    tenant_id=tenant_id,
    query="best rated product by customers",
    timestamp=datetime.utcnow(),
    executive_summary="Analysis for: best rated product...",
    insights=[
        Insight(
            title="Products with Most Positive Reviews",
            description="Found 5 products with highly positive reviews",
            category="sentiment",
            confidence=0.85,
            supporting_evidence=[
                SupportingEvidence(
                    source_data_type="sentiment_analysis",
                    transformation_applied=json.dumps({
                        "sku": "PROD-001",
                        "name": "Premium Widget",
                        "average_sentiment": 0.92,
                        "review_count": 45,
                        "positive_percentage": 91.1,
                        "badge": "91% positive",
                        "badge_variant": "success"
                    })
                ),
                // ... more products
            ]
        )
    ],
    key_metrics=[
        MetricWithTrend(
            name="Customer Sentiment Score",
            value=0.78,
            unit="score",
            trend=TrendDirection.STABLE
        )
    ],
    risks=[],
    action_items=[],
    data_quality_warnings=[],
    overall_confidence=85.0,  # 0-100 scale
    agent_results={
        'execution_mode': 'quick',
        'agents_used': ['sentiment'],
        'execution_time': 18.5
    }
)
```

---

## 🎯 KEY ANSWER TO YOUR QUESTION

### "How are you evaluating the query?"

**The evaluation happens in 3 stages:**

1. **Pattern Matching** (Query Router):
   - Keyword matching against predefined patterns
   - "best rated" + "customers" → SENTIMENT pattern
   - Fast, deterministic, no LLM needed

2. **Intent Understanding** (LLM Reasoning Engine):
   - LLM analyzes query semantics (if available)
   - Fallback: Keyword scoring system
   - Determines which agents to use

3. **Product Resolution** (Execution Service):
   - Translates query intent to database queries
   - "best rated" → `ORDER BY average_rating DESC`
   - Fetches relevant products from database

### "How are you synthesizing the result?"

**The synthesis happens in 4 stages:**

1. **Data Aggregation**:
   - Collects results from all agents
   - Sentiment agent returns product_sentiments sorted by score

2. **Insight Extraction**:
   - Identifies patterns in agent results
   - "Top 5 products with >60% positive sentiment"
   - Stores detailed product data in supporting_evidence

3. **Summary Generation**:
   - Rule-based: Template-driven text generation
   - LLM-enhanced: Natural language generation
   - Combines insights, metrics, risks, actions

4. **Report Assembly**:
   - Packages everything into StructuredReport
   - Includes confidence scores, metadata, lineage
   - Returns to user via API

---

## 🔍 WHAT'S ACTUALLY HAPPENING IN YOUR SCREENSHOT

Looking at your screenshot showing "Overall Confidence: 0.9%":

**The Issue:**
The executive summary is showing `0.9%` instead of `90%` or `0.9` (as a decimal).

**Root Cause:**
In `_generate_rule_based_summary()`:
```python
summary_parts.append(f"\nOverall Confidence: {overall_confidence:.1%}\n")
```

The `overall_confidence` is already on a 0-1 scale (0.9), and the `:.1%` format multiplies by 100 and adds `%`, resulting in `90.0%`.

BUT, if the value passed is already multiplied by 100 (90.0), then `:.1%` would show `9000.0%`.

**The actual bug is likely here:**
```python
overall_confidence=overall_confidence * 100,  # Convert to 0-100 scale
```

This converts 0.9 → 90.0, but then the summary formatter uses `:.1%` which expects 0-1 scale.

**Fix:** Either:
1. Don't multiply by 100 in the report
2. Don't use `%` formatter in the summary

---

## 📊 CONFIDENCE CALCULATION DETAILS

**How confidence is calculated:**

1. **Agent Level**:
   ```python
   # Sentiment agent
   base_confidence = 0.8
   qa_score = 0.95  # Data quality
   anomaly_penalty = 1.0  # No anomalies
   
   final_confidence = base_confidence * qa_score * anomaly_penalty
   # = 0.8 * 0.95 * 1.0 = 0.76
   ```

2. **Overall Level**:
   ```python
   # Weighted average of all agents
   total_confidence = sum(agent.confidence * weight for agent in agents)
   total_weight = sum(weight for agent in agents)
   
   overall_confidence = total_confidence / total_weight
   # For single agent: 0.76 / 1.0 = 0.76
   ```

3. **Display**:
   ```python
   # In StructuredReport
   overall_confidence=overall_confidence * 100  # 76.0
   
   # In summary
   f"{overall_confidence:.1%}"  # Should be 76.0%
   ```

---

## 🚨 POTENTIAL ISSUES IN YOUR SYSTEM

Based on the screenshot showing "Overall Confidence: 0.9%":

1. **Confidence Scale Mismatch**:
   - Report stores as 0-100 scale (90.0)
   - Summary expects 0-1 scale (0.9)
   - Result: Incorrect display

2. **Missing Product Details**:
   - Executive summary is generic
   - Doesn't show WHICH product is "best rated"
   - Product details are in `supporting_evidence` but not surfaced

3. **No Product Ranking in Summary**:
   - The actual answer ("Premium Widget is best rated") is buried in the data
   - Summary should explicitly state: "Best rated product: Premium Widget (91% positive, 45 reviews)"

---

## 💡 RECOMMENDATIONS

1. **Fix Confidence Display**:
   ```python
   # In _generate_rule_based_summary
   summary_parts.append(f"\nOverall Confidence: {overall_confidence:.1f}%\n")
   # OR
   summary_parts.append(f"\nOverall Confidence: {overall_confidence/100:.1%}\n")
   ```

2. **Enhance Summary for "Which Product" Queries**:
   ```python
   # Detect "which" or "best" queries
   if "which" in query.lower() or "best" in query.lower():
       # Extract top product from insights
       top_product = product_sentiments[0]
       summary_parts.insert(1, 
           f"\n**Answer: {top_product['product_name']} "
           f"({top_product['positive_percentage']:.0f}% positive, "
           f"{top_product['review_count']} reviews)**\n"
       )
   ```

3. **Add Query Type Detection**:
   ```python
   query_types = {
       'which': 'specific_answer',  # Needs direct answer
       'how many': 'count',  # Needs number
       'what is': 'definition',  # Needs explanation
       'analyze': 'comprehensive'  # Needs full report
   }
   ```

---

## 📝 SUMMARY

**Your query "best rated product by customers" flows through:**

1. API → Query Router → Identifies as SENTIMENT query
2. LLM Engine → Confirms SENTIMENT intent
3. Execution Service → Fetches products, runs sentiment agent
4. Sentiment Agent → Calculates per-product sentiment, sorts by score
5. Result Synthesizer → Extracts insights, generates summary
6. Final Report → Returns with confidence 0.9 (90%)

**The "synthesis" is NOT using LLM to generate the answer.**
It's using:
- Database queries to find products
- Sentiment calculations on reviews
- Sorting by sentiment score
- Template-based summary generation

**The actual "best rated product" is determined by:**
```python
product_sentiments.sort(key=lambda x: x['average_sentiment'], reverse=True)
top_product = product_sentiments[0]  # Highest sentiment = best rated
```

This is pure data analysis, not LLM generation!
