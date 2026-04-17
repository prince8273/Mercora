# Project Structure

## Root
```
/
├── src/                  # Backend Python source
├── frontend/             # React frontend
├── tests/                # Backend test suite
├── alembic/              # DB migration scripts
├── scripts/              # One-off data scripts (seeding, checks, fixes)
├── docs/                 # Architecture and API documentation
├── config/               # Python config package
├── .env                  # Local environment variables (not committed)
├── src/main.py           # FastAPI app entry point
├── src/config.py         # Pydantic settings (single source of truth for config)
├── pytest.ini            # Test configuration
├── requirements.txt      # Python dependencies
└── alembic.ini           # Alembic migration config
```

## Backend — `src/`
```
src/
├── main.py               # App factory, lifespan, middleware, router registration
├── config.py             # Settings via pydantic-settings
├── database.py           # SQLAlchemy async engine + session factory
├── tenant_session.py     # Tenant-scoped DB session helpers
├── api/                  # FastAPI routers (one file per domain)
├── agents/               # AI agents: pricing, sentiment, demand forecast
├── orchestration/        # Query routing, LLM reasoning, execution, result synthesis
├── processing/           # Data pipeline: validate, normalize, deduplicate, spam filter
├── ingestion/            # Scheduled data ingestion, marketplace/scraper connectors
├── models/               # SQLAlchemy ORM models
├── schemas/              # Pydantic request/response schemas
├── crud/                 # DB access layer (one file per model)
├── auth/                 # JWT, RBAC, security dependencies
├── cache/                # Redis cache manager + event bus
├── middleware/           # Tenant isolation middleware
├── services/             # Higher-level service logic
├── memory/               # Agent memory and user preference management
├── ml/                   # Model registry, drift detection, retraining
├── model_management/     # Model monitoring and retraining workflows
├── monitoring/           # Prometheus metrics
├── observability/        # Structured logging, tracing, alerting
├── audit/                # Audit trail and data lineage tracking
├── error_handling/       # Standardized error responses, graceful degradation
├── performance/          # SLA monitoring
├── retention/            # Data lifecycle and retention policies
└── cli/                  # Click CLI commands
```

## Frontend — `frontend/src/`
```
frontend/src/
├── main.jsx              # React entry point
├── App.jsx               # Root component, routing setup
├── pages/                # Top-level page components (one per route)
├── features/             # Feature-scoped components: dashboard, pricing, sentiment, forecast, query, settings
├── components/           # Shared UI components
│   ├── atoms/            # Smallest primitives
│   ├── molecules/        # Composed from atoms
│   ├── organisms/        # Complex sections
│   ├── layouts/          # Page layout wrappers
│   ├── ui/               # Generic UI kit components
│   └── modals/           # Modal dialogs
├── hooks/                # Custom React hooks (data fetching, WebSocket, etc.)
├── stores/               # Zustand global state stores
├── services/             # API call functions (per domain)
├── lib/                  # Core utilities: apiClient, queryClient, websocket
├── contexts/             # React contexts (Auth, Theme)
├── routes/               # Route definitions
├── i18n/                 # Internationalization config and locale files
├── utils/                # Pure utility functions
└── styles/               # Global CSS
```

## Tests — `tests/`
- Files named `test_*.py`
- Property-based tests named `test_property_*.py` and marked with `@pytest.mark.property`
- Integration tests in `tests/integration/`
- Shared fixtures in `tests/conftest.py`

## Key Conventions
- All API routes are prefixed with `/api/v1` (set in `settings.api_v1_prefix`)
- Every DB model has a corresponding Pydantic schema in `src/schemas/` and CRUD module in `src/crud/`
- Tenant isolation is enforced at the middleware level — never bypass `TenantIsolationMiddleware`
- New API endpoints go in `src/api/`, registered in `src/main.py`
- Agent logic lives in `src/agents/`, orchestration wiring in `src/orchestration/`
- Use `src/config.py` `settings` object for all configuration — never hardcode values
