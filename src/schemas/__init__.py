"""Pydantic schemas for API validation"""
from src.schemas.product import ProductBase, ProductCreate, ProductUpdate, ProductResponse
from src.schemas.review import ReviewBase, ReviewCreate, ReviewResponse
from src.schemas.sales_record import (
    SalesRecordBase,
    SalesRecordCreate,
    SalesRecordUpdate,
    SalesRecordResponse,
    SalesAggregation
)
from src.schemas.price_history import (
    PriceHistoryBase,
    PriceHistoryCreate,
    PriceHistoryResponse,
    PriceChange,
    PriceTrend
)

__all__ = [
    # Product
    "ProductBase",
    "ProductCreate",
    "ProductUpdate",
    "ProductResponse",
    # Review
    "ReviewBase",
    "ReviewCreate",
    "ReviewResponse",
    # Sales Record
    "SalesRecordBase",
    "SalesRecordCreate",
    "SalesRecordUpdate",
    "SalesRecordResponse",
    "SalesAggregation",
    # Price History
    "PriceHistoryBase",
    "PriceHistoryCreate",
    "PriceHistoryResponse",
    "PriceChange",
    "PriceTrend"
]
