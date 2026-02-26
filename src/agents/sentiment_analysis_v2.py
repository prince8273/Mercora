"""Enhanced Sentiment Analysis Agent with QA Score Integration"""
from typing import List, Dict, Any, Optional
from collections import Counter
import re
from uuid import UUID

from transformers import pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans

from src.schemas.review import ReviewResponse
from src.schemas.sentiment import (
    SentimentClassification,
    TopicCluster,
    FeatureRequest,
    ComplaintPattern,
    SentimentAnalysisResult
)
from src.schemas.data_quality import DataQualityReport


class EnhancedSentimentAgent:
    """
    Enhanced Sentiment Analysis Agent with Data QA Integration.
    
    Confidence Calculation:
    final_confidence = agent_confidence × data_quality_score × anomaly_penalty
    
    TENANT ISOLATION:
    All database queries are filtered by tenant_id to ensure data isolation.
    """
    
    def __init__(self, tenant_id: UUID):
        """
        Initialize the enhanced sentiment analysis agent.
        
        Args:
            tenant_id: UUID of the tenant this agent operates for
        """
        self.tenant_id = tenant_id
        
        # Load HuggingFace sentiment model
        self.sentiment_pipeline = pipeline(
            "sentiment-analysis",
            model="distilbert-base-uncased-finetuned-sst-2-english"
        )
        
        # Keywords for feature requests and complaints
        self.feature_keywords = [
            "wish", "would like", "should have", "need", "want",
            "add", "include", "feature", "option", "support"
        ]
        
        self.complaint_keywords = [
            "broken", "defective", "poor", "bad", "terrible",
            "disappointed", "issue", "problem", "doesn't work", "failed"
        ]
        
        # Anomaly penalty factors
        self.anomaly_penalties = {
            'low': 0.95,
            'medium': 0.85,
            'high': 0.70,
            'critical': 0.50
        }
    
    def calculate_confidence_with_qa(
        self,
        base_confidence: float,
        qa_report: DataQualityReport,
        product_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Calculate final confidence incorporating QA scores and anomalies.
        
        Args:
            base_confidence: Agent's base confidence (0-1)
            qa_report: Data quality assessment report
            product_id: Optional product ID for product-specific penalties
            
        Returns:
            Dictionary with final confidence and explanation
        """
        confidence = base_confidence
        
        # Apply data quality score
        qa_score = qa_report.overall_quality_score
        confidence *= qa_score
        
        # Calculate anomaly penalty
        anomaly_penalty = self._calculate_anomaly_penalty(qa_report, product_id)
        confidence *= anomaly_penalty
        
        # Build explanation
        explanation = self._build_confidence_explanation(
            base_confidence,
            qa_score,
            anomaly_penalty,
            qa_report,
            product_id
        )
        
        return {
            'final_confidence': round(confidence, 3),
            'base_confidence': round(base_confidence, 3),
            'data_quality_score': round(qa_score, 3),
            'anomaly_penalty': round(anomaly_penalty, 3),
            'explanation': explanation,
            'quality_dimensions': {
                'completeness': qa_report.dimensions.completeness.score,
                'validity': qa_report.dimensions.validity.score,
                'freshness': qa_report.dimensions.freshness.score,
                'consistency': qa_report.dimensions.consistency.score,
                'accuracy': qa_report.dimensions.accuracy.score
            }
        }
    
    def _calculate_anomaly_penalty(
        self,
        qa_report: DataQualityReport,
        product_id: Optional[UUID] = None
    ) -> float:
        """Calculate penalty factor based on detected anomalies"""
        if not qa_report.anomalies:
            return 1.0
        
        relevant_anomalies = qa_report.anomalies
        if product_id:
            relevant_anomalies = [
                a for a in qa_report.anomalies
                if not a.affected_entities or str(product_id) in a.affected_entities
            ]
        
        if not relevant_anomalies:
            return 1.0
        
        penalties = [self.anomaly_penalties.get(a.severity, 0.90) for a in relevant_anomalies]
        return min(penalties)
    
    def _build_confidence_explanation(
        self,
        base_confidence: float,
        qa_score: float,
        anomaly_penalty: float,
        qa_report: DataQualityReport,
        product_id: Optional[UUID]
    ) -> str:
        """Build human-readable confidence explanation"""
        parts = []
        
        parts.append(f"Base sentiment confidence: {base_confidence:.1%}")
        
        if qa_score < 0.9:
            impact = (1.0 - qa_score) * 100
            parts.append(f"Review quality reduced confidence by {impact:.1f}%")
            
            low_dimensions = []
            if qa_report.dimensions.accuracy.score < 0.8:
                low_dimensions.append("spam detected")
            if qa_report.dimensions.consistency.score < 0.8:
                low_dimensions.append("rating-text mismatches")
            if qa_report.dimensions.freshness.score < 0.8:
                low_dimensions.append("old reviews")
            
            if low_dimensions:
                parts.append(f"Issues: {', '.join(low_dimensions)}")
        
        if anomaly_penalty < 1.0:
            impact = (1.0 - anomaly_penalty) * 100
            parts.append(f"Detected anomalies reduced confidence by {impact:.1f}%")
            
            for anomaly in qa_report.anomalies[:2]:
                if anomaly.type in ['review_surge', 'rating_polarization']:
                    parts.append(f"⚠ {anomaly.type}: {anomaly.description}")
        
        return " | ".join(parts)
    
    def classify_sentiment(self, review: ReviewResponse) -> SentimentClassification:
        """Classify sentiment of a single review using HuggingFace model"""
        result = self.sentiment_pipeline(review.text[:512])[0]
        
        label = result['label'].lower()
        confidence = result['score']
        
        if label == 'positive' and confidence > 0.6:
            sentiment = 'positive'
        elif label == 'negative' and confidence > 0.6:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
            confidence = 1.0 - confidence
        
        return SentimentClassification(
            sentiment=sentiment,
            confidence=confidence
        )
    
    def cluster_by_topic(
        self,
        reviews: List[ReviewResponse],
        num_clusters: int = 5
    ) -> List[TopicCluster]:
        """Cluster reviews by topic using TF-IDF and K-means"""
        if len(reviews) < num_clusters:
            num_clusters = max(1, len(reviews))
        
        texts = [r.text for r in reviews]
        
        if len(texts) == 0:
            return []
        
        vectorizer = TfidfVectorizer(
            max_features=100,
            stop_words='english',
            ngram_range=(1, 2)
        )
        
        try:
            X = vectorizer.fit_transform(texts)
            kmeans = KMeans(n_clusters=num_clusters, random_state=42, n_init=10)
            kmeans.fit(X)
            
            feature_names = vectorizer.get_feature_names_out()
            clusters = []
            
            for i in range(num_clusters):
                cluster_reviews = [
                    reviews[j] for j in range(len(reviews))
                    if kmeans.labels_[j] == i
                ]
                
                if not cluster_reviews:
                    continue
                
                center = kmeans.cluster_centers_[i]
                top_indices = center.argsort()[-5:][::-1]
                keywords = [feature_names[idx] for idx in top_indices]
                
                sample_reviews = [r.text[:100] + "..." for r in cluster_reviews[:3]]
                
                cluster = TopicCluster(
                    topic_id=i,
                    keywords=keywords,
                    review_count=len(cluster_reviews),
                    sample_reviews=sample_reviews
                )
                clusters.append(cluster)
            
            return clusters
        
        except Exception as e:
            print(f"Clustering failed: {e}")
            return []
    
    def extract_features(self, reviews: List[ReviewResponse]) -> List[FeatureRequest]:
        """Extract feature requests from reviews"""
        feature_mentions = []
        
        for review in reviews:
            text_lower = review.text.lower()
            
            has_feature_keyword = any(
                keyword in text_lower for keyword in self.feature_keywords
            )
            
            if has_feature_keyword:
                sentences = re.split(r'[.!?]', review.text)
                for sentence in sentences:
                    sentence_lower = sentence.lower()
                    if any(keyword in sentence_lower for keyword in self.feature_keywords):
                        feature_mentions.append(sentence.strip())
        
        mention_counts = Counter(feature_mentions)
        
        feature_requests = []
        for feature, count in mention_counts.most_common(10):
            if count >= 1:
                feature_request = FeatureRequest(
                    feature=feature,
                    frequency=count,
                    sample_mentions=[feature]
                )
                feature_requests.append(feature_request)
        
        return feature_requests
    
    def analyze_complaints(self, reviews: List[ReviewResponse]) -> List[ComplaintPattern]:
        """Identify recurring complaint patterns"""
        complaint_mentions = []
        
        for review in reviews:
            text_lower = review.text.lower()
            
            has_complaint_keyword = any(
                keyword in text_lower for keyword in self.complaint_keywords
            )
            
            if has_complaint_keyword:
                sentences = re.split(r'[.!?]', review.text)
                for sentence in sentences:
                    sentence_lower = sentence.lower()
                    if any(keyword in sentence_lower for keyword in self.complaint_keywords):
                        complaint_mentions.append(sentence.strip())
        
        complaint_counts = Counter(complaint_mentions)
        
        complaint_patterns = []
        for complaint, count in complaint_counts.most_common(10):
            if count >= 1:
                severity = "low"
                complaint_lower = complaint.lower()
                if any(word in complaint_lower for word in ["broken", "defective", "failed"]):
                    severity = "high"
                elif any(word in complaint_lower for word in ["poor", "bad", "issue"]):
                    severity = "medium"
                
                pattern = ComplaintPattern(
                    pattern=complaint,
                    frequency=count,
                    severity=severity,
                    sample_reviews=[complaint]
                )
                complaint_patterns.append(pattern)
        
        return complaint_patterns
    
    def calculate_aggregate_sentiment_with_qa(
        self,
        reviews: List[ReviewResponse],
        qa_report: DataQualityReport
    ) -> SentimentAnalysisResult:
        """
        Calculate aggregate sentiment with QA-adjusted confidence.
        
        Args:
            reviews: List of reviews for the product
            qa_report: Data quality report for reviews
            
        Returns:
            Complete sentiment analysis result with QA metadata
        """
        if not reviews:
            return SentimentAnalysisResult(
                product_id=reviews[0].product_id if reviews else UUID(int=0),
                aggregate_sentiment=0.0,
                sentiment_distribution={"positive": 0, "negative": 0, "neutral": 0},
                top_topics=[],
                feature_requests=[],
                complaint_patterns=[],
                confidence_score=0.0,
                total_reviews=0
            )
        
        product_id = reviews[0].product_id
        
        # Classify all reviews
        sentiment_scores = []
        sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
        
        for review in reviews:
            if review.sentiment:
                sentiment = review.sentiment
                confidence = review.sentiment_confidence or 0.5
            else:
                classification = self.classify_sentiment(review)
                sentiment = classification.sentiment
                confidence = classification.confidence
            
            if sentiment == "positive":
                sentiment_scores.append(1.0 * confidence)
                sentiment_counts["positive"] += 1
            elif sentiment == "negative":
                sentiment_scores.append(-1.0 * confidence)
                sentiment_counts["negative"] += 1
            else:
                sentiment_scores.append(0.0)
                sentiment_counts["neutral"] += 1
        
        aggregate_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.0
        
        # Cluster by topic
        top_topics = self.cluster_by_topic(reviews, num_clusters=min(5, len(reviews)))
        
        # Extract features and complaints
        feature_requests = self.extract_features(reviews)
        complaint_patterns = self.analyze_complaints(reviews)
        
        # Calculate base confidence
        base_confidence = min(1.0, len(reviews) / 20.0)
        
        # Apply QA-adjusted confidence
        confidence_data = self.calculate_confidence_with_qa(
            base_confidence,
            qa_report,
            product_id
        )
        
        return SentimentAnalysisResult(
            product_id=product_id,
            aggregate_sentiment=aggregate_sentiment,
            sentiment_distribution=sentiment_counts,
            top_topics=top_topics,
            feature_requests=feature_requests,
            complaint_patterns=complaint_patterns,
            confidence_score=confidence_data['final_confidence'],
            total_reviews=len(reviews),
            # Add QA metadata
            qa_metadata={
                'base_confidence': confidence_data['base_confidence'],
                'data_quality_score': confidence_data['data_quality_score'],
                'anomaly_penalty': confidence_data['anomaly_penalty'],
                'confidence_explanation': confidence_data['explanation'],
                'quality_dimensions': confidence_data['quality_dimensions']
            }
        )
