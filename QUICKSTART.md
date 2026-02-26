# Quick Start Guide

## Prerequisites

- Python 3.11 or higher
- pip (Python package installer)

## Setup (First Time)

### Windows

```powershell
# Run the setup script
.\setup.ps1
```

Or manually:
```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### Linux/macOS

```bash
# Run the setup script
chmod +x setup.sh
./setup.sh
```

Or manually:
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Running the Application

### Activate Virtual Environment

**Windows:**
```powershell
.\venv\Scripts\Activate.ps1
```

**Linux/macOS:**
```bash
source venv/bin/activate
```

### Start the Server

```bash
python src/main.py
```

The application will start on http://localhost:8000

### Access the API

- **API Root:** http://localhost:8000/
- **Health Check:** http://localhost:8000/health
- **Interactive API Docs:** http://localhost:8000/docs
- **Alternative API Docs:** http://localhost:8000/redoc

## Running Tests

```bash
# Activate virtual environment first (see above)

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=src --cov-report=html
```

## Project Structure

```
.
├── src/                    # Application source code
│   ├── main.py            # FastAPI application entry point
│   ├── config.py          # Configuration management
│   ├── database.py        # Database connection and session
│   └── logging_config.py  # Logging configuration
├── tests/                 # Test files
│   ├── conftest.py        # Pytest fixtures
│   └── test_health.py     # Health check tests
├── config/                # Configuration files
├── .env                   # Environment variables (local)
├── .env.example          # Example environment variables
├── requirements.txt       # Python dependencies
└── README.md             # Full documentation
```

## Configuration

Edit the `.env` file to configure the application:

```env
# Application Settings
APP_NAME="E-commerce Intelligence Agent"
DEBUG=True
LOG_LEVEL=INFO

# Database
DATABASE_URL=sqlite+aiosqlite:///./ecommerce_intelligence.db

# Security (CHANGE IN PRODUCTION!)
SECRET_KEY=your-secret-key-here
```

## Next Steps

1. Review the [README.md](README.md) for detailed documentation
2. Check the [requirements document](.kiro/specs/ecommerce-intelligence-agent/requirements.md)
3. Review the [design document](.kiro/specs/ecommerce-intelligence-agent/design.md)
4. Follow the [implementation tasks](.kiro/specs/ecommerce-intelligence-agent/tasks.md)

## Troubleshooting

### Virtual Environment Not Activating

**Windows:** You may need to enable script execution:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Import Errors

Make sure the virtual environment is activated and dependencies are installed:
```bash
pip install -r requirements.txt
```

### Database Errors

The SQLite database will be created automatically on first run. If you encounter issues, delete the `ecommerce_intelligence.db` file and restart the application.
