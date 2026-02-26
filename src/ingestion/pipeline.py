"""Data ingestion pipeline integrating all components"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import UUID
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from src.ingestion.scheduler import IngestionScheduler
from src.ingestion.marketplace_connector import MarketplaceConnector, RawDataRecord
from src.ingestion.competitor_scraper import CompetitorScraper, ScrapedData
from src.processing.validator import DataValidator
from src.processing.normalizer import SKUNormalizer
from src.processing.deduplicator import Deduplicator
from src.processing.missing_data_handler import MissingDataHandler
from src.processing.spam_filter import SpamFilter
from src.processing.lineage_tracker import LineageTracker, TransformationType
from src.models.product import Product
from src.models.review import Review

logger = logging.getLogger(__name__)


class IngestionPipeline:
    """
    Complete data ingestion pipeline.
    
    Integrates ingestion, validation, normalization, and storage.
    
    Responsibilities:
    - Orchestrate data collection from multiple sources
    - Validate and clean ingested data
    - Handle errors with isolation
    - Store processed data
    """
    
    def __init__(self, tenant_id: UUID, db: Optional[AsyncSession] = None):
        """
        Initialize ingestion pipeline.
        
        Args:
            tenant_id: Tenant UUID
            db: Optional database session for persistence
        """
        self.tenant_id = tenant_id
        self.db = db
        self.scheduler = IngestionScheduler()
        self.validator = DataValidator()
        self.normalizer = SKUNormalizer()
        self.deduplicator = Deduplicator()
        self.missing_data_handler = MissingDataHandler()
        self.spam_filter = SpamFilter(spam_threshold=0.6)
        self.lineage_tracker = LineageTracker(tenant_id)
        
        # Track ingestion statistics
        self.stats = {
            'total_ingested': 0,
            'total_validated': 0,
            'total_rejected': 0,
            'total_spam_filtered': 0,
            'total_stored': 0,
            'errors': []
        }
    
    async def ingest_from_marketplace(
        self,
        marketplace: str,
        credentials: Dict[str, str],
        data_types: List[str] = None
    ) -> Dict[str, Any]:
        """
        Ingest data from a marketplace API.
        
        Args:
            marketplace: Marketplace name
            credentials: API credentials
            data_types: Types of data to fetch (products, sales, inventory)
            
        Returns:
            Ingestion result dictionary
        """
        if data_types is None:
            data_types = ['products']
        
        logger.info(f"Starting ingestion from {marketplace}")
        
        result = {
            'marketplace': marketplace,
            'start_time': datetime.utcnow(),
            'data_types': data_types,
            'records_ingested': 0,
            'records_validated': 0,
            'records_rejected': 0,
            'errors': []
        }
        
        try:
            # Create connector
            connector = MarketplaceConnector(
                tenant_id=self.tenant_id,
                marketplace=marketplace,
                credentials=credentials
            )
            
            # Authenticate
            if not connector.authenticate():
                raise Exception(f"Authentication failed for {marketplace}")
            
            # Fetch data based on types
            all_records = []
            
            if 'products' in data_types:
                try:
                    products = connector.fetch_with_retry(connector.fetch_products, limit=50)
                    all_records.extend(products)
                    logger.info(f"Fetched {len(products)} products from {marketplace}")
                except Exception as e:
                    logger.error(f"Failed to fetch products: {str(e)}")
                    result['errors'].append(f"Products: {str(e)}")
            
            if 'sales' in data_types:
                try:
                    start_date = datetime.utcnow().replace(day=1)
                    end_date = datetime.utcnow()
                    sales = connector.fetch_with_retry(
                        connector.fetch_sales_data,
                        start_date=start_date,
                        end_date=end_date
                    )
                    all_records.extend(sales)
                    logger.info(f"Fetched {len(sales)} sales records from {marketplace}")
                except Exception as e:
                    logger.error(f"Failed to fetch sales: {str(e)}")
                    result['errors'].append(f"Sales: {str(e)}")
            
            if 'inventory' in data_types:
                try:
                    inventory = connector.fetch_with_retry(connector.fetch_inventory)
                    all_records.extend(inventory)
                    logger.info(f"Fetched {len(inventory)} inventory records from {marketplace}")
                except Exception as e:
                    logger.error(f"Failed to fetch inventory: {str(e)}")
                    result['errors'].append(f"Inventory: {str(e)}")
            
            result['records_ingested'] = len(all_records)
            self.stats['total_ingested'] += len(all_records)
            
            # Process records
            if all_records:
                processed = await self._process_records(all_records)
                result['records_validated'] = processed['validated']
                result['records_rejected'] = processed['rejected']
                result['processed_data'] = processed['data']
            
        except Exception as e:
            logger.error(f"Ingestion from {marketplace} failed: {str(e)}")
            result['errors'].append(str(e))
            self.stats['errors'].append({
                'marketplace': marketplace,
                'error': str(e),
                'timestamp': datetime.utcnow()
            })
        
        result['end_time'] = datetime.utcnow()
        result['duration_seconds'] = (result['end_time'] - result['start_time']).total_seconds()
        
        return result
    
    async def ingest_from_competitors(
        self,
        competitor_urls: Dict[str, List[str]]
    ) -> Dict[str, Any]:
        """
        Ingest data from competitor websites via scraping.
        
        Args:
            competitor_urls: Dictionary mapping competitor names to URL lists
            
        Returns:
            Ingestion result dictionary
        """
        logger.info(f"Starting competitor scraping for {len(competitor_urls)} competitors")
        
        result = {
            'start_time': datetime.utcnow(),
            'competitors': list(competitor_urls.keys()),
            'total_urls': sum(len(urls) for urls in competitor_urls.values()),
            'records_scraped': 0,
            'records_validated': 0,
            'records_rejected': 0,
            'errors': []
        }
        
        try:
            # Create scraper
            scraper = CompetitorScraper(tenant_id=self.tenant_id)
            
            # Scrape data
            scraped_data = scraper.scrape_competitor_prices(competitor_urls)
            result['records_scraped'] = len(scraped_data)
            self.stats['total_ingested'] += len(scraped_data)
            
            # Convert to raw records format
            raw_records = []
            for scraped in scraped_data:
                record = RawDataRecord(
                    source=scraped.domain,
                    data_type=scraped.data_type,
                    data=scraped.data,
                    timestamp=scraped.timestamp,
                    metadata=scraped.metadata
                )
                raw_records.append(record)
            
            # Process records
            if raw_records:
                processed = await self._process_records(raw_records)
                result['records_validated'] = processed['validated']
                result['records_rejected'] = processed['rejected']
                result['processed_data'] = processed['data']
            
        except Exception as e:
            logger.error(f"Competitor scraping failed: {str(e)}")
            result['errors'].append(str(e))
            self.stats['errors'].append({
                'source': 'competitor_scraping',
                'error': str(e),
                'timestamp': datetime.utcnow()
            })
        
        result['end_time'] = datetime.utcnow()
        result['duration_seconds'] = (result['end_time'] - result['start_time']).total_seconds()
        
        return result
    
    async def _process_records(self, records: List[RawDataRecord]) -> Dict[str, Any]:
        """
        Process raw records through validation and cleaning pipeline.
        
        Args:
            records: List of raw data records
            
        Returns:
            Processing result dictionary
        """
        # Start lineage tracking for this pipeline run
        pipeline_id = self.lineage_tracker.start_pipeline("data_processing")
        
        validated_count = 0
        rejected_count = 0
        spam_filtered_count = 0
        processed_data = []
        
        # Group by data type
        products = [r for r in records if r.data_type == 'product']
        reviews = [r for r in records if r.data_type == 'review']
        
        # Process products
        if products:
            product_data = [r.data for r in products]
            
            # Track ingestion
            ingestion_node_id = self.lineage_tracker.track_ingestion(
                source=products[0].source if products else "unknown",
                data_type="product",
                record_count=len(product_data),
                metadata={'raw_records': len(products)}
            )
            
            # Validate
            validated_products = []
            for product in product_data:
                validation_result = self.validator.validate_product_data(product)
                if validation_result.is_valid:
                    validated_products.append(validation_result.validated_data)
                    validated_count += 1
                else:
                    rejected_count += 1
                    logger.warning(f"Product validation failed: {validation_result.errors}")
            
            # Track validation
            validation_node_id = self.lineage_tracker.track_transformation(
                source_node_id=ingestion_node_id,
                transformation_type=TransformationType.VALIDATION,
                records_in=len(product_data),
                records_out=len(validated_products),
                metadata={
                    'rejected': rejected_count,
                    'validation_errors': rejected_count
                }
            )
            
            # Normalize SKUs
            for product in validated_products:
                normalized_sku = self.normalizer.normalize_sku(
                    product['sku'],
                    product.get('marketplace')
                )
                product['normalized_sku'] = normalized_sku
            
            # Track normalization
            normalization_node_id = self.lineage_tracker.track_transformation(
                source_node_id=validation_node_id,
                transformation_type=TransformationType.NORMALIZATION,
                records_in=len(validated_products),
                records_out=len(validated_products),
                metadata={'normalized_field': 'sku'}
            )
            
            # Deduplicate
            deduplicated = self.deduplicator.deduplicate_products(validated_products)
            duplicates_removed = len(validated_products) - len(deduplicated)
            
            # Track deduplication
            dedup_node_id = self.lineage_tracker.track_transformation(
                source_node_id=normalization_node_id,
                transformation_type=TransformationType.DEDUPLICATION,
                records_in=len(validated_products),
                records_out=len(deduplicated),
                metadata={'duplicates_removed': duplicates_removed}
            )
            
            # Handle missing data
            for product in deduplicated:
                complete_product = self.missing_data_handler.handle_missing_product_data(
                    product,
                    apply_defaults=True
                )
                processed_data.append(complete_product)
            
            # Track missing data handling
            self.lineage_tracker.track_transformation(
                source_node_id=dedup_node_id,
                transformation_type=TransformationType.MISSING_DATA_HANDLING,
                records_in=len(deduplicated),
                records_out=len(processed_data),
                metadata={'defaults_applied': True}
            )
        
        # Process reviews
        if reviews:
            review_data = [r.data for r in reviews]
            
            # Track ingestion
            ingestion_node_id = self.lineage_tracker.track_ingestion(
                source=reviews[0].source if reviews else "unknown",
                data_type="review",
                record_count=len(review_data),
                metadata={'raw_records': len(reviews)}
            )
            
            # Validate
            validated_reviews = []
            for review in review_data:
                validation_result = self.validator.validate_review_data(review)
                if validation_result.is_valid:
                    validated_reviews.append(validation_result.validated_data)
                    validated_count += 1
                else:
                    rejected_count += 1
                    logger.warning(f"Review validation failed: {validation_result.errors}")
            
            # Track validation
            validation_node_id = self.lineage_tracker.track_transformation(
                source_node_id=ingestion_node_id,
                transformation_type=TransformationType.VALIDATION,
                records_in=len(review_data),
                records_out=len(validated_reviews),
                metadata={
                    'rejected': rejected_count,
                    'validation_errors': rejected_count
                }
            )
            
            # Filter spam
            filtered_reviews = self.spam_filter.filter_spam_reviews(
                validated_reviews,
                mark_only=False  # Remove spam reviews
            )
            spam_filtered_count = len(validated_reviews) - len(filtered_reviews)
            
            # Track spam filtering
            spam_filter_node_id = self.lineage_tracker.track_transformation(
                source_node_id=validation_node_id,
                transformation_type=TransformationType.SPAM_FILTERING,
                records_in=len(validated_reviews),
                records_out=len(filtered_reviews),
                metadata={
                    'spam_removed': spam_filtered_count,
                    'spam_rate': spam_filtered_count / len(validated_reviews) if validated_reviews else 0.0
                }
            )
            
            # Deduplicate
            deduplicated_reviews = self.deduplicator.deduplicate_reviews(filtered_reviews)
            duplicates_removed = len(filtered_reviews) - len(deduplicated_reviews)
            
            # Track deduplication
            dedup_node_id = self.lineage_tracker.track_transformation(
                source_node_id=spam_filter_node_id,
                transformation_type=TransformationType.DEDUPLICATION,
                records_in=len(filtered_reviews),
                records_out=len(deduplicated_reviews),
                metadata={'duplicates_removed': duplicates_removed}
            )
            
            # Handle missing data
            for review in deduplicated_reviews:
                complete_review = self.missing_data_handler.handle_missing_review_data(
                    review,
                    apply_defaults=True
                )
                processed_data.append(complete_review)
            
            # Track missing data handling
            self.lineage_tracker.track_transformation(
                source_node_id=dedup_node_id,
                transformation_type=TransformationType.MISSING_DATA_HANDLING,
                records_in=len(deduplicated_reviews),
                records_out=len(processed_data),
                metadata={'defaults_applied': True}
            )
        
        self.stats['total_validated'] += validated_count
        self.stats['total_rejected'] += rejected_count
        self.stats['total_spam_filtered'] += spam_filtered_count
        self.stats['total_stored'] += len(processed_data)
        
        # Persist to database if session provided
        if self.db:
            await self._persist_to_database(processed_data, products, reviews)
        
        return {
            'validated': validated_count,
            'rejected': rejected_count,
            'spam_filtered': spam_filtered_count,
            'data': processed_data,
            'pipeline_id': pipeline_id
        }
    
    async def _persist_to_database(
        self,
        processed_data: List[Dict[str, Any]],
        products: List[RawDataRecord],
        reviews: List[RawDataRecord]
    ) -> None:
        """
        Persist processed data to database.
        
        Args:
            processed_data: List of processed data dictionaries
            products: Original product records
            reviews: Original review records
        """
        try:
            # Separate products and reviews from processed data
            product_count = len(products)
            
            # Save products
            for i, product_data in enumerate(processed_data[:product_count]):
                product = Product(
                    tenant_id=self.tenant_id,
                    sku=product_data.get('sku'),
                    normalized_sku=product_data.get('normalized_sku'),
                    name=product_data.get('name'),
                    category=product_data.get('category'),
                    price=product_data.get('price'),
                    currency=product_data.get('currency', 'USD'),
                    marketplace=product_data.get('marketplace'),
                    inventory_level=product_data.get('inventory_level'),
                    extra_metadata=product_data.get('metadata', {})
                )
                self.db.add(product)
            
            # Save reviews
            for review_data in processed_data[product_count:]:
                review = Review(
                    tenant_id=self.tenant_id,
                    product_id=review_data.get('product_id'),
                    rating=review_data.get('rating'),
                    text=review_data.get('text'),
                    source=review_data.get('source'),
                    sentiment=review_data.get('sentiment'),
                    sentiment_confidence=review_data.get('sentiment_confidence'),
                    is_spam=review_data.get('is_spam', False)
                )
                self.db.add(review)
            
            # Commit all changes
            await self.db.commit()
            logger.info(f"Persisted {len(processed_data)} records to database")
            
        except Exception as e:
            logger.error(f"Failed to persist data to database: {e}")
            await self.db.rollback()
            raise
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get ingestion pipeline statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            **self.stats,
            'success_rate': (
                self.stats['total_validated'] / self.stats['total_ingested']
                if self.stats['total_ingested'] > 0 else 0.0
            ),
            'spam_filter_stats': self.spam_filter.get_statistics(),
            'lineage_pipelines': self.lineage_tracker.get_all_pipelines()
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
