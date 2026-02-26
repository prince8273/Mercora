# LLM Intelligence to UI Component Mapping

**Date:** February 24, 2026  
**Purpose:** Map every LLM output to frontend components and identify gaps

---

## 🧠 LLM ENGINE OUTPUTS (What Backend Produces)

Your multi-agent orchestration layer produces:

1. **Revenue Opportunities** - Untapped revenue potential
2. **Business Decisions** - Strategic recommendations
3. **Pricing Recommendations** - Optimal price suggestions
4. **Demand Forecasts** - Future demand predictions
5. **Sentiment Insights** - Customer sentiment analysis
6. **Competitor Analysis** - Competitive positioning
7. **Inventory Risks** - Stock-out/overstock warnings
8. **Pricing Gaps** - Price competitiveness analysis
9. **Demand Signals** - Early demand indicators
10. **Sentiment Themes** - Topic-based sentiment breakdown
11. **Confidence Scores** - AI confidence in predictions

---

## 📊 CURRENT UI MAPPING (What's Already Visible)

### ✅ Dashboard Page (OverviewPage.jsx)

#### Component: QuickInsights
**Shows:**
- AI-generated insights with types (trend, warning, opportunity, alert, success, info)
- Title, summary, details
- Metrics array
- Recommendations

**LLM Outputs Displayed:**
- ✅ Revenue opportunities (type: "opportunity")
- ✅ Business trends (type: "trend")
- ✅ Warnings (type: "warning")
- ✅ General insights (type: "info")

**What's MISSING:**
- ❌ Confidence scores (no confidence badge)
- ❌ Action buttons (can't act on insights)
- ❌ Priority levels (no urgency indicator)
- ❌ Impact metrics (no revenue impact shown)

#### Component: AlertPanel
**Shows:**
- Alerts with priority (critical, warning, info)
- Title, message, details
- Dismiss functionality
- Timestamp

**LLM Outputs Displayed:**
- ✅ Inventory risks (as alerts)
- ✅ Price change alerts
- ✅ General warnings

**What's MISSING:**
- ❌ Confidence scores
- ❌ Action buttons (can't take action)
- ❌ Impact metrics

---

### ✅ Pricing Page (PricingPage.jsx)

#### Component: RecommendationPanel
**Shows:**
- Pricing recommendations list
- Current price vs recommended price
- Confidence score ✅
- Expected impact (revenue, margin) ✅
- Reasoning/explanation ✅
- Accept/Reject buttons ✅

**LLM Outputs Displayed:**
- ✅ Pricing recommendations
- ✅ Confidence scores
- ✅ Expected revenue impact
- ✅ Reasoning

**What's MISSING:**
- ❌ Competitor context (why this price vs competitors)
- ❌ Historical success rate (how often these work)
- ❌ Risk assessment (what if it fails)

#### Component: CompetitorMatrix
**Shows:**
- Your price vs competitor prices
- Price gaps (color-coded)
- Product comparison table

**LLM Outputs Displayed:**
- ✅ Competitor pricing data
- ✅ Pricing gaps (visual)

**What's MISSING:**
- ❌ AI insights on gaps (no explanation why gap matters)
- ❌ Recommended actions (no "what to do about it")
- ❌ Opportunity scoring (which gaps are most important)

#### Component: PriceTrendChart
**Shows:**
- Historical price trends
- Your price vs competitors over time

**LLM Outputs Displayed:**
- ✅ Price history
- ✅ Competitor trends

**What's MISSING:**
- ❌ AI predictions (no future price suggestions)
- ❌ Trend analysis (no "prices are rising" insight)
- ❌ Optimal timing (no "best time to change price")

---

### ✅ Sentiment Page (SentimentPage.jsx)

#### Component: SentimentOverview
**Shows:**
- Overall sentiment score (gauge)
- Sentiment distribution (positive/neutral/negative %)
- Trend indicator (up/down)
- Total reviews count

**LLM Outputs Displayed:**
- ✅ Sentiment analysis results
- ✅ Distribution breakdown
- ✅ Trend direction

**What's MISSING:**
- ❌ Confidence score (how reliable is this sentiment?)
- ❌ AI insights (what does this sentiment mean for business?)
- ❌ Recommended actions (what to do about negative sentiment)

#### Component: ThemeBreakdown
**Shows:**
- Sentiment themes (Quality, Shipping, etc.)
- Theme sentiment (positive/negative/neutral)
- Count and percentage
- Sample reviews

**LLM Outputs Displayed:**
- ✅ Sentiment themes (AI-extracted topics)
- ✅ Theme-level sentiment

**What's MISSING:**
- ❌ Theme importance (which themes matter most)
- ❌ Trend over time (is this theme getting worse?)
- ❌ Recommended actions (how to improve this theme)

#### Component: ComplaintAnalysis
**Shows:**
- Complaint categories
- Severity levels
- Frequency counts
- Sample reviews

**LLM Outputs Displayed:**
- ✅ Complaint categorization (AI-powered)
- ✅ Severity assessment

**What's MISSING:**
- ❌ Root cause analysis (why are customers complaining?)
- ❌ Business impact (how much revenue at risk?)
- ❌ Recommended fixes (what to do about it)

---

### ✅ Forecast Page (ForecastPage.jsx)

#### Component: ForecastChart
**Shows:**
- Historical demand (actual)
- Predicted demand (forecast)
- Confidence band (upper/lower bounds)
- Confidence level percentage ✅
- Stats (avg historical, avg forecast, peak demand)

**LLM Outputs Displayed:**
- ✅ Demand forecasts (AI predictions)
- ✅ Confidence intervals
- ✅ Confidence level

**What's MISSING:**
- ❌ Demand drivers (why is demand changing?)
- ❌ Scenario analysis (what if scenarios)
- ❌ Recommended actions (what to do with this forecast)

#### Component: InventoryAlerts
**Shows:**
- Inventory alerts (stock-out risk, overstock)
- Priority levels (critical, warning, info)
- Recommendations ✅
- Impact description ✅
- Action buttons ✅

**LLM Outputs Displayed:**
- ✅ Inventory risks (AI-detected)
- ✅ Recommendations
- ✅ Impact assessment

**What's MISSING:**
- ❌ Confidence scores (how sure is the AI?)
- ❌ Cost analysis (cost of action vs inaction)

#### Component: AccuracyMetrics
**Shows:**
- Forecast accuracy stats (MAPE, RMSE)
- Model performance

**LLM Outputs Displayed:**
- ✅ Model accuracy metrics

**What's MISSING:**
- ❌ Confidence trend (is model getting better?)
- ❌ Reliability score (can I trust this model?)

---

### ✅ Intelligence Page (IntelligencePage.jsx)

#### Component: ResultsPanel
**Shows:**
- Executive summary
- Insights list
- Data visualizations
- Action items with priorities ✅

**LLM Outputs Displayed:**
- ✅ Query results (AI-generated)
- ✅ Insights
- ✅ Action items
- ✅ Visualizations

**What's MISSING:**
- ❌ Confidence scores (how reliable is this answer?)
- ❌ Data sources (where did this come from?)
- ❌ Alternative interpretations (other ways to look at this)


---

## ❌ MISSING UI COMPONENTS (LLM Intelligence NOT Visible)

### 1. Revenue Opportunity Cards (CRITICAL MISSING!)

**LLM Output:** Revenue opportunities with potential value, confidence, and actions

**Current Status:** ❌ Partially visible in QuickInsights but NO dedicated component

**What's Needed:**
```jsx
<RevenueOpportunityCard
  opportunity={{
    id: "opp-001",
    title: "Increase price on Wireless Mouse",
    potentialRevenue: 5200.00,
    confidence: 0.85,
    timeframe: "30 days",
    effort: "low",
    reasoning: "Competitors pricing 15% higher, demand is strong",
    actions: [
      { label: "Apply Recommendation", action: "apply_pricing" },
      { label: "View Analysis", action: "view_details" }
    ]
  }}
  onAccept={handleAccept}
  onReject={handleReject}
  onViewDetails={handleViewDetails}
/>
```

**Where to Display:** Dashboard page (new section) or dedicated "Opportunities" page

**UI Elements:**
- 💰 Revenue impact badge (large, prominent)
- 🎯 Confidence score badge (0-100%)
- ⏱️ Timeframe indicator
- 🔧 Effort level (low/medium/high)
- 📊 Reasoning explanation
- ✅ Accept button
- ❌ Reject button
- 👁️ View details button

---

### 2. Business Decision Panel (CRITICAL MISSING!)

**LLM Output:** Strategic business decisions with pros/cons, confidence, and impact

**Current Status:** ❌ NOT visible anywhere

**What's Needed:**
```jsx
<BusinessDecisionPanel
  decisions={[
    {
      id: "dec-001",
      title: "Expand into Home Decor category",
      type: "expansion",
      confidence: 0.78,
      expectedImpact: {
        revenue: 25000,
        margin: 35.5,
        timeToROI: "6 months"
      },
      pros: [
        "High demand in target market",
        "Low competition",
        "Synergy with existing products"
      ],
      cons: [
        "Requires inventory investment",
        "New supplier relationships needed"
      ],
      dataSupport: [
        "Market research shows 45% growth",
        "Customer surveys indicate interest"
      ],
      recommendedAction: "Start with 10 SKUs, test for 3 months"
    }
  ]}
  onAccept={handleAcceptDecision}
  onReject={handleRejectDecision}
  onRequestMoreInfo={handleRequestMoreInfo}
/>
```

**Where to Display:** Dashboard page (new section) or dedicated "Decisions" page

**UI Elements:**
- 🎯 Decision type badge (expansion, optimization, risk mitigation)
- 📊 Confidence score (with visual indicator)
- 💰 Expected impact metrics (revenue, margin, ROI)
- ✅ Pros list (green checkmarks)
- ❌ Cons list (red warnings)
- 📈 Data support section (evidence)
- 💡 Recommended action (highlighted)
- Action buttons (Accept, Reject, More Info)

---

### 3. Confidence Score Badge Component (MISSING!)

**LLM Output:** Confidence scores for all predictions (0-1 or 0-100%)

**Current Status:** ❌ Only shown in RecommendationPanel, missing everywhere else

**What's Needed:**
```jsx
<ConfidenceScore
  score={0.85}
  size="sm|md|lg"
  showLabel={true}
  tooltip="AI is 85% confident in this prediction based on historical accuracy"
/>
```

**Visual Design:**
- 🟢 High confidence (>80%): Green badge
- 🟡 Medium confidence (50-80%): Yellow badge
- 🔴 Low confidence (<50%): Red badge
- Progress bar or circular gauge
- Tooltip with explanation

**Where to Add:**
- ✅ RecommendationPanel (already has it)
- ❌ QuickInsights (MISSING)
- ❌ AlertPanel (MISSING)
- ❌ SentimentOverview (MISSING)
- ❌ ForecastChart (has percentage but no visual badge)
- ❌ InventoryAlerts (MISSING)
- ❌ ResultsPanel (MISSING)

---

### 4. Demand Signal Indicators (MISSING!)

**LLM Output:** Early demand signals (trending up/down, seasonal patterns, anomalies)

**Current Status:** ❌ NOT visible anywhere

**What's Needed:**
```jsx
<DemandSignalCard
  signal={{
    productId: "prod-001",
    productName: "Wireless Mouse",
    signal: "trending_up",
    strength: "strong",
    confidence: 0.82,
    description: "Demand increasing 25% week-over-week",
    drivers: [
      "Back-to-school season",
      "Competitor stock-out",
      "Positive reviews surge"
    ],
    recommendation: "Increase inventory by 30% for next 2 weeks",
    potentialImpact: {
      revenue: 8500,
      units: 280
    }
  }}
  onTakeAction={handleTakeAction}
/>
```

**Where to Display:** Dashboard page or Forecast page

**UI Elements:**
- 📈 Signal type icon (trending up/down, seasonal, anomaly)
- 💪 Signal strength (weak/moderate/strong)
- 🎯 Confidence score
- 📊 Description
- 🔍 Drivers list (why is this happening)
- 💡 Recommendation
- 💰 Potential impact
- Action button

---

### 5. Competitor Intelligence Panel (MISSING!)

**LLM Output:** Competitor analysis with positioning, threats, opportunities

**Current Status:** ❌ Only raw price data in CompetitorMatrix, no AI insights

**What's Needed:**
```jsx
<CompetitorIntelligencePanel
  analysis={{
    competitorId: "comp-001",
    competitorName: "Competitor A",
    positioning: "premium",
    strengths: [
      "Lower prices on 60% of products",
      "Faster shipping",
      "Higher review count"
    ],
    weaknesses: [
      "Lower product quality (based on reviews)",
      "Poor customer service",
      "Limited product range"
    ],
    threats: [
      {
        type: "price_war",
        severity: "high",
        description: "Competitor dropped prices 15% last week",
        recommendation: "Monitor closely, consider targeted promotions"
      }
    ],
    opportunities: [
      {
        type: "quality_advantage",
        potential: "high",
        description: "Your products have 4.7★ vs their 3.9★",
        recommendation: "Emphasize quality in marketing"
      }
    ],
    confidence: 0.79
  }}
/>
```

**Where to Display:** Pricing page (new section)

**UI Elements:**
- 🏢 Competitor profile card
- 📊 Positioning badge (premium/value/balanced)
- ✅ Strengths list
- ❌ Weaknesses list
- ⚠️ Threats section (with severity)
- 💡 Opportunities section (with potential)
- 🎯 Confidence score
- Recommended actions

---

### 6. Impact Metrics Component (MISSING!)

**LLM Output:** Business impact of actions (revenue, margin, units, risk)

**Current Status:** ❌ Partially shown in some places, not standardized

**What's Needed:**
```jsx
<ImpactMetrics
  metrics={{
    revenue: { value: 5200, change: 12.5, timeframe: "30 days" },
    margin: { value: 35.2, change: 2.1 },
    units: { value: 180, change: 15 },
    risk: { level: "low", description: "Minimal downside risk" }
  }}
  layout="horizontal|vertical|grid"
  showChange={true}
  showTimeframe={true}
/>
```

**Where to Add:**
- Revenue opportunity cards
- Business decision panel
- Pricing recommendations (enhance existing)
- Inventory alerts (enhance existing)
- Query results

**UI Elements:**
- 💰 Revenue impact (with $ amount)
- 📊 Margin impact (with %)
- 📦 Units impact (with count)
- ⚠️ Risk level (low/medium/high)
- 📈 Change indicators (up/down arrows)
- ⏱️ Timeframe labels

---

### 7. Action Recommendation Component (MISSING!)

**LLM Output:** Specific actions to take with priority, effort, and impact

**Current Status:** ❌ Partially in some components, not standardized

**What's Needed:**
```jsx
<ActionRecommendation
  action={{
    id: "action-001",
    title: "Increase inventory for Wireless Mouse",
    priority: "high",
    effort: "medium",
    impact: "high",
    description: "Order 200 units to meet forecasted demand",
    reasoning: "Forecast shows 30% demand increase, current stock will run out in 5 days",
    steps: [
      "Contact supplier for quote",
      "Place order for 200 units",
      "Update inventory system"
    ],
    deadline: "2024-01-20",
    estimatedCost: 2400,
    expectedReturn: 6800,
    confidence: 0.88
  }}
  onAccept={handleAccept}
  onSnooze={handleSnooze}
  onReject={handleReject}
/>
```

**Where to Display:** Dashboard (new "Actions" section), all insight components

**UI Elements:**
- 🎯 Priority badge (high/medium/low)
- 🔧 Effort indicator (low/medium/high)
- 📊 Impact indicator (low/medium/high)
- 📝 Description
- 💡 Reasoning
- ✅ Steps checklist
- ⏰ Deadline
- 💰 Cost vs Return
- 🎯 Confidence score
- Action buttons (Accept, Snooze, Reject)


---

## 🎯 MINIMUM VIABLE COMPONENT SET

To fully surface LLM intelligence, you need these **7 core components**:

### 1. ConfidenceScore (Atom)
**Purpose:** Show AI confidence in predictions  
**Usage:** Add to ALL AI-generated content  
**Priority:** 🔴 CRITICAL

```jsx
<ConfidenceScore score={0.85} size="md" />
```

### 2. ImpactMetrics (Molecule)
**Purpose:** Show business impact of actions  
**Usage:** Revenue opportunities, decisions, recommendations  
**Priority:** 🔴 CRITICAL

```jsx
<ImpactMetrics 
  revenue={5200} 
  margin={35.2} 
  units={180} 
  risk="low" 
/>
```

### 3. ActionRecommendation (Molecule)
**Purpose:** Display actionable recommendations  
**Usage:** All pages with AI insights  
**Priority:** 🔴 CRITICAL

```jsx
<ActionRecommendation
  title="Increase inventory"
  priority="high"
  impact="high"
  onAccept={handleAccept}
/>
```

### 4. RevenueOpportunityCard (Organism)
**Purpose:** Show revenue opportunities  
**Usage:** Dashboard page  
**Priority:** 🔴 CRITICAL

```jsx
<RevenueOpportunityCard
  opportunity={opportunityData}
  onAccept={handleAccept}
/>
```

### 5. BusinessDecisionPanel (Organism)
**Purpose:** Display strategic decisions  
**Usage:** Dashboard page or dedicated Decisions page  
**Priority:** 🟡 HIGH

```jsx
<BusinessDecisionPanel
  decisions={decisionsData}
  onAccept={handleAccept}
/>
```

### 6. DemandSignalCard (Organism)
**Purpose:** Show early demand signals  
**Usage:** Dashboard or Forecast page  
**Priority:** 🟡 HIGH

```jsx
<DemandSignalCard
  signal={signalData}
  onTakeAction={handleAction}
/>
```

### 7. CompetitorIntelligencePanel (Organism)
**Purpose:** Display competitor analysis  
**Usage:** Pricing page  
**Priority:** 🟢 MEDIUM

```jsx
<CompetitorIntelligencePanel
  analysis={competitorData}
/>
```

---

## 📋 COMPONENT-BY-COMPONENT BREAKDOWN

### LLM Output → UI Component Mapping

| LLM Output | Current Component | Status | Missing Component | Priority |
|------------|-------------------|--------|-------------------|----------|
| **Revenue Opportunities** | QuickInsights | ⚠️ Partial | RevenueOpportunityCard | 🔴 CRITICAL |
| **Business Decisions** | None | ❌ Missing | BusinessDecisionPanel | 🔴 CRITICAL |
| **Pricing Recommendations** | RecommendationPanel | ✅ Good | Add confidence badge | 🟢 MEDIUM |
| **Demand Forecasts** | ForecastChart | ✅ Good | Add action recommendations | 🟡 HIGH |
| **Sentiment Insights** | SentimentOverview | ⚠️ Partial | Add confidence + actions | 🟡 HIGH |
| **Competitor Analysis** | CompetitorMatrix | ⚠️ Partial | CompetitorIntelligencePanel | 🟡 HIGH |
| **Inventory Risks** | InventoryAlerts | ✅ Good | Add confidence scores | 🟢 MEDIUM |
| **Pricing Gaps** | CompetitorMatrix | ⚠️ Partial | Add AI insights overlay | 🟡 HIGH |
| **Demand Signals** | None | ❌ Missing | DemandSignalCard | 🔴 CRITICAL |
| **Sentiment Themes** | ThemeBreakdown | ⚠️ Partial | Add actions + importance | 🟡 HIGH |
| **Confidence Scores** | RecommendationPanel only | ⚠️ Partial | ConfidenceScore component | 🔴 CRITICAL |

---

## 🚀 IMPLEMENTATION ROADMAP

### Phase 1: Core Intelligence Components (CRITICAL)
**Goal:** Make AI confidence and impact visible everywhere

1. **ConfidenceScore Component** (Atom)
   - Visual badge with color coding
   - Tooltip with explanation
   - Add to ALL existing AI components

2. **ImpactMetrics Component** (Molecule)
   - Revenue, margin, units, risk display
   - Standardized across all components

3. **ActionRecommendation Component** (Molecule)
   - Priority, effort, impact indicators
   - Accept/Reject/Snooze actions
   - Add to insights, alerts, recommendations

**Time:** 1-2 days  
**Impact:** Makes existing AI outputs more actionable

---

### Phase 2: Revenue & Decisions (CRITICAL)
**Goal:** Surface high-value opportunities and strategic decisions

4. **RevenueOpportunityCard Component** (Organism)
   - Dedicated component for revenue opportunities
   - Prominent on dashboard
   - Action buttons

5. **BusinessDecisionPanel Component** (Organism)
   - Strategic decision display
   - Pros/cons analysis
   - Data support section

6. **Dashboard "Opportunities" Section**
   - New section on dashboard
   - Shows top 3-5 revenue opportunities
   - Shows pending business decisions

**Time:** 2-3 days  
**Impact:** Surfaces most valuable LLM outputs

---

### Phase 3: Demand & Competitor Intelligence (HIGH)
**Goal:** Show predictive insights and competitive positioning

7. **DemandSignalCard Component** (Organism)
   - Early demand indicators
   - Signal strength visualization
   - Recommended actions

8. **CompetitorIntelligencePanel Component** (Organism)
   - Competitor strengths/weaknesses
   - Threats and opportunities
   - Strategic recommendations

9. **Enhance Existing Components**
   - Add confidence scores to SentimentOverview
   - Add action recommendations to ThemeBreakdown
   - Add AI insights to CompetitorMatrix

**Time:** 2-3 days  
**Impact:** Completes competitive and predictive intelligence

---

### Phase 4: Polish & Integration (MEDIUM)
**Goal:** Refine and integrate all components

10. **Create "Opportunities" Page** (Optional)
    - Dedicated page for all opportunities
    - Revenue, pricing, inventory, demand
    - Filterable and sortable

11. **Create "Decisions" Page** (Optional)
    - Dedicated page for strategic decisions
    - Decision history
    - Outcome tracking

12. **Add Intelligence Overlays**
    - Hover tooltips with AI insights
    - Contextual help
    - Explanation panels

**Time:** 2-3 days  
**Impact:** Professional polish and discoverability

---

## 📊 BEFORE vs AFTER

### BEFORE (Current State)
```
Dashboard:
- QuickInsights: Shows insights but no confidence, no clear actions
- AlertPanel: Shows alerts but no confidence, limited actions

Pricing:
- RecommendationPanel: Good! Has confidence and actions ✅
- CompetitorMatrix: Just data, no AI insights

Sentiment:
- SentimentOverview: Shows sentiment but no confidence
- ThemeBreakdown: Shows themes but no actions

Forecast:
- ForecastChart: Shows predictions but no actions
- InventoryAlerts: Shows alerts but no confidence

Intelligence:
- ResultsPanel: Shows results but no confidence
```

### AFTER (With New Components)
```
Dashboard:
- QuickInsights: + ConfidenceScore + ActionRecommendation ✅
- AlertPanel: + ConfidenceScore + ImpactMetrics ✅
- RevenueOpportunityCard: NEW! Shows top opportunities ✅
- BusinessDecisionPanel: NEW! Shows strategic decisions ✅
- DemandSignalCard: NEW! Shows demand signals ✅

Pricing:
- RecommendationPanel: Already good ✅
- CompetitorMatrix: + AI insights overlay ✅
- CompetitorIntelligencePanel: NEW! Deep competitor analysis ✅

Sentiment:
- SentimentOverview: + ConfidenceScore + ActionRecommendation ✅
- ThemeBreakdown: + ActionRecommendation + Importance ✅

Forecast:
- ForecastChart: + ActionRecommendation ✅
- InventoryAlerts: + ConfidenceScore ✅

Intelligence:
- ResultsPanel: + ConfidenceScore + ImpactMetrics ✅
```

---

## 🎯 KEY TAKEAWAYS

### What's Working:
1. ✅ **RecommendationPanel** - Best example! Has confidence, impact, actions
2. ✅ **InventoryAlerts** - Has recommendations and impact
3. ✅ **ResultsPanel** - Shows insights and action items

### What's Missing:
1. ❌ **Confidence scores** - Only in RecommendationPanel
2. ❌ **Revenue opportunities** - No dedicated component
3. ❌ **Business decisions** - Not visible anywhere
4. ❌ **Demand signals** - Not visible anywhere
5. ❌ **Competitor intelligence** - Only raw data, no AI insights
6. ❌ **Impact metrics** - Not standardized
7. ❌ **Action recommendations** - Not standardized

### Minimum Components Needed:
1. 🔴 **ConfidenceScore** (Atom) - Add everywhere
2. 🔴 **ImpactMetrics** (Molecule) - Standardize impact display
3. 🔴 **ActionRecommendation** (Molecule) - Standardize actions
4. 🔴 **RevenueOpportunityCard** (Organism) - Show opportunities
5. 🟡 **BusinessDecisionPanel** (Organism) - Show decisions
6. 🟡 **DemandSignalCard** (Organism) - Show demand signals
7. 🟢 **CompetitorIntelligencePanel** (Organism) - Show competitor insights

### Implementation Priority:
1. **Phase 1** (1-2 days): ConfidenceScore, ImpactMetrics, ActionRecommendation
2. **Phase 2** (2-3 days): RevenueOpportunityCard, BusinessDecisionPanel
3. **Phase 3** (2-3 days): DemandSignalCard, CompetitorIntelligencePanel
4. **Phase 4** (2-3 days): Polish and optional pages

**Total Time:** 7-11 days to fully surface all LLM intelligence

---

## 💡 DESIGN PRINCIPLES

### 1. Confidence First
Every AI output MUST show confidence score prominently

### 2. Impact Visible
Every recommendation MUST show business impact (revenue, margin, units)

### 3. Action Oriented
Every insight MUST have clear, actionable next steps

### 4. Context Rich
Every recommendation MUST explain WHY (reasoning, data support)

### 5. Risk Aware
Every decision MUST show potential risks and downsides

### 6. Consistent UI
All AI components MUST use same visual language (badges, colors, layouts)

---

**Last Updated:** February 24, 2026  
**Status:** Complete mapping - Ready for implementation  
**Next Action:** Build Phase 1 components (ConfidenceScore, ImpactMetrics, ActionRecommendation)

