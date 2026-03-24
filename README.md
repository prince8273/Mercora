# Mercora — E-commerce Intelligence Platform

> AI-powered decision intelligence for e-commerce teams. Meet **Dhana**, **Vivek**, and **Agrim** — your digital workers for pricing, sentiment, and demand forecasting.

---

## 🚀 Quick Start

**Prerequisites:** Python 3.11+, Node.js 18+, PostgreSQL, Redis

### 1. Clone & Install

```bash
git clone https://github.com/prince8273/Mercora.git
cd Mercora
```

```bash
# Backend
python -m venv venv
.\venv\Scripts\Activate.ps1   # Windows
pip install -r requirements.txt
alembic upgrade head
```

```bash
# Frontend
cd frontend
npm install
```

### 2. Environment Variables

`.env` (root):
```env
DATABASE_URL=postgresql://user:password@localhost/dbname
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key-here
```

`frontend/.env`:
```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=http://localhost:8000
```

### 3. Run

```bash
# Backend
uvicorn main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend && npm run dev
```

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |

---

## 🤖 AI Agents

| Agent | Role |
|---|---|
| **Dhana** | Pricing strategist — competitor monitoring, margin optimization |
| **Vivek** | Sentiment analyst — review analysis, customer insights |
| **Agrim** | Demand forecaster — inventory planning, seasonality detection |

### How the Agents Work

```
                        ┌─────────────────────────────┐
                        │     E-commerce Data Input    │
                        │  (Products, Reviews, Sales)  │
                        └──────────────┬──────────────┘
                                       │
                        ┌──────────────▼──────────────┐
                        │     AI Orchestration Layer   │
                        │     (Multi-Agent Router)     │
                        └──────┬──────────┬────────────┘
                               │          │          │
               ┌───────────────▼─┐  ┌─────▼──────┐  ┌▼──────────────┐
               │     DHANA       │  │   VIVEK    │  │    AGRIM      │
               │ Pricing Agent   │  │ Sentiment  │  │   Forecast    │
               │                 │  │   Agent    │  │    Agent      │
               │ • Competitor    │  │            │  │               │
               │   price scan    │  │ • Review   │  │ • Demand      │
               │ • Margin calc   │  │   analysis │  │   prediction  │
               │ • Auto reprice  │  │ • Theme    │  │ • Seasonality │
               │ • Promo detect  │  │   extract  │  │ • Reorder     │
               └───────┬─────────┘  └─────┬──────┘  └──────┬────────┘
                       │                  │                  │
                        └─────────────────┼─────────────────┘
                                          │
                        ┌─────────────────▼──────────────┐
                        │        Dashboard & Insights     │
                        │   KPIs · Alerts · Trends · AI  │
                        │         Recommendations         │
                        └────────────────────────────────┘
```

### Agent Workflow

```
User Query
    │
    ▼
┌─────────────────────────────────────────────┐
│  Natural Language Processing                │
│  "Optimize my pricing for max profit"       │
└──────────────────────┬──────────────────────┘
                       │
                       ▼
              Route to Agent(s)
           ┌──────────┴──────────┐
           │                     │
    ┌──────▼──────┐       ┌──────▼──────┐
    │   Dhana     │       │    Agrim    │
    │  analyzes   │       │  forecasts  │
    │  competitor │       │  demand to  │
    │  prices     │       │  set stock  │
    └──────┬──────┘       └──────┬──────┘
           │                     │
           └──────────┬──────────┘
                      │
                      ▼
           ┌──────────────────────┐
           │  Structured Output   │
           │  · Recommended price │
           │  · Confidence score  │
           │  · Action items      │
           └──────────────────────┘
```

---

## �️ Tech Stack

| Layer | Stack |
|---|---|
| Frontend | React 18, Vite 5, React Query, React Router v6, Recharts |
| Backend | FastAPI, Python 3.11, SQLAlchemy, Alembic, JWT |
| Database | PostgreSQL, Redis |
| Realtime | Socket.IO |

---

## 📄 License

Proprietary — Mercora / E-commerce Intelligence Platform
