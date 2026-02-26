"""Tests for Product CRUD operations and API endpoints"""
import pytest
from decimal import Decimal
from uuid import uuid4
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.crud.product import (
    create_product,
    get_product,
    get_products,
    update_product,
    delete_product,
    normalize_sku
)
from src.schemas.product import ProductCreate, ProductUpdate


class TestSKUNormalization:
    """Tests for SKU normalization"""
    
    def test_normalize_sku_basic(self):
        """Test basic SKU normalization"""
        assert normalize_sku("abc-123") == "ABC123"
        assert normalize_sku("xyz_456") == "XYZ456"
        assert normalize_sku("test@product#789") == "TESTPRODUCT789"
    
    def test_normalize_sku_consistency(self):
        """Test that normalization is consistent"""
        sku = "test-SKU-123"
        result1 = normalize_sku(sku)
        result2 = normalize_sku(sku)
        assert result1 == result2
        assert result1.isalnum()
        assert result1.isupper()


class TestProductCRUD:
    """Tests for Product CRUD operations"""
    
    @pytest.mark.asyncio
    async def test_create_product(self, test_db: AsyncSession):
        """Test creating a product"""
        product_data = ProductCreate(
            sku="TEST-001",
            name="Test Product",
            category="Electronics",
            price=Decimal("99.99"),
            currency="USD",
            marketplace="amazon",
            inventory_level=100,
            metadata={"brand": "TestBrand"}
        )
        
        product = await create_product(test_db, product_data)
        
        assert product.id is not None
        assert product.sku == "TEST-001"
        assert product.normalized_sku == "TEST001"
        assert product.name == "Test Product"
        assert product.price == Decimal("99.99")
        assert product.marketplace == "amazon"
        assert product.inventory_level == 100
        assert product.created_at is not None
        assert product.updated_at is not None
    
    @pytest.mark.asyncio
    async def test_get_product(self, test_db: AsyncSession):
        """Test retrieving a product by ID"""
        # Create a product
        product_data = ProductCreate(
            sku="TEST-002",
            name="Test Product 2",
            price=Decimal("49.99"),
            marketplace="ebay"
        )
        created_product = await create_product(test_db, product_data)
        
        # Retrieve the product
        retrieved_product = await get_product(test_db, created_product.id)
        
        assert retrieved_product is not None
        assert retrieved_product.id == created_product.id
        assert retrieved_product.sku == "TEST-002"
        assert retrieved_product.name == "Test Product 2"
    
    @pytest.mark.asyncio
    async def test_get_product_not_found(self, test_db: AsyncSession):
        """Test retrieving a non-existent product"""
        non_existent_id = uuid4()
        product = await get_product(test_db, non_existent_id)
        assert product is None
    
    @pytest.mark.asyncio
    async def test_get_products_pagination(self, test_db: AsyncSession):
        """Test retrieving products with pagination"""
        # Create multiple products
        for i in range(5):
            product_data = ProductCreate(
                sku=f"TEST-{i:03d}",
                name=f"Test Product {i}",
                price=Decimal("10.00") * (i + 1),
                marketplace="amazon"
            )
            await create_product(test_db, product_data)
        
        # Get first 3 products
        products = await get_products(test_db, skip=0, limit=3)
        assert len(products) == 3
        
        # Get next 2 products
        products = await get_products(test_db, skip=3, limit=3)
        assert len(products) == 2
    
    @pytest.mark.asyncio
    async def test_update_product(self, test_db: AsyncSession):
        """Test updating a product"""
        # Create a product
        product_data = ProductCreate(
            sku="TEST-003",
            name="Original Name",
            price=Decimal("29.99"),
            marketplace="walmart"
        )
        created_product = await create_product(test_db, product_data)
        
        # Update the product
        update_data = ProductUpdate(
            name="Updated Name",
            price=Decimal("39.99"),
            inventory_level=50
        )
        updated_product = await update_product(test_db, created_product.id, update_data)
        
        assert updated_product is not None
        assert updated_product.id == created_product.id
        assert updated_product.name == "Updated Name"
        assert updated_product.price == Decimal("39.99")
        assert updated_product.inventory_level == 50
        assert updated_product.sku == "TEST-003"  # Unchanged
    
    @pytest.mark.asyncio
    async def test_update_product_sku(self, test_db: AsyncSession):
        """Test updating a product's SKU updates normalized_sku"""
        # Create a product
        product_data = ProductCreate(
            sku="OLD-SKU",
            name="Test Product",
            price=Decimal("19.99"),
            marketplace="amazon"
        )
        created_product = await create_product(test_db, product_data)
        assert created_product.normalized_sku == "OLDSKU"
        
        # Update the SKU
        update_data = ProductUpdate(sku="NEW-SKU")
        updated_product = await update_product(test_db, created_product.id, update_data)
        
        assert updated_product.sku == "NEW-SKU"
        assert updated_product.normalized_sku == "NEWSKU"
    
    @pytest.mark.asyncio
    async def test_update_product_not_found(self, test_db: AsyncSession):
        """Test updating a non-existent product"""
        non_existent_id = uuid4()
        update_data = ProductUpdate(name="Updated Name")
        updated_product = await update_product(test_db, non_existent_id, update_data)
        assert updated_product is None
    
    @pytest.mark.asyncio
    async def test_delete_product(self, test_db: AsyncSession):
        """Test deleting a product"""
        # Create a product
        product_data = ProductCreate(
            sku="TEST-004",
            name="To Be Deleted",
            price=Decimal("15.99"),
            marketplace="amazon"
        )
        created_product = await create_product(test_db, product_data)
        
        # Delete the product
        deleted = await delete_product(test_db, created_product.id)
        assert deleted is True
        
        # Verify it's deleted
        retrieved_product = await get_product(test_db, created_product.id)
        assert retrieved_product is None
    
    @pytest.mark.asyncio
    async def test_delete_product_not_found(self, test_db: AsyncSession):
        """Test deleting a non-existent product"""
        non_existent_id = uuid4()
        deleted = await delete_product(test_db, non_existent_id)
        assert deleted is False


class TestProductAPI:
    """Tests for Product API endpoints"""
    
    @pytest.mark.asyncio
    async def test_create_product_endpoint(self, client: AsyncClient):
        """Test POST /api/v1/products"""
        product_data = {
            "sku": "API-001",
            "name": "API Test Product",
            "category": "Test Category",
            "price": "79.99",
            "currency": "USD",
            "marketplace": "amazon",
            "inventory_level": 25
        }
        
        response = await client.post("/api/v1/products", json=product_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["sku"] == "API-001"
        assert data["name"] == "API Test Product"
        assert data["normalized_sku"] == "API001"
        assert "id" in data
        assert "created_at" in data
    
    @pytest.mark.asyncio
    async def test_get_product_endpoint(self, client: AsyncClient):
        """Test GET /api/v1/products/{product_id}"""
        # Create a product first
        product_data = {
            "sku": "API-002",
            "name": "Get Test Product",
            "price": "29.99",
            "marketplace": "ebay"
        }
        create_response = await client.post("/api/v1/products", json=product_data)
        product_id = create_response.json()["id"]
        
        # Get the product
        response = await client.get(f"/api/v1/products/{product_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == product_id
        assert data["sku"] == "API-002"
    
    @pytest.mark.asyncio
    async def test_get_product_not_found(self, client: AsyncClient):
        """Test GET /api/v1/products/{product_id} with non-existent ID"""
        non_existent_id = str(uuid4())
        response = await client.get(f"/api/v1/products/{non_existent_id}")
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_get_products_endpoint(self, client: AsyncClient):
        """Test GET /api/v1/products"""
        # Create multiple products
        for i in range(3):
            product_data = {
                "sku": f"API-LIST-{i}",
                "name": f"List Product {i}",
                "price": "19.99",
                "marketplace": "amazon"
            }
            await client.post("/api/v1/products", json=product_data)
        
        # Get products
        response = await client.get("/api/v1/products")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 3
    
    @pytest.mark.asyncio
    async def test_get_products_pagination(self, client: AsyncClient):
        """Test GET /api/v1/products with pagination"""
        response = await client.get("/api/v1/products?skip=0&limit=2")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 2
    
    @pytest.mark.asyncio
    async def test_update_product_endpoint(self, client: AsyncClient):
        """Test PUT /api/v1/products/{product_id}"""
        # Create a product
        product_data = {
            "sku": "API-003",
            "name": "Update Test Product",
            "price": "39.99",
            "marketplace": "walmart"
        }
        create_response = await client.post("/api/v1/products", json=product_data)
        product_id = create_response.json()["id"]
        
        # Update the product
        update_data = {
            "name": "Updated Product Name",
            "price": "49.99"
        }
        response = await client.put(f"/api/v1/products/{product_id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == product_id
        assert data["name"] == "Updated Product Name"
        assert data["price"] == "49.99"
    
    @pytest.mark.asyncio
    async def test_update_product_not_found(self, client: AsyncClient):
        """Test PUT /api/v1/products/{product_id} with non-existent ID"""
        non_existent_id = str(uuid4())
        update_data = {"name": "Updated Name"}
        response = await client.put(f"/api/v1/products/{non_existent_id}", json=update_data)
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_delete_product_endpoint(self, client: AsyncClient):
        """Test DELETE /api/v1/products/{product_id}"""
        # Create a product
        product_data = {
            "sku": "API-004",
            "name": "Delete Test Product",
            "price": "19.99",
            "marketplace": "amazon"
        }
        create_response = await client.post("/api/v1/products", json=product_data)
        product_id = create_response.json()["id"]
        
        # Delete the product
        response = await client.delete(f"/api/v1/products/{product_id}")
        assert response.status_code == 204
        
        # Verify it's deleted
        get_response = await client.get(f"/api/v1/products/{product_id}")
        assert get_response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_delete_product_not_found(self, client: AsyncClient):
        """Test DELETE /api/v1/products/{product_id} with non-existent ID"""
        non_existent_id = str(uuid4())
        response = await client.delete(f"/api/v1/products/{non_existent_id}")
        assert response.status_code == 404
