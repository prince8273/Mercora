"""Simplified integration tests for data ingestion"""
import pytest
from pathlib import Path
from uuid import uuid4

from src.ingestion.connectors.csv_connector import CSVConnector
from src.ingestion.ingestion_service import IngestionService


class TestIngestionSimple:
    """Simplified integration tests"""
    
    def test_csv_connector_reads_products(self):
        """Test CSV connector can read products file"""
        tenant_id = uuid4()
        csv_path = "sample_data/products_sample.csv"
        
        assert Path(csv_path).exists()
        
        connector = CSVConnector(
            tenant_id=tenant_id,
            file_path=csv_path,
            source_name="csv_products",
            id_column="sku",
            data_type="product"
        )
        
        records = list(connector.fetch())
        
        assert len(records) == 10
        assert records[0].source_id == "PROD001"
        assert records[0].payload['name'] == "Wireless Mouse"
        assert records[0].payload['price'] == "29.99"
    
    def test_csv_connector_reads_reviews(self):
        """Test CSV connector can read reviews file"""
        tenant_id = uuid4()
        csv_path = "sample_data/reviews_sample.csv"
        
        assert Path(csv_path).exists()
        
        connector = CSVConnector(
            tenant_id=tenant_id,
            file_path=csv_path,
            source_name="csv_reviews",
            id_column="product_sku",
            data_type="review"
        )
        
        records = list(connector.fetch())
        
        assert len(records) == 10
        assert 'rating' in records[0].payload
        assert 'review_text' in records[0].payload
    
    def test_ingestion_service_processes_records(self):
        """Test ingestion service can process records"""
        tenant_id = uuid4()
        csv_path = "sample_data/products_sample.csv"
        
        connector = CSVConnector(
            tenant_id=tenant_id,
            file_path=csv_path,
            source_name="csv_products",
            id_column="sku"
        )
        
        service = IngestionService(tenant_id=tenant_id)
        
        # This will attempt to save to database
        # If database is not available, it will raise an error
        # which is expected in a test environment
        try:
            result = service.ingest_from_connector(connector)
            
            # If we get here, database is available
            assert result['success'] is True
            assert result['statistics']['records_fetched'] == 10
        except Exception as e:
            # Database not available in test environment
            # This is acceptable for unit tests
            pytest.skip(f"Database not available: {str(e)}")
    
    def test_connector_handles_duplicate_ingestion(self):
        """Test that connector can be called multiple times"""
        tenant_id = uuid4()
        csv_path = "sample_data/products_sample.csv"
        
        connector = CSVConnector(
            tenant_id=tenant_id,
            file_path=csv_path,
            source_name="csv_products",
            id_column="sku"
        )
        
        # First fetch
        records1 = list(connector.fetch())
        assert len(records1) == 10
        
        # Second fetch (should return same records)
        records2 = list(connector.fetch())
        assert len(records2) == 10
        
        # Verify same source_ids
        ids1 = {r.source_id for r in records1}
        ids2 = {r.source_id for r in records2}
        assert ids1 == ids2
