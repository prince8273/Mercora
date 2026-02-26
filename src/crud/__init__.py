"""CRUD operations"""
from src.crud.product import (
    create_product,
    get_product,
    get_products,
    update_product,
    delete_product
)
from src.crud.review import (
    create_review,
    get_review,
    get_reviews_by_product,
    get_reviews,
    update_review_sentiment,
    mark_review_as_spam,
    delete_review,
    get_review_statistics
)
from src.crud.sales_record import (
    create_sales_record,
    get_sales_record,
    get_sales_records_by_product,
    get_sales_records,
    update_sales_record,
    delete_sales_record,
    get_sales_aggregation,
    get_daily_sales
)
from src.crud.price_history import (
    create_price_history,
    get_price_history,
    get_price_history_by_product,
    get_latest_price,
    delete_price_history,
    detect_price_changes,
    get_price_trend,
    get_competitor_price_comparison,
    bulk_create_price_history
)

__all__ = [
    # Product
    "create_product",
    "get_product",
    "get_products",
    "update_product",
    "delete_product",
    # Review
    "create_review",
    "get_review",
    "get_reviews_by_product",
    "get_reviews",
    "update_review_sentiment",
    "mark_review_as_spam",
    "delete_review",
    "get_review_statistics",
    # Sales Record
    "create_sales_record",
    "get_sales_record",
    "get_sales_records_by_product",
    "get_sales_records",
    "update_sales_record",
    "delete_sales_record",
    "get_sales_aggregation",
    "get_daily_sales",
    # Price History
    "create_price_history",
    "get_price_history",
    "get_price_history_by_product",
    "get_latest_price",
    "delete_price_history",
    "detect_price_changes",
    "get_price_trend",
    "get_competitor_price_comparison",
    "bulk_create_price_history"
]
