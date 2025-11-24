# 🚀 Getting Started với Backend Implementation Stories

## Chào mừng Backend Developer!

Đây là bộ stories để implement backend DareZone từ đầu. Mỗi story là một task cụ thể với acceptance criteria rõ ràng.

---

## 📋 Workflow Chuẩn

### 1. **Đọc Story**
```bash
# Mở story file, đọc kỹ:
# - Description (làm gì)
# - Goals (mục tiêu)
# - Acceptance Criteria (definition of done)
# - Technical Implementation (chi tiết kỹ thuật)
```

### 2. **Check Dependencies**
```bash
# Đảm bảo các story dependencies đã hoàn thành
# VD: Story 3 (Auth) cần Story 2 (Project) hoàn thành trước
```

### 3. **Create Branch**
```bash
git checkout main
git pull origin main
git checkout -b story-{number}-{title}

# VD:
git checkout -b story-3-authentication
```

### 4. **Implement**
```bash
# Follow technical implementation trong story
# Tạo files theo structure đã định
# Copy code templates và customize

# Commit nhỏ, thường xuyên:
git add .
git commit -m "feat(story-3): implement token verification"
git commit -m "feat(story-3): add auth endpoints"
git commit -m "test(story-3): add auth tests"
```

### 5. **Test Thoroughly**
```bash
# Run tests
pytest tests/test_auth.py -v

# Manual testing
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN"

# Check coverage
pytest --cov=app tests/
```

### 6. **Update Documentation**
```bash
# Swagger docs tự động update
# Nhưng check xem có rõ ràng không tại /docs
```

### 7. **Create Pull Request**
```bash
git push origin story-3-authentication

# Tạo PR trên GitHub/GitLab:
# - Title: "[Story 3] Authentication System"
# - Description: Checklist từ acceptance criteria
# - Request review
```

### 8. **Code Review & Merge**
```bash
# Sau khi approved:
git checkout main
git pull origin main
git branch -d story-3-authentication
```

### 9. **Update Story Status**
```bash
# Update README.md tracking table:
# 📝 TODO → 🚧 IN PROGRESS → ✅ DONE
```

---

## 🎯 Phase 1: Core Backend (Tuần 1-4)

**Mục tiêu:** MVP backend có thể connect với mobile app

### Week 1: Foundation
- **Day 1-3:** [Story 1](./phase-1/story-1-database-setup.md) - Setup Supabase & DB
- **Day 4-5:** [Story 2](./phase-1/story-2-project-structure.md) - FastAPI Project Structure

### Week 2: Authentication & Users
- **Day 1-3:** [Story 3](./phase-1/story-3-authentication.md) - Authentication System
- **Day 4-5:** [Story 4](./phase-1/story-4-user-management.md) - User Management API
  - Implement user profile CRUD
  - Update profile endpoint
  - Get user stats

### Week 3: Core Features
- **Day 1-5:** [Story 5](./phase-1/story-5-challenge-management.md) - Challenge Management
  - Create, join, leave challenges
  - Invite code system
  - Member management

### Week 4: Check-ins & Deploy
- **Day 1-4:** [Story 6](./phase-1/story-6-checkin-system.md) - Check-in System
  - Create check-ins
  - Streak calculation
  - Points system
- **Day 5:** [Story 7](./phase-1/story-7-deployment.md) - Deploy to Railway/Render
  - CI/CD setup
  - Environment config
  - Health monitoring

**🎉 Phase 1 Done:** Backend có thể test với mobile app!

---

## 🎯 Phase 2: Social Features (Tuần 5-7)

**Mục tiêu:** Social interactions đầy đủ

### Week 5: Friends & Notifications
- **Day 1-3:** [Story 8](./phase-2/story-8-friendship.md) - Friendship System
- **Day 4-5:** [Story 9](./phase-2/story-9-notifications.md) - Notification System

### Week 6: Media & Hitch
- **Day 1-3:** [Story 10](./phase-2/story-10-media-upload.md) - Media Upload
  - Supabase Storage integration
  - Photo/video upload
  - File validation
- **Day 4-5:** [Story 11](./phase-2/story-11-hitch-system.md) - Hitch Reminders
  - Hitch log
  - Rate limiting
  - Push notifications

### Week 7: History & Stats
- **Day 1-3:** [Story 12](./phase-2/story-12-history-stats.md) - History & Stats API
  - Challenge history
  - User stats aggregation
  - Leaderboards

**🎉 Phase 2 Done:** App đầy đủ features B2C!

---

## 🎯 Phase 3: B2B & Production (Tuần 8-10)

**Mục tiêu:** B2B support và production-ready

### Week 8: B2B Core
- **Day 1-3:** [Story 13](./phase-3/story-13-organizations.md) - Organizations
- **Day 4-5:** [Story 14](./phase-3/story-14-programs.md) - Programs & Cohorts

### Week 9: Analytics & Performance
- **Day 1-3:** [Story 15](./phase-3/story-15-analytics.md) - Analytics Dashboard
- **Day 4-5:** [Story 16](./phase-3/story-16-performance.md) - Performance Optimization
  - Query optimization
  - Caching
  - Indexing

### Week 10: Production Hardening
- **Day 1-2:** [Story 17](./phase-3/story-17-scheduled-jobs.md) - Scheduled Jobs
  - Auto-complete challenges
  - Stats aggregation
  - Notification scheduler
- **Day 3-5:** [Story 18](./phase-3/story-18-production-hardening.md) - Production Hardening
  - Security audit
  - Load testing
  - Monitoring setup

**🎉 Phase 3 Done:** Production-ready!

---

## 🔥 Quick Start (Day 1)

```bash
# 1. Clone repo
git clone [repo-url]
cd darezone-backend

# 2. Setup Supabase
# - Tạo project tại https://supabase.com
# - Note down URL, anon key, service_role key

# 3. Create .env
cp .env.example .env
# Điền Supabase credentials

# 4. Apply migrations
# - Go to Supabase Dashboard → SQL Editor
# - Copy migrations/001_initial_schema.sql
# - Execute

# 5. Setup Python
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 6. Run server
uvicorn app.main:app --reload

# 7. Test
curl http://localhost:8000/health
open http://localhost:8000/docs

# ✅ Nếu thấy "ok" và Swagger docs → Ready!
```

---

## 📊 Progress Tracking

### Cách Update Progress

```markdown
# Trong README.md

| Story | Status | Assignee | Points | Start | End |
|-------|--------|----------|--------|-------|-----|
| Story 1 | ✅ DONE | You | 3 | 11/23 | 11/25 |
| Story 2 | 🚧 IN PROGRESS | You | 2 | 11/26 | - |
| Story 3 | 📝 TODO | - | 3 | - | - |
```

### Daily Standup Template

```
## Hôm qua:
- Completed Story 1: Database setup
- All tables created, RLS working

## Hôm nay:
- Starting Story 2: FastAPI structure
- Goal: Get health check working

## Blockers:
- None / [describe blocker]
```

---

## 💡 Tips & Best Practices

### 1. **Don't Skip Tests**
```python
# ❌ BAD: Code rồi sau mới test
def create_challenge(...):
    # 100 lines of code
    pass
# Giờ mới viết test → khó debug

# ✅ GOOD: Test-driven development
def test_create_challenge_success():
    # Write test first
    pass

def create_challenge(...):
    # Implement to pass test
    pass
```

### 2. **Commit Often, Small Commits**
```bash
# ❌ BAD
git commit -m "implement everything"

# ✅ GOOD
git commit -m "feat: add challenge schema"
git commit -m "feat: add create challenge endpoint"
git commit -m "test: add challenge creation tests"
git commit -m "docs: update swagger for challenges"
```

### 3. **Read Existing Code**
```bash
# Trước khi implement story mới:
# 1. Đọc code của story trước
# 2. Hiểu pattern đã dùng
# 3. Follow cùng style
```

### 4. **Ask Early**
```bash
# Nếu stuck > 30 phút:
# - Check story again
# - Google error
# - Ask team/mentor
# Don't waste hours!
```

### 5. **Manual Test ASAP**
```bash
# Sau khi viết endpoint:
curl http://localhost:8000/api/v1/challenges \
  -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{"name":"Test",...}'

# Xem response, fix bugs ngay
# Đừng đợi viết hết rồi mới test
```

---

## 🐛 Troubleshooting

### Database Issues

```python
# Error: "relation 'challenges' does not exist"
# → Run migrations in correct order (001, 002, 003...)

# Error: "RLS policy blocks access"
# → Check RLS policies, or use service_role key temporarily

# Error: Foreign key violation
# → Check referenced records exist first
```

### Auth Issues

```python
# Error: "Invalid token"
# → Token expired? Get fresh token from frontend
# → Supabase URL/keys correct?

# Error: "User not found"
# → User profile created after signup?
```

### CORS Issues

```python
# Error: "CORS blocked"
# → Add your IP to ALLOWED_ORIGINS
# → Check mobile app sends correct Origin header
```

---

## 📚 Reference Documents

- **[Backend Spec](../backend-spec.md)** - Full technical specification
- **[API Docs](http://localhost:8000/docs)** - Swagger (when server running)
- **[Supabase Docs](https://supabase.com/docs)** - Database & Auth
- **[FastAPI Docs](https://fastapi.tiangolo.com)** - Framework docs

---

## 🤝 Need Help?

1. **Story unclear?** → Re-read acceptance criteria
2. **Technical question?** → Check backend-spec.md
3. **Bug?** → Check troubleshooting section
4. **Still stuck?** → Ask team/create issue

---

## ✅ You're Ready!

Start với **[Story 1: Database Setup](./phase-1/story-1-database-setup.md)**

Good luck! 🚀

---

Last Updated: 2025-11-23
