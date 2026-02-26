"""
Tests for Result Synthesizer

These tests verify the Result Synthesizer functionality including:
- Multi-agent result synthesis
- Insight extraction
- Metric extraction
- Risk identification
- Action item generation and prioritization
- Executive summary generation
- Overall confidence calculation
"""
import pytest
from uuid import uuid4
from unittest.mock import Mock, patch, MagicMock

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


class TestResultSynthesizer:
    """Tests for ResultSynthesizer"""
    
    def test_synthesizer_initialization(self):
        """Test ResultSynthesizer initializes correctly"""
        tenant_id = uuid4()
        
        synthesizer = ResultSynthesizer(
            tenant_id=tenant_id,
            synthesis_mode=SynthesisMode.SIMPLE
        )
        
        assert synthesizer.tenant_id == tenant_id
        assert synthesizer.synthesis_mode == SynthesisMode.SIMPLE
        assert synthesizer.llm_engine is None
    
    def test_synthesizer_with_llm(self):
        """Test ResultSynthesizer with LLM engine"""
        tenant_id = uuid4()
        
        with patch('src.orchestration.result_synthesizer.LLMReasoningEngine'):
            mock_llm = Mock()
            synthesizer = ResultSynthesizer(
                tenant_id=tenant_id,
                llm_engine=mock_llm,
                synthesis_mode=SynthesisMode.ENHANCED
            )
            
            assert synthesizer.llm_engine == mock_llm
            assert synthesizer.synthesis_mode == SynthesisMode.ENHANCED
    
    def test_extract_pricing_insights(self):
        """Test extracting insights from pricing agent results"""
        tenant_id = uuid4()
        synthesizer = ResultSynthesizer(tenant_id=tenant_id)
        
        pricing_result = {
            "price_gaps": [
                {"gap_percentage": 15.0, "product_id": str(uuid4())},
                {"gap_percentage": 12.0, "product_id": str(uuid4())},
            ],
            "recommendations": [
                {"confidence": 0.85, "product_name": "Product A"},
                {"confidence": 0.90, "product_name": "Product B"},
            ]
        }
        
        insights = synthesizer._extract_pricing_insights(pricing_result, "pricing")
        
        assert len(insights) == 2
        assert any("Price Gaps" in i.title for i in insights)
        assert any("Recommendations" in i.title for i in insights)
        assert all(i.agent_source == "pricing" for i in insights)
    
    def test_extract_sentiment_insights(self):
        """Test extracting insights from sentiment agent results"""
        tenant_id = uuid4()
        synthesizer = ResultSynthesizer(tenant_id=tenant_id)
        
        sentiment_result = {
            "aggregate_sentiment_score": 0.72,
            "confidence": 0.85,
            "feature_requests": [
                {"feature": "Dark mode", "frequency": 50},
                {"feature": "Export feature", "frequency": 30},
            ],
            "complaint_patterns": [
                {"pattern": "Slow performance", "severity": "high", "frequency": 20}
            ]
        }
        
        insights = synthesizer._extract_sentiment_insights(sentiment_result, "sentiment")
        
        assert len(insights) == 3
        assert any("Sentiment" in i.title for i in insights)
        assert any("Feature Requests" in i.title for i in insights)
        assert any("Complaints" in i.title for i in insights)
    
    def test_extract_forecast_insights(self):
        """Test extracting insights from forecast agent results"""
        tenant_id = uuid4()
        synthesizer = ResultSynthesizer(tenant_id=tenant_id)
        
        forecast_result = {
            "trend": "increasing",
            "final_confidence": 0.88,
            "seasonality": {
                "weekly": {"strength": 0.8, "detected": True},
                "monthly": {"strength": 0.75, "detected": True}
            },
            "alerts": [
                {"alert_type": "stockout_risk", "severity": "high"},
                {"alert_type": "stockout_risk", "severity": "critical"}
            ]
        }
        
        insights = synthesizer._extract_forecast_insights(forecast_result, "forecast")
        
        assert len(insights) == 3
        assert any("Trend" in i.title for i in insights)
        assert any("Seasonal" in i.title for i in insights)
        assert any("Inventory Alerts" in i.title for i in insights)
    
    def test_extract_metrics(self):
        """Test extracting metrics from agent results"""
        tenant_id = uuid4()
        synthesizer = ResultSynthesizer(tenant_id=tenant_id)
        
        agent_results = {
            AgentType.PRICING: {
                "price_gaps": [
                    {"gap_percentage": 10.0},
                    {"gap_percentage": 15.0},
                    {"gap_percentage": 20.0}
                ]
            },
            AgentType.SENTIMENT: {
                "aggregate_sentiment_score": 0.72,
                "confidence": 0.85
            },
            AgentType.FORECAST: {
                "forecast_points": [
                    {"predicted_quantity": 100},
                    {"predicted_quantity": 120},
                    {"predicted_quantity": 110}
                ],
                "trend": "increasing",
                "final_confidence": 0.88
            }
        }
        
        metrics = synthesizer._extract_metrics(agent_results)
        
        assert len(metrics) == 3
        assert any("Price Gap" in m.name for m in metrics)
        assert any("Sentiment" in m.name for m in metrics)
        assert any("Demand" in m.name for m in metrics)
        assert all(isinstance(m, MetricWithTrend) for m in metrics)
    
    def test_identify_risks(self):
        """Test identifying risks from agent results"""
        tenant_id = uuid4()
        synthesizer = ResultSynthesizer(tenant_id=tenant_id)
        
        agent_results = {
            AgentType.PRICING: {
                "price_gaps": [
                    {"gap_percentage": 25.0},  # >20% overpriced
                    {"gap_percentage": 22.0}
                ]
            },
            AgentType.SENTIMENT: {
                "aggregate_sentiment_score": 0.35  # <0.4 low sentiment
            },
            AgentType.FORECAST: {
                "alerts": [
                    {"alert_type": "stockout_risk", "severity": "critical"}
                ]
            }
        }
        
        risks = synthesizer._identify_risks(agent_results)
        
        assert len(risks) == 3
        assert any("Price Competitiveness" in r.title for r in risks)
        assert any("Customer Satisfaction" in r.title for r in risks)
        assert any("Stockout" in r.title for r in risks)
        assert all(isinstance(r, RiskAssessment) for r in risks)
    
    def test_generate_action_items(self):
        """Test generating action items from results"""
        tenant_id = uuid4()
        synthesizer = ResultSynthesizer(tenant_id=tenant_id)
        
        agent_results = {
            AgentType.PRICING: {
                "recommendations": [
                    {
                        "product_name": "Product A",
                        "recommended_price": 29.99,
                        "confidence": 0.85
                    }
                ]
            },
            AgentType.SENTIMENT: {
                "complaint_patterns": [
                    {
                        "pattern": "Quality issues",
                        "frequency": 50,
                        "severity": "high"
                    }
                ]
            },
            AgentType.FORECAST: {
                "alerts": [
                    {
                        "message": "Stockout risk for Product B",
                        "recommended_action": "Increase inventory",
                        "severity": "critical"
                    }
                ]
            }
        }
        
        insights = []
        risks = []
        
        actions = synthesizer._generate_action_items(agent_results, insights, risks)
        
        assert len(actions) == 3
        assert any("price" in a.title.lower() for a in actions)
        assert any("complaint" in a.title.lower() for a in actions)
        assert any(a.source_agent == "pricing" for a in actions)
        assert any(a.source_agent == "sentiment" for a in actions)
        assert any(a.source_agent == "forecast" for a in actions)
    
    def test_prioritize_action_items(self):
        """Test action item prioritization"""
        tenant_id = uuid4()
        synthesizer = ResultSynthesizer(tenant_id=tenant_id)
        
        actions = [
            ActionItem(
                action_id=str(uuid4()),
                title="Low priority action",
                description="Test",
                priority="low",
                impact="low",
                urgency="low",
                source_agent="test",
                confidence=0.7
            ),
            ActionItem(
                action_id=str(uuid4()),
                title="High priority action",
                description="Test",
                priority="high",
                impact="high",
                urgency="high",
                source_agent="test",
                confidence=0.9
            ),
            ActionItem(
                action_id=str(uuid4()),
                title="Medium priority action",
                description="Test",
                priority="medium",
                impact="medium",
                urgency="medium",
                source_agent="test",
                confidence=0.8
            )
        ]
        
        prioritized = synthesizer._prioritize_action_items(actions)
        
        assert len(prioritized) == 3
        assert prioritized[0].priority == "high"
        assert prioritized[-1].priority == "low"
    
    def test_calculate_overall_confidence(self):
        """Test overall confidence calculation"""
        tenant_id = uuid4()
        synthesizer = ResultSynthesizer(tenant_id=tenant_id)
        
        agent_results = {
            AgentType.PRICING: {"confidence": 0.85},
            AgentType.SENTIMENT: {"final_confidence": 0.80},
            AgentType.FORECAST: {"final_confidence": 0.90}
        }
        
        confidence = synthesizer._calculate_overall_confidence(agent_results)
        
        assert 0.0 <= confidence <= 1.0
        assert confidence == pytest.approx(0.85, abs=0.01)  # Average of 0.85, 0.80, 0.90
    
    def test_calculate_overall_confidence_empty(self):
        """Test overall confidence with no results"""
        tenant_id = uuid4()
        synthesizer = ResultSynthesizer(tenant_id=tenant_id)
        
        confidence = synthesizer._calculate_overall_confidence({})
        
        assert confidence == 0.0
    
    def test_generate_rule_based_summary(self):
        """Test rule-based executive summary generation"""
        tenant_id = uuid4()
        synthesizer = ResultSynthesizer(tenant_id=tenant_id, synthesis_mode=SynthesisMode.SIMPLE)
        
        query = "Analyze product performance"
        insights = [
            Insight(
                insight_id=str(uuid4()),
                title="Test Insight",
                description="Test description",
                category="test",
                agent_source="test",
                confidence=0.9,
                supporting_evidence=[]
            )
        ]
        metrics = []
        risks = [
            RiskAssessment(
                risk_id=str(uuid4()),
                title="Test Risk",
                description="Test risk description",
                severity=SeverityLevel.HIGH,
                impact="High impact",
                likelihood="High",
                confidence=0.85
            )
        ]
        actions = [
            ActionItem(
                action_id=str(uuid4()),
                title="Test Action",
                description="Test",
                priority="high",
                impact="high",
                urgency="high",
                source_agent="test",
                confidence=0.9
            )
        ]
        
        summary = synthesizer._generate_rule_based_summary(
            query, insights, metrics, risks, actions, 0.85
        )
        
        assert "Analyze product performance" in summary
        assert "85.0%" in summary or "0.85" in summary
        assert "Test Insight" in summary
        assert "Test Risk" in summary
        assert "Test Action" in summary
    
    def test_synthesize_results_complete(self):
        """Test complete result synthesis"""
        tenant_id = uuid4()
        synthesizer = ResultSynthesizer(tenant_id=tenant_id, synthesis_mode=SynthesisMode.SIMPLE)
        
        query = "Analyze product performance"
        
        agent_results = {
            AgentType.PRICING: {
                "price_gaps": [{"gap_percentage": 15.0}],
                "recommendations": [{"confidence": 0.85, "product_name": "Product A", "recommended_price": 29.99}],
                "confidence": 0.85
            },
            AgentType.SENTIMENT: {
                "aggregate_sentiment_score": 0.72,
                "confidence": 0.80,
                "feature_requests": [],
                "complaint_patterns": []
            },
            AgentType.FORECAST: {
                "forecast_points": [{"predicted_quantity": 100}],
                "trend": "increasing",
                "final_confidence": 0.88,
                "seasonality": {},
                "alerts": []
            }
        }
        
        execution_metadata = {
            "execution_time": 45.2,
            "mode": "deep"
        }
        
        report = synthesizer.synthesize_results(
            query_id="test-query-123",
            query=query,
            agent_results=agent_results,
            execution_metadata=execution_metadata
        )
        
        assert isinstance(report, StructuredReport)
        assert report.query == query
        assert report.tenant_id == tenant_id
        assert len(report.insights) > 0
        assert len(report.key_metrics) > 0
        assert len(report.action_items) > 0
        assert 0.0 <= report.overall_confidence <= 100.0
        assert report.executive_summary
    
    def test_extract_warnings(self):
        """Test extracting data quality warnings"""
        tenant_id = uuid4()
        synthesizer = ResultSynthesizer(tenant_id=tenant_id)
        
        agent_results = {
            AgentType.PRICING: {
                "data_quality_score": 0.65,  # <0.8
                "qa_metadata": {}
            },
            AgentType.SENTIMENT: {
                "data_quality_score": 0.55,  # <0.6
                "qa_metadata": {}
            }
        }
        
        warnings = synthesizer._extract_warnings(agent_results)
        
        assert len(warnings) == 2
        assert any("pricing" in w.affected_data for w in warnings)
        assert any("sentiment" in w.affected_data for w in warnings)
    
    def test_store_analytical_results(self):
        """Test storing analytical results"""
        tenant_id = uuid4()
        synthesizer = ResultSynthesizer(tenant_id=tenant_id)
        
        report = StructuredReport(
            report_id=uuid4(),
            tenant_id=tenant_id,
            query="Test query",
            executive_summary="Test summary",
            overall_confidence=85.0
        )
        
        result = synthesizer.store_analytical_results(report)
        
        # Currently returns True (placeholder)
        assert result is True


class TestSynthesisIntegration:
    """Integration tests for Result Synthesizer"""
    
    def test_multi_agent_synthesis(self):
        """Test synthesizing results from multiple agents"""
        tenant_id = uuid4()
        synthesizer = ResultSynthesizer(tenant_id=tenant_id, synthesis_mode=SynthesisMode.SIMPLE)
        
        # Simulate results from all three agents
        agent_results = {
            AgentType.PRICING: {
                "price_gaps": [
                    {"gap_percentage": 15.0, "product_id": str(uuid4())},
                    {"gap_percentage": 25.0, "product_id": str(uuid4())}
                ],
                "recommendations": [
                    {"confidence": 0.90, "product_name": "Product A", "recommended_price": 29.99}
                ],
                "confidence": 0.85
            },
            AgentType.SENTIMENT: {
                "aggregate_sentiment_score": 0.35,  # Low sentiment
                "confidence": 0.80,
                "feature_requests": [
                    {"feature": "Dark mode", "frequency": 50}
                ],
                "complaint_patterns": [
                    {"pattern": "Quality issues", "frequency": 30, "severity": "high"}
                ]
            },
            AgentType.FORECAST: {
                "forecast_points": [
                    {"predicted_quantity": 100},
                    {"predicted_quantity": 120}
                ],
                "trend": "increasing",
                "final_confidence": 0.88,
                "seasonality": {
                    "weekly": {"strength": 0.8, "detected": True}
                },
                "alerts": [
                    {
                        "alert_type": "stockout_risk",
                        "severity": "critical",
                        "message": "Stockout risk",
                        "recommended_action": "Increase inventory"
                    }
                ]
            }
        }
        
        report = synthesizer.synthesize_results(
            query_id="integration-test",
            query="Comprehensive product analysis",
            agent_results=agent_results,
            execution_metadata={"mode": "deep"}
        )
        
        # Verify report structure
        assert isinstance(report, StructuredReport)
        assert report.query == "Comprehensive product analysis"
        
        # Verify insights from all agents
        assert len(report.insights) >= 3
        pricing_insights = [i for i in report.insights if i.agent_source == "pricing"]
        sentiment_insights = [i for i in report.insights if i.agent_source == "sentiment"]
        forecast_insights = [i for i in report.insights if i.agent_source == "forecast"]
        assert len(pricing_insights) > 0
        assert len(sentiment_insights) > 0
        assert len(forecast_insights) > 0
        
        # Verify metrics from all agents
        assert len(report.key_metrics) == 3
        
        # Verify risks identified
        assert len(report.risks) >= 3
        
        # Verify action items generated
        assert len(report.action_items) >= 3
        
        # Verify overall confidence (0-100 scale)
        assert 70.0 <= report.overall_confidence <= 90.0
        
        # Verify executive summary
        assert len(report.executive_summary) > 100
        assert "Comprehensive product analysis" in report.executive_summary


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
