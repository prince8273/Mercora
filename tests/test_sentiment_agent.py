"""Tests for Sentiment Analysis Agent"""
import pytest
from uuid import uuid4
from datetime import datetime

from src.agents.sentiment_analysis import SentimentAgent
from src.schemas.review import ReviewResponse


@pytest.fixture
def sentiment_agent():
    """Create a sentiment agent instance"""
    tenant_id = uuid4()
    return SentimentAgent(tenant_id=tenant_id)


@pytest.fixture
def sample_reviews():
    """Create sample reviews for testing"""
    product_id = uuid4()
    
    return [
        ReviewResponse(
            id=uuid4(),
            product_id=product_id,
            rating=5,
            text="This product is amazing! I love it so much. Great quality and fast shipping.",
            sentiment=None,
            sentiment_confidence=None,
            is_spam=False,
            created_at=datetime.utcnow(),
            source="amazon"
        ),
        ReviewResponse(
            id=uuid4(),
            product_id=product_id,
            rating=1,
            text="Terrible product. It broke after one day. Very disappointed with the quality.",
            sentiment=None,
            sentiment_confidence=None,
            is_spam=False,
            created_at=datetime.utcnow(),
            source="amazon"
        ),
        ReviewResponse(
            id=uuid4(),
            product_id=product_id,
            rating=3,
            text="It's okay. Does the job but nothing special. Would like to see better features.",
            sentiment=None,
            sentiment_confidence=None,
            is_spam=False,
            created_at=datetime.utcnow(),
            source="amazon"
        ),
        ReviewResponse(
            id=uuid4(),
            product_id=product_id,
            rating=4,
            text="Good product overall. I wish it had more color options though.",
            sentiment=None,
            sentiment_confidence=None,
            is_spam=False,
            created_at=datetime.utcnow(),
            source="amazon"
        ),
        ReviewResponse(
            id=uuid4(),
            product_id=product_id,
            rating=2,
            text="Poor quality. The product doesn't work as advertised. Issue with the battery.",
            sentiment=None,
            sentiment_confidence=None,
            is_spam=False,
            created_at=datetime.utcnow(),
            source="amazon"
        ),
    ]


def test_classify_sentiment_positive(sentiment_agent, sample_reviews):
    """Test sentiment classification for positive review"""
    positive_review = sample_reviews[0]
    
    classification = sentiment_agent.classify_sentiment(positive_review)
    
    assert classification.sentiment in ["positive", "negative", "neutral"]
    assert 0.0 <= classification.confidence <= 1.0
    # The first review should be classified as positive
    assert classification.sentiment == "positive"


def test_classify_sentiment_negative(sentiment_agent, sample_reviews):
    """Test sentiment classification for negative review"""
    negative_review = sample_reviews[1]
    
    classification = sentiment_agent.classify_sentiment(negative_review)
    
    assert classification.sentiment in ["positive", "negative", "neutral"]
    assert 0.0 <= classification.confidence <= 1.0
    # The second review should be classified as negative
    assert classification.sentiment == "negative"


def test_cluster_by_topic(sentiment_agent, sample_reviews):
    """Test topic clustering"""
    clusters = sentiment_agent.cluster_by_topic(sample_reviews, num_clusters=3)
    
    # Should return clusters
    assert isinstance(clusters, list)
    
    # Each cluster should have required fields
    for cluster in clusters:
        assert hasattr(cluster, 'topic_id')
        assert hasattr(cluster, 'keywords')
        assert hasattr(cluster, 'review_count')
        assert hasattr(cluster, 'sample_reviews')
        assert cluster.review_count > 0


def test_extract_features(sentiment_agent, sample_reviews):
    """Test feature request extraction"""
    features = sentiment_agent.extract_features(sample_reviews)
    
    # Should return a list
    assert isinstance(features, list)
    
    # Should find at least one feature request (reviews mention "wish" and "would like")
    assert len(features) > 0
    
    # Each feature should have required fields
    for feature in features:
        assert hasattr(feature, 'feature')
        assert hasattr(feature, 'frequency')
        assert feature.frequency >= 1


def test_analyze_complaints(sentiment_agent, sample_reviews):
    """Test complaint pattern identification"""
    complaints = sentiment_agent.analyze_complaints(sample_reviews)
    
    # Should return a list
    assert isinstance(complaints, list)
    
    # Should find complaints (reviews mention "broke", "poor", "doesn't work")
    assert len(complaints) > 0
    
    # Each complaint should have required fields
    for complaint in complaints:
        assert hasattr(complaint, 'pattern')
        assert hasattr(complaint, 'frequency')
        assert hasattr(complaint, 'severity')
        assert complaint.severity in ["low", "medium", "high"]
        assert complaint.frequency >= 1


def test_calculate_aggregate_sentiment(sentiment_agent, sample_reviews):
    """Test aggregate sentiment calculation"""
    result = sentiment_agent.calculate_aggregate_sentiment(sample_reviews)
    
    # Check all required fields
    assert result.product_id == sample_reviews[0].product_id
    assert -1.0 <= result.aggregate_sentiment <= 1.0
    assert isinstance(result.sentiment_distribution, dict)
    assert "positive" in result.sentiment_distribution
    assert "negative" in result.sentiment_distribution
    assert "neutral" in result.sentiment_distribution
    assert isinstance(result.top_topics, list)
    assert isinstance(result.feature_requests, list)
    assert isinstance(result.complaint_patterns, list)
    assert 0.0 <= result.confidence_score <= 1.0
    assert result.total_reviews == len(sample_reviews)
    
    # Sentiment distribution should sum to total reviews
    total_classified = sum(result.sentiment_distribution.values())
    assert total_classified == len(sample_reviews)


def test_empty_reviews(sentiment_agent):
    """Test handling of empty review list"""
    result = sentiment_agent.calculate_aggregate_sentiment([])
    
    assert result.aggregate_sentiment == 0.0
    assert result.total_reviews == 0
    assert result.confidence_score == 0.0
