"""Advanced spam filtering for reviews"""
from typing import List, Dict, Any, Tuple
import re
from datetime import datetime


class SpamFilter:
    """
    Advanced spam detection and filtering for reviews.
    
    Uses multiple detection strategies:
    - Pattern matching (URLs, promotional text)
    - Keyword detection
    - Text analysis (caps ratio, repeated chars)
    - Behavioral signals (review length, rating patterns)
    """
    
    # Spam patterns
    SPAM_PATTERNS = [
        r'(buy|click|visit)\s+(here|now|link)',
        r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
        r'(viagra|cialis|pharmacy|casino|lottery)',
        r'(\w)\1{5,}',  # Repeated characters
        r'FREE\s+MONEY|CLICK\s+HERE|LIMITED\s+TIME',
        r'www\.|\.com|\.net|\.org',  # URLs
        r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}',  # Phone numbers
    ]
    
    SPAM_KEYWORDS = [
        'viagra', 'cialis', 'pharmacy', 'casino', 'lottery',
        'free money', 'click here', 'buy now', 'limited time',
        'act now', 'special offer', 'winner', 'congratulations',
        'discount code', 'promo code', 'coupon', 'giveaway',
        'follow me', 'check out my', 'visit my website'
    ]
    
    def __init__(self, spam_threshold: float = 0.5):
        """
        Initialize spam filter.
        
        Args:
            spam_threshold: Confidence threshold for spam classification (0.0-1.0)
        """
        self.spam_threshold = spam_threshold
        self.stats = {
            'total_checked': 0,
            'spam_detected': 0,
            'spam_filtered': 0
        }
    
    def is_spam(self, review_text: str, rating: int = None) -> Tuple[bool, float, List[str]]:
        """
        Detect if a review is spam.
        
        Args:
            review_text: Review text content
            rating: Review rating (1-5)
            
        Returns:
            Tuple of (is_spam, confidence, reasons)
        """
        self.stats['total_checked'] += 1
        
        reasons = []
        spam_score = 0.0
        
        if not review_text or len(review_text.strip()) == 0:
            return True, 1.0, ["Empty review"]
        
        text_lower = review_text.lower()
        
        # Check patterns (high weight)
        pattern_matches = 0
        for pattern in self.SPAM_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                pattern_matches += 1
                reasons.append(f"Spam pattern: {pattern[:30]}")
        
        if pattern_matches > 0:
            spam_score += min(0.5, pattern_matches * 0.2)
        
        # Check keywords (medium weight)
        keyword_matches = 0
        for keyword in self.SPAM_KEYWORDS:
            if keyword in text_lower:
                keyword_matches += 1
                reasons.append(f"Spam keyword: {keyword}")
        
        if keyword_matches > 0:
            spam_score += min(0.4, keyword_matches * 0.15)
        
        # Check excessive caps (medium weight)
        if len(review_text) > 10:
            caps_ratio = sum(1 for c in review_text if c.isupper()) / len(review_text)
            if caps_ratio > 0.5:
                spam_score += 0.2
                reasons.append(f"Excessive caps: {caps_ratio:.1%}")
        
        # Check repeated characters (low weight)
        if re.search(r'(.)\1{4,}', review_text):
            spam_score += 0.1
            reasons.append("Repeated characters")
        
        # Check very short reviews (low weight)
        if len(review_text.strip()) < 10:
            spam_score += 0.15
            reasons.append("Very short review")
        
        # Check suspicious rating patterns (if rating provided)
        if rating is not None:
            if rating == 5 and len(review_text.strip()) < 20:
                spam_score += 0.1
                reasons.append("Suspiciously short 5-star review")
        
        # Determine if spam
        is_spam = spam_score >= self.spam_threshold
        
        if is_spam:
            self.stats['spam_detected'] += 1
        
        return is_spam, spam_score, reasons
    
    def filter_spam_reviews(
        self,
        reviews: List[Dict[str, Any]],
        mark_only: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Filter spam reviews from a list.
        
        Args:
            reviews: List of review dictionaries
            mark_only: If True, mark spam but don't remove. If False, remove spam.
            
        Returns:
            Filtered or marked review list
        """
        result = []
        
        for review in reviews:
            text = review.get('text', '')
            rating = review.get('rating')
            
            is_spam, confidence, reasons = self.is_spam(text, rating)
            
            # Add spam metadata
            review['is_spam'] = is_spam
            review['spam_confidence'] = confidence
            review['spam_reasons'] = reasons
            
            if mark_only:
                # Keep all reviews but mark spam
                result.append(review)
            else:
                # Only keep non-spam reviews
                if not is_spam:
                    result.append(review)
                else:
                    self.stats['spam_filtered'] += 1
        
        return result
    
    def batch_check_spam(
        self,
        reviews: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Check multiple reviews for spam and return statistics.
        
        Args:
            reviews: List of review dictionaries
            
        Returns:
            Dictionary with spam statistics and flagged reviews
        """
        spam_reviews = []
        clean_reviews = []
        
        for review in reviews:
            text = review.get('text', '')
            rating = review.get('rating')
            
            is_spam, confidence, reasons = self.is_spam(text, rating)
            
            review_with_spam_info = {
                **review,
                'is_spam': is_spam,
                'spam_confidence': confidence,
                'spam_reasons': reasons
            }
            
            if is_spam:
                spam_reviews.append(review_with_spam_info)
            else:
                clean_reviews.append(review_with_spam_info)
        
        return {
            'total_reviews': len(reviews),
            'spam_count': len(spam_reviews),
            'clean_count': len(clean_reviews),
            'spam_rate': len(spam_reviews) / len(reviews) if reviews else 0.0,
            'spam_reviews': spam_reviews,
            'clean_reviews': clean_reviews
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get spam filter statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            **self.stats,
            'spam_rate': (
                self.stats['spam_detected'] / self.stats['total_checked']
                if self.stats['total_checked'] > 0 else 0.0
            )
        }
