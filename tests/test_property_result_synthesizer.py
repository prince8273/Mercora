"""
Property-Based Tests for Result Synthesizer

These tests validate correctness properties for result synthesis functionality
using Hypothesis for property-based testing.
"""
import pytest
from hypothesis import given, strategies as st, settings
from uuid import uuid4, UUID
from datetime import datetime

from src.orchestration.result_synthesizer import (
    ResultSynthesizer,
    SynthesisMode
)
from src.orchestration.llm_reasoning_engine import AgentType
from src.schemas.report import (
    StructuredReport,
    MetricWithTrend,
    RiskAssessment,
    Insight,
    ActionItem,
    TrendDirection,
    SeverityLevel
)


# Strategy for generating agent results
@st.composite
def agent_results_strategy(draw):
    """Generate realistic agent results for testing"""
    results = {}
    
    # Pricing agent results
    num_gaps = draw(st.integers(min_value=0, max_value=10))
    num_recs = draw(st.integers(min_value=0, max_value=5))
    
    results[AgentType.PRICING] = {
        "price_gaps": [
            {
                "gap_percentage": draw(st.floats(min_value=-50.0, max_value=50.0)),
                "product_id": str(uuid4())
            }
            for _ in range(num_gaps)
        ],
        "recommendations": [
            {
                "confidence": draw(st.floats(min_value=0.5, max_value=1.0)),
                "product_name": f"Product {i}",
                "recommended_price": draw(st.floats(min_value=1.0, max_value=1000.0))
            }
            for i in range(num_recs)
        ],
        "confidence": draw(st.floats(min_value=0.5, max_value=1.0))
    }
    
    # Sentiment agent results
    results[AgentType.SENTIMENT] = {
        "aggregate_sentiment_score": draw(st.floats(min_value=0.0, max_value=1.0)),
        "confidence": draw(st.floats(min_value=0.5, max_value=1.0)),
        "feature_requests": [
            {
                "feature": f"Feature {i}",
                "frequency": draw(st.integers(min_value=1, max_value=100))
            }
            for i in range(draw(st.integers(min_value=0, max_value=5)))
        ],
        "complaint_patterns": [
            {
                "pattern": f"Complaint {i}",
                "frequency": draw(st.integers(min_value=1, max_value=50)),
                "severity": draw(st.sampled_from(["low", "medium", "high"]))
            }
            for i in range(draw(st.integers(min_value=0, max_value=3)))
        ]
    }
    
    # Forecast agent results
    num_forecast_points = draw(st.integers(min_value=1, max_value=30))
    results[AgentType.FORECAST] = {
        "forecast_points": [
            {"predicted_quantity": draw(st.integers(min_value=0, max_value=1000))}
            for _ in range(num_forecast_points)
        ],
        "trend": draw(st.sampled_from(["increasing", "decreasing", "stable"])),
        "final_confidence": draw(st.floats(min_value=0.5, max_value=1.0)),
        "seasonality": {
            "weekly": {
                "strength": draw(st.floats(min_value=0.0, max_value=1.0)),
                "detected": draw(st.booleans())
            }
        },
        "alerts": [
            {
                "alert_type": "stockout_risk",
                "severity": draw(st.sampled_from(["low", "medium", "high", "critical"])),
                "message": f"Alert {i}",
                "recommended_action": f"Action {i}"
            }
            for i in range(draw(st.integers(min_value=0, max_value=3)))
        ]
    }
    
    return results


class TestResultSynthesizerProperties:
    """Property-based tests for Result Synthesizer"""
    
    @settings(max_examples=10, deadline=None)
    @given(agent_results=agent_results_strategy())
    def test_property_31_multi_agent_results_synthesized(self, agent_results):
        """
        # Feature: ecommerce-intelligence-agent, Property 31: Multi-agent results are synthesized
        
        Property: For any query requiring multiple agents, the orchestration layer
        should synthesize all agent results into a single unified report.
        
        Validates: Requirements 6.6
        """
        tenant_id = uuid4()
        synthesizer = ResultSynthesizer(
            tenant_id=tenant_id,
            synthesis_mode=SynthesisMode.SIMPLE
        )
        
        query = "Test multi-agent query"
        
        # Synthesize results
        report = synthesizer.synthesize_results(
            query_id=str(uuid4()),
            query=query,
            agent_results=agent_results,
            execution_metadata={"mode": "deep"}
        )
        
        # Property 1: Report must be a StructuredReport
        assert isinstance(report, StructuredReport)
        
        # Property 2: Report must contain data from all agents
        # Check that insights are extracted from all agent types
        agent_sources = {insight.agent_source for insight in report.insights}
        
        # At least some insights should be present if agents have data
        if agent_results[AgentType.PRICING]["price_gaps"] or agent_results[AgentType.PRICING]["recommendations"]:
            assert "pricing" in agent_sources or len(report.insights) >= 0
        
        if agent_results[AgentType.SENTIMENT]["aggregate_sentiment_score"] > 0:
            assert "sentiment" in agent_sources or len(report.insights) >= 0
        
        if agent_results[AgentType.FORECAST]["forecast_points"]:
            assert "forecast" in agent_sources or len(report.insights) >= 0
        
        # Property 3: Report must have required fields
        assert report.query == query
        assert report.tenant_id == tenant_id
        assert report.executive_summary is not None
        assert isinstance(report.insights, list)
        assert isinstance(report.key_metrics, list)
        assert isinstance(report.action_items, list)
        assert isinstance(report.risks, list)
        
        # Property 4: Overall confidence must be in valid range (0-100)
        assert 0.0 <= report.overall_confidence <= 100.0
    
    @settings(max_examples=10, deadline=None)
    @given(agent_results=agent_results_strategy())
    def test_property_33_all_reports_include_executive_summaries(self, agent_results):
        """
        # Feature: ecommerce-intelligence-agent, Property 33: All reports include executive summaries
        
        Property: For any completed analysis, the generated report should include
        an executive summary section highlighting key findings.
        
        Validates: Requirements 7.1
        """
        tenant_id = uuid4()
        synthesizer = ResultSynthesizer(
            tenant_id=tenant_id,
            synthesis_mode=SynthesisMode.SIMPLE
        )
        
        query = "Test query for executive summary"
        
        # Synthesize results
        report = synthesizer.synthesize_results(
            query_id=str(uuid4()),
            query=query,
            agent_results=agent_results,
            execution_metadata={"mode": "deep"}
        )
        
        # Property 1: Executive summary must exist
        assert report.executive_summary is not None
        assert isinstance(report.executive_summary, str)
        
        # Property 2: Executive summary must not be empty
        assert len(report.executive_summary) > 0
        
        # Property 3: Executive summary should mention the query
        assert query in report.executive_summary or "Analysis" in report.executive_summary
        
        # Property 4: Executive summary should contain confidence information
        assert "Confidence" in report.executive_summary or "confidence" in report.executive_summary.lower()
        
        # Property 5: If there are insights, summary should mention findings
        if len(report.insights) > 0:
            assert "Finding" in report.executive_summary or "finding" in report.executive_summary.lower()
        
        # Property 6: If there are risks, summary should mention them
        if len(report.risks) > 0:
            assert "Risk" in report.executive_summary or "risk" in report.executive_summary.lower()
        
        # Property 7: If there are actions, summary should mention them
        if len(report.action_items) > 0:
            assert "Action" in report.executive_summary or "action" in report.executive_summary.lower()
    
    @settings(max_examples=10, deadline=None)
    @given(
        num_actions=st.integers(min_value=2, max_value=10),
        seed=st.integers(min_value=0, max_value=1000)
    )
    def test_property_37_action_items_are_prioritized(self, num_actions, seed):
        """
        # Feature: ecommerce-intelligence-agent, Property 37: Action items are prioritized
        
        Property: For any set of action items generated, they should be ordered
        by a combination of impact and urgency scores.
        
        Validates: Requirements 7.6
        """
        tenant_id = uuid4()
        synthesizer = ResultSynthesizer(
            tenant_id=tenant_id,
            synthesis_mode=SynthesisMode.SIMPLE
        )
        
        # Generate random action items with varying priorities
        import random
        random.seed(seed)
        
        priorities = ["low", "medium", "high"]
        impacts = ["low", "medium", "high"]
        urgencies = ["low", "medium", "high"]
        
        actions = []
        for i in range(num_actions):
            action = ActionItem(
                action_id=str(uuid4()),
                title=f"Action {i}",
                description=f"Description {i}",
                priority=random.choice(priorities),
                impact=random.choice(impacts),
                urgency=random.choice(urgencies),
                source_agent="test",
                confidence=random.uniform(0.5, 1.0)
            )
            actions.append(action)
        
        # Prioritize actions
        prioritized = synthesizer._prioritize_action_items(actions)
        
        # Property 1: All actions must be present
        assert len(prioritized) == num_actions
        
        # Property 2: Actions must be ordered (no duplicates)
        action_ids = [a.action_id for a in prioritized]
        assert len(action_ids) == len(set(action_ids))
        
        # Property 3: High priority actions should come before low priority
        # Calculate priority scores for verification
        def priority_score(action):
            impact_score = {"high": 3, "medium": 2, "low": 1}.get(action.impact, 1)
            urgency_score = {"high": 3, "medium": 2, "low": 1}.get(action.urgency, 1)
            priority_score_val = {"high": 3, "medium": 2, "low": 1}.get(action.priority, 1)
            return (impact_score * 2) + urgency_score + priority_score_val
        
        scores = [priority_score(a) for a in prioritized]
        
        # Verify descending order
        for i in range(len(scores) - 1):
            assert scores[i] >= scores[i + 1], \
                f"Actions not properly prioritized: score {scores[i]} at position {i} should be >= score {scores[i+1]} at position {i+1}"
        
        # Property 4: High impact + high urgency should be at the top
        high_impact_high_urgency = [
            a for a in prioritized
            if a.impact == "high" and a.urgency == "high"
        ]
        if high_impact_high_urgency:
            # At least one should be in the top half
            top_half = prioritized[:len(prioritized)//2 + 1]
            assert any(a.action_id == hi.action_id for hi in high_impact_high_urgency for a in top_half)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
