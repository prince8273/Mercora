"""Data processing pipeline orchestration"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime

from src.processing.validator import DataValidator, ValidationResult
from src.processing.normalizer import SKUNormalizer
from src.processing.deduplicator import Deduplicator
from src.processing.spam_filter import SpamFilter
from src.processing.missing_data_handler import MissingDataHandler
from src.processing.lineage_tracker import LineageTracker, TransformationType


class ProcessingPipeline:
    """
    Orchestrates the complete data processing pipeline.
    
    Pipeline stages:
    1. Validation - Validate data against schemas
    2. Spam Filtering - Remove spam reviews
    3. Normalization - Normalize SKUs and formats
    4. Deduplication - Remove duplicate records
    5. Missing Data Handling - Handle missing fields
    
    All stages are tracked via lineage tracker.
    """
    
    def __init__(self, tenant_id: UUID):
        """
        Initialize processing pipeline.
        
        Args:
            tenant_id: Tenant UUID for isolation
        """
        self.tenant_id = tenant_id
        
        # Initialize components
        self.validator = DataValidator()
        self.normalizer = SKUNormalizer()
        self.deduplicator = Deduplicator()
        self.spam_filter = SpamFilter(spam_threshold=0.5)
        self.missing_data_handler = MissingDataHandler()
        self.lineage_tracker = LineageTracker(tenant_id)
        
        # Pipeline statistics
        self.stats = {
            'pipelines_executed': 0,
            'total_records_processed': 0,
            'total_records_filtered': 0
        }
    
    def process_products(
        self,
        products: List[Dict[str, Any]],
        source: str = "unknown",
        skip_validation: bool = False,
        skip_deduplication: bool = False
    ) -> Dict[str, Any]:
        """
        Process product data through the complete pipeline.
        
        Args:
            products: List of raw product dictionaries
            source: Data source name
            skip_validation: Skip validation stage
            skip_deduplication: Skip deduplication stage
            
        Returns:
            Dictionary with processed products and pipeline metadata
        """
        pipeline_id = self.lineage_tracker.start_pipeline(f"product_processing_{source}")
        
        # Track ingestion
        ingestion_node_id = self.lineage_tracker.track_ingestion(
            source=source,
            data_type="product",
            record_count=len(products),
            metadata={'raw_record_count': len(products)}
        )
        
        current_node_id = ingestion_node_id
        current_data = products
        
        # Stage 1: Validation
        if not skip_validation:
            validated_data, current_node_id = self._validate_products(
                current_data, current_node_id
            )
            current_data = validated_data
        
        # Stage 2: Normalization
        normalized_data, current_node_id = self._normalize_products(
            current_data, current_node_id
        )
        current_data = normalized_data
        
        # Stage 3: Deduplication
        if not skip_deduplication:
            deduplicated_data, current_node_id = self._deduplicate_products(
                current_data, current_node_id
            )
            current_data = deduplicated_data
        
        # Stage 4: Missing Data Handling
        final_data, current_node_id = self._handle_missing_product_data(
            current_data, current_node_id
        )
        
        # Update statistics
        self.stats['pipelines_executed'] += 1
        self.stats['total_records_processed'] += len(products)
        self.stats['total_records_filtered'] += len(products) - len(final_data)
        
        # Get pipeline lineage
        lineage = self.lineage_tracker.get_pipeline_lineage(pipeline_id)
        
        return {
            'success': True,
            'pipeline_id': pipeline_id,
            'products': final_data,
            'statistics': {
                'input_count': len(products),
                'output_count': len(final_data),
                'filtered_count': len(products) - len(final_data),
                'retention_rate': len(final_data) / len(products) if products else 0.0
            },
            'lineage': lineage
        }
    
    def process_reviews(
        self,
        reviews: List[Dict[str, Any]],
        source: str = "unknown",
        skip_validation: bool = False,
        skip_spam_filtering: bool = False,
        skip_deduplication: bool = False
    ) -> Dict[str, Any]:
        """
        Process review data through the complete pipeline.
        
        Args:
            reviews: List of raw review dictionaries
            source: Data source name
            skip_validation: Skip validation stage
            skip_spam_filtering: Skip spam filtering stage
            skip_deduplication: Skip deduplication stage
            
        Returns:
            Dictionary with processed reviews and pipeline metadata
        """
        pipeline_id = self.lineage_tracker.start_pipeline(f"review_processing_{source}")
        
        # Track ingestion
        ingestion_node_id = self.lineage_tracker.track_ingestion(
            source=source,
            data_type="review",
            record_count=len(reviews),
            metadata={'raw_record_count': len(reviews)}
        )
        
        current_node_id = ingestion_node_id
        current_data = reviews
        
        # Stage 1: Validation
        if not skip_validation:
            validated_data, current_node_id = self._validate_reviews(
                current_data, current_node_id
            )
            current_data = validated_data
        
        # Stage 2: Spam Filtering
        if not skip_spam_filtering:
            filtered_data, current_node_id = self._filter_spam_reviews(
                current_data, current_node_id
            )
            current_data = filtered_data
        
        # Stage 3: Deduplication
        if not skip_deduplication:
            deduplicated_data, current_node_id = self._deduplicate_reviews(
                current_data, current_node_id
            )
            current_data = deduplicated_data
        
        # Stage 4: Missing Data Handling
        final_data, current_node_id = self._handle_missing_review_data(
            current_data, current_node_id
        )
        
        # Update statistics
        self.stats['pipelines_executed'] += 1
        self.stats['total_records_processed'] += len(reviews)
        self.stats['total_records_filtered'] += len(reviews) - len(final_data)
        
        # Get pipeline lineage
        lineage = self.lineage_tracker.get_pipeline_lineage(pipeline_id)
        
        return {
            'success': True,
            'pipeline_id': pipeline_id,
            'reviews': final_data,
            'statistics': {
                'input_count': len(reviews),
                'output_count': len(final_data),
                'filtered_count': len(reviews) - len(final_data),
                'spam_filtered': len(reviews) - len(final_data),  # Approximate
                'retention_rate': len(final_data) / len(reviews) if reviews else 0.0
            },
            'lineage': lineage
        }
    
    def _validate_products(
        self,
        products: List[Dict[str, Any]],
        source_node_id: str
    ) -> tuple[List[Dict[str, Any]], str]:
        """Validate products and track lineage"""
        validated = []
        validation_errors = []
        
        for product in products:
            result = self.validator.validate_product_data(product)
            if result.is_valid:
                validated.append(result.validated_data)
            else:
                validation_errors.append({
                    'product': product,
                    'errors': result.errors
                })
        
        # Track transformation
        node_id = self.lineage_tracker.track_transformation(
            source_node_id=source_node_id,
            transformation_type=TransformationType.VALIDATION,
            records_in=len(products),
            records_out=len(validated),
            metadata={
                'validation_errors': len(validation_errors),
                'error_rate': len(validation_errors) / len(products) if products else 0.0
            }
        )
        
        return validated, node_id
    
    def _validate_reviews(
        self,
        reviews: List[Dict[str, Any]],
        source_node_id: str
    ) -> tuple[List[Dict[str, Any]], str]:
        """Validate reviews and track lineage"""
        validated = []
        validation_errors = []
        
        for review in reviews:
            result = self.validator.validate_review_data(review)
            if result.is_valid:
                validated.append(result.validated_data)
            else:
                validation_errors.append({
                    'review': review,
                    'errors': result.errors
                })
        
        # Track transformation
        node_id = self.lineage_tracker.track_transformation(
            source_node_id=source_node_id,
            transformation_type=TransformationType.VALIDATION,
            records_in=len(reviews),
            records_out=len(validated),
            metadata={
                'validation_errors': len(validation_errors),
                'error_rate': len(validation_errors) / len(reviews) if reviews else 0.0
            }
        )
        
        return validated, node_id
    
    def _normalize_products(
        self,
        products: List[Dict[str, Any]],
        source_node_id: str
    ) -> tuple[List[Dict[str, Any]], str]:
        """Normalize product SKUs and track lineage"""
        normalized = []
        
        for product in products:
            sku = product.get('sku', '')
            marketplace = product.get('marketplace', '')
            
            normalized_sku = self.normalizer.normalize_sku(sku, marketplace)
            
            product['normalized_sku'] = normalized_sku
            product['original_sku'] = sku
            normalized.append(product)
        
        # Track transformation
        node_id = self.lineage_tracker.track_transformation(
            source_node_id=source_node_id,
            transformation_type=TransformationType.NORMALIZATION,
            records_in=len(products),
            records_out=len(normalized),
            metadata={'normalization_applied': True}
        )
        
        return normalized, node_id
    
    def _deduplicate_products(
        self,
        products: List[Dict[str, Any]],
        source_node_id: str
    ) -> tuple[List[Dict[str, Any]], str]:
        """Deduplicate products and track lineage"""
        deduplicated = self.deduplicator.deduplicate_products(products)
        
        duplicates_removed = len(products) - len(deduplicated)
        
        # Track transformation
        node_id = self.lineage_tracker.track_transformation(
            source_node_id=source_node_id,
            transformation_type=TransformationType.DEDUPLICATION,
            records_in=len(products),
            records_out=len(deduplicated),
            metadata={
                'duplicates_removed': duplicates_removed,
                'deduplication_rate': duplicates_removed / len(products) if products else 0.0
            }
        )
        
        return deduplicated, node_id
    
    def _deduplicate_reviews(
        self,
        reviews: List[Dict[str, Any]],
        source_node_id: str
    ) -> tuple[List[Dict[str, Any]], str]:
        """Deduplicate reviews and track lineage"""
        deduplicated = self.deduplicator.deduplicate_reviews(reviews)
        
        duplicates_removed = len(reviews) - len(deduplicated)
        
        # Track transformation
        node_id = self.lineage_tracker.track_transformation(
            source_node_id=source_node_id,
            transformation_type=TransformationType.DEDUPLICATION,
            records_in=len(reviews),
            records_out=len(deduplicated),
            metadata={
                'duplicates_removed': duplicates_removed,
                'deduplication_rate': duplicates_removed / len(reviews) if reviews else 0.0
            }
        )
        
        return deduplicated, node_id
    
    def _filter_spam_reviews(
        self,
        reviews: List[Dict[str, Any]],
        source_node_id: str
    ) -> tuple[List[Dict[str, Any]], str]:
        """Filter spam reviews and track lineage"""
        filtered = self.spam_filter.filter_spam_reviews(reviews, mark_only=False)
        
        spam_removed = len(reviews) - len(filtered)
        
        # Track transformation
        node_id = self.lineage_tracker.track_transformation(
            source_node_id=source_node_id,
            transformation_type=TransformationType.SPAM_FILTERING,
            records_in=len(reviews),
            records_out=len(filtered),
            metadata={
                'spam_removed': spam_removed,
                'spam_rate': spam_removed / len(reviews) if reviews else 0.0,
                'spam_filter_stats': self.spam_filter.get_statistics()
            }
        )
        
        return filtered, node_id
    
    def _handle_missing_product_data(
        self,
        products: List[Dict[str, Any]],
        source_node_id: str
    ) -> tuple[List[Dict[str, Any]], str]:
        """Handle missing product data and track lineage"""
        handled = []
        
        for product in products:
            handled_product = self.missing_data_handler.handle_missing_product_data(
                product, apply_defaults=True
            )
            handled.append(handled_product)
        
        # Count records with missing data
        records_with_missing = sum(
            1 for p in handled if p.get('_has_missing_data', False)
        )
        
        # Track transformation
        node_id = self.lineage_tracker.track_transformation(
            source_node_id=source_node_id,
            transformation_type=TransformationType.MISSING_DATA_HANDLING,
            records_in=len(products),
            records_out=len(handled),
            metadata={
                'records_with_missing_data': records_with_missing,
                'missing_data_rate': records_with_missing / len(products) if products else 0.0
            }
        )
        
        return handled, node_id
    
    def _handle_missing_review_data(
        self,
        reviews: List[Dict[str, Any]],
        source_node_id: str
    ) -> tuple[List[Dict[str, Any]], str]:
        """Handle missing review data and track lineage"""
        handled = []
        
        for review in reviews:
            handled_review = self.missing_data_handler.handle_missing_review_data(
                review, apply_defaults=True
            )
            handled.append(handled_review)
        
        # Count records with missing data
        records_with_missing = sum(
            1 for r in handled if r.get('_has_missing_data', False)
        )
        
        # Track transformation
        node_id = self.lineage_tracker.track_transformation(
            source_node_id=source_node_id,
            transformation_type=TransformationType.MISSING_DATA_HANDLING,
            records_in=len(reviews),
            records_out=len(handled),
            metadata={
                'records_with_missing_data': records_with_missing,
                'missing_data_rate': records_with_missing / len(reviews) if reviews else 0.0
            }
        )
        
        return handled, node_id
    
    def get_pipeline_statistics(self) -> Dict[str, Any]:
        """
        Get overall pipeline statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            **self.stats,
            'spam_filter_stats': self.spam_filter.get_statistics(),
            'all_pipelines': self.lineage_tracker.get_all_pipelines()
        }
    
    def get_lineage_for_pipeline(self, pipeline_id: str) -> Dict[str, Any]:
        """
        Get complete lineage for a specific pipeline execution.
        
        Args:
            pipeline_id: Pipeline execution ID
            
        Returns:
            Complete lineage information
        """
        return self.lineage_tracker.get_pipeline_lineage(pipeline_id)
    
    def export_lineage_graph(self) -> Dict[str, Any]:
        """
        Export complete lineage graph for visualization.
        
        Returns:
            Graph data suitable for visualization
        """
        return self.lineage_tracker.export_lineage_graph()
