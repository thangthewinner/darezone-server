# Story 2: FastAPI Project Structure

**Phase:** 1 - Core Backend  
**Points:** 2 (2 days)  
**Priority:** 🔥 CRITICAL  
**Dependencies:** [Story 1: Database Setup](./story-1-database-setup.md)

---

## 📖 Description

Setup FastAPI project với production-ready structure, bao gồm: core configuration, API routing, dependency injection, middleware, và basic health check.

---

## 🎯 Goals

- [ ] FastAPI app runs successfully
- [ ] Project structure clean và scalable
- [ ] Environment config loaded properly
- [ ] Health check endpoint working
- [ ] CORS configured for mobile app

---

## ✅ Acceptance Criteria

### 1. Project Initialized
- [ ] Python 3.11+ virtual environment created
- [ ] All dependencies installed from requirements.txt
- [ ] FastAPI app runs on `http://localhost:8000`
- [ ] Swagger docs accessible at `/docs`

### 2. Core Modules Created
- [ ] `app/main.py` - FastAPI app entry point
- [ ] `app/core/config.py` - Settings management
- [ ] `app/core/dependencies.py` - Dependency injection
- [ ] `app/core/security.py` - Auth helpers (skeleton)
- [ ] `app/core/exceptions.py` - Custom exceptions

### 3. API Structure
- [ ] `app/api/v1/` - API version 1 routes
- [ ] Router system setup
- [ ] Health check endpoint working

### 4. Middleware Configured
- [ ] CORS middleware for mobile origins
- [ ] Request logging middleware
- [ ] Error handling middleware

### 5. Configuration
- [ ] Pydantic Settings for env vars
- [ ] `.env.example` template
- [ ] Config validates on startup

### 6. Documentation
- [ ] README.md with setup instructions
- [ ] API docs auto-generated (Swagger)
- [ ] Development workflow documented

---

## 🛠️ Technical Implementation

### Step 1: Initialize Project

```bash
# Create project directory
mkdir darezone-backend
cd darezone-backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Create project structure
mkdir -p app/{core,api/{v1},schemas,services,repositories,utils,middleware}
mkdir -p tests
touch app/__init__.py
touch app/core/__init__.py
touch app/api/__init__.py
touch app/api/v1/__init__.py
```

### Step 2: Create requirements.txt

```txt
# Core
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0

# Database & Auth
supabase==2.3.0
asyncpg==0.29.0

# Utilities
python-multipart==0.0.6
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-dotenv==1.0.0

# HTTP
httpx==0.25.1

# Development
pytest==7.4.3
pytest-asyncio==0.21.1
black==23.11.0
flake8==6.1.0
mypy==1.7.1
```

### Step 3: Create app/core/config.py

```python
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    """Application settings"""
    
    # App
    APP_NAME: str = "DareZone API"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Supabase
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:19006",
        "http://localhost:8081",
    ]
    
    # Business Logic
    MAX_HABITS_PER_CHALLENGE: int = 4
    DEFAULT_HITCH_COUNT: int = 2
    POINTS_PER_CHECKIN: int = 10
    POINTS_STREAK_MULTIPLIER: int = 2
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Singleton instance
settings = Settings()
```

### Step 4: Create app/main.py

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1 import router as api_router

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(api_router, prefix="/api/v1")

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint for load balancer"""
    return {
        "status": "ok",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "docs": "/docs",
        "health": "/health"
    }
```

### Step 5: Create app/api/v1/router.py

```python
from fastapi import APIRouter

router = APIRouter()

# Placeholder for future endpoints
@router.get("/")
async def api_root():
    """API v1 root"""
    return {
        "version": "1.0",
        "endpoints": {
            "auth": "/api/v1/auth",
            "users": "/api/v1/users",
            "challenges": "/api/v1/challenges",
        }
    }
```

### Step 6: Create app/api/v1/__init__.py

```python
from fastapi import APIRouter
from .router import router as base_router

router = APIRouter()
router.include_router(base_router)

# Future imports:
# from .auth import router as auth_router
# from .users import router as users_router
# router.include_router(auth_router, prefix="/auth", tags=["auth"])
# router.include_router(users_router, prefix="/users", tags=["users"])
```

### Step 7: Create app/core/dependencies.py

```python
from supabase import Client, create_client
from app.core.config import settings
from functools import lru_cache

@lru_cache()
def get_supabase_client() -> Client:
    """
    Get Supabase client singleton
    Uses service role key for backend operations
    """
    return create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_SERVICE_ROLE_KEY
    )
```

### Step 8: Create app/core/exceptions.py

```python
from fastapi import HTTPException, status

class DareZoneException(Exception):
    """Base exception for DareZone"""
    pass

class AuthenticationError(DareZoneException):
    """Authentication failed"""
    pass

class AuthorizationError(DareZoneException):
    """User not authorized"""
    pass

class ValidationError(DareZoneException):
    """Input validation failed"""
    pass

class NotFoundError(DareZoneException):
    """Resource not found"""
    pass

# HTTP Exception helpers
def unauthorized_exception(detail: str = "Not authenticated"):
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )

def forbidden_exception(detail: str = "Not authorized"):
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=detail
    )

def not_found_exception(detail: str = "Resource not found"):
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=detail
    )
```

### Step 9: Create app/middleware/logging.py

```python
import logging
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all HTTP requests"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Log request
        logger.info(f"{request.method} {request.url.path}")
        
        # Process request
        response = await call_next(request)
        
        # Log response
        process_time = time.time() - start_time
        logger.info(
            f"{request.method} {request.url.path} "
            f"- {response.status_code} "
            f"- {process_time:.3f}s"
        )
        
        response.headers["X-Process-Time"] = str(process_time)
        return response
```

### Step 10: Create .env.example

```bash
# Supabase (REQUIRED)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# App Config
APP_NAME=DareZone API
APP_VERSION=1.0.0
ENVIRONMENT=development
DEBUG=true

# CORS
ALLOWED_ORIGINS=["http://localhost:19006","exp://192.168.1.8:8081"]

# Business Rules
MAX_HABITS_PER_CHALLENGE=4
DEFAULT_HITCH_COUNT=2
POINTS_PER_CHECKIN=10
POINTS_STREAK_MULTIPLIER=2
```

### Step 11: Create README.md

```markdown
# DareZone Backend

FastAPI backend for DareZone habit-building app.

## Setup

1. Clone repository
2. Create virtual environment: `python3.11 -m venv venv`
3. Activate: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Copy `.env.example` to `.env` and fill in values
6. Run: `uvicorn app.main:app --reload`

## Development

- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health
- Run tests: `pytest`
- Format code: `black app tests`

## Project Structure

```
app/
├── main.py              # FastAPI app
├── core/                # Core config & dependencies
├── api/v1/              # API routes
├── schemas/             # Pydantic DTOs
├── services/            # Business logic
├── repositories/        # Data access
└── middleware/          # Custom middleware
```
```

### Step 12: Run and Test

```bash
# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Test endpoints
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/

# Check docs
open http://localhost:8000/docs
```

---

## 📦 Files to Create

```
darezone-backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI entry
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py          # Settings
│   │   ├── dependencies.py    # DI
│   │   ├── security.py        # Auth (skeleton)
│   │   └── exceptions.py      # Custom exceptions
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── router.py      # API router
│   └── middleware/
│       ├── __init__.py
│       └── logging.py         # Request logging
├── tests/
│   ├── __init__.py
│   └── test_main.py           # Basic tests
├── .env.example               # Env template
├── .gitignore
├── requirements.txt
├── README.md
└── pytest.ini
```

---

## 🧪 Testing Checklist

### Manual Tests

```bash
# 1. Server starts without errors
uvicorn app.main:app --reload

# 2. Health check works
curl http://localhost:8000/health
# Expected: {"status":"ok","version":"1.0.0","environment":"development"}

# 3. API root works
curl http://localhost:8000/api/v1/
# Expected: {"version":"1.0","endpoints":{...}}

# 4. Swagger docs load
open http://localhost:8000/docs

# 5. CORS headers present
curl -H "Origin: http://localhost:19006" http://localhost:8000/health -v
# Expected: Access-Control-Allow-Origin header

# 6. Config loads from .env
# Change DEBUG=false in .env, restart, check logs
```

### Automated Tests

```python
# tests/test_main.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "Welcome" in response.json()["message"]

def test_api_v1_root():
    response = client.get("/api/v1/")
    assert response.status_code == 200
    assert response.json()["version"] == "1.0"
```

---

## 📝 Notes

### Development Workflow

```bash
# 1. Start server with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 2. Code changes auto-reload server

# 3. Test in browser/Postman/curl

# 4. Check Swagger docs for API structure
```

### Common Issues

**Issue**: Import errors
```bash
# Solution: Make sure venv is activated
source venv/bin/activate

# Solution: Install in editable mode
pip install -e .
```

**Issue**: Port already in use
```bash
# Solution: Change port or kill existing process
lsof -ti:8000 | xargs kill -9
uvicorn app.main:app --reload --port 8001
```

**Issue**: CORS errors from mobile
```bash
# Solution: Add your local IP to ALLOWED_ORIGINS
# Find IP: ifconfig (Mac/Linux) or ipconfig (Windows)
ALLOWED_ORIGINS=["http://localhost:19006","exp://192.168.1.8:8081"]
```

### Best Practices

1. **Virtual Environment**: Always use venv, never install globally
2. **Git Ignore**: Add `.env`, `venv/`, `__pycache__/`
3. **Code Style**: Use Black formatter, Flake8 linter
4. **Type Hints**: Use mypy for type checking
5. **Imports**: Use absolute imports (`from app.core import ...`)

---

## ✅ Definition of Done

- [ ] FastAPI app runs successfully
- [ ] Health check endpoint returns 200
- [ ] Swagger docs accessible at `/docs`
- [ ] Environment config loads from `.env`
- [ ] CORS configured and tested
- [ ] All files created per structure
- [ ] README.md complete with setup instructions
- [ ] Basic tests pass (`pytest`)
- [ ] Code formatted with Black
- [ ] `.gitignore` configured
- [ ] Peer review completed

---

**Previous:** [Story 1: Database Setup](./story-1-database-setup.md)  
**Next:** [Story 3: Authentication System](./story-3-authentication.md)
