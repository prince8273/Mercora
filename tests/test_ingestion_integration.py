"""Integration tests for data ingestion pipeline"""
import pytest
import asyncio
from datetime import datetime
from uuid import uuid4
from pathlib import Path
from sqlalchemy import text

from src.ingestion.connectors.csv_connector import CSVConnector
from src.ingestion.ingestion_service import IngestionService
from src.models.raw_ingestion_record import RawIngestionRecord
from src.database import AsyncSessionLocal


class TestIngestionIntegration:
    """Integration tests for end-to-end ingestion flow"""
    
    @pytest.fixture
    def tenant_id(self):
        """Fixture for tenant ID"""
        # Use the demo tenant from seed script
        return uuid4()
    
    @pytest.fixture
    def sample_products_csv(self):
        """Path to sample products CSV"""
        return "sample_data/products_sample.csv"
    
    @pytest.fixture
    def sample_reviews_csv(self):
        """Path to sample reviews CSV"""
        return "sample_data/reviews_sample.csv"
    
    @pytest.fixture(autouse=True)
    async def cleanup_test_data(self, tenant_id):
        """Clean up test data before and after each test"""
        async with AsyncSessionLocal() as db:
            try:
                # Clean up before test
                result = await db.execute(
                    text(f"DELETE FROM raw_ingestion_records WHERE tenant_id = '{tenant_id}'")
                )
                await db.commit()
                
                yield
                
                # Clean up after test
                result = await db.execute(
                    text(f"DELETE FROM raw_ingestion_records WHERE tenant_id = '{tenant_id}'")
                )
                await db.commit()
            except Exception as e:
                await db.rollback()
                raise
    
    @pytest.mark.asyncio
    async def test_ingest_products_csv_end_to_end(self, tenant_id, sample_products_csv):
        """Test complete ingestion flow: CSV → raw_ingestion_records"""
        # Verify CSV file exists
        assert Path(sample_products_csv).exists()
        
        # Create connector
        connector = CSVConnector(
            tenant_id=tenant_id,
            file_path=sample_products_csv,
            source_name="csv_products",
            id_column="sku",
            data_type="product"
        )
        
        # Create ingestion service
        service = IngestionService(tenant_id=tenant_id)
        
        # Ingest data
        result = service.ingest_from_connector(connector)
        
        # Verify result
        assert result['success'] is True
        assert result['statistics']['records_fetched'] == 10
        assert result['statistics']['records_saved'] == 10
        assert result['statistics']['records_skipped_duplicate'] == 0
        assert result['statistics']['records_failed'] == 0
        
        # Verify data in database
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                text(f"SELECT * FROM raw_ingestion_records WHERE tenant_id = '{tenant_id}' AND source = 'csv_products'")
            )
            records = result.fetchall()
            
            assert len(records) == 10
    
    def test_ingest_reviews_csv_end_to_end(self, tenant_id, sample_reviews_csv):
        """Test ingestion of reviews CSV"""
        assert Path(sample_reviews_csv).exists()
        
        connector = CSVConnector(
            tenant_id=tenant_id,
            file_path=sample_reviews_csv,
            source_name="csv_reviews",
            id_column="product_sku",  # Different ID column
            data_type="review"
        )
        
        service = IngestionService(tenant_id=tenant_id)
        result = service.ingest_from_connector(connector)
        
        assert result['success'] is True
        assert result['statistics']['records_fetched'] == 10
        assert result['statistics']['records_saved'] == 10
        
        # Verify in database
        db = next(get_db())
        try:
            records = db.query(RawIngestionRecord).filter(
                RawIngestionRecord.tenant_id == tenant_id,
                RawIngestionRecord.source == "csv_reviews"
            ).all()
            
            assert len(records) == 10
            
            # Check review-specific fields
            first_record = records[0]
            assert 'rating' in first_record.payload
            assert 'review_text' in first_record.payload
            assert first_record.ingestion_metadata['data_type'] == 'review'
        finally:
            db.close()
    
    def test_idempotency_duplicate_ingestion(self, tenant_id, sample_products_csv):
        """Test that re-ingesting same data doesn't create duplicates"""
        connector = CSVConnector(
            tenant_id=tenant_id,
            file_path=sample_products_csv,
            source_name="csv_products",
            id_column="sku",
            data_type="product"
        )
        
        service = IngestionService(tenant_id=tenant_id)
        
        # First ingestion
        result1 = service.ingest_from_connector(connector)
        assert result1['statistics']['records_saved'] == 10
        assert result1['statistics']['records_skipped_duplicate'] == 0
        
        # Second ingestion (should skip duplicates)
        result2 = service.ingest_from_connector(connector)
        assert result2['statistics']['records_fetched'] == 10
        assert result2['statistics']['records_saved'] == 0
        assert result2['statistics']['records_skipped_duplicate'] == 10
        
        # Verify only 10 records in database
        db = next(get_db())
        try:
            count = db.query(RawIngestionRecord).filter(
                RawIngestionRecord.tenant_id == tenant_id,
                RawIngestionRecord.source == "csv_products"
            ).count()
            
            assert count == 10
        finally:
            db.close()
    
    def test_incremental_pull_with_since(self, tenant_id, sample_products_csv):
        """Test incremental pull using 'since' parameter"""
        connector = CSVConnector(
            tenant_id=tenant_id,
            file_path=sample_products_csv,
            source_name="csv_products",
            id_column="sku",
            data_type="product"
        )
        
        service = IngestionService(tenant_id=tenant_id)
        
        # First ingestion
        result1 = service.ingest_from_connector(connector)
        assert result1['statistics']['records_saved'] == 10
        
        # Get timestamp
        first_ingestion_time = datetime.utcnow()
        
        # Second ingestion with 'since' (should skip all)
        result2 = service.ingest_from_connector(
            connector,
            since=first_ingestion_time
        )
        
        # Should fetch but skip all as duplicates
        assert result2['statistics']['records_fetched'] <= 10
        assert result2['statistics']['records_saved'] == 0
    
    def test_tenant_isolation(self, sample_products_csv):
        """Test that different tenants have isolated data"""
        tenant1_id = uuid4()
        tenant2_id = uuid4()
        
        # Ingest for tenant 1
        connector1 = CSVConnector(
            tenant_id=tenant1_id,
            file_path=sample_products_csv,
            source_name="csv_products",
            id_column="sku"
        )
        service1 = IngestionService(tenant_id=tenant1_id)
        result1 = service1.ingest_from_connector(connector1)
        assert result1['statistics']['records_saved'] == 10
        
        # Ingest for tenant 2 (same source_ids, different tenant)
        connector2 = CSVConnector(
            tenant_id=tenant2_id,
            file_path=sample_products_csv,
            source_name="csv_products",
            id_column="sku"
        )
        service2 = IngestionService(tenant_id=tenant2_id)
        result2 = service2.ingest_from_connector(connector2)
        assert result2['statistics']['records_saved'] == 10  # Should save, not skip
        
        # Verify both tenants have their own records
        db = next(get_db())
        try:
            tenant1_count = db.query(RawIngestionRecord).filter(
                RawIngestionRecord.tenant_id == tenant1_id
            ).count()
            
            tenant2_count = db.query(RawIngestionRecord).filter(
                RawIngestionRecord.tenant_id == tenant2_id
            ).count()
            
            assert tenant1_count == 10
            assert tenant2_count == 10
            
            # Cleanup
            db.query(RawIngestionRecord).filter(
                RawIngestionRecord.tenant_id.in_([tenant1_id, tenant2_id])
            ).delete()
            db.commit()
        finally:
            db.close()
    
    def test_ingestion_statistics_accuracy(self, tenant_id, sample_products_csv):
        """Test that ingestion statistics are accurate"""
        connector = CSVConnector(
            tenant_id=tenant_id,
            file_path=sample_products_csv,
            source_name="csv_products",
            id_column="sku"
        )
        
        service = IngestionService(tenant_id=tenant_id)
        result = service.ingest_from_connector(connector)
        
        stats = result['statistics']
        
        # Verify statistics add up
        assert stats['records_fetched'] == (
            stats['records_saved'] + 
            stats['records_skipped_duplicate'] + 
            stats['records_failed']
        )
        
        # Verify duration is tracked
        assert result['duration_seconds'] > 0
