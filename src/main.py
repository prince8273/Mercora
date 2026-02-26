"""Main FastAPI application"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.config import settings
from src.logging_config import setup_logging
from src.database import init_db
from src.cache.cache_manager import CacheManager
from src.cache.instance import set_cache_manager
from src.cache.event_bus import initialize_cache_invalidation
from src.ingestion.scheduled_service import get_scheduled_service
from src.api.products import router as products_router
from src.api.pricing import router as pricing_router
from src.api.query import router as query_router
from src.api.sentiment import router as sentiment_router
from src.api.auth import router as auth_router
from src.api.forecast import router as forecast_router
from src.api.dashboard import router as dashboard_router
from src.api.analytics import router as analytics_router
from src.api.history import router as history_router
from src.api.ingestion import router as ingestion_router
from src.api.lineage import router as lineage_router
from src.api.models import router as models_router
from src.api.processing import router as processing_router
from src.api.web_scraping import router as web_scraping_router
from src.api.amazon_data import router as amazon_router
from src.api.amazon_seller_api import router as amazon_seller_router
from src.api.insights import router as insights_router
from src.api.competitor_dashboard import router as competitor_dashboard_router
from src.api.cache import router as cache_router
from src.api.csv_upload import router as csv_upload_router
from src.api.metrics import router as metrics_router
from src.api.preferences import router as preferences_router
from src.api.websocket import router as websocket_router
from src.middleware.tenant_isolation import TenantIsolationMiddleware

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting application...")
    await init_db()
    logger.info("Database initialized")
    
    # Initialize metrics
    from src.monitoring.metrics import initialize_app_info
    initialize_app_info(
        name=settings.app_name,
        version=settings.app_version,
        environment="development" if settings.debug else "production"
    )
    logger.info("Metrics initialized")
    
    # Initialize cache manager if enabled
    cache_manager = None
    if settings.cache_enabled:
        try:
            cache_manager = CacheManager(redis_url=settings.redis_url)
            await cache_manager.connect()
            if cache_manager._redis:
                logger.info("Redis cache initialized")
                set_cache_manager(cache_manager)
                
                # Initialize event-driven cache invalidation
                initialize_cache_invalidation(cache_manager)
                logger.info("Cache invalidation system initialized")
            else:
                logger.warning("Redis cache unavailable. Continuing without cache.")
                set_cache_manager(None)
        except Exception as e:
            logger.warning(f"Failed to initialize Redis cache: {e}. Continuing without cache.")
            set_cache_manager(None)
    else:
        logger.info("Cache disabled in configuration")
        set_cache_manager(None)
    
    # Start scheduled ingestion service
    try:
        scheduled_service = get_scheduled_service()
        scheduled_service.start()
        logger.info("Scheduled ingestion service started")
    except Exception as e:
        logger.error(f"Failed to start scheduled ingestion service: {str(e)}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    
    # Disconnect cache
    from src.cache.instance import get_cache_manager
    cache_manager = get_cache_manager()
    if cache_manager:
        try:
            await cache_manager.disconnect()
            logger.info("Redis cache disconnected")
        except Exception as e:
            logger.error(f"Failed to disconnect cache: {e}")
    
    try:
        scheduled_service = get_scheduled_service()
        scheduled_service.stop()
        logger.info("Scheduled ingestion service stopped")
    except Exception as e:
        logger.error(f"Failed to stop scheduled ingestion service: {str(e)}")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    E-commerce Intelligence Research Agent API
    
    This API provides comprehensive e-commerce intelligence including:
    * **Query Execution**: Natural language query processing with multi-agent orchestration
    * **Pricing Intelligence**: Competitive pricing analysis and recommendations
    * **Sentiment Analysis**: Customer review analysis and insights
    * **Demand Forecasting**: Sales forecasting and inventory optimization
    * **User Preferences**: Personalized KPI tracking and business goals
    * **Real-time Updates**: WebSocket support for query progress tracking
    
    ## Authentication
    
    Most endpoints require JWT authentication. Include the token in the Authorization header:
    ```
    Authorization: Bearer <your_jwt_token>
    ```
    
    ## Tenant Isolation
    
    All data is automatically isolated by tenant. The tenant context is extracted from
    the JWT token and enforced at the middleware level.
    """,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "auth", "description": "Authentication and authorization"},
        {"name": "query", "description": "Natural language query execution"},
        {"name": "pricing", "description": "Pricing intelligence and analysis"},
        {"name": "sentiment", "description": "Sentiment analysis and review insights"},
        {"name": "forecast", "description": "Demand forecasting and inventory"},
        {"name": "preferences", "description": "User preferences and personalization"},
        {"name": "websocket", "description": "Real-time updates via WebSocket"},
        {"name": "products", "description": "Product management"},
        {"name": "dashboard", "description": "Dashboard and analytics"},
        {"name": "ingestion", "description": "Data ingestion and processing"},
        {"name": "models", "description": "ML model management"},
    ]
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Alternative dev port
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# CRITICAL: Add Tenant Isolation Middleware
# This MUST be added AFTER CORS middleware to ensure tenant context is set
# for all authenticated requests
app.add_middleware(TenantIsolationMiddleware)
logger.info("Tenant Isolation Middleware enabled")

# Include routers
app.include_router(auth_router, prefix=settings.api_v1_prefix)  # Auth first (no auth required)
app.include_router(products_router, prefix=settings.api_v1_prefix)
app.include_router(pricing_router, prefix=settings.api_v1_prefix)
app.include_router(query_router, prefix=settings.api_v1_prefix)
app.include_router(sentiment_router, prefix=settings.api_v1_prefix)
app.include_router(forecast_router, prefix=settings.api_v1_prefix)
app.include_router(dashboard_router, prefix=settings.api_v1_prefix)
app.include_router(analytics_router, prefix=settings.api_v1_prefix)
app.include_router(history_router, prefix=settings.api_v1_prefix)
app.include_router(ingestion_router, prefix=settings.api_v1_prefix)
app.include_router(lineage_router, prefix=settings.api_v1_prefix)
app.include_router(models_router, prefix=settings.api_v1_prefix)
app.include_router(processing_router, prefix=settings.api_v1_prefix)
app.include_router(web_scraping_router, prefix=settings.api_v1_prefix)
app.include_router(amazon_router, prefix=settings.api_v1_prefix)
app.include_router(amazon_seller_router, prefix=settings.api_v1_prefix)
app.include_router(insights_router, prefix=settings.api_v1_prefix)
app.include_router(competitor_dashboard_router, prefix=settings.api_v1_prefix)
app.include_router(cache_router, prefix=settings.api_v1_prefix)
app.include_router(csv_upload_router, prefix=settings.api_v1_prefix)
app.include_router(metrics_router, prefix=settings.api_v1_prefix)
app.include_router(preferences_router, prefix=settings.api_v1_prefix)
app.include_router(websocket_router, prefix=settings.api_v1_prefix)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return JSONResponse(
        content={
            "status": "healthy",
            "app_name": settings.app_name,
            "version": settings.app_version
        }
    )


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "E-commerce Intelligence Research Agent API",
        "version": settings.app_version,
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
