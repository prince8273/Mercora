# E-commerce Intelligence Platform

AI-Powered Decision Intelligence SaaS Platform for E-commerce

---

## 🚀 Quick Start

### Windows:
**Double-click:** `START.bat`

OR

```powershell
.\start-all.ps1
```

### Linux/Mac:
```bash
chmod +x start-all.sh
./start-all.sh
```

**That's it!** Both frontend and backend will start automatically.

---

## 📋 What You Get

- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

---

## 🔐 Test Login

**Email:** test@example.com  
**Password:** password123

*(Create this user first - see [STARTUP_GUIDE.md](STARTUP_GUIDE.md))*

---

## 📚 Documentation

- **[STARTUP_GUIDE.md](STARTUP_GUIDE.md)** - Complete setup and startup guide
- **[HOW_TO_LOGIN.md](HOW_TO_LOGIN.md)** - Login troubleshooting
- **[START_SERVERS_README.md](START_SERVERS_README.md)** - Server startup options
- **[FRONTEND_ARCHITECTURE.md](FRONTEND_ARCHITECTURE.md)** - Frontend architecture
- **[PROJECT_STATUS_SUMMARY.md](PROJECT_STATUS_SUMMARY.md)** - Project status

---

## 🏗️ Architecture

### Backend (FastAPI + Python)
- 23 API routers with 100+ endpoints
- Multi-agent AI orchestration
- Real-time WebSocket updates
- Redis caching
- PostgreSQL database
- JWT authentication
- Multi-tenancy support

### Frontend (React + Vite)
- Modern React 18 with hooks
- React Query for server state
- Real-time updates via WebSocket
- Responsive design
- Dark mode support
- TypeScript-ready

---

## 🎯 Features

### Intelligence Query
- Natural language query processing
- Multi-agent orchestration
- Real-time progress tracking
- Structured insights

### Pricing Analysis
- Competitor price monitoring
- AI-powered recommendations
- Price trend analysis
- Promotion tracking

### Sentiment Analysis
- Customer review analysis
- Theme extraction
- Feature request identification
- Complaint categorization

### Demand Forecasting
- Time series forecasting
- Seasonality detection
- Inventory alerts
- Reorder recommendations

### Dashboard
- Real-time KPIs
- Trend visualization
- Quick insights
- Alert management

---

## 🔧 Tech Stack

### Backend
- **Framework:** FastAPI
- **Language:** Python 3.11+
- **Database:** PostgreSQL
- **Cache:** Redis
- **ORM:** SQLAlchemy
- **Migrations:** Alembic
- **Auth:** JWT
- **WebSocket:** Socket.IO

### Frontend
- **Framework:** React 18
- **Build Tool:** Vite 5
- **State:** React Query + Zustand
- **Routing:** React Router v6
- **HTTP:** Axios
- **Charts:** Recharts
- **Icons:** Lucide React
- **WebSocket:** Socket.IO Client

---

## 📦 Installation

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL (optional, SQLite works too)
- Redis (optional)

### Setup

1. **Clone repository**
```bash
git clone <repository-url>
cd ecommerce-intelligence
```

2. **Backend setup**
```bash
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows
source venv/bin/activate      # Linux/Mac
pip install -r requirements.txt
```

3. **Frontend setup**
```bash
cd frontend
npm install
cd ..
```

4. **Environment variables**

Create `.env` in root:
```env
DATABASE_URL=postgresql://user:password@localhost/dbname
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key-here
```

Create `frontend/.env`:
```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=http://localhost:8000
```

5. **Database migrations**
```bash
alembic upgrade head
```

6. **Start servers**
```bash
.\start-all.ps1  # Windows
./start-all.sh   # Linux/Mac
```

---

## 🧪 Testing

### Backend Tests
```bash
pytest
```

### Frontend Tests
```bash
cd frontend
npm test
```

---

## 📊 Project Status

- **Backend:** ✅ 100% Complete
- **Frontend UI:** ✅ 100% Complete
- **Integration:** 🟡 35% Complete
- **Overall:** 🟡 66% Complete

See [PROJECT_STATUS_SUMMARY.md](PROJECT_STATUS_SUMMARY.md) for details.

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## 📄 License

Proprietary - E-commerce Intelligence Platform

---

## 🆘 Support

- **Issues:** Check [STARTUP_GUIDE.md](STARTUP_GUIDE.md) troubleshooting section
- **Login Problems:** See [HOW_TO_LOGIN.md](HOW_TO_LOGIN.md)
- **Architecture:** See [FRONTEND_ARCHITECTURE.md](FRONTEND_ARCHITECTURE.md)

---

## 🎉 Getting Started

1. Run `.\start-all.ps1` (Windows) or `./start-all.sh` (Linux/Mac)
2. Create test user at http://localhost:8000/docs
3. Login at http://localhost:5173
4. Explore the platform!

**Happy coding!** 🚀
