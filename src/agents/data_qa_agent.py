"""Data Quality Assurance Agent - Layer 0 of Tiered Intelligence"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from statistics import mean, stdev
from collections import Counter
from uuid import UUID
import re

from src.schemas.product import ProductResponse
from src.schemas.review import ReviewResponse
from src.schemas.data_quality import (
    DataQualityReport,
    DataQualityDimensions,
    QualityDimension,
    Anomaly,
    MissingData,
    ProductQualityMetadata,
    ReviewQualityMetadata
)


class DataQAAgent:
    """
    Layer 0: Data Quality Assurance Agent
    
    Validates input data quality, flags anomalies, scores reliability,
    and influences confidence of downstream agents.
    
    Responsibilities:
    - Data completeness validation
    - Data validity checks
    - Anomaly detection
    - Freshness assessment
    - Reliability scoring
    
    TENANT ISOLATION:
    All database queries are filtered by tenant_id to ensure data isolation.
    """
    
    def __init__(self, tenant_id: UUID):
        """
        Initialize the Data QA Agent.
        
        Args:
            tenant_id: UUID of the tenant this agent operates for
        """
        self.tenant_id = tenant_id
        
        # Thresholds for anomaly detection
        self.price_outlier_threshold = 3.0  # Standard deviations
        self.freshness_threshold_days = 30
        self.min_reviews_for_confidence = 5
        
        # Required fields for different entity types
        self.required_product_fields = ['id', 'sku', 'name', 'price', 'marketplace']
        self.required_review_fields = ['id', 'product_id', 'rating', 'text']
    
    def assess_product_data_quality(
        self,
        products: List[ProductResponse]
    ) -> DataQualityReport:
        """
        Assess quality of product data.
        
        Args:
            products: List of products to assess
            
        Returns:
            Complete data quality report
        """
        if not products:
            return self._create_empty_report()
        
        # Assess each dimension
        completeness = self._assess_product_completeness(products)
        validity = self._assess_product_validity(products)
        freshness = self._assess_product_freshness(products)
        consistency = self._assess_product_consistency(products)
        accuracy = self._assess_product_accuracy(products)
        
        # Detect anomalies
        anomalies = self._detect_product_anomalies(products)
        
        # Identify missing data
        missing_data = self._identify_missing_product_data(products)
        
        # Generate recommendations
        recommendations = self._generate_product_recommendations(
            anomalies, missing_data, products
        )
        
        # Calculate overall score (weighted average)
        overall_score = self._calculate_overall_score({
            'completeness': (completeness.score, 0.25),
            'validity': (validity.score, 0.25),
            'freshness': (freshness.score, 0.15),
            'consistency': (consistency.score, 0.20),
            'accuracy': (accuracy.score, 0.15)
        })
        
        return DataQualityReport(
            overall_quality_score=overall_score,
            dimensions=DataQualityDimensions(
                completeness=completeness,
                validity=validity,
                freshness=freshness,
                consistency=consistency,
                accuracy=accuracy
            ),
            anomalies=anomalies,
            missing_data=missing_data,
            recommendations=recommendations,
            entities_assessed=len(products),
            assessment_timestamp=datetime.utcnow().isoformat()
        )
    
    def assess_review_data_quality(
        self,
        reviews: List[ReviewResponse]
    ) -> DataQualityReport:
        """
        Assess quality of review data.
        
        Args:
            reviews: List of reviews to assess
            
        Returns:
            Complete data quality report
        """
        if not reviews:
            return self._create_empty_report()
        
        # Assess each dimension
        completeness = self._assess_review_completeness(reviews)
        validity = self._assess_review_validity(reviews)
        freshness = self._assess_review_freshness(reviews)
        consistency = self._assess_review_consistency(reviews)
        accuracy = self._assess_review_accuracy(reviews)
        
        # Detect anomalies
        anomalies = self._detect_review_anomalies(reviews)
        
        # Identify missing data
        missing_data = self._identify_missing_review_data(reviews)
        
        # Generate recommendations
        recommendations = self._generate_review_recommendations(
            anomalies, missing_data, reviews
        )
        
        # Calculate overall score
        overall_score = self._calculate_overall_score({
            'completeness': (completeness.score, 0.20),
            'validity': (validity.score, 0.25),
            'freshness': (freshness.score, 0.15),
            'consistency': (consistency.score, 0.20),
            'accuracy': (accuracy.score, 0.20)
        })
        
        return DataQualityReport(
            overall_quality_score=overall_score,
            dimensions=DataQualityDimensions(
                completeness=completeness,
                validity=validity,
                freshness=freshness,
                consistency=consistency,
                accuracy=accuracy
            ),
            anomalies=anomalies,
            missing_data=missing_data,
            recommendations=recommendations,
            entities_assessed=len(reviews),
            assessment_timestamp=datetime.utcnow().isoformat()
        )
    
    def get_product_quality_metadata(
        self,
        product: ProductResponse,
        quality_report: DataQualityReport
    ) -> ProductQualityMetadata:
        """
        Get quality metadata for a specific product.
        
        Args:
            product: Product to get metadata for
            quality_report: Overall quality report
            
        Returns:
            Product-specific quality metadata
        """
        issues = []
        warnings = []
        
        # Check for product-specific anomalies
        for anomaly in quality_report.anomalies:
            if str(product.id) in anomaly.affected_entities:
                if anomaly.severity in ['high', 'critical']:
                    issues.append(f"{anomaly.type}: {anomaly.description}")
                else:
                    warnings.append(f"{anomaly.type}: {anomaly.description}")
        
        # Calculate product-specific quality score
        product_score = self._calculate_product_specific_score(product)
        
        return ProductQualityMetadata(
            product_id=product.id,
            quality_score=product_score,
            issues=issues,
            warnings=warnings
        )
    
    # ==================== Product Assessment Methods ====================
    
    def _assess_product_completeness(self, products: List[ProductResponse]) -> QualityDimension:
        """Assess completeness of product data"""
        total_fields = len(self.required_product_fields) + 3  # + optional fields
        scores = []
        issues_count = 0
        
        for product in products:
            present_fields = 0
            
            # Check required fields
            for field in self.required_product_fields:
                if getattr(product, field, None) is not None:
                    present_fields += 1
            
            # Check optional but important fields
            if product.category:
                present_fields += 1
            if product.inventory_level is not None:
                present_fields += 1
            if product.metadata:
                present_fields += 1
            
            score = present_fields / total_fields
            scores.append(score)
            
            if score < 0.8:
                issues_count += 1
        
        avg_score = mean(scores) if scores else 0.0
        
        return QualityDimension(
            score=avg_score,
            issues_count=issues_count,
            details=f"{issues_count} products with incomplete data"
        )
    
    def _assess_product_validity(self, products: List[ProductResponse]) -> QualityDimension:
        """Assess validity of product data"""
        issues_count = 0
        
        for product in products:
            # Check price validity
            if product.price <= 0:
                issues_count += 1
            
            # Check SKU format
            if not product.sku or len(product.sku) < 3:
                issues_count += 1
            
            # Check currency code
            if len(product.currency) != 3:
                issues_count += 1
            
            # Check inventory
            if product.inventory_level is not None and product.inventory_level < 0:
                issues_count += 1
        
        score = max(0.0, 1.0 - (issues_count / len(products)))
        
        return QualityDimension(
            score=score,
            issues_count=issues_count,
            details=f"{issues_count} validation issues found"
        )
    
    def _assess_product_freshness(self, products: List[ProductResponse]) -> QualityDimension:
        """Assess freshness of product data"""
        now = datetime.utcnow()
        threshold = timedelta(days=self.freshness_threshold_days)
        stale_count = 0
        
        for product in products:
            if product.updated_at:
                age = now - product.updated_at
                if age > threshold:
                    stale_count += 1
        
        score = max(0.0, 1.0 - (stale_count / len(products)))
        
        return QualityDimension(
            score=score,
            issues_count=stale_count,
            details=f"{stale_count} products with stale data (>{self.freshness_threshold_days} days)"
        )
    
    def _assess_product_consistency(self, products: List[ProductResponse]) -> QualityDimension:
        """Assess consistency of product data"""
        issues_count = 0
        
        # Check for duplicate SKUs
        skus = [p.sku for p in products]
        sku_counts = Counter(skus)
        duplicates = sum(1 for count in sku_counts.values() if count > 1)
        issues_count += duplicates
        
        # Check for inconsistent naming
        names = [p.name.lower() for p in products]
        name_counts = Counter(names)
        duplicate_names = sum(1 for count in name_counts.values() if count > 1)
        issues_count += duplicate_names
        
        score = max(0.0, 1.0 - (issues_count / len(products)))
        
        return QualityDimension(
            score=score,
            issues_count=issues_count,
            details=f"{duplicates} duplicate SKUs, {duplicate_names} duplicate names"
        )
    
    def _assess_product_accuracy(self, products: List[ProductResponse]) -> QualityDimension:
        """Assess accuracy of product data (based on heuristics)"""
        issues_count = 0
        
        for product in products:
            # Check for suspiciously round prices (might be placeholders)
            if product.price % 100 == 0 and product.price > 100:
                issues_count += 0.5  # Soft warning
            
            # Check for generic names
            generic_terms = ['product', 'item', 'test', 'sample', 'demo']
            if any(term in product.name.lower() for term in generic_terms):
                issues_count += 1
        
        score = max(0.0, 1.0 - (issues_count / len(products)))
        
        return QualityDimension(
            score=score,
            issues_count=int(issues_count),
            details=f"{int(issues_count)} potential accuracy issues"
        )
    
    def _detect_product_anomalies(self, products: List[ProductResponse]) -> List[Anomaly]:
        """Detect anomalies in product data"""
        anomalies = []
        
        if len(products) < 3:
            return anomalies  # Need more data for statistical analysis
        
        # Price outlier detection
        prices = [float(p.price) for p in products]
        price_mean = mean(prices)
        price_std = stdev(prices) if len(prices) > 1 else 0
        
        if price_std > 0:
            for product in products:
                z_score = abs((float(product.price) - price_mean) / price_std)
                if z_score > self.price_outlier_threshold:
                    anomalies.append(Anomaly(
                        type="price_outlier",
                        severity="medium" if z_score < 4 else "high",
                        description=f"Price ${product.price} is {z_score:.1f} std devs from mean ${price_mean:.2f}",
                        affected_entities=[str(product.id)],
                        confidence=min(0.95, z_score / 5.0)
                    ))
        
        # Zero inventory detection
        zero_inventory = [p for p in products if p.inventory_level == 0]
        if len(zero_inventory) > len(products) * 0.5:
            anomalies.append(Anomaly(
                type="high_out_of_stock_rate",
                severity="high",
                description=f"{len(zero_inventory)} products out of stock ({len(zero_inventory)/len(products)*100:.1f}%)",
                affected_entities=[str(p.id) for p in zero_inventory],
                confidence=0.9
            ))
        
        return anomalies
    
    def _identify_missing_product_data(self, products: List[ProductResponse]) -> List[MissingData]:
        """Identify missing product data"""
        missing = []
        
        # Check for missing categories
        no_category = sum(1 for p in products if not p.category)
        if no_category > 0:
            missing.append(MissingData(
                field="category",
                impact="medium",
                affected_count=no_category,
                recommendation="Add product categories for better analysis"
            ))
        
        # Check for missing inventory data
        no_inventory = sum(1 for p in products if p.inventory_level is None)
        if no_inventory > 0:
            missing.append(MissingData(
                field="inventory_level",
                impact="medium",
                affected_count=no_inventory,
                recommendation="Add inventory levels for demand forecasting"
            ))
        
        return missing
    
    # ==================== Review Assessment Methods ====================
    
    def _assess_review_completeness(self, reviews: List[ReviewResponse]) -> QualityDimension:
        """Assess completeness of review data"""
        issues_count = 0
        
        for review in reviews:
            if not review.text or len(review.text) < 10:
                issues_count += 1
            if not review.rating or review.rating < 1 or review.rating > 5:
                issues_count += 1
        
        score = max(0.0, 1.0 - (issues_count / (len(reviews) * 2)))
        
        return QualityDimension(
            score=score,
            issues_count=issues_count,
            details=f"{issues_count} incomplete reviews"
        )
    
    def _assess_review_validity(self, reviews: List[ReviewResponse]) -> QualityDimension:
        """Assess validity of review data"""
        issues_count = 0
        
        for review in reviews:
            # Check rating range
            if review.rating < 1 or review.rating > 5:
                issues_count += 1
            
            # Check text length (too short or suspiciously long)
            if len(review.text) < 5 or len(review.text) > 5000:
                issues_count += 1
        
        score = max(0.0, 1.0 - (issues_count / len(reviews)))
        
        return QualityDimension(
            score=score,
            issues_count=issues_count,
            details=f"{issues_count} invalid reviews"
        )
    
    def _assess_review_freshness(self, reviews: List[ReviewResponse]) -> QualityDimension:
        """Assess freshness of review data"""
        now = datetime.utcnow()
        threshold = timedelta(days=90)  # Reviews older than 90 days
        old_count = 0
        
        for review in reviews:
            if review.created_at:
                age = now - review.created_at
                if age > threshold:
                    old_count += 1
        
        score = max(0.0, 1.0 - (old_count / len(reviews)))
        
        return QualityDimension(
            score=score,
            issues_count=old_count,
            details=f"{old_count} reviews older than 90 days"
        )
    
    def _assess_review_consistency(self, reviews: List[ReviewResponse]) -> QualityDimension:
        """Assess consistency of review data"""
        issues_count = 0
        
        # Check for rating-text mismatch
        for review in reviews:
            text_lower = review.text.lower()
            
            # Positive rating with negative text
            if review.rating >= 4 and any(word in text_lower for word in ['terrible', 'awful', 'worst', 'hate']):
                issues_count += 1
            
            # Negative rating with positive text
            if review.rating <= 2 and any(word in text_lower for word in ['excellent', 'amazing', 'best', 'love']):
                issues_count += 1
        
        score = max(0.0, 1.0 - (issues_count / len(reviews)))
        
        return QualityDimension(
            score=score,
            issues_count=issues_count,
            details=f"{issues_count} rating-text mismatches"
        )
    
    def _assess_review_accuracy(self, reviews: List[ReviewResponse]) -> QualityDimension:
        """Assess accuracy of review data (spam detection)"""
        spam_count = sum(1 for r in reviews if r.is_spam)
        
        # Additional spam indicators
        suspicious_count = 0
        for review in reviews:
            # Very short reviews
            if len(review.text) < 10:
                suspicious_count += 0.5
            
            # Excessive caps
            if sum(1 for c in review.text if c.isupper()) / len(review.text) > 0.5:
                suspicious_count += 0.5
            
            # Repeated characters
            if re.search(r'(.)\1{4,}', review.text):
                suspicious_count += 0.5
        
        total_issues = spam_count + int(suspicious_count)
        score = max(0.0, 1.0 - (total_issues / len(reviews)))
        
        return QualityDimension(
            score=score,
            issues_count=total_issues,
            details=f"{spam_count} spam, {int(suspicious_count)} suspicious reviews"
        )
    
    def _detect_review_anomalies(self, reviews: List[ReviewResponse]) -> List[Anomaly]:
        """Detect anomalies in review data"""
        anomalies = []
        
        # Check for review bombing (many reviews in short time)
        if len(reviews) >= 10:
            recent_reviews = [r for r in reviews if (datetime.utcnow() - r.created_at).days < 7]
            if len(recent_reviews) > len(reviews) * 0.5:
                anomalies.append(Anomaly(
                    type="review_surge",
                    severity="medium",
                    description=f"{len(recent_reviews)} reviews in last 7 days (possible review bombing)",
                    affected_entities=[str(r.id) for r in recent_reviews],
                    confidence=0.7
                ))
        
        # Check for rating polarization
        ratings = [r.rating for r in reviews]
        if len(ratings) >= 5:
            extreme_ratings = sum(1 for r in ratings if r == 1 or r == 5)
            if extreme_ratings / len(ratings) > 0.8:
                anomalies.append(Anomaly(
                    type="rating_polarization",
                    severity="low",
                    description=f"{extreme_ratings/len(ratings)*100:.1f}% of ratings are extreme (1 or 5 stars)",
                    affected_entities=[],
                    confidence=0.6
                ))
        
        return anomalies
    
    def _identify_missing_review_data(self, reviews: List[ReviewResponse]) -> List[MissingData]:
        """Identify missing review data"""
        missing = []
        
        # Check for missing sentiment analysis
        no_sentiment = sum(1 for r in reviews if not r.sentiment)
        if no_sentiment > 0:
            missing.append(MissingData(
                field="sentiment",
                impact="low",
                affected_count=no_sentiment,
                recommendation="Run sentiment analysis on reviews"
            ))
        
        return missing
    
    # ==================== Helper Methods ====================
    
    def _generate_product_recommendations(
        self,
        anomalies: List[Anomaly],
        missing_data: List[MissingData],
        products: List[ProductResponse]
    ) -> List[str]:
        """Generate actionable recommendations for product data"""
        recommendations = []
        
        # Recommendations based on anomalies
        for anomaly in anomalies:
            if anomaly.type == "price_outlier" and anomaly.severity == "high":
                recommendations.append(f"Verify pricing for products with outlier prices")
            elif anomaly.type == "high_out_of_stock_rate":
                recommendations.append("Review inventory management - high out-of-stock rate detected")
        
        # Recommendations based on missing data
        for missing in missing_data:
            if missing.recommendation:
                recommendations.append(missing.recommendation)
        
        # General recommendations
        stale_products = sum(1 for p in products if (datetime.utcnow() - p.updated_at).days > 30)
        if stale_products > len(products) * 0.3:
            recommendations.append(f"Refresh data for {stale_products} products (>30 days old)")
        
        return recommendations
    
    def _generate_review_recommendations(
        self,
        anomalies: List[Anomaly],
        missing_data: List[MissingData],
        reviews: List[ReviewResponse]
    ) -> List[str]:
        """Generate actionable recommendations for review data"""
        recommendations = []
        
        for anomaly in anomalies:
            if anomaly.type == "review_surge":
                recommendations.append("Investigate recent review surge for authenticity")
            elif anomaly.type == "rating_polarization":
                recommendations.append("Analyze polarized ratings for product quality issues")
        
        for missing in missing_data:
            if missing.recommendation:
                recommendations.append(missing.recommendation)
        
        # Check if enough reviews for confidence
        if len(reviews) < self.min_reviews_for_confidence:
            recommendations.append(f"Collect more reviews (current: {len(reviews)}, recommended: {self.min_reviews_for_confidence}+)")
        
        return recommendations
    
    def _calculate_overall_score(self, dimension_scores: Dict[str, tuple]) -> float:
        """Calculate weighted overall quality score"""
        total_weight = sum(weight for _, weight in dimension_scores.values())
        weighted_sum = sum(score * weight for score, weight in dimension_scores.values())
        return round(weighted_sum / total_weight, 3)
    
    def _calculate_product_specific_score(self, product: ProductResponse) -> float:
        """Calculate quality score for a specific product"""
        score = 1.0
        
        # Deduct for missing fields
        if not product.category:
            score -= 0.1
        if product.inventory_level is None:
            score -= 0.1
        
        # Deduct for invalid data
        if product.price <= 0:
            score -= 0.3
        
        # Deduct for stale data
        if (datetime.utcnow() - product.updated_at).days > 30:
            score -= 0.2
        
        return max(0.0, score)
    
    def _create_empty_report(self) -> DataQualityReport:
        """Create an empty quality report"""
        empty_dimension = QualityDimension(score=0.0, issues_count=0, details="No data to assess")
        
        return DataQualityReport(
            overall_quality_score=0.0,
            dimensions=DataQualityDimensions(
                completeness=empty_dimension,
                validity=empty_dimension,
                freshness=empty_dimension,
                consistency=empty_dimension,
                accuracy=empty_dimension
            ),
            anomalies=[],
            missing_data=[],
            recommendations=["No data available for quality assessment"],
            entities_assessed=0,
            assessment_timestamp=datetime.utcnow().isoformat()
        )
