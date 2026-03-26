"""
Result Synthesizer - Multi-Agent Result Synthesis

This component synthesizes results from multiple intelligence agents into:
1. Executive summary with key findings
2. Prioritized action items
3. Overall confidence assessment
4. Comprehensive structured report

Features:
- Multi-agent result aggregation
- Executive summary generation (with optional LLM)
- Action item prioritization
- Confidence score calculation
- Analytical database storage
"""
import logging
import json
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4
from datetime import datetime
from enum import Enum

from src.schemas.report import (
    StructuredReport,
    MetricWithTrend,
    RiskAssessment,
    DataQualityWarning,
    SupportingEvidence,
    Insight,
    ActionItem,
    TrendDirection,
    SeverityLevel
)
from src.orchestration.llm_reasoning_engine import LLMReasoningEngine, AgentType
from src.orchestration.prompt_optimizer import get_prompt_optimizer

logger = logging.getLogger(__name__)


class SynthesisMode(str, Enum):
    """Synthesis mode for result generation"""
    SIMPLE = "simple"  # Rule-based synthesis without LLM
    ENHANCED = "enhanced"  # LLM-powered synthesis with rich summaries


class ResultSynthesizer:
    """
    Synthesizes results from multiple intelligence agents.
    
    Capabilities:
    - Aggregate results from pricing, sentiment, and forecast agents
    - Generate executive summaries (rule-based or LLM-powered)
    - Prioritize action items using impact/urgency matrix
    - Calculate overall confidence from agent confidences
    - Store results in analytical database
    
    Note: Analytical database storage is currently in-memory for demo purposes.
    In production, this would integrate with a time-series or analytical database
    (e.g., TimescaleDB, ClickHouse, or data warehouse).
    """
    
    # Class-level in-memory storage for demo (Phase 2: replace with real DB)
    _analytical_storage: Dict[UUID, List[StructuredReport]] = {}
    
    def __init__(
        self,
        tenant_id: UUID,
        llm_engine: Optional[LLMReasoningEngine] = None,
        synthesis_mode: SynthesisMode = SynthesisMode.SIMPLE
    ):
        """
        Initialize Result Synthesizer
        
        Args:
            tenant_id: Tenant UUID for multi-tenancy isolation
            llm_engine: Optional LLM engine for enhanced synthesis
            synthesis_mode: Simple (rule-based) or Enhanced (LLM-powered)
        """
        self.tenant_id = tenant_id
        self.llm_engine = llm_engine
        self.synthesis_mode = synthesis_mode
        self.prompt_optimizer = get_prompt_optimizer()
        
        # Initialize tenant storage if not exists
        if tenant_id not in self._analytical_storage:
            self._analytical_storage[tenant_id] = []
        
        logger.info(f"ResultSynthesizer initialized for tenant {tenant_id} in {synthesis_mode.value} mode")
    
    def synthesize_results(
        self,
        query_id: str,
        query: str,
        agent_results: Dict[AgentType, Dict[str, Any]],
        execution_metadata: Dict[str, Any]
    ) -> StructuredReport:
        """
        Synthesize results from multiple agents into a structured report.
        
        Args:
            query_id: Unique query identifier
            query: Original user query
            agent_results: Dictionary mapping agent types to their results
            execution_metadata: Metadata about execution (duration, mode, etc.)
            
        Returns:
            StructuredReport with synthesized results
        """
        logger.info(f"Synthesizing results for query {query_id} from {len(agent_results)} agents")
        
        # Stash for use in LLM summary generation
        self._current_agent_results = agent_results

        # Extract insights from agent results
        insights = self._extract_insights(agent_results)
        
        # Extract metrics with trends
        metrics = self._extract_metrics(agent_results)
        
        # Identify risks
        risks = self._identify_risks(agent_results)
        
        # Extract data quality warnings
        warnings = self._extract_warnings(agent_results)
        
        # Generate action items
        action_items = self._generate_action_items(agent_results, insights, risks)
        
        # Prioritize action items
        prioritized_actions = self._prioritize_action_items(action_items)
        
        # Calculate overall confidence
        overall_confidence = self._calculate_overall_confidence(agent_results)
        
        # Generate executive summary
        executive_summary = self._generate_executive_summary(
            query,
            insights,
            metrics,
            risks,
            prioritized_actions,
            overall_confidence
        )

        # Cross-data reasoning — only when 2+ distinct agent types returned data
        # and we have an LLM engine available (ENHANCED mode)
        if (
            self.synthesis_mode == SynthesisMode.ENHANCED
            and self.llm_engine
            and len(agent_results) >= 2
        ):
            # Build rich per-agent summaries using the same formatter
            agent_summaries = {}
            for agent_type, result in agent_results.items():
                if not isinstance(result, dict):
                    continue
                # Use _format_agent_data_for_llm for a single agent
                single = {agent_type: result}
                rich_text = self._format_agent_data_for_llm(single)
                if rich_text and rich_text != "No data available.":
                    agent_summaries[agent_type.value] = rich_text

            if len(agent_summaries) >= 2:
                cross_insight = self.llm_engine.cross_data_reasoning(query, agent_summaries)
                if cross_insight:
                    insights.append(Insight(
                        insight_id=str(uuid4()),
                        title="Cross-Data Analysis",
                        description=cross_insight,
                        category="cross_analysis",
                        agent_source="llm_reasoning",
                        confidence=overall_confidence,
                        supporting_evidence=[]
                    ))
        
        # Create structured report
        report = StructuredReport(
            report_id=str(uuid4()),
            tenant_id=self.tenant_id,
            query=query,
            timestamp=datetime.utcnow(),
            executive_summary=executive_summary,
            insights=insights,
            key_metrics=metrics,
            risks=risks,
            action_items=prioritized_actions,
            data_quality_warnings=warnings,
            overall_confidence=overall_confidence * 100,  # Convert to 0-100 scale
            agent_results=execution_metadata,
            recommendations=[]
        )
        
        logger.info(f"Report {report.report_id} generated with {len(insights)} insights, {len(prioritized_actions)} actions")
        
        return report
    
    def _extract_insights(self, agent_results: Dict[AgentType, Dict[str, Any]]) -> List[Insight]:
        """Extract insights from agent results"""
        insights = []
        
        import logging
        logger = logging.getLogger(__name__)
        
        for agent_type, result in agent_results.items():
            agent_name = agent_type.value
            logger.info(f"Extracting insights from {agent_name}: result keys = {result.keys() if result else 'None'}")
            if result and 'data' in result:
                logger.info(f"  data keys = {result['data'].keys() if isinstance(result['data'], dict) else type(result['data'])}")
            
            # Extract insights based on agent type
            if agent_type == AgentType.PRICING:
                insights.extend(self._extract_pricing_insights(result, agent_name))
            elif agent_type == AgentType.SENTIMENT:
                insights.extend(self._extract_sentiment_insights(result, agent_name))
            elif agent_type == AgentType.DEMAND_FORECAST:
                insights.extend(self._extract_forecast_insights(result, agent_name))
            elif agent_type.value == 'sales':
                insights.extend(self._extract_sales_insights(result, agent_name))
            elif agent_type.value == 'general':
                insights.extend(self._extract_general_insights(result, agent_name))
        
        logger.info(f"Total insights extracted: {len(insights)}")
        return insights
    
    def _extract_pricing_insights(self, result: Dict[str, Any], agent_name: str) -> List[Insight]:
        """Extract insights from pricing agent results"""
        insights = []
        
        import logging
        logger = logging.getLogger(__name__)
        
        # Get data from result (agents wrap their data in a 'data' field)
        data = result.get("data") if result.get("data") is not None else result
        
        logger.info(f"Pricing insights - data type: {type(data)}, is dict: {isinstance(data, dict)}")
        if isinstance(data, dict):
            logger.info(f"Pricing insights - data keys: {data.keys()}")
            if 'data' in data:
                logger.info(f"Pricing insights - nested data keys: {data['data'].keys() if isinstance(data['data'], dict) else type(data['data'])}")
                # Double nesting - unwrap one more level
                data = data['data']
        
        # Get agent confidence from result
        agent_confidence = result.get("confidence", result.get("final_confidence", 0.8))
        
        logger.info(f"Pricing insights - looking for price_gaps in data")
        
        # Price gaps
        price_gaps = data.get("price_gaps", []) if isinstance(data, dict) else []
        logger.info(f"Pricing insights - found {len(price_gaps)} price gaps")
        
        if price_gaps:
            significant_gaps = [g for g in price_gaps if abs(g.get("gap_percentage", 0)) > 10]
            logger.info(f"Pricing insights - {len(significant_gaps)} significant gaps (>10%)")
            if significant_gaps:
                # Calculate confidence based on data quality and number of gaps
                gap_confidence = agent_confidence * min(1.0, len(significant_gaps) / 10)
                
                insight = Insight(
                    insight_id=str(uuid4()),
                    title="Significant Price Gaps Detected",
                    description=f"Found {len(significant_gaps)} products with >10% price difference from competitors",
                    category="pricing",
                    agent_source=agent_name,
                    confidence=gap_confidence,
                    supporting_evidence=[]
                )
                insights.append(insight)
                logger.info(f"Pricing insights - added gap insight")
        
        # Recommendations
        recommendations = data.get("recommendations", []) if isinstance(data, dict) else []
        logger.info(f"Pricing insights - found {len(recommendations)} recommendations")
        
        if recommendations:
            high_confidence_recs = [r for r in recommendations if r.get("confidence", 0) > 0.8]
            logger.info(f"Pricing insights - {len(high_confidence_recs)} high-confidence recommendations")
            if high_confidence_recs:
                # Use average confidence of high-confidence recommendations
                avg_rec_confidence = sum(r.get("confidence", 0) for r in high_confidence_recs) / len(high_confidence_recs)
                
                insight = Insight(
                    insight_id=str(uuid4()),
                    title="High-Confidence Pricing Recommendations",
                    description=f"{len(high_confidence_recs)} pricing adjustments recommended with >80% confidence",
                    category="pricing",
                    agent_source=agent_name,
                    confidence=avg_rec_confidence,
                    supporting_evidence=[]
                )
                insights.append(insight)
                logger.info(f"Pricing insights - added recommendation insight")
        
        logger.info(f"Pricing insights - returning {len(insights)} total insights")
        return insights
    
    def _extract_sentiment_insights(self, result: Dict[str, Any], agent_name: str) -> List[Insight]:
        """Extract insights from sentiment agent results"""
        insights = []
        
        # Get data from result (agents wrap their data in a 'data' field)
        data = result.get("data") if result.get("data") is not None else result
        
        # Get agent confidence from result
        agent_confidence = result.get("confidence", result.get("final_confidence", 0.8))
        
        # Check if we have product-level sentiment data
        product_sentiments = data.get("product_sentiments", []) if isinstance(data, dict) else []
        
        if product_sentiments:
            # Find products with most positive reviews
            positive_products = sorted(
                [p for p in product_sentiments if p.get("average_sentiment", 0) > 0.4],
                key=lambda x: x.get("average_sentiment", 0),
                reverse=True
            )[:10]  # Top 10
            
            if positive_products:
                # Store detailed product info in supporting_evidence
                product_evidence = []
                for prod in positive_products:
                    product_name = prod.get("product_name", "Unknown Product")
                    sku = prod.get("sku", prod.get("product_id", "N/A"))
                    avg_sentiment = prod.get("average_sentiment", 0)
                    review_count = prod.get("review_count", 0)
                    positive_pct = prod.get("positive_percentage", 0)
                    
                    evidence = SupportingEvidence(
                        evidence_id=str(uuid4()),
                        insight_id="",
                        source_data_type="sentiment_analysis",
                        source_record_ids=[str(prod.get("product_id", ""))],
                        data_lineage_path=["sentiment_agent", "product_analysis"],
                        confidence=agent_confidence,
                        transformation_applied=json.dumps({
                            "sku": sku,
                            "name": product_name,
                            "average_sentiment": round(avg_sentiment, 2),
                            "review_count": review_count,
                            "positive_percentage": round(positive_pct, 1),
                            "badge": f"{positive_pct:.0f}% positive",
                            "badge_variant": "success" if positive_pct > 80 else "warning"
                        })
                    )
                    product_evidence.append(evidence)
                
                description = f"Found {len(positive_products)} products with highly positive reviews (>40% sentiment score)"
                
                insight = Insight(
                    insight_id=str(uuid4()),
                    title="Products with Most Positive Reviews",
                    description=description,
                    category="sentiment",
                    agent_source=agent_name,
                    confidence=agent_confidence,
                    supporting_evidence=product_evidence
                )
                
                # Update evidence with insight_id
                for evidence in insight.supporting_evidence:
                    evidence.insight_id = insight.insight_id
                
                insights.append(insight)
        
        # Overall sentiment
        sentiment_score = data.get("aggregate_sentiment_score", 0)
        if sentiment_score:
            sentiment_label = "positive" if sentiment_score > 0.6 else "negative" if sentiment_score < 0.4 else "neutral"
            
            # Confidence based on sentiment score extremity (more extreme = more confident)
            score_confidence = agent_confidence * (abs(sentiment_score - 0.5) * 2)
            
            insight = Insight(
                insight_id=str(uuid4()),
                title=f"Overall Customer Sentiment: {sentiment_label.title()}",
                description=f"Aggregate sentiment score: {sentiment_score:.2f}",
                category="sentiment",
                agent_source=agent_name,
                confidence=score_confidence,
                supporting_evidence=[]
            )
            insights.append(insight)
        
        # Feature requests
        feature_requests = data.get("feature_requests", [])
        if feature_requests:
            top_requests = sorted(feature_requests, key=lambda x: x.get("frequency", 0), reverse=True)[:3]
            if top_requests:
                # Confidence based on frequency of top requests
                total_frequency = sum(r.get("frequency", 0) for r in feature_requests)
                top_frequency = sum(r.get("frequency", 0) for r in top_requests)
                freq_confidence = agent_confidence * (top_frequency / total_frequency if total_frequency > 0 else 0.5)
                
                insight = Insight(
                    insight_id=str(uuid4()),
                    title="Top Customer Feature Requests",
                    description=f"Customers requesting: {', '.join([r.get('feature', '') for r in top_requests])}",
                    category="sentiment",
                    agent_source=agent_name,
                    confidence=freq_confidence,
                    supporting_evidence=[]
                )
                insights.append(insight)
        
        # Complaints
        complaints = data.get("complaint_patterns", [])
        if complaints:
            critical_complaints = [c for c in complaints if c.get("severity", "") == "high"]
            if critical_complaints:
                # High confidence for critical complaints (they're important)
                complaint_confidence = agent_confidence * 0.95
                
                insight = Insight(
                    insight_id=str(uuid4()),
                    title="Critical Customer Complaints Detected",
                    description=f"{len(critical_complaints)} high-severity complaint patterns identified",
                    category="sentiment",
                    agent_source=agent_name,
                    confidence=complaint_confidence,
                    supporting_evidence=[]
                )
                insights.append(insight)
        
        return insights
    
    def _extract_forecast_insights(self, result: Dict[str, Any], agent_name: str) -> List[Insight]:
        """Extract insights from forecast agent results"""
        insights = []
        
        # Get data from result (agents wrap their data in a 'data' field)
        data = result.get("data") if result.get("data") is not None else result
        
        # Get agent confidence from result
        agent_confidence = result.get("final_confidence", result.get("confidence", 0.8))
        
        # Trend
        trend = data.get("trend", "stable")
        if trend != "stable":
            insight = Insight(
                insight_id=str(uuid4()),
                title=f"Demand Trend: {trend.title()}",
                description=f"Forecasted demand shows {trend} trend over the next period",
                category="forecast",
                agent_source=agent_name,
                confidence=agent_confidence,
                supporting_evidence=[]
            )
            insights.append(insight)
        
        # Seasonality
        seasonality = data.get("seasonality", {})
        strong_patterns = {k: v for k, v in seasonality.items() if v.get("strength", 0) > 0.7}
        if strong_patterns:
            # Confidence based on average strength of patterns
            avg_strength = sum(v.get("strength", 0) for v in strong_patterns.values()) / len(strong_patterns)
            seasonality_confidence = agent_confidence * avg_strength
            
            insight = Insight(
                insight_id=str(uuid4()),
                title="Strong Seasonal Patterns Detected",
                description=f"Detected {len(strong_patterns)} strong seasonal patterns: {', '.join(strong_patterns.keys())}",
                category="forecast",
                agent_source=agent_name,
                confidence=seasonality_confidence,
                supporting_evidence=[]
            )
            insights.append(insight)
        
        # Inventory alerts
        alerts = data.get("alerts", [])
        critical_alerts = [a for a in alerts if a.get("severity") in ["high", "critical"]]
        if critical_alerts:
            # High confidence for critical alerts
            alert_confidence = agent_confidence * 0.95
            
            insight = Insight(
                insight_id=str(uuid4()),
                title="Critical Inventory Alerts",
                description=f"{len(critical_alerts)} critical inventory risks identified",
                category="forecast",
                agent_source=agent_name,
                confidence=alert_confidence,
                supporting_evidence=[]
            )
            insights.append(insight)
        
        return insights
    
    def _extract_general_insights(self, result: Dict[str, Any], agent_name: str) -> List[Insight]:
        """Extract insights from the general agent results"""
        insights = []
        data = result.get("data") if result.get("data") is not None else result
        if isinstance(data, dict) and 'data' in data:
            data = data['data']

        if not isinstance(data, dict):
            return insights

        analysis_type = data.get('analysis_type', 'general')
        agent_confidence = result.get("confidence", 0.9)
        message = data.get('message', '')
        items = data.get('items', [])
        columns = data.get('columns', [])

        # Build supporting evidence from items
        evidence = []
        for item in items[:15]:
            # For time-series data (revenue_trend / sentiment_trend), use month as the identifier
            if analysis_type in ('revenue_trend', 'sentiment_trend'):
                sku = item.get('month', 'N/A')
                name = ''
            else:
                sku = item.get('sku') or item.get('category') or item.get('marketplace') or 'N/A'
                name = item.get('name') or item.get('category') or item.get('marketplace') or ''

            # Build metrics from whatever numeric fields exist in the item
            metrics = []

            # For performance diagnostics, show diagnostic-relevant columns only
            # (revenue/price are misleading for a "why not performing" query)
            if analysis_type == 'performance_diagnostic':
                diagnostic_keys = [
                    ('avg_rating', '{:.1f}★'),
                    ('complaint_rate', '{:.1f}%'),
                    ('complaints', '{}'),
                    ('units_sold', '{:,}'),
                    ('inventory', '{:,}'),
                ]
                label_map = {
                    'avg_rating': 'Avg Rating',
                    'complaint_rate': 'Complaint Rate',
                    'complaints': 'Complaints',
                    'units_sold': 'Units Sold',
                    'inventory': 'Stock',
                }
                for key, fmt in diagnostic_keys:
                    val = item.get(key)
                    if val is not None:
                        try:
                            formatted = fmt.format(val)
                        except Exception:
                            formatted = str(val)
                        metrics.append({'label': label_map[key], 'value': formatted})
            else:
                numeric_keys = [
                    ('revenue', '₹{:,.2f}'), ('total_revenue', '₹{:,.2f}'),
                    ('price', '₹{:,.2f}'), ('avg_price', '₹{:,.2f}'),
                    ('units_sold', '{:,}'), ('units', '{:,}'), ('total_units', '{:,}'),
                    ('inventory', '{:,}'), ('inventory_level', '{:,}'), ('stock', '{:,}'),
                    ('review_count', '{:,}'), ('avg_rating', '{:.2f}★'),
                    ('positive', '{:,}'), ('negative', '{:,}'), ('positive_pct', '{:.1f}%'),
                    ('orders', '{:,}'), ('order_count', '{:,}'),
                    ('count', '{:,}'), ('product_count', '{:,}'), ('products', '{:,}'),
                ]
                seen_labels = set()
                for key, fmt in numeric_keys:
                    val = item.get(key)
                    if val is not None and key not in seen_labels:
                        seen_labels.add(key)
                        label = key.replace('_', ' ').title()
                        try:
                            formatted = fmt.format(val)
                        except Exception:
                            formatted = str(val)
                        metrics.append({'label': label, 'value': formatted})

            # Use column names as labels if provided
            if columns and not metrics:
                for col in columns:
                    col_key = col.lower().replace(' ', '_')
                    val = item.get(col_key) or item.get(col.lower())
                    if val is not None:
                        metrics.append({'label': col, 'value': str(val)})

            # For performance_diagnostic, include complaints + issues + review texts
            extra = {}
            if analysis_type == 'performance_diagnostic':
                complaints_val = item.get('complaints', 0)
                complaint_rate_val = item.get('complaint_rate', 0)
                issues_val = item.get('issues', '')
                extra['complaints'] = int(complaints_val) if complaints_val else 0
                extra['complaint_rate'] = float(complaint_rate_val) if complaint_rate_val else 0.0
                extra['issues'] = issues_val or 'none detected'
                extra['low_reviews'] = item.get('low_reviews', [])
                # Use complaint_rate threshold (>15%) or explicit issues to flag danger
                has_real_issue = (
                    extra['complaint_rate'] > 15
                    or (extra['issues'] not in ('none detected', 'no issues detected', ''))
                )
                badge_variant = 'danger' if has_real_issue else 'success'
            else:
                badge_variant = 'success'

            ev = SupportingEvidence(
                evidence_id=str(uuid4()),
                insight_id="",
                source_data_type="database",
                source_record_ids=[],
                data_lineage_path=["general_agent", analysis_type],
                confidence=agent_confidence,
                transformation_applied=json.dumps({
                    "sku": sku,
                    "name": name,
                    "analysis_type": analysis_type,
                    "metrics": metrics,
                    "badge": metrics[0]['value'] if metrics else None,
                    "badge_variant": badge_variant,
                    **extra,
                })
            )
            evidence.append(ev)

        title_map = {
            'inventory': 'Inventory Overview',
            'product_list': 'Product Catalogue',
            'product_count': 'Product Count',
            'price_summary': 'Price Summary by Category',
            'price_list': 'Product Pricing',
            'reviews': 'Product Ratings & Reviews',
            'marketplace': 'Marketplace Performance',
            'revenue_by_category': 'Revenue by Category',
            'revenue_trend': 'Revenue Trend Over Time',
            'sentiment_trend': 'Customer Sentiment Trends',
            'category_deep_dive': f'Category Deep Dive: {data.get("category", "").title()}',
            'product_search': 'Matching Products',
            'data_summary': 'Data Overview',
            'top_products': 'Top Products',
        }
        title = title_map.get(analysis_type, 'Analysis Result')

        insight = Insight(
            insight_id=str(uuid4()),
            title=title,
            description=message,
            category="general",
            agent_source=agent_name,
            confidence=agent_confidence,
            supporting_evidence=evidence
        )
        for ev in insight.supporting_evidence:
            ev.insight_id = insight.insight_id
        insights.append(insight)

        # Extra callout for zero-sales products in category deep dives
        zero_count = data.get('zero_sales_count', 0)
        if zero_count:
            insights.append(Insight(
                insight_id=str(uuid4()),
                title="Products With Zero Sales",
                description=f"{zero_count} products in this category have never sold. Consider reviewing pricing or visibility.",
                category="general",
                agent_source=agent_name,
                confidence=agent_confidence,
                supporting_evidence=[]
            ))

        return insights

    def _extract_sales_insights(self, result: Dict[str, Any], agent_name: str) -> List[Insight]:
        """Extract insights from sales agent results"""
        insights = []
        data = result.get("data") if result.get("data") is not None else result
        if isinstance(data, dict) and 'data' in data:
            data = data['data']

        analysis_type = data.get('analysis_type', '') if isinstance(data, dict) else ''
        agent_confidence = result.get("confidence", 0.9)

        if analysis_type == 'revenue_by_category':
            categories = data.get('categories', [])
            if categories:
                evidence = [
                    SupportingEvidence(
                        evidence_id=str(uuid4()),
                        insight_id="",
                        source_data_type="sales_records",
                        source_record_ids=[],
                        data_lineage_path=["sales_agent", "category_aggregation"],
                        confidence=agent_confidence,
                        transformation_applied=json.dumps({
                            "sku": cat['category'],
                            "name": "",
                            "badge": f"₹{cat['total_revenue']:,.0f}",
                            "badge_variant": "success",
                            "metrics": [
                                {"label": "Revenue", "value": f"₹{cat['total_revenue']:,.2f}"},
                                {"label": "Units", "value": str(cat['total_units'])},
                            ]
                        })
                    )
                    for cat in categories[:10]
                ]
                insight = Insight(
                    insight_id=str(uuid4()),
                    title="Revenue by Category",
                    description=data.get('message', f"Revenue breakdown across {len(categories)} categories"),
                    category="sales",
                    agent_source=agent_name,
                    confidence=agent_confidence,
                    supporting_evidence=evidence
                )
                for ev in insight.supporting_evidence:
                    ev.insight_id = insight.insight_id
                insights.append(insight)

        elif analysis_type == 'top_products':
            products = data.get('products', [])
            category_filter = data.get('category_filter')
            if products:
                evidence = [
                    SupportingEvidence(
                        evidence_id=str(uuid4()),
                        insight_id="",
                        source_data_type="sales_records",
                        source_record_ids=[],
                        data_lineage_path=["sales_agent", "product_aggregation"],
                        confidence=agent_confidence,
                        transformation_applied=json.dumps({
                            "sku": p['sku'],
                            "name": p['name'],
                            "badge": f"₹{p['total_revenue']:,.0f}",
                            "badge_variant": "success",
                            "metrics": [
                                {"label": "Revenue", "value": f"₹{p['total_revenue']:,.2f}"},
                                {"label": "Units", "value": str(p['total_units'])},
                                {"label": "Category", "value": p['category']},
                            ]
                        })
                    )
                    for p in products[:10]
                ]
                title = (f"Top Products in {category_filter.title()}"
                         if category_filter else "Top Products by Revenue")
                insight = Insight(
                    insight_id=str(uuid4()),
                    title=title,
                    description=data.get('message', f"Top {len(products)} products by revenue"),
                    category="sales",
                    agent_source=agent_name,
                    confidence=agent_confidence,
                    supporting_evidence=evidence
                )
                for ev in insight.supporting_evidence:
                    ev.insight_id = insight.insight_id
                insights.append(insight)

        return insights

    def _extract_metrics(self, agent_results: Dict[AgentType, Dict[str, Any]]) -> List[MetricWithTrend]:
        """Extract metrics with trends from agent results"""
        metrics = []
        
        for agent_type, result in agent_results.items():
            # Unwrap data — agents wrap their payload in a 'data' key
            data = result.get("data") if result.get("data") is not None else result
            if isinstance(data, dict) and 'data' in data:
                data = data['data']

            if agent_type == AgentType.PRICING:
                price_gaps = data.get("price_gaps", []) if isinstance(data, dict) else []
                if price_gaps:
                    avg_gap = sum(g.get("gap_percentage", 0) for g in price_gaps) / len(price_gaps)
                    metrics.append(MetricWithTrend(
                        name="Average Price Gap",
                        value=round(avg_gap, 1),
                        unit="percentage",
                        trend=TrendDirection.STABLE,
                        confidence=result.get("confidence", 0.85)
                    ))
            
            elif agent_type == AgentType.SENTIMENT:
                sentiment_score = data.get("aggregate_sentiment_score") if isinstance(data, dict) else None
                if sentiment_score is not None:
                    metrics.append(MetricWithTrend(
                        name="Customer Sentiment Score",
                        value=round(sentiment_score, 2),
                        unit="score",
                        trend=TrendDirection.STABLE,
                        confidence=result.get("confidence", 0.8)
                    ))
            
            elif agent_type == AgentType.DEMAND_FORECAST:
                forecast_points = data.get("forecast_points", []) if isinstance(data, dict) else []
                if forecast_points:
                    avg_forecast = sum(p.get("predicted_quantity", 0) for p in forecast_points) / len(forecast_points)
                    trend_str = data.get("trend", "stable") if isinstance(data, dict) else "stable"
                    trend = TrendDirection.UP if trend_str == "increasing" else TrendDirection.DOWN if trend_str == "decreasing" else TrendDirection.STABLE
                    metrics.append(MetricWithTrend(
                        name="Forecasted Demand",
                        value=round(avg_forecast, 0),
                        unit="units",
                        trend=trend,
                        confidence=result.get("final_confidence", 0.8)
                    ))

            elif agent_type.value in ('sales', 'general'):
                total_revenue = data.get("total_revenue") if isinstance(data, dict) else None
                if total_revenue:
                    metrics.append(MetricWithTrend(
                        name="Total Revenue",
                        value=round(float(total_revenue), 2),
                        unit="₹",
                        trend=TrendDirection.STABLE,
                        confidence=result.get("confidence", 0.9)
                    ))
                total_units = data.get("total_units") if isinstance(data, dict) else None
                if total_units:
                    metrics.append(MetricWithTrend(
                        name="Total Units Sold",
                        value=int(total_units),
                        unit="units",
                        trend=TrendDirection.STABLE,
                        confidence=result.get("confidence", 0.9)
                    ))
        
        return metrics
    
    def _identify_risks(self, agent_results: Dict[AgentType, Dict[str, Any]]) -> List[RiskAssessment]:
        """Identify risks from agent results"""
        risks = []
        
        for agent_type, result in agent_results.items():
            if agent_type == AgentType.PRICING:
                # Price competitiveness risk
                price_gaps = result.get("price_gaps", [])
                overpriced = [g for g in price_gaps if g.get("gap_percentage", 0) > 20]
                if overpriced:
                    risk = RiskAssessment(
                        risk_id=str(uuid4()),
                        title="Price Competitiveness Risk",
                        description=f"{len(overpriced)} products priced >20% above competitors",
                        severity=SeverityLevel.HIGH,
                        impact="Revenue loss due to uncompetitive pricing",
                        likelihood="High",
                        mitigation="Review and adjust pricing for affected products",
                        affected_areas=["pricing", "revenue"],
                        confidence=0.85
                    )
                    risks.append(risk)
            
            elif agent_type == AgentType.SENTIMENT:
                # Customer satisfaction risk
                sentiment_score = result.get("aggregate_sentiment_score", 0.5)
                if sentiment_score < 0.4:
                    risk = RiskAssessment(
                        risk_id=str(uuid4()),
                        title="Customer Satisfaction Risk",
                        description=f"Low sentiment score: {sentiment_score:.2f}",
                        severity=SeverityLevel.HIGH,
                        impact="Customer churn and negative brand perception",
                        likelihood="High",
                        mitigation="Address top complaint patterns and improve product quality",
                        affected_areas=["customer_satisfaction", "brand"],
                        confidence=0.9
                    )
                    risks.append(risk)
            
            elif agent_type == AgentType.DEMAND_FORECAST:
                # Inventory risk
                alerts = result.get("alerts", [])
                stockout_alerts = [a for a in alerts if a.get("alert_type") == "stockout_risk"]
                if stockout_alerts:
                    risk = RiskAssessment(
                        risk_id=str(uuid4()),
                        title="Stockout Risk",
                        description=f"{len(stockout_alerts)} products at risk of stockout",
                        severity=SeverityLevel.CRITICAL,
                        impact="Lost sales and customer dissatisfaction",
                        likelihood="High",
                        mitigation="Increase inventory levels and expedite reorders",
                        affected_areas=["inventory", "sales"],
                        confidence=0.9
                    )
                    risks.append(risk)
        
        return risks
    
    def _extract_warnings(self, agent_results: Dict[AgentType, Dict[str, Any]]) -> List[DataQualityWarning]:
        """Extract data quality warnings from agent results"""
        warnings = []
        
        for agent_type, result in agent_results.items():
            qa_metadata = result.get("qa_metadata", {})
            data_quality_score = result.get("data_quality_score", 1.0)
            
            if data_quality_score < 0.8:
                warning = DataQualityWarning(
                    warning_id=str(uuid4()),
                    message=f"Low data quality score ({data_quality_score:.2f}) for {agent_type.value} agent",
                    severity=SeverityLevel.MEDIUM if data_quality_score > 0.6 else SeverityLevel.HIGH,
                    affected_data=agent_type.value,
                    recommendation="Review data sources and improve data collection processes"
                )
                warnings.append(warning)
        
        return warnings
    
    def _generate_action_items(
        self,
        agent_results: Dict[AgentType, Dict[str, Any]],
        insights: List[Insight],
        risks: List[RiskAssessment]
    ) -> List[ActionItem]:
        """Generate action items from results"""
        actions = []
        
        # Actions from pricing agent
        if AgentType.PRICING in agent_results:
            result = agent_results[AgentType.PRICING]
            # Get data from nested structure
            data = result.get("data") if result.get("data") is not None else result
            if isinstance(data, dict) and 'data' in data:
                data = data['data']  # Unwrap double nesting
            
            recommendations = data.get("recommendations", []) if isinstance(data, dict) else []
            for rec in recommendations[:5]:  # Top 5
                action = ActionItem(
                    action_id=str(uuid4()),
                    title=rec.get('title', f"Adjust price for product"),
                    description=rec.get('description', f"Consider price adjustment"),
                    priority=rec.get('priority', 'medium'),
                    impact=rec.get('impact', 'high'),
                    urgency=rec.get('urgency', 'medium'),
                    source_agent="pricing",
                    confidence=rec.get("confidence", 0.8)
                )
                actions.append(action)
        
        # Actions from sentiment agent
        if AgentType.SENTIMENT in agent_results:
            result = agent_results[AgentType.SENTIMENT]
            # Get data from nested structure
            data = result.get("data") if result.get("data") is not None else result
            if isinstance(data, dict) and 'data' in data:
                data = data['data']  # Unwrap double nesting
            
            # Extract from recommendations if available
            recommendations = data.get("recommendations", []) if isinstance(data, dict) else []
            for rec in recommendations[:3]:  # Top 3
                action = ActionItem(
                    action_id=str(uuid4()),
                    title=rec.get('title', 'Address customer feedback'),
                    description=rec.get('description', 'Review customer concerns'),
                    priority=rec.get('priority', 'medium'),
                    impact=rec.get('impact', 'high'),
                    urgency=rec.get('urgency', 'high'),
                    source_agent="sentiment",
                    confidence=rec.get("confidence", 0.8)
                )
                actions.append(action)
            
            # Also check complaint_patterns
            complaints = data.get("complaint_patterns", []) if isinstance(data, dict) else []
            for complaint in complaints[:3]:  # Top 3
                action = ActionItem(
                    action_id=str(uuid4()),
                    title=f"Address complaint: {complaint.get('pattern', 'issue')}",
                    description=f"Frequency: {complaint.get('frequency', 0)} mentions",
                    priority="high" if complaint.get("severity") == "high" else "medium",
                    impact="high",
                    urgency="high",
                    source_agent="sentiment",
                    confidence=result.get("confidence", 0.8)
                )
                actions.append(action)
        
        # Actions from forecast agent
        if AgentType.DEMAND_FORECAST in agent_results:
            result = agent_results[AgentType.DEMAND_FORECAST]
            # Get data from nested structure
            data = result.get("data") if result.get("data") is not None else result
            if isinstance(data, dict) and 'data' in data:
                data = data['data']  # Unwrap double nesting
            
            # Extract from recommendations if available
            recommendations = data.get("recommendations", []) if isinstance(data, dict) else []
            for rec in recommendations[:3]:  # Top 3
                action = ActionItem(
                    action_id=str(uuid4()),
                    title=rec.get('title', 'Inventory action needed'),
                    description=rec.get('description', 'Review inventory levels'),
                    priority=rec.get('priority', 'medium'),
                    impact=rec.get('impact', 'high'),
                    urgency=rec.get('urgency', 'medium'),
                    source_agent="forecast",
                    confidence=rec.get("confidence", 0.8)
                )
                actions.append(action)
            
            # Also check alerts
            alerts = data.get("alerts", []) if isinstance(data, dict) else []
            for alert in alerts[:3]:  # Top 3
                action = ActionItem(
                    action_id=str(uuid4()),
                    title=alert.get("message", "Inventory action needed"),
                    description=alert.get("recommended_action", "Review inventory levels"),
                    priority="high" if alert.get("severity") in ["high", "critical"] else "medium",
                    impact="high",
                    urgency="high" if alert.get("severity") == "critical" else "medium",
                    source_agent="forecast",
                    confidence=result.get("final_confidence", 0.8)
                )
                actions.append(action)
        
        # Actions from general agent
        for agent_key in agent_results:
            if agent_key.value == 'general':
                result = agent_results[agent_key]
                data = result.get("data") if result.get("data") is not None else result
                if isinstance(data, dict) and 'data' in data:
                    data = data['data']
                analysis_type = data.get('analysis_type', '') if isinstance(data, dict) else ''
                # Surface zero-sales as a high-priority action
                zero_count = data.get('zero_sales_count', 0) if isinstance(data, dict) else 0
                if zero_count:
                    category = data.get('category', 'this category')
                    actions.append(ActionItem(
                        action_id=str(uuid4()),
                        title=f"Investigate {zero_count} zero-sales products in {category}",
                        description="These products have no recorded sales. Review pricing, listing quality, and visibility.",
                        priority="high",
                        impact="high",
                        urgency="high",
                        source_agent="general",
                        confidence=result.get("confidence", 0.9)
                    ))
                # Low inventory action
                items = data.get('items', []) if isinstance(data, dict) else []
                if analysis_type == 'inventory':
                    low_stock = [i for i in items if (i.get('inventory') or 0) < 20]
                    if low_stock:
                        actions.append(ActionItem(
                            action_id=str(uuid4()),
                            title=f"Restock {len(low_stock)} critically low inventory products",
                            description=f"Products with fewer than 20 units: {', '.join(i['sku'] for i in low_stock[:3])}{'...' if len(low_stock) > 3 else ''}",
                            priority="high",
                            impact="high",
                            urgency="high",
                            source_agent="general",
                            confidence=result.get("confidence", 0.9)
                        ))

        return actions
    
    def _prioritize_action_items(self, action_items: List[ActionItem]) -> List[ActionItem]:
        """
        Prioritize action items using impact/urgency matrix.
        
        Priority calculation:
        - High priority: high impact + high urgency
        - Medium priority: high impact OR high urgency
        - Low priority: low impact + low urgency
        """
        def priority_score(action: ActionItem) -> int:
            """Calculate priority score (higher = more important)"""
            impact_score = {"high": 3, "medium": 2, "low": 1}.get(action.impact, 1)
            urgency_score = {"high": 3, "medium": 2, "low": 1}.get(action.urgency, 1)
            priority_score = {"high": 3, "medium": 2, "low": 1}.get(action.priority, 1)
            
            return (impact_score * 2) + urgency_score + priority_score
        
        # Sort by priority score (descending)
        sorted_actions = sorted(action_items, key=priority_score, reverse=True)
        
        return sorted_actions
    
    def _calculate_overall_confidence(self, agent_results: Dict[AgentType, Dict[str, Any]]) -> float:
        """
        Calculate overall confidence from agent confidences.
        
        Uses weighted average based on number of results from each agent.
        """
        if not agent_results:
            return 0.0
        
        total_confidence = 0.0
        total_weight = 0.0
        
        for agent_type, result in agent_results.items():
            confidence = result.get("final_confidence") or result.get("confidence")
            if confidence is None:
                confidence = 0.8  # Default confidence
            weight = 1.0  # Equal weight for now
            
            total_confidence += confidence * weight
            total_weight += weight
        
        overall_confidence = total_confidence / total_weight if total_weight > 0 else 0.0
        
        return round(overall_confidence, 3)
    
    def _generate_executive_summary(
        self,
        query: str,
        insights: List[Insight],
        metrics: List[MetricWithTrend],
        risks: List[RiskAssessment],
        action_items: List[ActionItem],
        overall_confidence: float
    ) -> str:
        """Generate executive summary"""
        
        if self.synthesis_mode == SynthesisMode.ENHANCED and self.llm_engine:
            return self._generate_llm_summary(
                query, insights, metrics, risks, action_items,
                overall_confidence, agent_results=self._current_agent_results
            )
        else:
            return self._generate_rule_based_summary(query, insights, metrics, risks, action_items, overall_confidence)
    
    def _generate_rule_based_summary(
        self,
        query: str,
        insights: List[Insight],
        metrics: List[MetricWithTrend],
        risks: List[RiskAssessment],
        action_items: List[ActionItem],
        overall_confidence: float
    ) -> str:
        """Generate rule-based executive summary"""
        summary_parts = []
        
        # Opening
        summary_parts.append(f"Analysis for: {query}")
        summary_parts.append(f"\nOverall Confidence: {overall_confidence:.1%}\n")
        
        # Key findings
        if insights:
            summary_parts.append(f"Key Findings ({len(insights)}):")
            for insight in insights[:3]:  # Top 3
                summary_parts.append(f"- {insight.title}: {insight.description}")
        
        # Critical risks
        critical_risks = [r for r in risks if r.severity in [SeverityLevel.CRITICAL, SeverityLevel.HIGH]]
        if critical_risks:
            summary_parts.append(f"\nCritical Risks ({len(critical_risks)}):")
            for risk in critical_risks[:2]:  # Top 2
                summary_parts.append(f"- {risk.title}: {risk.description}")
        
        # Top actions
        if action_items:
            summary_parts.append(f"\nRecommended Actions ({len(action_items)}):")
            for action in action_items[:3]:  # Top 3
                summary_parts.append(f"- [{action.priority.upper()}] {action.title}")
        
        return "\n".join(summary_parts)
    
    def _generate_llm_summary(
        self,
        query: str,
        insights: List[Insight],
        metrics: List[MetricWithTrend],
        risks: List[RiskAssessment],
        action_items: List[ActionItem],
        overall_confidence: float,
        agent_results: Optional[Dict] = None
    ) -> str:
        """Generate LLM-powered narrative executive summary"""
        # Build a rich data summary — prefer raw agent data over abstracted insights
        if agent_results:
            data_summary = self._format_agent_data_for_llm(agent_results)
        else:
            data_summary = self._format_results_for_llm(insights, metrics, risks, action_items)

        try:
            narrative = self.llm_engine.generate_narrative_summary(
                query=query,
                data_summary=data_summary,
                overall_confidence=overall_confidence
            )
            logger.info(f"[LLM SUMMARY] narrative returned: {repr(narrative[:120]) if narrative else 'None'}")
            if narrative:
                return narrative
            logger.warning("[LLM SUMMARY] generate_narrative_summary returned None — falling back to rule-based")
        except Exception as e:
            logger.error(f"LLM narrative summary failed: {e}", exc_info=True)

        # Fallback to rule-based
        return self._generate_rule_based_summary(query, insights, metrics, risks, action_items, overall_confidence)

    def _format_agent_data_for_llm(self, agent_results: Dict) -> str:
        """Format raw agent data into a rich text block for the LLM."""
        parts = []
        for agent_type, result in agent_results.items():
            if not isinstance(result, dict):
                continue
            data = result.get("data", {})
            if not isinstance(data, dict):
                continue
            # Unwrap double-nesting (some agents wrap data.data)
            if "data" in data and isinstance(data["data"], dict):
                data = data["data"]

            agent_name = agent_type.value.upper()
            msg = data.get("message", "")
            if msg:
                parts.append(f"[{agent_name}] {msg}")

            # GENERAL / SALES — flatten items table
            items = data.get("items", [])
            for item in items[:15]:
                if isinstance(item, dict):
                    row = "  " + " | ".join(
                        f"{k}: {v}" for k, v in item.items()
                        if v not in (None, "", []) and k not in ("low_reviews", "issues")
                    )
                    if row.strip():
                        parts.append(row)

            # PRICING — price gaps
            for gap in data.get("price_gaps", [])[:10]:
                parts.append(
                    f"  Price gap: {gap.get('product_name','?')} | "
                    f"our: ₹{gap.get('our_price',0):.2f} | "
                    f"competitor: ₹{gap.get('competitor_price',0):.2f} | "
                    f"gap: {gap.get('gap_percentage',0):+.1f}%"
                )

            # SENTIMENT — product sentiments
            for ps in data.get("product_sentiments", [])[:10]:
                parts.append(
                    f"  Sentiment: {ps.get('product_name','?')} | "
                    f"score: {ps.get('average_sentiment',0):.2f} | "
                    f"reviews: {ps.get('review_count',0)} | "
                    f"positive: {ps.get('positive_percentage',0):.0f}%"
                )
            # Complaint patterns
            for cp in data.get("complaint_patterns", [])[:5]:
                parts.append(
                    f"  Complaint pattern: {cp.get('pattern','?')} | "
                    f"frequency: {cp.get('frequency',0)} | "
                    f"severity: {cp.get('severity','?')}"
                )

            # FORECAST — key numbers
            for key in ["forecasted_demand", "demand_change_pct", "supply_gap", "trend"]:
                val = data.get(key)
                if val is not None:
                    parts.append(f"  {key.replace('_',' ').title()}: {val}")

            # Top-level numeric fields (revenue, units, etc.)
            for key in ["total_revenue", "total_units", "total_orders", "overall_margin_pct",
                        "total_complaints", "overall_avg_rating", "growth_pct",
                        "aggregate_sentiment_score", "average_sentiment",
                        "positive_count", "negative_count"]:
                val = data.get(key)
                if val is not None:
                    parts.append(f"  {key.replace('_',' ').title()}: {val}")

        return "\n".join(parts) if parts else "No data available."
    
    def _format_results_for_llm(
        self,
        insights: List[Insight],
        metrics: List[MetricWithTrend],
        risks: List[RiskAssessment],
        action_items: List[ActionItem]
    ) -> str:
        """Format results for LLM input"""
        parts = []
        
        if insights:
            parts.append("Insights:")
            for insight in insights:
                parts.append(f"- {insight.title}: {insight.description}")
        
        if metrics:
            parts.append("\nMetrics:")
            for metric in metrics:
                parts.append(f"- {metric.name}: {metric.value} (trend: {metric.trend.value})")
        
        if risks:
            parts.append("\nRisks:")
            for risk in risks:
                parts.append(f"- [{risk.severity.value.upper()}] {risk.title}: {risk.description}")
        
        if action_items:
            parts.append("\nActions:")
            for action in action_items[:5]:
                parts.append(f"- [{action.priority.upper()}] {action.title}")
        
        return "\n".join(parts)
    
    def store_analytical_results(self, report: StructuredReport) -> bool:
        """
        Store analytical results in analytical database.
        
        Current Implementation: In-memory storage for demo purposes.
        Phase 2: Replace with real analytical database (TimescaleDB, ClickHouse, etc.)
        
        Args:
            report: Structured report to store
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Store in tenant-isolated in-memory storage
            if self.tenant_id not in self._analytical_storage:
                self._analytical_storage[self.tenant_id] = []
            
            self._analytical_storage[self.tenant_id].append(report)
            
            logger.info(
                f"Stored report {report.report_id} for tenant {self.tenant_id} "
                f"(total reports: {len(self._analytical_storage[self.tenant_id])})"
            )
            
            return True
        except Exception as e:
            logger.error(f"Failed to store analytical results: {e}")
            return False
    
    def get_historical_reports(
        self,
        limit: int = 10,
        query_filter: Optional[str] = None
    ) -> List[StructuredReport]:
        """
        Retrieve historical reports for this tenant.
        
        Args:
            limit: Maximum number of reports to return
            query_filter: Optional query string filter
            
        Returns:
            List of historical reports
        """
        reports = self._analytical_storage.get(self.tenant_id, [])
        
        # Filter by query if provided
        if query_filter:
            reports = [r for r in reports if query_filter.lower() in r.query.lower()]
        
        # Sort by timestamp (most recent first) and limit
        sorted_reports = sorted(reports, key=lambda r: r.timestamp or datetime.min, reverse=True)
        
        return sorted_reports[:limit]
    
    @classmethod
    def get_storage_stats(cls) -> Dict[str, Any]:
        """
        Get storage statistics across all tenants.
        
        Returns:
            Dictionary with storage stats
        """
        return {
            "total_tenants": len(cls._analytical_storage),
            "total_reports": sum(len(reports) for reports in cls._analytical_storage.values()),
            "reports_by_tenant": {
                str(tenant_id): len(reports)
                for tenant_id, reports in cls._analytical_storage.items()
            }
        }
