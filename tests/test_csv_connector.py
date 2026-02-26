"""Unit tests for CSV connector"""
import pytest
import tempfile
from pathlib import Path
from datetime import datetime
from uuid import uuid4

from src.ingestion.connectors.csv_connector import CSVConnector
from src.ingestion.base import RawRecord


class TestCSVConnector:
    """Test suite for CSV connector"""
    
    @pytest.fixture
    def tenant_id(self):
        """Fixture for tenant ID"""
        return uuid4()
    
    @pytest.fixture
    def sample_csv_file(self):
        """Create a temporary CSV file for testing"""
        content = """sku,name,category,price,currency,marketplace,inventory_level
PROD001,Wireless Mouse,Electronics,29.99,USD,Amazon,150
PROD002,USB-C Cable,Electronics,12.99,USD,Amazon,300
PROD003,Laptop Stand,Office,49.99,USD,Amazon,75
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        Path(temp_path).unlink(missing_ok=True)
    
    @pytest.fixture
    def empty_csv_file(self):
        """Create an empty CSV file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("")
            temp_path = f.name
        
        yield temp_path
        
        Path(temp_path).unlink(missing_ok=True)
    
    @pytest.fixture
    def csv_no_header(self):
        """Create CSV without header"""
        content = """PROD001,Wireless Mouse,Electronics,29.99,USD,Amazon,150
PROD002,USB-C Cable,Electronics,12.99,USD,Amazon,300
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        yield temp_path
        
        Path(temp_path).unlink(missing_ok=True)
    
    def test_connector_initialization(self, tenant_id, sample_csv_file):
        """Test connector initializes correctly"""
        connector = CSVConnector(
            tenant_id=tenant_id,
            file_path=sample_csv_file,
            source_name="test_csv",
            id_column="sku"
        )
        
        assert connector.tenant_id == tenant_id
        assert connector.source_name == "test_csv"
        assert connector.id_column == "sku"
        assert connector.file_path.exists()
    
    def test_connector_file_not_found(self, tenant_id):
        """Test connector raises error for non-existent file"""
        with pytest.raises(FileNotFoundError):
            CSVConnector(
                tenant_id=tenant_id,
                file_path="/nonexistent/file.csv",
                source_name="test_csv"
            )
    
    def test_fetch_records(self, tenant_id, sample_csv_file):
        """Test fetching records from CSV"""
        connector = CSVConnector(
            tenant_id=tenant_id,
            file_path=sample_csv_file,
            source_name="test_csv",
            id_column="sku"
        )
        
        records = list(connector.fetch())
        
        assert len(records) == 3
        assert all(isinstance(r, RawRecord) for r in records)
        
        # Check first record
        first_record = records[0]
        assert first_record.source_id == "PROD001"
        assert first_record.payload['name'] == "Wireless Mouse"
        assert first_record.payload['price'] == "29.99"
        assert first_record.metadata['source_file'] == Path(sample_csv_file).name
        assert first_record.metadata['row_number'] == 2
    
    def test_fetch_with_missing_id_column(self, tenant_id):
        """Test fetch raises error when ID column is missing"""
        content = """name,price,currency
Product A,10.00,USD
Product B,20.00,USD
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            connector = CSVConnector(
                tenant_id=tenant_id,
                file_path=temp_path,
                source_name="test_csv",
                id_column="sku"  # This column doesn't exist
            )
            
            with pytest.raises(ValueError, match="ID column 'sku' not found"):
                list(connector.fetch())
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def test_fetch_skips_empty_id(self, tenant_id):
        """Test fetch skips rows with empty ID"""
        content = """sku,name,price
PROD001,Product A,10.00
,Product B,20.00
PROD003,Product C,30.00
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            connector = CSVConnector(
                tenant_id=tenant_id,
                file_path=temp_path,
                source_name="test_csv",
                id_column="sku"
            )
            
            records = list(connector.fetch())
            
            # Should skip row with empty sku
            assert len(records) == 2
            assert records[0].source_id == "PROD001"
            assert records[1].source_id == "PROD003"
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def test_fetch_handles_whitespace(self, tenant_id):
        """Test fetch trims whitespace from values"""
        content = """sku,name,price
  PROD001  ,  Product A  ,  10.00  
PROD002,Product B,20.00
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            connector = CSVConnector(
                tenant_id=tenant_id,
                file_path=temp_path,
                source_name="test_csv",
                id_column="sku"
            )
            
            records = list(connector.fetch())
            
            assert records[0].source_id == "PROD001"
            assert records[0].payload['name'] == "Product A"
            assert records[0].payload['price'] == "10.00"
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def test_get_source_info(self, tenant_id, sample_csv_file):
        """Test get_source_info returns correct metadata"""
        connector = CSVConnector(
            tenant_id=tenant_id,
            file_path=sample_csv_file,
            source_name="test_csv",
            id_column="sku",
            data_type="product"
        )
        
        info = connector.get_source_info()
        
        assert info['tenant_id'] == str(tenant_id)
        assert info['source_name'] == "test_csv"
        assert info['connector_type'] == "CSVConnector"
        assert info['file_exists'] is True
        assert info['file_size_bytes'] > 0
        assert info['id_column'] == "sku"
        assert info['data_type'] == "product"
    
    def test_fetch_empty_csv(self, tenant_id, empty_csv_file):
        """Test fetch handles empty CSV file"""
        connector = CSVConnector(
            tenant_id=tenant_id,
            file_path=empty_csv_file,
            source_name="test_csv",
            id_column="sku"
        )
        
        with pytest.raises(ValueError, match="no header row"):
            list(connector.fetch())
    
    def test_record_metadata_includes_all_fields(self, tenant_id, sample_csv_file):
        """Test that record metadata includes all expected fields"""
        connector = CSVConnector(
            tenant_id=tenant_id,
            file_path=sample_csv_file,
            source_name="test_csv",
            id_column="sku",
            data_type="product"
        )
        
        records = list(connector.fetch())
        first_record = records[0]
        
        assert 'source_file' in first_record.metadata
        assert 'row_number' in first_record.metadata
        assert 'data_type' in first_record.metadata
        assert 'column_count' in first_record.metadata
        assert first_record.metadata['data_type'] == "product"
    
    def test_fetch_preserves_all_columns(self, tenant_id, sample_csv_file):
        """Test that all CSV columns are preserved in payload"""
        connector = CSVConnector(
            tenant_id=tenant_id,
            file_path=sample_csv_file,
            source_name="test_csv",
            id_column="sku"
        )
        
        records = list(connector.fetch())
        first_record = records[0]
        
        expected_columns = ['sku', 'name', 'category', 'price', 'currency', 'marketplace', 'inventory_level']
        for col in expected_columns:
            assert col in first_record.payload
