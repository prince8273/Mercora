# E-commerce Intelligence Agent - Architecture Overview

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Component Details](#component-details)
4. [Data Flow](#data-flow)
5. [Technology Stack](#technology-stack)
6. [Design Patterns](#design-patterns)
7. [Security Architecture](#security-architecture)
8. [Scalability](#scalability)
9. [Deployment Architecture](#deployment-architecture)

---

## System Overview

The E-commerce Intelligence Agent is a multi-agent AI system that provides actionable business intelligence for e-commerce companies. The system follows a layered architecture with clear separation of concerns.

### Key Characteristics

- **Multi-Agent System**: Specialized agents for pricing, sentiment, and forecasting
- **LLM-Powered**: Uses Google Gemini for natural language understanding
- **Modular Design**: Loosely coupled components with well-defined interfaces
- **Event-Driven**: Asynchronous processing with event bus
- **Scalable**: Horizontal scaling support for all components

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │Dashboard │  │  Query   │  │  Upload  │  │ Metrics  │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP/REST
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API Gateway (FastAPI)                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Authentication Middleware                    │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┼─────────────┐
                │             │             │
                ▼             ▼             ▼
┌──────────────────┐  ┌──────────────┐  ┌──────────────┐
│  Data Ingestion  │  │ Orchestration│  │   Monitoring │
│      Layer       │  │    Layer     │  │    Layer     │
└──────────────────┘  └──────────────┘  └──────────────┘
        │                     │                  │
        │                     │                  │
        ▼                     ▼                  ▼
┌──────────────────┐  ┌──────────────┐  ┌──────────────┐
│  Data Processing │  │ Intelligence │  │   Metrics    │
│      Layer       │  │    Agents    │  │  Collection  │
└──────────────────┘  └──────────────┘  └──────────────┘
        │                     │                  │
        │                     │                  │
        ▼                     ▼                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Storage Layer                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │PostgreSQL│  │  Redis   │  │  Vector  │  │   S3     │       │
│  │   (DB)   │  │ (Cache)  │  │   (DB)   │  │(Storage) │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      External Services                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │  Gemini  │  │Marketplace│  │Competitor│  │Prometheus│       │
│  │   LLM    │  │   APIs   │  │ Websites │  │ Metrics  │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
└─────────────────────────────────────────────────────────────────┘
```

---

## Component Details

### 1. Frontend Layer

**Technology:** React + Vite

**Components:**
- **Dashboard**: Overview of key metrics and insights
- **Query Interface**: Natural language query input
- **Data Upload**: CSV file upload and validation
- **Metrics Dashboard**: Real-time system monitoring
- **Authentication**: Login/signup pages

**Responsibilities:**
- User interface rendering
- Form validation
- API communication
- State management (React Query)
- Real-time updates

### 2. API Gateway

**Technology:** FastAPI

**Components:**
- **Authentication Middleware**: JWT token validation
- **Rate Limiting**: Request throttling
- **CORS Middleware**: Cross-origin request handling
- **Error Handling**: Standardized error responses
- **Request Logging**: Audit trail

**Responsibilities:**
- Request routing
- Authentication/authorization
- Input validation
- Response formatting
- API documentation (OpenAPI)

### 3. Data Ingestion Layer

**Technology:** Python + Celery

**Components:**
- **Scheduler**: Celery Beat for scheduled tasks
- **Marketplace Connector**: API integration
- **Web Scraper**: Competitor data collection
- **CSV Parser**: File upload processing

**Responsibilities:**
- Data collection from external sources
- Rate limiting and retry logic
- Raw data storage
- Error handling and logging

### 4. Data Processing Layer

**Technology:** Python

**Components:**
- **Validator**: Schema and data type validation
- **Normalizer**: SKU normalization and standardization
- **Deduplicator**: Duplicate record removal
- **Spam Filter**: Review spam detection
- **Missing Data Handler**: Default value application

**Responsibilities:**
- Data cleaning and validation
- Data transformation
- Quality assurance
- Lineage tracking

### 5. Orchestration Layer

**Technology:** Python + LLM

**Components:**
- **Query Router**: Pattern-based routing
- **LLM Reasoning Engine**: Query understanding (Gemini)
- **Execution Service**: Agent coordination
- **Execution Queue**: Request queue management
- **Result Synthesizer**: Multi-agent result aggregation

**Responsibilities:**
- Query parsing and understanding
- Agent selection
- Parallel execution
- Result synthesis
- Confidence scoring

### 6. Intelligence Agents

**Technology:** Python + ML Libraries

**Agents:**
- **Pricing Intelligence Agent**: Competitive pricing analysis
- **Sentiment Analysis Agent**: Review sentiment classification
- **Demand Forecast Agent**: Time-series forecasting

**Responsibilities:**
- Specialized analysis
- Model inference
- Confidence calculation
- Result formatting

### 7. Monitoring Layer

**Technology:** Prometheus + Grafana

**Components:**
- **Metrics Collection**: Prometheus client
- **Metrics Endpoint**: `/metrics` API
- **Dashboards**: Grafana visualizations
- **Alerting**: Alert manager

**Responsibilities:**
- Performance monitoring
- Error tracking
- Resource utilization
- Alert generation

### 8. Storage Layer

**Databases:**
- **PostgreSQL**: Operational data (products, reviews, sales)
- **Redis**: Caching and session storage
- **Vector DB**: Semantic search (future)
- **S3**: File storage and archival (future)

**Responsibilities:**
- Data persistence
- Query optimization
- Backup and recovery
- Data archival

---

## Data Flow

### Query Execution Flow

```
1. User submits query via frontend
   ↓
2. API Gateway validates authentication
   ↓
3. Query Router checks cache
   ↓ (cache miss)
4. LLM Reasoning Engine understands query
   ↓
5. Execution Service selects agents
   ↓
6. Agents execute in parallel
   ↓
7. Result Synthesizer aggregates results
   ↓
8. Response cached and returned
   ↓
9. Frontend displays structured report
```

### CSV Upload Flow

```
1. User uploads CSV file
   ↓
2. API Gateway validates file format
   ↓
3. CSV Parser extracts records
   ↓
4. Data Processing Layer validates/cleans
   ↓
5. Records stored in database
   ↓
6. LLM analyzes uploaded data
   ↓
7. Agents generate insights
   ↓
8. Analysis results returned to user
```

### Data Ingestion Flow

```
1. Scheduler triggers ingestion task
   ↓
2. Marketplace Connector fetches data
   ↓
3. Raw data stored with metadata
   ↓
4. Processing pipeline validates/cleans
   ↓
5. Cleaned data stored in database
   ↓
6. Event published to event bus
   ↓
7. Cache invalidated for affected data
```

---

## Technology Stack

### Backend

- **Framework**: FastAPI 0.104+
- **Language**: Python 3.11+
- **ORM**: SQLAlchemy 2.0+
- **Database**: PostgreSQL 15+ / SQLite (dev)
- **Cache**: Redis 7+
- **Task Queue**: Celery 5+
- **LLM**: Google Gemini API
- **Testing**: pytest + Hypothesis

### Frontend

- **Framework**: React 18+
- **Build Tool**: Vite 5+
- **State Management**: React Query (TanStack Query)
- **Routing**: React Router 6+
- **HTTP Client**: Axios
- **UI Components**: Custom + Lucide Icons

### Infrastructure

- **Containerization**: Docker + Docker Compose
- **Orchestration**: Kubernetes (optional)
- **Monitoring**: Prometheus + Grafana
- **Logging**: Structured logging (JSON)
- **CI/CD**: GitHub Actions (future)

### External Services

- **LLM Provider**: Google Gemini
- **Marketplace APIs**: Amazon SP-API, Shopify, etc.
- **Web Scraping**: BeautifulSoup, Scrapy

---

## Design Patterns

### 1. Layered Architecture

**Pattern**: Separation of concerns into distinct layers

**Benefits:**
- Clear boundaries between components
- Independent testing and deployment
- Easy to understand and maintain

### 2. Repository Pattern

**Pattern**: Data access abstraction

**Implementation:**
```python
class ProductRepository:
    async def get_by_id(self, product_id: UUID) -> Product
    async def list(self, filters: Dict) -> List[Product]
    async def create(self, product: Product) -> Product
```

**Benefits:**
- Decouples business logic from data access
- Easy to mock for testing
- Consistent data access patterns

### 3. Strategy Pattern

**Pattern**: Interchangeable algorithms

**Implementation:**
```python
class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str) -> str

class GeminiProvider(LLMProvider):
    async def generate(self, prompt: str) -> str
        # Gemini-specific implementation

class OpenAIProvider(LLMProvider):
    async def generate(self, prompt: str) -> str
        # OpenAI-specific implementation
```

**Benefits:**
- Easy to switch LLM providers
- Testable with mock providers
- Extensible for new providers

### 4. Observer Pattern

**Pattern**: Event-driven architecture

**Implementation:**
```python
class EventBus:
    def publish(self, event: Event) -> None
    def subscribe(self, event_type: str, handler: Callable) -> None

# Cache invalidation on data updates
event_bus.subscribe('data.updated', cache_invalidation_handler)
```

**Benefits:**
- Loose coupling between components
- Asynchronous processing
- Easy to add new event handlers

### 5. Decorator Pattern

**Pattern**: Metrics and logging decorators

**Implementation:**
```python
@track_query_metrics(execution_mode="quick")
@track_llm_metrics(provider="gemini")
async def execute_query(query: str) -> Report:
    # Query execution logic
```

**Benefits:**
- Cross-cutting concerns (metrics, logging)
- Clean separation of business logic
- Reusable decorators

---

## Security Architecture

### Authentication

- **Method**: JWT (JSON Web Tokens)
- **Token Expiry**: 24 hours
- **Refresh Tokens**: Not implemented (future)
- **Password Hashing**: bcrypt

### Authorization

- **Model**: Role-Based Access Control (RBAC) - partial
- **Roles**: Admin, User (future: Analyst, Viewer)
- **Permissions**: Endpoint-level authorization

### Data Security

- **Encryption at Rest**: Database encryption (production)
- **Encryption in Transit**: TLS 1.3 (production)
- **Secrets Management**: Environment variables (dev), Vault (production)
- **API Keys**: Secure storage, rotation policy

### Multi-Tenancy

- **Isolation**: Tenant ID in all data records
- **Validation**: Middleware enforces tenant context
- **Queries**: Automatic tenant filtering

---

## Scalability

### Horizontal Scaling

**Stateless Components:**
- API Gateway (FastAPI)
- Intelligence Agents
- Data Processing Workers

**Scaling Strategy:**
- Load balancer distributes requests
- Auto-scaling based on CPU/memory
- Kubernetes HPA (Horizontal Pod Autoscaler)

### Vertical Scaling

**Stateful Components:**
- PostgreSQL (read replicas)
- Redis (clustering)
- Vector DB (sharding)

### Caching Strategy

**Levels:**
1. **Application Cache**: Redis for query results
2. **Database Cache**: PostgreSQL query cache
3. **CDN Cache**: Static assets (frontend)

**Cache Invalidation:**
- Event-driven invalidation
- TTL-based expiration
- Manual invalidation API

### Performance Optimization

**Database:**
- Indexes on frequently queried fields
- Connection pooling
- Query optimization
- Read replicas for analytics

**API:**
- Response compression
- Pagination for large datasets
- Async I/O for concurrent requests
- Rate limiting to prevent abuse

**LLM:**
- Prompt caching
- Result caching
- Batch processing
- Token optimization

---

## Deployment Architecture

### Development Environment

```
┌─────────────────────────────────────┐
│         Developer Machine           │
│  ┌──────────┐      ┌──────────┐   │
│  │ Backend  │      │ Frontend │   │
│  │  :8000   │      │  :5173   │   │
│  └──────────┘      └──────────┘   │
│  ┌──────────┐      ┌──────────┐   │
│  │PostgreSQL│      │  Redis   │   │
│  │  :5432   │      │  :6379   │   │
│  └──────────┘      └──────────┘   │
└─────────────────────────────────────┘
```

### Production Environment

```
┌─────────────────────────────────────────────────────────┐
│                    Load Balancer                         │
└─────────────────────────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  API Server  │ │  API Server  │ │  API Server  │
│   (Pod 1)    │ │   (Pod 2)    │ │   (Pod 3)    │
└──────────────┘ └──────────────┘ └──────────────┘
        │               │               │
        └───────────────┼───────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  PostgreSQL  │ │    Redis     │ │  Prometheus  │
│   (Primary)  │ │  (Cluster)   │ │   (Metrics)  │
└──────────────┘ └──────────────┘ └──────────────┘
        │
        ▼
┌──────────────┐
│  PostgreSQL  │
│  (Replica)   │
└──────────────┘
```

### Container Architecture

**Docker Compose Services:**
- `backend`: FastAPI application
- `frontend`: React application (Nginx)
- `postgres`: PostgreSQL database
- `redis`: Redis cache
- `celery-worker`: Background task worker
- `celery-beat`: Task scheduler
- `prometheus`: Metrics collection
- `grafana`: Metrics visualization

---

## Future Enhancements

### Planned Features

1. **Vector Database Integration**
   - Semantic search for queries
   - Conversation history embeddings
   - Similar query recommendations

2. **Real-Time Updates**
   - WebSocket support
   - Live query progress
   - Real-time metrics

3. **Advanced Analytics**
   - Custom dashboards
   - Report scheduling
   - Data export

4. **Multi-Model Support**
   - Multiple LLM providers
   - Model selection per query
   - Cost optimization

5. **Enhanced Security**
   - OAuth2 integration
   - SSO support
   - Advanced RBAC
   - Audit logging

---

**Version:** 1.0.0  
**Last Updated:** February 21, 2026  
**Maintained By:** Development Team
