# Story 7: Deployment & CI/CD

**Phase:** 1 - Core Backend  
**Points:** 2 (2 days)  
**Priority:** 🔥 CRITICAL  
**Dependencies:** [Story 6: Check-in System](./story-6-checkin-system.md)

---

## 📖 Description

Deploy backend to production (Railway/Render), setup CI/CD, configure monitoring, và environment management.

---

## 🎯 Goals

- [ ] Backend deployed và accessible
- [ ] Auto-deploy on git push
- [ ] Environment variables secured
- [ ] Health monitoring setup
- [ ] Logs accessible

---

## ✅ Acceptance Criteria

### 1. Production Deployment
- [ ] Backend running on Railway hoặc Render
- [ ] Public URL accessible (https://)
- [ ] Health check endpoint returns 200
- [ ] Swagger docs disabled in production

### 2. CI/CD Pipeline
- [ ] Auto-deploy on push to `main` branch
- [ ] Tests run before deploy
- [ ] Failed tests block deployment
- [ ] GitHub Actions or platform CI configured

### 3. Environment Configuration
- [ ] Production .env variables set
- [ ] Secrets not in git
- [ ] ALLOWED_ORIGINS includes production domains
- [ ] DEBUG=false in production

### 4. Monitoring
- [ ] Health check endpoint monitored
- [ ] Error logging configured
- [ ] Uptime monitoring (optional: UptimeRobot)
- [ ] Performance metrics visible

### 5. Database
- [ ] Supabase production project setup
- [ ] Migrations applied
- [ ] Backups enabled
- [ ] RLS policies active

---

## 🛠️ Technical Implementation

### Option A: Deploy to Railway

```bash
# 1. Install Railway CLI
npm install -g @railway/cli

# 2. Login
railway login

# 3. Initialize project
railway init

# 4. Set environment variables
railway variables set SUPABASE_URL=https://prod.supabase.co
railway variables set SUPABASE_SERVICE_ROLE_KEY=xxx
railway variables set ENVIRONMENT=production
railway variables set DEBUG=false
railway variables set ALLOWED_ORIGINS='["https://darezone.app"]'

# 5. Deploy
railway up

# 6. Get URL
railway domain
# Creates: https://darezone-backend-production.up.railway.app
```

### Option B: Deploy to Render

```yaml
# render.yaml
services:
  - type: web
    name: darezone-api
    env: python
    region: singapore
    plan: starter
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: SUPABASE_URL
        sync: false
      - key: SUPABASE_SERVICE_ROLE_KEY
        sync: false
      - key: ENVIRONMENT
        value: production
      - key: DEBUG
        value: false
      - key: PYTHON_VERSION
        value: 3.11.0
    healthCheckPath: /health
```

### GitHub Actions CI/CD

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      
      - name: Run tests
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.TEST_SERVICE_KEY }}
        run: |
          pytest tests/ -v --cov=app
  
  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to Railway
        uses: bervProject/railway-deploy@main
        with:
          railway_token: ${{ secrets.RAILWAY_TOKEN }}
          service: darezone-api
```

### Production app/main.py Adjustments

```python
from app.core.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    # Disable docs in production
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# Logging configuration
if settings.ENVIRONMENT == "production":
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='{"time":"%(asctime)s","level":"%(levelname)s","message":"%(message)s"}'
    )
```

### Health Check with Database

```python
@app.get("/health")
async def health_check(supabase: Client = Depends(get_supabase_client)):
    """
    Enhanced health check with DB connection test
    """
    try:
        # Test DB connection
        result = supabase.table('user_profiles').select('id').limit(1).execute()
        db_status = "ok" if result else "error"
    except Exception:
        db_status = "error"
    
    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "database": db_status,
        "timestamp": datetime.now().isoformat()
    }
```

### Dockerfile (Optional)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 📦 Deployment Checklist

### Pre-Deployment

- [ ] All tests passing locally
- [ ] Environment variables documented in .env.example
- [ ] No secrets in git history
- [ ] Database migrations applied to production DB
- [ ] CORS origins updated for production domains

### Deployment

- [ ] Create production account (Railway/Render)
- [ ] Set all environment variables
- [ ] Deploy application
- [ ] Verify health check returns 200
- [ ] Test API endpoints from mobile app

### Post-Deployment

- [ ] Set up custom domain (optional)
- [ ] Configure SSL certificate (auto on Railway/Render)
- [ ] Set up monitoring (UptimeRobot, Sentry)
- [ ] Test mobile app against production API
- [ ] Document production URL for team

---

## 🧪 Testing Checklist

```bash
# 1. Health check
curl https://your-app.railway.app/health

# 2. Test authentication
curl https://your-app.railway.app/api/v1/auth/me \
  -H "Authorization: Bearer TOKEN"

# 3. Test CORS from mobile domain
curl -H "Origin: https://darezone.app" \
  https://your-app.railway.app/health -v

# 4. Load testing (optional)
ab -n 1000 -c 10 https://your-app.railway.app/health
```

---

## 📝 Notes

### Environment Variables Checklist

```bash
# Required
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=xxx
SUPABASE_ANON_KEY=xxx

# App Config
ENVIRONMENT=production
DEBUG=false
APP_NAME=DareZone API
APP_VERSION=1.0.0

# Security
ALLOWED_ORIGINS=["https://darezone.app","https://app.darezone.com"]
SECRET_KEY=<generate-new-for-production>

# Optional
SENTRY_DSN=https://xxx@sentry.io/xxx
LOG_LEVEL=INFO
```

### Monitoring Setup

```bash
# 1. UptimeRobot (free tier)
# - Add monitor: https://your-app.railway.app/health
# - Check interval: 5 minutes
# - Alert email on downtime

# 2. Sentry (error tracking)
pip install sentry-sdk[fastapi]

# app/main.py
import sentry_sdk
if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,
        traces_sample_rate=0.1
    )
```

### Common Issues

**Issue**: Deployment fails with "Module not found"
```bash
# Solution: Check requirements.txt is complete
pip freeze > requirements.txt
```

**Issue**: Database connection fails
```bash
# Solution: Check Supabase URL and keys correct
# Verify IP not blocked by Supabase firewall
```

**Issue**: CORS errors from production
```bash
# Solution: Update ALLOWED_ORIGINS
ALLOWED_ORIGINS='["https://darezone.app"]'
```

---

## ✅ Definition of Done

- [ ] Backend deployed to Railway/Render
- [ ] Production URL accessible
- [ ] Health check returns 200
- [ ] Mobile app connects successfully
- [ ] CI/CD pipeline working
- [ ] Environment variables secured
- [ ] Monitoring configured
- [ ] Documentation updated with prod URL
- [ ] Team can access logs
- [ ] Backup strategy in place

---

**Previous:** [Story 6: Check-in System](./story-6-checkin-system.md)  
**Next Phase:** [Phase 2: Social Features](../phase-2/)
