"""Database models"""
# Import Role and association tables first since other models reference them
from src.models.role import Role, user_roles, role_permissions
from src.models.product import Product, GUID
from src.models.review import Review
from src.models.tenant import Tenant
from src.models.user import User
from src.models.user_preferences import UserPreferences
from src.models.sales_record import SalesRecord
from src.models.price_history import PriceHistory
from src.models.raw_ingestion_record import RawIngestionRecord
from src.models.analytical_report import AnalyticalReport
from src.models.forecast_result import ForecastResult
from src.models.aggregated_metrics import AggregatedMetrics

__all__ = [
    "Product",
    "Review",
    "Tenant",
    "User",
    "UserPreferences",
    "Role",
    "SalesRecord",
    "PriceHistory",
    "RawIngestionRecord",
    "AnalyticalReport",
    "ForecastResult",
    "AggregatedMetrics",
    "GUID",
    "user_roles",
    "role_permissions"
]
