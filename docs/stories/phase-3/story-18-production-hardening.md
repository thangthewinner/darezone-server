# Story 18: Production Hardening

**Phase:** 3 - B2B & Advanced  
**Points:** 2 (2 days)  
**Priority:** 🔥 CRITICAL  
**Dependencies:** [Story 17: Scheduled Jobs](./story-17-scheduled-jobs.md)

---

## 📖 Description

Final production hardening: security audit, rate limiting, monitoring, backup strategy, và documentation.

---

## 🎯 Goals

- [ ] Security vulnerabilities fixed
- [ ] Rate limiting enforced
- [ ] Monitoring & alerts configured
- [ ] Backup strategy in place
- [ ] Production runbook documented

---

## ✅ Acceptance Criteria

### 1. Security Audit
- [ ] SQL injection tests passed
- [ ] XSS prevention verified
- [ ] CORS properly configured
- [ ] Secrets not in git/logs
- [ ] RLS policies reviewed
- [ ] API authentication enforced

### 2. Rate Limiting
- [ ] Global rate limit: 100 req/min/IP
- [ ] Auth endpoints: 10 req/min
- [ ] Upload endpoints: 5 req/min
- [ ] 429 responses returned

### 3. Monitoring & Alerts
- [ ] Uptime monitoring (UptimeRobot)
- [ ] Error tracking (Sentry)
- [ ] Performance monitoring
- [ ] Alert emails configured
- [ ] Slack notifications (optional)

### 4. Backup Strategy
- [ ] Daily database backups
- [ ] Backup retention: 30 days
- [ ] Restore procedure tested
- [ ] Storage files backed up

### 5. Documentation
- [ ] API documentation complete
- [ ] Deployment runbook
- [ ] Incident response plan
- [ ] Monitoring dashboard guide

---

## 🛠️ Implementation

### Rate Limiting

```python
# app/middleware/rate_limit.py

from fastapi import Request, HTTPException
from datetime import datetime, timedelta
import redis

redis_client = redis.Redis(host='localhost', port=6379)

async def rate_limit_middleware(request: Request, call_next):
    """Rate limit by IP address"""
    
    # Get client IP
    client_ip = request.client.host
    
    # Different limits per path
    if request.url.path.startswith('/api/v1/auth'):
        limit, window = 10, 60  # 10 req/min
    elif request.url.path.startswith('/api/v1/media'):
        limit, window = 5, 60   # 5 req/min
    else:
        limit, window = 100, 60  # 100 req/min
    
    # Check rate limit
    key = f"rate_limit:{client_ip}:{request.url.path}"
    current = redis_client.get(key)
    
    if current and int(current) >= limit:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Try again later."
        )
    
    # Increment counter
    pipe = redis_client.pipeline()
    pipe.incr(key)
    pipe.expire(key, window)
    pipe.execute()
    
    response = await call_next(request)
    return response

# Add to main.py
app.middleware("http")(rate_limit_middleware)
```

### Security Headers

```python
# app/middleware/security.py

from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

# Add to main.py
if settings.ENVIRONMENT == "production":
    # Force HTTPS
    app.add_middleware(HTTPSRedirectMiddleware)
    
    # Trusted hosts
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["darezone-api.com", "*.darezone-api.com"]
    )
    
    # Security headers
    @app.middleware("http")
    async def add_security_headers(request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000"
        return response
```

### Monitoring Setup

```python
# app/main.py - Sentry Integration

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,
        traces_sample_rate=0.1,
        integrations=[FastApiIntegration()]
    )
```

### Backup Script

```bash
#!/bin/bash
# scripts/backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"

# Database backup
supabase db dump > "$BACKUP_DIR/db_backup_$DATE.sql"

# Compress
gzip "$BACKUP_DIR/db_backup_$DATE.sql"

# Upload to S3 (optional)
aws s3 cp "$BACKUP_DIR/db_backup_$DATE.sql.gz" \
  s3://darezone-backups/

# Cleanup old backups (keep 30 days)
find $BACKUP_DIR -name "db_backup_*.sql.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
```

### Production Checklist

```markdown
# Pre-Launch Checklist

## Security
- [ ] All secrets in environment variables (not in code)
- [ ] HTTPS enabled
- [ ] CORS configured correctly
- [ ] RLS policies active on all tables
- [ ] SQL injection tests passed
- [ ] Rate limiting active

## Performance
- [ ] All indexes created
- [ ] Load testing passed (100 concurrent users)
- [ ] Response times < 200ms p95
- [ ] No memory leaks

## Monitoring
- [ ] Sentry error tracking configured
- [ ] UptimeRobot monitoring active
- [ ] Health check endpoint monitored
- [ ] Alert emails configured

## Backups
- [ ] Daily database backups scheduled
- [ ] Backup restore tested
- [ ] Storage files backed up
- [ ] 30-day retention configured

## Documentation
- [ ] API docs complete
- [ ] Deployment runbook written
- [ ] Incident response plan documented
- [ ] Team trained on monitoring

## Testing
- [ ] All tests passing
- [ ] End-to-end tests run
- [ ] Mobile app tested against production API
- [ ] Load testing completed
```

---

## 📦 Files

```
app/middleware/rate_limit.py
app/middleware/security.py
scripts/backup.sh
docs/PRODUCTION_RUNBOOK.md
docs/INCIDENT_RESPONSE.md
.github/workflows/security-scan.yml
```

---

## 🧪 Testing

```python
def test_rate_limiting()
def test_security_headers()
def test_sql_injection_prevention()
def test_xss_prevention()
```

---

## ✅ Definition of Done

- [ ] Security audit completed
- [ ] Rate limiting enforced
- [ ] Monitoring configured
- [ ] Alerts working
- [ ] Backups automated
- [ ] Restore procedure tested
- [ ] Production runbook complete
- [ ] Team trained
- [ ] Launch-ready!

---

## 🎉 Congratulations!

All 18 stories complete! Backend is **production-ready**.

---

**Final Steps:**
1. Run full test suite
2. Load test production environment
3. Train team on operations
4. Launch! 🚀
