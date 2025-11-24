# DareZone Backend API

FastAPI backend for DareZone - A habit-building social application with B2C and B2B features.

## 📋 Project Status

**Current Phase:** Phase 1 - Core Backend  
**Story:** Story 2 - FastAPI Project Structure ✅ COMPLETED  
**Next:** Story 3 - Authentication System

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Supabase account (free tier OK)
- Virtual environment activated

### Setup

1. **Navigate to backend directory**
   ```bash
   cd darezone-server
   ```

2. **Activate virtual environment**
   ```bash
   source .venv/bin/activate  # Linux/Mac
   # or
   .venv\Scripts\activate  # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   # .env file should already exist with your Supabase credentials
   # If not, copy from .env.example and fill in values
   cp .env.example .env
   # Edit .env with your credentials
   ```

5. **Run the server**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

6. **Verify it's running**
   - Health check: http://localhost:8000/health
   - API docs: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

---

## 📁 Project Structure

```
darezone-server/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app entry point
│   │
│   ├── core/                      # Core configuration
│   │   ├── __init__.py
│   │   ├── config.py              # Settings (Pydantic)
│   │   ├── dependencies.py        # Dependency injection
│   │   ├── security.py            # Auth helpers (skeleton)
│   │   └── exceptions.py          # Custom exceptions
│   │
│   ├── api/                       # API routes
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── router.py          # API v1 router
│   │
│   ├── middleware/                # Custom middleware
│   │   ├── __init__.py
│   │   └── logging.py             # Request logging
│   │
│   ├── schemas/                   # Pydantic DTOs (future)
│   ├── services/                  # Business logic (future)
│   ├── repositories/              # Data access (future)
│   └── utils/                     # Utilities (future)
│
├── tests/                         # Test suite
│   ├── __init__.py
│   └── test_main.py               # Basic tests
│
├── docs/                          # Documentation
│   ├── migrations/                # Database migrations
│   └── stories/                   # Implementation stories
│
├── .env                           # Environment variables (not in git)
├── .env.example                   # Environment template
├── .gitignore
├── requirements.txt
├── pytest.ini
└── README.md
```

---

## 🔧 Development

### Run Server

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_main.py -v
```

### Code Quality

```bash
# Format code with Black
black app tests

# Lint with Flake8
flake8 app tests

# Type checking with mypy
mypy app
```

---

## 📚 API Documentation

### Interactive Docs

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

#### Core Endpoints

- `GET /` - Welcome message
- `GET /health` - Health check (for load balancers)
- `GET /api/v1/` - API v1 root

#### Future Endpoints (Story 3+)

- `POST /api/v1/auth/signup` - User registration
- `POST /api/v1/auth/login` - User login
- `GET /api/v1/auth/me` - Current user
- `GET /api/v1/users/me` - User profile
- `POST /api/v1/challenges` - Create challenge
- `POST /api/v1/checkins` - Daily check-in

---

## 🗄️ Database

### Supabase PostgreSQL

- **Schema**: 11 tables with RLS policies
- **Features**: Auto-generated invite codes, streak tracking, points system
- **Status**: ✅ Already setup (Story 1)

### Migrations

Database migrations are located in `docs/migrations/`:
- `001_initial_schema.sql` - All tables
- `002_rls_policies.sql` - Row Level Security
- `003_seed_habits.sql` - System habits
- `004_indexes.sql` - Performance indexes
- `005_triggers.sql` - Auto-update triggers

---

## ⚙️ Configuration

### Environment Variables

Key variables in `.env`:

```bash
# Supabase (Required)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# App Config
APP_NAME=DareZone API
ENVIRONMENT=development
DEBUG=true

# Business Rules
MAX_HABITS_PER_CHALLENGE=4
DEFAULT_HITCH_COUNT=2
POINTS_PER_CHECKIN=10
```

See `.env.example` for full list of available variables.

---

## 🧪 Testing

### Manual Testing

```bash
# 1. Health check
curl http://localhost:8000/health

# 2. API root
curl http://localhost:8000/api/v1/

# 3. Check CORS headers
curl -H "Origin: http://localhost:19006" \
     -H "Access-Control-Request-Method: GET" \
     -H "Access-Control-Request-Headers: X-Requested-With" \
     -X OPTIONS http://localhost:8000/health -v
```

### Automated Tests

Run the test suite:

```bash
pytest tests/ -v
```

---

## 📖 Implementation Stories

### Phase 1: Core Backend (Current)

- ✅ **Story 1**: Database Setup (3 days) - COMPLETED
- ✅ **Story 2**: FastAPI Project Structure (2 days) - COMPLETED
- 📝 **Story 3**: Authentication System (3 days) - NEXT
- 📝 **Story 4**: User Management (3 days)
- 📝 **Story 5**: Challenge Management (5 days)
- 📝 **Story 6**: Check-in System (4 days)
- 📝 **Story 7**: Deployment & CI/CD (2 days)

See `docs/stories/` for detailed implementation guides.

---

## 🛠️ Tech Stack

- **Framework**: FastAPI 0.104+
- **Language**: Python 3.11+
- **Database**: Supabase PostgreSQL 15+
- **Auth**: Supabase Auth (JWT)
- **Storage**: Supabase Storage
- **Server**: Uvicorn (ASGI)

### Key Dependencies

- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `pydantic` - Data validation
- `supabase` - Database client
- `python-jose` - JWT handling
- `pytest` - Testing

---

## 🔐 Security

- **RLS Policies**: All database tables protected
- **JWT Auth**: Supabase-based authentication (Story 3)
- **CORS**: Configured for mobile app origins
- **Rate Limiting**: Coming in Story 18
- **Input Validation**: Pydantic schemas

---

## 🚧 Development Workflow

1. **Pick a story** from `docs/stories/`
2. **Create feature branch**: `git checkout -b story-{number}-{name}`
3. **Implement** following acceptance criteria
4. **Write tests** for new functionality
5. **Run tests**: `pytest`
6. **Format code**: `black app tests`
7. **Create PR** and request review
8. **Merge** after approval

---

## 📞 Support

### Documentation

- [Backend Specification](docs/backend/backend-spec.md)
- [Migration Guide](docs/migrations/README.md)
- [Testing Guide](docs/migrations/TESTING.md)
- [Stories](docs/stories/README.md)

### Common Issues

**Issue**: Import errors
```bash
# Solution: Activate venv
source .venv/bin/activate
```

**Issue**: Port 8000 already in use
```bash
# Solution: Use different port
uvicorn app.main:app --reload --port 8001
```

**Issue**: Supabase connection fails
```bash
# Solution: Check .env credentials
# Verify SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY
```

---

## 📄 License

MIT License - See LICENSE file

---

## ✅ Story 2 Completion Checklist

- [x] FastAPI app runs successfully
- [x] Project structure created
- [x] Environment config loads from `.env`
- [x] Health check endpoint working
- [x] CORS configured
- [x] Swagger docs accessible
- [x] Request logging middleware
- [x] Code formatted with Black
- [x] `.gitignore` configured
- [x] README with setup instructions

**Status**: ✅ Story 2 COMPLETED - Ready for Story 3 (Authentication)

---

**Project Version:** 1.0.0  
**Last Updated:** 2025-11-24  
**Current Story:** Story 2 - FastAPI Project Structure ✅
