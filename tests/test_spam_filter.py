"""Tests for spam filter"""
import pytest
from src.processing.spam_filter import SpamFilter


def test_spam_filter_initialization():
    """Test spam filter initialization"""
    filter = SpamFilter(spam_threshold=0.7)
    assert filter.spam_threshold == 0.7
    assert filter.stats['total_checked'] == 0


def test_detect_url_spam():
    """Test detection of URL spam"""
    filter = SpamFilter()
    
    text = "Check out this amazing product at http://spam-site.com"
    is_spam, confidence, reasons = filter.is_spam(text)
    
    assert is_spam is True
    assert confidence > 0.6
    assert any('pattern' in r.lower() for r in reasons)


def test_detect_keyword_spam():
    """Test detection of keyword spam"""
    filter = SpamFilter()
    
    text = "FREE MONEY! Click here now for special offer!"
    is_spam, confidence, reasons = filter.is_spam(text)
    
    assert is_spam is True
    assert confidence > 0.6
    assert len(reasons) > 0


def test_detect_caps_spam():
    """Test detection of excessive caps"""
    filter = SpamFilter()
    
    text = "THIS IS AN AMAZING PRODUCT BUY NOW!!!"
    is_spam, confidence, reasons = filter.is_spam(text)
    
    assert is_spam is True
    assert any('caps' in r.lower() for r in reasons)


def test_detect_repeated_chars():
    """Test detection of repeated characters"""
    filter = SpamFilter()
    
    text = "Greaaaaat product!!!!!!"
    is_spam, confidence, reasons = filter.is_spam(text)
    
    assert is_spam is True
    assert any('repeated' in r.lower() for r in reasons)


def test_legitimate_review():
    """Test that legitimate reviews are not flagged"""
    filter = SpamFilter()
    
    text = "This product works well and arrived on time. Good quality for the price."
    is_spam, confidence, reasons = filter.is_spam(text)
    
    assert is_spam is False
    assert confidence < 0.6


def test_filter_spam_reviews():
    """Test filtering spam from review list"""
    filter = SpamFilter()
    
    reviews = [
        {'text': 'Great product, highly recommend!', 'rating': 5},
        {'text': 'Click here for FREE MONEY http://spam.com', 'rating': 5},
        {'text': 'Good quality and fast shipping', 'rating': 4},
        {'text': 'AMAZING DEAL BUY NOW!!!', 'rating': 5}
    ]
    
    filtered = filter.filter_spam_reviews(reviews, mark_only=False)
    
    assert len(filtered) == 2
    assert all(not r.get('is_spam', False) for r in filtered)


def test_mark_spam_reviews():
    """Test marking spam without removing"""
    filter = SpamFilter()
    
    reviews = [
        {'text': 'Great product!', 'rating': 5},
        {'text': 'Visit my website www.spam.com', 'rating': 5}
    ]
    
    marked = filter.filter_spam_reviews(reviews, mark_only=True)
    
    assert len(marked) == 2
    assert marked[0]['is_spam'] is False
    assert marked[1]['is_spam'] is True


def test_batch_check_spam():
    """Test batch spam checking"""
    filter = SpamFilter()
    
    reviews = [
        {'text': 'Excellent product', 'rating': 5},
        {'text': 'FREE MONEY click here', 'rating': 5},
        {'text': 'Good value', 'rating': 4}
    ]
    
    result = filter.batch_check_spam(reviews)
    
    assert result['total_reviews'] == 3
    assert result['spam_count'] == 1
    assert result['clean_count'] == 2
    assert 0 < result['spam_rate'] < 1


def test_empty_review():
    """Test handling of empty reviews"""
    filter = SpamFilter()
    
    is_spam, confidence, reasons = filter.is_spam("")
    
    assert is_spam is True
    assert confidence == 1.0
    assert "Empty review" in reasons


def test_short_review_with_high_rating():
    """Test suspicious short 5-star review"""
    filter = SpamFilter()
    
    text = "Great!"
    is_spam, confidence, reasons = filter.is_spam(text, rating=5)
    
    # Should be flagged as suspicious
    assert is_spam is True


def test_statistics():
    """Test spam filter statistics"""
    filter = SpamFilter()
    
    filter.is_spam("Good product")
    filter.is_spam("FREE MONEY")
    filter.is_spam("Nice quality")
    
    stats = filter.get_statistics()
    
    assert stats['total_checked'] == 3
    assert stats['spam_detected'] >= 1
    assert 'spam_rate' in stats
