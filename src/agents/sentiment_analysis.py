"""Sentiment Analysis Agent for customer review analysis"""
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


class SentimentAgent:
    """
    Analyzes customer reviews and feedback using HuggingFace models.
    
    MVP Simplified Scope:
    - Real HuggingFace sentiment model (distilbert-base-uncased-finetuned-sst-2-english)
    - Basic sentiment classification (positive/negative/neutral)
    - Simple topic clustering using keyword extraction
    - No complex NLP - keep it functional
    
    TENANT ISOLATION:
    All database queries are filtered by tenant_id to ensure data isolation.
    """
    
    def __init__(self, tenant_id: UUID):
        """
        Initialize the sentiment analysis agent.
        
        Args:
            tenant_id: UUID of the tenant this agent operates for
        """
        self.tenant_id = tenant_id
        
        # Load HuggingFace sentiment model
        # Using distilbert-base-uncased-finetuned-sst-2-english for sentiment
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
    
    def classify_sentiment(self, review: ReviewResponse) -> SentimentClassification:
        """
        Classify sentiment of a single review using HuggingFace model.
        
        Args:
            review: Review to classify
            
        Returns:
            Sentiment classification with confidence
        """
        # Use HuggingFace model for sentiment
        result = self.sentiment_pipeline(review.text[:512])[0]  # Limit to 512 tokens
        
        # Map HuggingFace labels to our format
        # Model returns POSITIVE or NEGATIVE
        label = result['label'].lower()
        confidence = result['score']
        
        # Map to positive/negative/neutral
        # For MVP, we'll use a simple threshold approach
        if label == 'positive' and confidence > 0.6:
            sentiment = 'positive'
        elif label == 'negative' and confidence > 0.6:
            sentiment = 'negative'
        else:
            # Low confidence or ambiguous -> neutral
            sentiment = 'neutral'
            confidence = 1.0 - confidence  # Invert confidence for neutral
        
        return SentimentClassification(
            sentiment=sentiment,
            confidence=confidence
        )
    
    def cluster_by_topic(
        self,
        reviews: List[ReviewResponse],
        num_clusters: int = 5
    ) -> List[TopicCluster]:
        """
        Cluster reviews by topic using simple keyword-based clustering.
        
        Args:
            reviews: List of reviews to cluster
            num_clusters: Number of clusters to create
            
        Returns:
            List of topic clusters
        """
        if len(reviews) < num_clusters:
            num_clusters = max(1, len(reviews))
        
        # Extract review texts
        texts = [r.text for r in reviews]
        
        if len(texts) == 0:
            return []
        
        # Use TF-IDF for feature extraction
        vectorizer = TfidfVectorizer(
            max_features=100,
            stop_words='english',
            ngram_range=(1, 2)
        )
        
        try:
            X = vectorizer.fit_transform(texts)
            
            # Perform K-means clustering
            kmeans = KMeans(n_clusters=num_clusters, random_state=42, n_init=10)
            kmeans.fit(X)
            
            # Extract top keywords for each cluster
            feature_names = vectorizer.get_feature_names_out()
            clusters = []
            
            for i in range(num_clusters):
                # Get reviews in this cluster
                cluster_reviews = [
                    reviews[j] for j in range(len(reviews))
                    if kmeans.labels_[j] == i
                ]
                
                if not cluster_reviews:
                    continue
                
                # Get top keywords for this cluster
                center = kmeans.cluster_centers_[i]
                top_indices = center.argsort()[-5:][::-1]
                keywords = [feature_names[idx] for idx in top_indices]
                
                # Get sample reviews
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
            # If clustering fails, return empty list
            print(f"Clustering failed: {e}")
            return []
    
    def extract_features(self, reviews: List[ReviewResponse]) -> List[FeatureRequest]:
        """
        Extract feature requests from reviews using keyword matching.
        
        Args:
            reviews: List of reviews to analyze
            
        Returns:
            List of feature requests ranked by frequency
        """
        feature_mentions = []
        
        for review in reviews:
            text_lower = review.text.lower()
            
            # Check if review contains feature request keywords
            has_feature_keyword = any(
                keyword in text_lower for keyword in self.feature_keywords
            )
            
            if has_feature_keyword:
                # Extract sentences with feature keywords
                sentences = re.split(r'[.!?]', review.text)
                for sentence in sentences:
                    sentence_lower = sentence.lower()
                    if any(keyword in sentence_lower for keyword in self.feature_keywords):
                        feature_mentions.append(sentence.strip())
        
        # Count frequency of similar mentions
        # For MVP, we'll do simple exact matching
        mention_counts = Counter(feature_mentions)
        
        # Create feature requests
        feature_requests = []
        for feature, count in mention_counts.most_common(10):
            if count >= 1:  # At least mentioned once
                feature_request = FeatureRequest(
                    feature=feature,
                    frequency=count,
                    sample_mentions=[feature]
                )
                feature_requests.append(feature_request)
        
        return feature_requests
    
    def analyze_complaints(self, reviews: List[ReviewResponse]) -> List[ComplaintPattern]:
        """
        Identify recurring complaint patterns using keyword matching.
        
        Args:
            reviews: List of reviews to analyze
            
        Returns:
            List of complaint patterns
        """
        complaint_mentions = []
        
        for review in reviews:
            text_lower = review.text.lower()
            
            # Check if review contains complaint keywords
            has_complaint_keyword = any(
                keyword in text_lower for keyword in self.complaint_keywords
            )
            
            if has_complaint_keyword:
                # Extract sentences with complaint keywords
                sentences = re.split(r'[.!?]', review.text)
                for sentence in sentences:
                    sentence_lower = sentence.lower()
                    if any(keyword in sentence_lower for keyword in self.complaint_keywords):
                        complaint_mentions.append(sentence.strip())
        
        # Count frequency of similar complaints
        complaint_counts = Counter(complaint_mentions)
        
        # Create complaint patterns
        complaint_patterns = []
        for complaint, count in complaint_counts.most_common(10):
            if count >= 1:
                # Determine severity based on keywords
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
    
    def calculate_aggregate_sentiment(
        self,
        reviews: List[ReviewResponse],
        data_quality_score: float = 1.0,
        anomaly_penalty: float = 1.0
    ) -> SentimentAnalysisResult:
        """
        Calculate aggregate sentiment and analysis for a product.
        
        Args:
            reviews: List of reviews for the product
            
        Returns:
            Complete sentiment analysis result
        """
        if not reviews:
            # Return empty result for no reviews
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
        
        # Classify all reviews if not already classified
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
            
            # Convert sentiment to numeric score
            if sentiment == "positive":
                sentiment_scores.append(1.0 * confidence)
                sentiment_counts["positive"] += 1
            elif sentiment == "negative":
                sentiment_scores.append(-1.0 * confidence)
                sentiment_counts["negative"] += 1
            else:
                sentiment_scores.append(0.0)
                sentiment_counts["neutral"] += 1
        
        # Calculate aggregate sentiment
        aggregate_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.0
        
        # Cluster by topic
        top_topics = self.cluster_by_topic(reviews, num_clusters=min(5, len(reviews)))
        
        # Extract features and complaints
        feature_requests = self.extract_features(reviews)
        complaint_patterns = self.analyze_complaints(reviews)
        
        # Calculate base confidence based on review count
        base_confidence = min(1.0, len(reviews) / 20.0)  # Full confidence at 20+ reviews
        
        # Apply tiered confidence formula:
        # final_confidence = agent_confidence × data_quality_score × anomaly_penalty
        final_confidence = base_confidence * data_quality_score * anomaly_penalty
        final_confidence = max(0.0, min(1.0, final_confidence))  # Clamp to [0, 1]
        
        return SentimentAnalysisResult(
            product_id=product_id,
            aggregate_sentiment=aggregate_sentiment,
            sentiment_distribution=sentiment_counts,
            top_topics=top_topics,
            feature_requests=feature_requests,
            complaint_patterns=complaint_patterns,
            confidence_score=final_confidence,
            total_reviews=len(reviews)
        )
