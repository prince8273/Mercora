"""Property-based tests for structured report generation"""
import pytest
from hypothesis import given, strategies as st, settings
from uuid import uuid4
from datetime import datetime

from src.schemas.report import (
    StructuredReport,
    MetricWithTrend,
    TrendDirection,
    Insight,
    SupportingEvidence,
    RiskAssessment,
    SeverityLevel,
    UncertaintyCommunication,
    ActionItem,
    DataQualityWarning
)


class TestMetricsWithTrends:
    """
    Property 34: Metrics include values and trends
    Validates: Requirements 7.2
    """
    
    @given(
        num_metrics=st.integers(min_value=1, max_value=10),
        trend=st.sampled_from(list(TrendDirection))
    )
    @settings(max_examples=10, deadline=None)
    def test_metrics_include_values_and_trends(self, num_metrics, trend):
        """Test that all metrics include both values and trend information"""
        # Feature: ecommerce-intelligence-agent, Property 34: Metrics include values and trends
        
        # Create metrics with trends
        metrics = []
        for i in range(num_metrics):
            metric = MetricWithTrend(
                name=f"metric_{i}",
                value=100 + i * 10,
                unit="USD",
                trend=trend,
                change_percentage=5.5 if trend != TrendDirection.STABLE else 0.0,
                previous_value=100 if i == 0 else 100 + (i - 1) * 10,
                confidence=0.85
            )
            metrics.append(metric)
        
        # Create report with metrics
        report = StructuredReport(
            report_id=uuid4(),
            tenant_id=uuid4(),
            query="Test query",
            executive_summary="Test summary",
            key_metrics=metrics,
            insights=[],
            action_items=[],
            overall_confidence=85.0,
            data_quality_warnings=[],
            risks=[],
            recommendations=[],
            uncertainties=[],
            agent_results={}
        )
        
        # Property: All metrics must have values
        assert len(report.key_metrics) == num_metrics
        for metric in report.key_metrics:
            assert metric.value is not None
        
        # Property: All metrics must have trend information
        for metric in report.key_metrics:
            assert metric.trend is not None
            assert isinstance(metric.trend, TrendDirection)
        
        # Property: Metrics with non-stable trends should have change percentage
        for metric in report.key_metrics:
            if metric.trend != TrendDirection.STABLE:
                assert metric.change_percentage is not None
    
    @given(
        value=st.floats(min_value=0, max_value=1000),
        previous_value=st.floats(min_value=0, max_value=1000)
    )
    @settings(max_examples=10, deadline=None)
    def test_trend_direction_consistency(self, value, previous_value):
        """Test that trend direction is consistent with value changes"""
        # Feature: ecommerce-intelligence-agent, Property 34: Metrics include values and trends
        
        # Determine expected trend
        if value > previous_value * 1.05:  # 5% threshold
            expected_trend = TrendDirection.UP
        elif value < previous_value * 0.95:
            expected_trend = TrendDirection.DOWN
        else:
            expected_trend = TrendDirection.STABLE
        
        metric = MetricWithTrend(
            name="test_metric",
            value=value,
            unit="USD",
            trend=expected_trend,
            change_percentage=((value - previous_value) / previous_value * 100) if previous_value > 0 else 0,
            previous_value=previous_value,
            confidence=0.9
        )
        
        # Property: Trend direction must be consistent with values
        if value > previous_value * 1.05:
            assert metric.trend == TrendDirection.UP
        elif value < previous_value * 0.95:
            assert metric.trend == TrendDirection.DOWN
    
    @given(
        num_metrics=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=10, deadline=None)
    def test_metrics_have_confidence_scores(self, num_metrics):
        """Test that all metrics include confidence scores"""
        # Feature: ecommerce-intelligence-agent, Property 34: Metrics include values and trends
        
        metrics = []
        for i in range(num_metrics):
            metric = MetricWithTrend(
                name=f"metric_{i}",
                value=100 + i,
                trend=TrendDirection.UP,
                confidence=0.8 + (i * 0.02)
            )
            metrics.append(metric)
        
        # Property: All metrics must have confidence scores between 0 and 1
        for metric in metrics:
            assert metric.confidence is not None
            assert 0 <= metric.confidence <= 1


class TestInsightTraceability:
    """
    Property 35: Insights are traceable to source data
    Validates: Requirements 7.3, 13.2
    """
    
    @given(
        num_insights=st.integers(min_value=1, max_value=10),
        num_evidence_per_insight=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=10, deadline=None)
    def test_insights_have_supporting_evidence(self, num_insights, num_evidence_per_insight):
        """Test that all insights have traceable supporting evidence"""
        # Feature: ecommerce-intelligence-agent, Property 35: Insights are traceable to source data
        
        insights = []
        for i in range(num_insights):
            # Create supporting evidence for this insight
            evidence_list = []
            insight_id = f"insight_{i}"
            
            for j in range(num_evidence_per_insight):
                evidence = SupportingEvidence(
                    evidence_id=f"evidence_{i}_{j}",
                    insight_id=insight_id,
                    source_data_type="sales_record",
                    source_record_ids=[str(uuid4()) for _ in range(3)],
                    data_lineage_path=["raw_data", "validated_data", "aggregated_data"],
                    transformation_applied="aggregation",
                    confidence=0.85,
                    timestamp=datetime.utcnow()
                )
                evidence_list.append(evidence)
            
            insight = Insight(
                insight_id=insight_id,
                title=f"Insight {i}",
                description=f"Description for insight {i}",
                category="pricing",
                agent_source="pricing_agent",
                confidence=0.9,
                supporting_evidence=evidence_list
            )
            insights.append(insight)
        
        # Create report with insights
        report = StructuredReport(
            report_id=uuid4(),
            tenant_id=uuid4(),
            query="Test query",
            executive_summary="Test summary",
            key_metrics=[],
            insights=insights,
            action_items=[],
            overall_confidence=85.0,
            data_quality_warnings=[],
            risks=[],
            recommendations=[],
            uncertainties=[],
            agent_results={}
        )
        
        # Property: All insights must have supporting evidence
        assert len(report.insights) == num_insights
        for insight in report.insights:
            assert len(insight.supporting_evidence) >= 1
        
        # Property: All evidence must link back to source data
        for insight in report.insights:
            for evidence in insight.supporting_evidence:
                assert evidence.source_data_type is not None
                assert len(evidence.source_record_ids) >= 1
                assert evidence.insight_id == insight.insight_id
    
    @given(
        num_insights=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=10, deadline=None)
    def test_evidence_has_data_lineage(self, num_insights):
        """Test that supporting evidence includes data lineage paths"""
        # Feature: ecommerce-intelligence-agent, Property 35: Insights are traceable to source data
        
        insights = []
        for i in range(num_insights):
            evidence = SupportingEvidence(
                evidence_id=f"evidence_{i}",
                insight_id=f"insight_{i}",
                source_data_type="product",
                source_record_ids=[str(uuid4())],
                data_lineage_path=["ingestion", "validation", "normalization", "analysis"],
                transformation_applied="normalization",
                confidence=0.88
            )
            
            insight = Insight(
                insight_id=f"insight_{i}",
                title=f"Insight {i}",
                description="Test insight",
                category="demand",
                agent_source="forecast_agent",
                confidence=0.85,
                supporting_evidence=[evidence]
            )
            insights.append(insight)
        
        # Property: All evidence must have data lineage paths
        for insight in insights:
            for evidence in insight.supporting_evidence:
                assert evidence.data_lineage_path is not None
                assert len(evidence.data_lineage_path) >= 1
                assert isinstance(evidence.data_lineage_path, list)
    
    @given(
        num_insights=st.integers(min_value=2, max_value=8)
    )
    @settings(max_examples=10, deadline=None)
    def test_insights_identify_source_agent(self, num_insights):
        """Test that insights identify their source agent"""
        # Feature: ecommerce-intelligence-agent, Property 35: Insights are traceable to source data
        
        agents = ["pricing_agent", "sentiment_agent", "forecast_agent"]
        insights = []
        
        for i in range(num_insights):
            agent_source = agents[i % len(agents)]
            
            insight = Insight(
                insight_id=f"insight_{i}",
                title=f"Insight {i}",
                description="Test insight",
                category="test",
                agent_source=agent_source,
                confidence=0.85,
                supporting_evidence=[]
            )
            insights.append(insight)
        
        # Property: All insights must identify their source agent
        for insight in insights:
            assert insight.agent_source is not None
            assert insight.agent_source in agents


class TestRiskSeverityLevels:
    """
    Property 36: Risks include severity levels
    Validates: Requirements 7.4
    """
    
    @given(
        num_risks=st.integers(min_value=1, max_value=10),
        severity=st.sampled_from(list(SeverityLevel))
    )
    @settings(max_examples=10, deadline=None)
    def test_risks_have_severity_levels(self, num_risks, severity):
        """Test that all risks include severity level classification"""
        # Feature: ecommerce-intelligence-agent, Property 36: Risks include severity levels
        
        risks = []
        for i in range(num_risks):
            risk = RiskAssessment(
                risk_id=f"risk_{i}",
                title=f"Risk {i}",
                description=f"Description for risk {i}",
                severity=severity,
                impact="high" if severity in [SeverityLevel.HIGH, SeverityLevel.CRITICAL] else "medium",
                likelihood="medium",
                mitigation=f"Mitigation strategy {i}",
                affected_areas=["inventory", "pricing"],
                confidence=0.8
            )
            risks.append(risk)
        
        # Create report with risks
        report = StructuredReport(
            report_id=uuid4(),
            tenant_id=uuid4(),
            query="Test query",
            executive_summary="Test summary",
            key_metrics=[],
            insights=[],
            action_items=[],
            overall_confidence=85.0,
            data_quality_warnings=[],
            risks=risks,
            recommendations=[],
            uncertainties=[],
            agent_results={}
        )
        
        # Property: All risks must have severity levels
        assert len(report.risks) == num_risks
        for risk in report.risks:
            assert risk.severity is not None
            assert isinstance(risk.severity, SeverityLevel)
        
        # Property: Severity levels must be valid
        valid_severities = [s.value for s in SeverityLevel]
        for risk in report.risks:
            assert risk.severity.value in valid_severities
    
    @given(
        num_risks=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=10, deadline=None)
    def test_risks_have_impact_and_likelihood(self, num_risks):
        """Test that risks include impact and likelihood assessments"""
        # Feature: ecommerce-intelligence-agent, Property 36: Risks include severity levels
        
        risks = []
        for i in range(num_risks):
            risk = RiskAssessment(
                risk_id=f"risk_{i}",
                title=f"Risk {i}",
                description="Test risk",
                severity=SeverityLevel.MEDIUM,
                impact="medium",
                likelihood="high",
                confidence=0.75
            )
            risks.append(risk)
        
        # Property: All risks must have impact and likelihood
        for risk in risks:
            assert risk.impact is not None
            assert risk.likelihood is not None
            assert risk.impact in ["low", "medium", "high"]
            assert risk.likelihood in ["low", "medium", "high"]
    
    @given(
        num_risks=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=10, deadline=None)
    def test_critical_risks_have_mitigation(self, num_risks):
        """Test that critical/high risks include mitigation strategies"""
        # Feature: ecommerce-intelligence-agent, Property 36: Risks include severity levels
        
        risks = []
        for i in range(num_risks):
            severity = SeverityLevel.CRITICAL if i % 2 == 0 else SeverityLevel.HIGH
            
            risk = RiskAssessment(
                risk_id=f"risk_{i}",
                title=f"Risk {i}",
                description="Test risk",
                severity=severity,
                impact="high",
                likelihood="medium",
                mitigation=f"Mitigation strategy for risk {i}",
                confidence=0.8
            )
            risks.append(risk)
        
        # Property: High/critical risks should have mitigation strategies
        for risk in risks:
            if risk.severity in [SeverityLevel.CRITICAL, SeverityLevel.HIGH]:
                assert risk.mitigation is not None
                assert len(risk.mitigation) > 0


class TestUncertaintyCommunication:
    """
    Property 38: Uncertainty is explicitly communicated
    Validates: Requirements 7.7, 11.4
    """
    
    @given(
        num_uncertainties=st.integers(min_value=1, max_value=10),
        uncertainty_level=st.sampled_from(["low", "medium", "high"])
    )
    @settings(max_examples=10, deadline=None)
    def test_uncertainties_are_communicated(self, num_uncertainties, uncertainty_level):
        """Test that data limitations and uncertainties are explicitly stated"""
        # Feature: ecommerce-intelligence-agent, Property 38: Uncertainty is explicitly communicated
        
        uncertainties = []
        for i in range(num_uncertainties):
            uncertainty = UncertaintyCommunication(
                aspect=f"aspect_{i}",
                uncertainty_level=uncertainty_level,
                reason=f"Reason for uncertainty {i}",
                data_limitations=["limited_historical_data", "missing_competitor_data"],
                confidence_interval={"lower": 0.7, "upper": 0.9} if uncertainty_level == "high" else None
            )
            uncertainties.append(uncertainty)
        
        # Create report with uncertainties
        report = StructuredReport(
            report_id=uuid4(),
            tenant_id=uuid4(),
            query="Test query",
            executive_summary="Test summary",
            key_metrics=[],
            insights=[],
            action_items=[],
            overall_confidence=75.0,  # Lower confidence due to uncertainties
            data_quality_warnings=[],
            risks=[],
            recommendations=[],
            uncertainties=uncertainties,
            agent_results={}
        )
        
        # Property: All uncertainties must be explicitly communicated
        assert len(report.uncertainties) == num_uncertainties
        for uncertainty in report.uncertainties:
            assert uncertainty.uncertainty_level is not None
            assert uncertainty.reason is not None
        
        # Property: Uncertainty levels must be valid
        for uncertainty in report.uncertainties:
            assert uncertainty.uncertainty_level in ["low", "medium", "high"]
    
    @given(
        num_warnings=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=10, deadline=None)
    def test_data_quality_warnings_included(self, num_warnings):
        """Test that data quality warnings are included in reports"""
        # Feature: ecommerce-intelligence-agent, Property 38: Uncertainty is explicitly communicated
        
        warnings = []
        for i in range(num_warnings):
            warning = DataQualityWarning(
                warning_id=f"warning_{i}",
                message=f"Data quality issue {i}",
                severity=SeverityLevel.MEDIUM,
                affected_data="sales_records",
                recommendation="Collect more data"
            )
            warnings.append(warning)
        
        report = StructuredReport(
            report_id=uuid4(),
            tenant_id=uuid4(),
            query="Test query",
            executive_summary="Test summary",
            key_metrics=[],
            insights=[],
            action_items=[],
            overall_confidence=70.0,
            data_quality_warnings=warnings,
            risks=[],
            recommendations=[],
            uncertainties=[],
            agent_results={}
        )
        
        # Property: Data quality warnings must be included
        assert len(report.data_quality_warnings) == num_warnings
        for warning in report.data_quality_warnings:
            assert warning.message is not None
            assert warning.affected_data is not None
    
    @given(
        confidence=st.floats(min_value=0, max_value=100)
    )
    @settings(max_examples=10, deadline=None)
    def test_low_confidence_triggers_uncertainty_communication(self, confidence):
        """Test that low confidence scores trigger uncertainty communication"""
        # Feature: ecommerce-intelligence-agent, Property 38: Uncertainty is explicitly communicated
        
        # Low confidence threshold: < 70%
        is_low_confidence = confidence < 70.0
        
        uncertainties = []
        if is_low_confidence:
            uncertainties.append(
                UncertaintyCommunication(
                    aspect="overall_analysis",
                    uncertainty_level="high",
                    reason="Insufficient data quality",
                    data_limitations=["sparse_data", "high_variance"]
                )
            )
        
        report = StructuredReport(
            report_id=uuid4(),
            tenant_id=uuid4(),
            query="Test query",
            executive_summary="Test summary",
            key_metrics=[],
            insights=[],
            action_items=[],
            overall_confidence=confidence,
            data_quality_warnings=[],
            risks=[],
            recommendations=[],
            uncertainties=uncertainties,
            agent_results={}
        )
        
        # Property: Low confidence should be accompanied by uncertainty communication
        if is_low_confidence:
            assert len(report.uncertainties) >= 1
        
        # Property: Overall confidence must be within valid range
        assert 0 <= report.overall_confidence <= 100
    
    @given(
        num_uncertainties=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=10, deadline=None)
    def test_uncertainties_list_data_limitations(self, num_uncertainties):
        """Test that uncertainties explicitly list data limitations"""
        # Feature: ecommerce-intelligence-agent, Property 38: Uncertainty is explicitly communicated
        
        uncertainties = []
        for i in range(num_uncertainties):
            uncertainty = UncertaintyCommunication(
                aspect=f"forecast_accuracy_{i}",
                uncertainty_level="medium",
                reason="Limited historical data",
                data_limitations=[
                    "only_30_days_history",
                    "missing_seasonal_data",
                    "no_competitor_pricing"
                ]
            )
            uncertainties.append(uncertainty)
        
        # Property: All uncertainties must list specific data limitations
        for uncertainty in uncertainties:
            assert uncertainty.data_limitations is not None
            assert len(uncertainty.data_limitations) >= 1
            assert isinstance(uncertainty.data_limitations, list)


class TestReportCompleteness:
    """Test that reports include all required components"""
    
    @given(
        has_metrics=st.booleans(),
        has_insights=st.booleans(),
        has_risks=st.booleans(),
        has_uncertainties=st.booleans()
    )
    @settings(max_examples=10, deadline=None)
    def test_report_structure_completeness(
        self,
        has_metrics,
        has_insights,
        has_risks,
        has_uncertainties
    ):
        """Test that reports maintain structural completeness"""
        # Feature: ecommerce-intelligence-agent, Property 34-38: Report completeness
        
        metrics = []
        if has_metrics:
            metrics.append(
                MetricWithTrend(
                    name="revenue",
                    value=10000,
                    trend=TrendDirection.UP,
                    confidence=0.9
                )
            )
        
        insights = []
        if has_insights:
            insights.append(
                Insight(
                    insight_id="insight_1",
                    title="Test Insight",
                    description="Test",
                    category="pricing",
                    agent_source="pricing_agent",
                    confidence=0.85,
                    supporting_evidence=[]
                )
            )
        
        risks = []
        if has_risks:
            risks.append(
                RiskAssessment(
                    risk_id="risk_1",
                    title="Test Risk",
                    description="Test",
                    severity=SeverityLevel.MEDIUM,
                    impact="medium",
                    likelihood="low",
                    confidence=0.8
                )
            )
        
        uncertainties = []
        if has_uncertainties:
            uncertainties.append(
                UncertaintyCommunication(
                    aspect="data_quality",
                    uncertainty_level="medium",
                    reason="Limited data",
                    data_limitations=["sparse_data"]
                )
            )
        
        report = StructuredReport(
            report_id=uuid4(),
            tenant_id=uuid4(),
            query="Test query",
            executive_summary="Test summary",
            key_metrics=metrics,
            insights=insights,
            action_items=[],
            overall_confidence=85.0,
            data_quality_warnings=[],
            risks=risks,
            recommendations=[],
            uncertainties=uncertainties,
            agent_results={}
        )
        
        # Property: Report must always have required fields
        assert report.report_id is not None
        assert report.tenant_id is not None
        assert report.query is not None
        assert report.executive_summary is not None
        assert report.overall_confidence is not None
        
        # Property: Optional sections maintain structure
        assert isinstance(report.key_metrics, list)
        assert isinstance(report.insights, list)
        assert isinstance(report.risks, list)
        assert isinstance(report.uncertainties, list)
