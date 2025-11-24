# DareZone Backend

FastAPI backend for DareZone - A habit-building social application.

## 📋 Project Status

**Current Phase:** Phase 1 - Core Backend  
**Story:** Story 1 - Database Setup ✅ COMPLETED  
**Next:** Story 2 - FastAPI Project Structure

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Supabase account (free tier OK)
- PostgreSQL knowledge (basic)

### Step 1: Clone & Setup Environment

```bash
# Navigate to backend directory
cd darezone-server

# Create virtual environment
python3.11 -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate  # Windows

# Copy environment variables
cp .env.example .env
# Edit .env with your Supabase credentials
```

### Step 2: Setup Supabase Database

**Option A: Using Supabase Dashboard (Recommended)**

1. Go to https://app.supabase.com/project/YOUR_PROJECT_ID/sql/new
2. Open `migrations/001_initial_schema.sql`
3. Copy entire content → Paste into SQL Editor → Run
4. Repeat for `002_rls_policies.sql`, `003_seed_habits.sql`, `004_indexes.sql`, `005_triggers.sql`
5. Verify in Table Editor - should see 11 tables

**Option B: Using Supabase CLI**

```bash
# Install Supabase CLI
npm install -g supabase

# Login
supabase login

# Link to your project
supabase link --project-ref YOUR_PROJECT_REF

# Apply migrations
supabase db push
```

**See [migrations/README.md](./migrations/README.md) for detailed instructions**

### Step 3: Verify Setup

Run verification tests from [migrations/TESTING.md](./migrations/TESTING.md)

```sql
-- Quick verification query
SELECT COUNT(*) FROM habits WHERE is_system = true;
-- Expected: 10
```

---

## 📁 Project Structure

```
darezone-server/
├── .env                    # Environment variables (not in git)
├── .env.example            # Environment template
├── migrations/             # Database migrations
│   ├── README.md           # Migration guide
│   ├── TESTING.md          # Testing guide
│   ├── 001_initial_schema.sql
│   ├── 002_rls_policies.sql
│   ├── 003_seed_habits.sql
│   ├── 004_indexes.sql
│   └── 005_triggers.sql
└── stories/                # Implementation stories
    ├── phase-1/            # Core backend (7 stories)
    ├── phase-2/            # Social features (5 stories)
    └── phase-3/            # B2B & Production (6 stories)
```

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [migrations/README.md](./migrations/README.md) | How to apply database migrations |
| [migrations/TESTING.md](./migrations/TESTING.md) | Complete testing guide with SQL tests |
| [stories/README.md](./stories/README.md) | All 18 implementation stories |
| [stories/GETTING-STARTED.md](./stories/GETTING-STARTED.md) | Developer workflow guide |
| [docs/backend/backend-spec.md](../docs/backend/backend-spec.md) | Full technical specification |

---

## 🗄️ Database Schema

### Core Tables (11 total)

| Table | Description | Key Features |
|-------|-------------|--------------|
| `user_profiles` | User data & stats | Streaks, points, org membership |
| `challenges` | Challenges created by users | Auto-generated invite codes |
| `habits` | System & custom habits | 10 system habits seeded |
| `challenge_habits` | Habits in challenges | Many-to-many junction |
| `challenge_members` | Users in challenges | Role, status, streaks |
| `check_ins` | Daily check-ins | One per habit per day |
| `friendships` | Friend connections | Bidirectional with status |
| `notifications` | In-app notifications | Type-based with expiry |
| `hitch_log` | Reminder history | Rate-limited per day |
| `organizations` | B2B organizations | Plans & feature flags |
| `programs` | B2B programs | Recurring challenges |

### Features

- ✅ **Row Level Security (RLS)** - All tables protected
- ✅ **Auto-generated invite codes** - For group challenges
- ✅ **Auto-increment counters** - Check-ins, members, stats
- ✅ **Automatic timestamps** - updated_at auto-updates
- ✅ **50+ Performance indexes** - Optimized queries
- ✅ **Constraint validation** - Dates, negatives, duplicates
- ✅ **10 System habits** - Pre-seeded for challenges

---

## 🔧 Environment Variables

Copy `.env.example` to `.env` and configure:

### Required

```env
# Supabase (from https://app.supabase.com/project/_/settings/api)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# App
APP_NAME=DareZone
ENVIRONMENT=development
DEBUG=true
```

### Optional (defaults provided)

```env
MAX_HABITS_PER_CHALLENGE=4
DEFAULT_HITCH_COUNT=2
POINTS_PER_CHECKIN=10
STORAGE_BUCKET_PHOTOS=darezone-photos
MAX_UPLOAD_SIZE_MB=10
```

See `.env.example` for full list.

---

## 🧪 Testing

### Database Testing

Follow [migrations/TESTING.md](./migrations/TESTING.md) for:

1. Table creation verification
2. Constraint validation tests
3. RLS policy tests
4. Trigger functionality tests
5. Performance index tests

### Quick Test

```sql
-- Test user creation
INSERT INTO user_profiles (id, email, display_name)
VALUES (
  '11111111-1111-1111-1111-111111111111',
  'test@darezone.com',
  'Test User'
);

-- Test challenge creation (invite_code auto-generated)
INSERT INTO challenges (name, start_date, end_date, created_by, type)
VALUES (
  'Test Challenge',
  CURRENT_DATE,
  CURRENT_DATE + 30,
  '11111111-1111-1111-1111-111111111111',
  'group'
);

-- Verify invite code generated
SELECT name, invite_code FROM challenges;
```

---

## 📖 Implementation Stories

### Phase 1: Core Backend (4 weeks)

- ✅ **Story 1**: Database Setup (3 days) - **COMPLETED**
- 📝 **Story 2**: FastAPI Project Structure (2 days)
- 📝 **Story 3**: Authentication System (3 days)
- 📝 **Story 4**: User Management (3 days)
- 📝 **Story 5**: Challenge Management (5 days)
- 📝 **Story 6**: Check-in System (4 days)
- 📝 **Story 7**: Deployment & CI/CD (2 days)

### Phase 2: Social Features (3 weeks)

- 📝 **Story 8-12**: Friends, Notifications, Media, Hitch, Stats

### Phase 3: B2B & Production (3 weeks)

- 📝 **Story 13-18**: Organizations, Programs, Analytics, Optimization

**See [stories/README.md](./stories/README.md) for complete roadmap**

---

## 🔐 Security

### Authentication

- Supabase Auth with JWT tokens
- RLS policies on all tables
- Service role key for backend operations only

### Data Protection

- Row Level Security (RLS) enforced
- Users can only see:
  - Their own data
  - Friends' data (where applicable)
  - Challenge members' data (where applicable)

### Rate Limiting

- Max 3 hitch reminders per user per day
- One check-in per habit per day
- Duplicate prevention via unique constraints

---

## 🛠️ Tech Stack

- **Database**: Supabase PostgreSQL 15+
- **Backend**: FastAPI 0.104+ (Python 3.11+) - *Coming in Story 2*
- **Storage**: Supabase Storage - *Coming in Story 10*
- **Auth**: Supabase Auth (JWT) - *Coming in Story 3*
- **Deployment**: Railway/Render - *Coming in Story 7*

---

## 📞 Support & Resources

### Documentation

- [Supabase Docs](https://supabase.com/docs)
- [PostgreSQL Docs](https://www.postgresql.org/docs/current/)
- [FastAPI Docs](https://fastapi.tiangolo.com)

### Common Issues

See [migrations/README.md#troubleshooting](./migrations/README.md#troubleshooting)

---

## ✅ Completed

- [x] Supabase project setup
- [x] Database schema with 11 tables
- [x] RLS policies (~40 policies)
- [x] Performance indexes (50+ indexes)
- [x] Auto-update triggers
- [x] 10 system habits seeded
- [x] Comprehensive testing guide
- [x] Environment configuration

---

## 🚧 Next Steps

1. Verify all migrations applied successfully
2. Run tests from [migrations/TESTING.md](./migrations/TESTING.md)
3. Proceed to **Story 2**: FastAPI Project Structure
4. Build API endpoints to interact with database

---

## 📄 License

MIT License - See LICENSE file

---

**Project Version:** 1.0.0  
**Database Version:** 1.0 (Story 1)  
**Last Updated:** 2025-11-23  
**Status:** ✅ Database Ready - Awaiting FastAPI Implementation
