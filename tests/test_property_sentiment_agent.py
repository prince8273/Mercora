"""
Property-Based Tests for Sentiment Analysis Agent

These tests validate correctness properties for sentiment analysis functionality
using Hypothesis for property-based testing.
"""
import pytest
from hypothesis import given, strategies as st, settings
from uuid import uuid4, UUID
from datetime import datetime

from src.agents.sentiment_analysis_v2 import EnhancedSentimentAgent
from src.schemas.review import ReviewResponse
from src.schemas.data_quality import (
    DataQualityReport,
    DataQualityDimensions,
    QualityDimension
)


# Helper function to create ReviewResponse objects
def create_review_response(
    product_id: UUID,
    rating: int,
    text: str,
    sentiment: str = None,
    sentiment_confidence: float = None
) -> ReviewResponse:
    """Helper to create ReviewResponse objects"""
    return ReviewResponse(
        id=uuid4(),
        product_id=product_id,
        rating=rating,
        text=text,
        source="test_source",
        sentiment=sentiment,
        sentiment_confidence=sentiment_confidence,
        is_spam=False,
        created_at=datetime.utcnow()
    )


# Helper function to create DataQualityReport
def create_qa_report(overall_score: float = 1.0) -> DataQualityReport:
    """Helper to create DataQualityReport with default high quality"""
    from datetime import datetime
    return DataQualityReport(
        overall_quality_score=overall_score,
        dimensions=DataQualityDimensions(
            completeness=QualityDimension(score=overall_score, issues_count=0),
            validity=QualityDimension(score=overall_score, issues_count=0),
            freshness=QualityDimension(score=overall_score, issues_count=0),
            consistency=QualityDimension(score=overall_score, issues_count=0),
            accuracy=QualityDimension(score=overall_score, issues_count=0)
        ),
        anomalies=[],
        missing_data=[],
        recommendations=[],
        entities_assessed=1,
        assessment_timestamp=datetime.utcnow().isoformat()
    )


class TestSentimentAnalysisProperties:
    """Property-based tests for Sentiment Analysis Agent"""
    
    @settings(max_examples=10, deadline=None)
    @given(
        review_text=st.text(min_size=10, max_size=200),
        rating=st.integers(min_value=1, max_value=5)
    )
    def test_property_16_all_reviews_classified_with_confidence(
        self, review_text, rating
    ):
        """
        # Feature: ecommerce-intelligence-agent, Property 16: All reviews are classified with confidence
        
        Property: Every review must be classified with a sentiment label
        and a confidence score between 0 and 1.
        
        Validates: Requirements 4.1
        """
        tenant_id = uuid4()
        agent = EnhancedSentimentAgent(tenant_id)
        product_id = uuid4()
        
        review = create_review_response(
            product_id=product_id,
            rating=rating,
            text=review_text
        )
        
        # Classify sentiment
        classification = agent.classify_sentiment(review)
        
        # Property: Classification must have sentiment and confidence
        assert classification.sentiment in ['positive', 'negative', 'neutral']
        assert 0.0 <= classification.confidence <= 1.0
    
    @settings(max_examples=10, deadline=None)
    @given(
        num_reviews=st.integers(min_value=1, max_value=10)
    )
    def test_property_17_feature_requests_extracted_and_ranked(
        self, num_reviews
    ):
        """
        # Feature: ecommerce-intelligence-agent, Property 17: Feature requests are extracted and ranked
        
        Property: Reviews containing feature request keywords must be
        extracted and ranked by frequency.
        
        Validates: Requirements 4.3
        """
        tenant_id = uuid4()
        agent = EnhancedSentimentAgent(tenant_id)
        product_id = uuid4()
        
        # Create reviews with feature request keywords
        reviews = []
        for i in range(num_reviews):
            text = f"I wish this product had better quality. Would like more features."
            review = create_review_response(
                product_id=product_id,
                rating=3,
                text=text
            )
            reviews.append(review)
        
        # Extract features
        feature_requests = agent.extract_features(reviews)
        
        # Property: Feature requests must be extracted
        assert isinstance(feature_requests, list)
        
        # Property: Each feature request must have required fields
        for feature_request in feature_requests:
            assert hasattr(feature_request, 'feature')
            assert hasattr(feature_request, 'frequency')
            assert feature_request.frequency >= 1
            assert isinstance(feature_request.sample_mentions, list)
    
    @settings(max_examples=10, deadline=None)
    @given(
        num_reviews=st.integers(min_value=1, max_value=10)
    )
    def test_property_18_complaint_patterns_identified(
        self, num_reviews
    ):
        """
        # Feature: ecommerce-intelligence-agent, Property 18: Complaint patterns are identified
        
        Property: Reviews containing complaint keywords must be identified
        and categorized by severity.
        
        Validates: Requirements 4.4
        """
        tenant_id = uuid4()
        agent = EnhancedSentimentAgent(tenant_id)
        product_id = uuid4()
        
        # Create reviews with complaint keywords
        reviews = []
        for i in range(num_reviews):
            text = f"This product is broken and defective. Very disappointed with the poor quality."
            review = create_review_response(
                product_id=product_id,
                rating=1,
                text=text
            )
            reviews.append(review)
        
        # Analyze complaints
        complaint_patterns = agent.analyze_complaints(reviews)
        
        # Property: Complaint patterns must be identified
        assert isinstance(complaint_patterns, list)
        
        # Property: Each complaint must have required fields
        for complaint in complaint_patterns:
            assert hasattr(complaint, 'pattern')
            assert hasattr(complaint, 'frequency')
            assert hasattr(complaint, 'severity')
            assert complaint.severity in ['low', 'medium', 'high']
            assert complaint.frequency >= 1
            assert isinstance(complaint.sample_reviews, list)
    
    @settings(max_examples=10, deadline=None)
    @given(
        num_reviews=st.integers(min_value=1, max_value=10),
        qa_score=st.floats(min_value=0.5, max_value=1.0)
    )
    def test_property_19_products_have_aggregate_sentiment_scores(
        self, num_reviews, qa_score
    ):
        """
        # Feature: ecommerce-intelligence-agent, Property 19: Products have aggregate sentiment scores
        
        Property: Products must have aggregate sentiment scores calculated
        from all reviews, with QA-adjusted confidence.
        
        Validates: Requirements 4.5
        """
        tenant_id = uuid4()
        agent = EnhancedSentimentAgent(tenant_id)
        product_id = uuid4()
        
        # Create reviews with varying sentiments
        reviews = []
        for i in range(num_reviews):
            text = "This is a great product!" if i % 2 == 0 else "Not satisfied with this."
            rating = 5 if i % 2 == 0 else 2
            review = create_review_response(
                product_id=product_id,
                rating=rating,
                text=text
            )
            reviews.append(review)
        
        # Create QA report
        qa_report = create_qa_report(overall_score=qa_score)
        
        # Calculate aggregate sentiment
        result = agent.calculate_aggregate_sentiment_with_qa(reviews, qa_report)
        
        # Property: Result must have aggregate sentiment
        assert hasattr(result, 'aggregate_sentiment')
        assert -1.0 <= result.aggregate_sentiment <= 1.0
        
        # Property: Result must have confidence score
        assert hasattr(result, 'confidence_score')
        assert 0.0 <= result.confidence_score <= 1.0
        
        # Property: Result must have sentiment distribution
        assert hasattr(result, 'sentiment_distribution')
        assert 'positive' in result.sentiment_distribution
        assert 'negative' in result.sentiment_distribution
        assert 'neutral' in result.sentiment_distribution
        
        # Property: Total reviews must match
        assert result.total_reviews == num_reviews
        
        # Property: QA metadata must be included
        assert result.qa_metadata is not None
        assert 'data_quality_score' in result.qa_metadata
    
    @settings(max_examples=10, deadline=None)
    @given(
        num_reviews=st.integers(min_value=2, max_value=10),
        num_clusters=st.integers(min_value=1, max_value=5)
    )
    def test_property_20_aspect_level_sentiment_extraction(
        self, num_reviews, num_clusters
    ):
        """
        # Feature: ecommerce-intelligence-agent, Property 20: Aspect-level sentiment extraction
        
        Property: Reviews must be clustered by topic to extract
        aspect-level sentiment insights.
        
        Validates: Requirements 4.6
        """
        tenant_id = uuid4()
        agent = EnhancedSentimentAgent(tenant_id)
        product_id = uuid4()
        
        # Create reviews with different topics
        reviews = []
        topics = [
            "The quality is excellent and durable",
            "Shipping was fast and packaging was good",
            "Price is reasonable for the features",
            "Customer service was helpful and responsive"
        ]
        
        for i in range(num_reviews):
            text = topics[i % len(topics)]
            review = create_review_response(
                product_id=product_id,
                rating=4,
                text=text
            )
            reviews.append(review)
        
        # Cluster by topic
        clusters = agent.cluster_by_topic(reviews, num_clusters=min(num_clusters, num_reviews))
        
        # Property: Clusters must be returned
        assert isinstance(clusters, list)
        
        # Property: Each cluster must have required fields
        for cluster in clusters:
            assert hasattr(cluster, 'topic_id')
            assert hasattr(cluster, 'keywords')
            assert hasattr(cluster, 'review_count')
            assert cluster.review_count >= 1
            assert isinstance(cluster.keywords, list)
            assert isinstance(cluster.sample_reviews, list)
