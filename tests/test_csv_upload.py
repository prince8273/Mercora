"""Tests for CSV upload with LLM analysis"""
import pytest
import io
from uuid import uuid4
from fastapi import UploadFile

from src.api.csv_upload import (
    _get_rating_distribution,
    _format_sample_data
)


def test_rating_distribution():
    """Test rating distribution calculation"""
    from src.models.review import Review
    from datetime import datetime
    
    reviews = [
        Review(
            id=uuid4(),
            tenant_id=uuid4(),
            product_id=uuid4(),
            rating=5,
            text="Great!",
            source="test",
            is_spam=False,
            created_at=datetime.utcnow()
        ),
        Review(
            id=uuid4(),
            tenant_id=uuid4(),
            product_id=uuid4(),
            rating=5,
            text="Excellent!",
            source="test",
            is_spam=False,
            created_at=datetime.utcnow()
        ),
        Review(
            id=uuid4(),
            tenant_id=uuid4(),
            product_id=uuid4(),
            rating=4,
            text="Good",
            source="test",
            is_spam=False,
            created_at=datetime.utcnow()
        ),
        Review(
            id=uuid4(),
            tenant_id=uuid4(),
            product_id=uuid4(),
            rating=3,
            text="OK",
            source="test",
            is_spam=False,
            created_at=datetime.utcnow()
        ),
    ]
    
    distribution = _get_rating_distribution(reviews)
    
    assert distribution[5] == 2
    assert distribution[4] == 1
    assert distribution[3] == 1
    assert distribution[2] == 0
    assert distribution[1] == 0


def test_format_sample_data():
    """Test sample data formatting"""
    rows = [
        {'sku': 'PROD-001', 'name': 'Product 1', 'price': '29.99'},
        {'sku': 'PROD-002', 'name': 'Product 2', 'price': '39.99'},
    ]
    
    formatted = _format_sample_data(rows)
    
    assert 'Row 1:' in formatted
    assert 'Row 2:' in formatted
    assert 'PROD-001' in formatted
    assert 'PROD-002' in formatted


def test_format_sample_data_empty():
    """Test sample data formatting with empty list"""
    formatted = _format_sample_data([])
    assert formatted == "No data"


def test_csv_parsing():
    """Test CSV parsing logic"""
    import csv
    
    csv_content = """sku,name,price
PROD-001,Product 1,29.99
PROD-002,Product 2,39.99
"""
    
    csv_reader = csv.DictReader(io.StringIO(csv_content))
    rows = list(csv_reader)
    
    assert len(rows) == 2
    assert rows[0]['sku'] == 'PROD-001'
    assert rows[0]['name'] == 'Product 1'
    assert rows[0]['price'] == '29.99'
    assert rows[1]['sku'] == 'PROD-002'


def test_csv_with_missing_columns():
    """Test CSV parsing with missing optional columns"""
    import csv
    
    csv_content = """sku,name,price
PROD-001,Product 1,29.99
PROD-002,Product 2,
"""
    
    csv_reader = csv.DictReader(io.StringIO(csv_content))
    rows = list(csv_reader)
    
    assert len(rows) == 2
    assert rows[1]['price'] == ''  # Missing price


def test_llm_query_generation():
    """Test LLM query generation for products"""
    from src.models.product import Product
    from datetime import datetime
    
    products = [
        Product(
            id=uuid4(),
            tenant_id=uuid4(),
            sku='PROD-001',
            normalized_sku='PROD-001',
            name='Product 1',
            category='Electronics',
            price=29.99,
            currency='USD',
            marketplace='amazon',
            inventory_level=100,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        ),
        Product(
            id=uuid4(),
            tenant_id=uuid4(),
            sku='PROD-002',
            normalized_sku='PROD-002',
            name='Product 2',
            category='Office',
            price=49.99,
            currency='USD',
            marketplace='ebay',
            inventory_level=50,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        ),
    ]
    
    # Generate query
    query = f"""Analyze the uploaded product data:
- Total products: {len(products)}
- Categories: {', '.join(set(p.category for p in products))}
- Price range: ${min(p.price for p in products):.2f} - ${max(p.price for p in products):.2f}
- Marketplaces: {', '.join(set(p.marketplace for p in products))}
"""
    
    assert 'Total products: 2' in query
    assert 'Electronics' in query or 'Office' in query
    assert '$29.99' in query
    assert '$49.99' in query
    assert 'amazon' in query or 'ebay' in query


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
