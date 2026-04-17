# Tech Stack

## Backend
- **Language**: Python 3.11+
- **Framework**: FastAPI 0.109+
- **ORM**: SQLAlchemy 2.0+ (async)
- **Migrations**: Alembic
- **Auth**: JWT via `python-jose`, passwords hashed with `passlib[bcrypt]`
- **Config**: `pydantic-settings` — settings loaded from `.env` via `src/config.py`, accessed as `settings.*`
- **Database**: SQLite (dev default via `aiosqlite`), PostgreSQL (production)
- **Cache**: Redis with in-memory fallback (`redis[hiredis]`)
- **Task Scheduling**: APScheduler
- **LLM**: OpenAI (`gpt-4`) or Google Gemini — switchable via `LLM_PROVIDER` env var
- **ML/NLP**: `transformers`, `torch`, `scikit-learn` (sentiment); `statsmodels`, `prophet` (forecasting)
- **Web Scraping**: `beautifulsoup4`, `lxml`, `requests` with `tenacity` retry logic
- **Monitoring**: Prometheus (`prometheus_client`)
- **Testing**: `pytest` + `pytest-asyncio` + `hypothesis` (property-based testing)
- **CLI**: `click`

## Frontend
- **Framework**: React 18 + Vite 5
- **Language**: JSX/TSX (mixed — JS for most components, TS for utilities/hooks)
- **State**: Zustand (global stores) + TanStack React Query (server state)
- **Routing**: React Router v6
- **HTTP**: Axios via `src/lib/apiClient.js`
- **UI**: Tailwind CSS + Radix UI primitives + Lucide icons + Framer Motion
- **Charts**: Recharts
- **Realtime**: Socket.IO client
- **i18n**: react-i18next
- **Testing**: Vitest + Testing Library + happy-dom

## Infrastructure
- Backend runs on port `8000`, frontend dev server on `5173`
- API prefix: `/api/v1`
- WebSocket support for real-time query progress
- Prometheus metrics at `/metrics`

---

## Common Commands

### Backend
```bash
# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start dev server
uvicorn src.main:app --reload --port 8000

# Run all tests
pytest

# Run specific test file
pytest tests/test_pricing_intelligence.py -v

# Run only property-based tests
pytest -m property

# Seed / reseed data
python scripts/reseed_recent_data.py
python scripts/import_mock_data.py
```

### Frontend
```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev

# Run tests (watch mode)
npm test

# Run tests (single pass)
npm run test:run

# Build for production
npm run build
```
