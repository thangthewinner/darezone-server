# Story 1: Supabase Setup & Database Schema

**Phase:** 1 - Core Backend  
**Points:** 3 (3 days)  
**Priority:** 🔥 CRITICAL  
**Dependencies:** None (First story)

---

## 📖 Description

Setup Supabase project và implement toàn bộ database schema bao gồm: tables, constraints, indexes, RLS policies, và seed data.

---

## 🎯 Goals

- [ ] Supabase project ready for development
- [ ] All tables created with proper constraints
- [ ] RLS policies implemented and tested
- [ ] System habits seeded
- [ ] Database accessible from backend

---

## ✅ Acceptance Criteria

### 1. Supabase Project Setup
- [ ] Project created on Supabase Dashboard
- [ ] Project URL and keys documented in .env.example
- [ ] Database accessible via connection string

### 2. Core Tables Created
- [ ] `user_profiles` table with full schema
- [ ] `challenges` table with enums and constraints
- [ ] `habits` table with system/custom support
- [ ] `challenge_habits` junction table
- [ ] `challenge_members` with role/status
- [ ] `check_ins` with unique constraint per day
- [ ] All foreign keys properly defined
- [ ] All indexes created

### 3. Supporting Tables
- [ ] `friendships` table
- [ ] `notifications` table
- [ ] `hitch_log` table
- [ ] `organizations` table (for B2B)
- [ ] `programs` table (for B2B)

### 4. Helper Functions
- [ ] `update_updated_at_column()` trigger function
- [ ] `generate_invite_code()` function
- [ ] Triggers attached to tables

### 5. RLS Policies Implemented
- [ ] All tables have RLS enabled
- [ ] User profiles policies (view own, friends, challenge members)
- [ ] Challenges policies (members only)
- [ ] Check-ins policies (create own, view challenge members)
- [ ] Friendships policies (both parties)
- [ ] Service role bypass policies

### 6. Seed Data
- [ ] 10 system habits inserted
- [ ] Test with proper icons and descriptions
- [ ] Categories assigned

### 7. Testing
- [ ] Can create user profile via SQL
- [ ] Can create challenge with RLS
- [ ] Can add members to challenge
- [ ] Can create check-in with constraint validation
- [ ] RLS prevents unauthorized access

---

## 🛠️ Technical Implementation

### Step 1: Create Supabase Project

```bash
# 1. Go to https://app.supabase.com
# 2. Click "New Project"
# 3. Fill in:
#    - Name: darezone-dev
#    - Database Password: [STRONG PASSWORD]
#    - Region: Southeast Asia (Singapore)
# 4. Wait for provisioning (~2 mins)
# 5. Note down:
#    - Project URL
#    - anon key
#    - service_role key
```

### Step 2: Create Migration Files

```bash
# Create migrations folder
mkdir -p migrations

# Create migration files in order
touch migrations/001_initial_schema.sql
touch migrations/002_rls_policies.sql
touch migrations/003_seed_habits.sql
touch migrations/004_indexes.sql
touch migrations/005_triggers.sql
```

### Step 3: Implement Schema (001_initial_schema.sql)

```sql
-- ENUMS
CREATE TYPE challenge_status AS ENUM ('pending', 'active', 'completed', 'failed', 'archived');
CREATE TYPE challenge_type AS ENUM ('individual', 'group', 'program');
CREATE TYPE checkin_type AS ENUM ('photo', 'video', 'caption', 'any');
CREATE TYPE member_role AS ENUM ('creator', 'admin', 'member');
CREATE TYPE member_status AS ENUM ('pending', 'active', 'left', 'kicked');
CREATE TYPE friendship_status AS ENUM ('pending', 'accepted', 'rejected', 'blocked');
CREATE TYPE notification_type AS ENUM (
  'friend_request', 'friend_accepted', 'challenge_invite',
  'challenge_started', 'challenge_completed', 'hitch_reminder',
  'streak_milestone', 'member_joined', 'member_left'
);
CREATE TYPE checkin_status AS ENUM ('pending', 'completed', 'verified', 'rejected');
CREATE TYPE program_period AS ENUM ('week', 'month', 'quarter');
CREATE TYPE program_difficulty AS ENUM ('easy', 'medium', 'hard');

-- USER PROFILES
CREATE TABLE public.user_profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email TEXT NOT NULL UNIQUE,
  full_name TEXT,
  display_name TEXT,
  avatar_url TEXT,
  bio TEXT,
  account_type TEXT DEFAULT 'b2c' CHECK (account_type IN ('b2c', 'b2b')),
  forced_mode TEXT CHECK (forced_mode IN ('b2c', 'b2b')),
  organization_id UUID,
  current_streak INTEGER DEFAULT 0 CHECK (current_streak >= 0),
  longest_streak INTEGER DEFAULT 0 CHECK (longest_streak >= 0),
  total_check_ins INTEGER DEFAULT 0 CHECK (total_check_ins >= 0),
  total_challenges_completed INTEGER DEFAULT 0 CHECK (total_challenges_completed >= 0),
  points INTEGER DEFAULT 0 CHECK (points >= 0),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  last_seen_at TIMESTAMPTZ DEFAULT NOW()
);

-- ORGANIZATIONS (B2B)
CREATE TABLE public.organizations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  slug TEXT UNIQUE NOT NULL,
  logo_url TEXT,
  description TEXT,
  plan TEXT DEFAULT 'starter' CHECK (plan IN ('starter', 'growth', 'enterprise')),
  max_members INTEGER DEFAULT 50,
  feature_flags JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  created_by UUID REFERENCES auth.users(id) ON DELETE SET NULL
);

-- CHALLENGES
CREATE TABLE public.challenges (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  description TEXT,
  type challenge_type DEFAULT 'individual',
  status challenge_status DEFAULT 'pending',
  start_date DATE NOT NULL,
  end_date DATE NOT NULL,
  duration_days INTEGER GENERATED ALWAYS AS (end_date - start_date) STORED,
  organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
  program_id UUID,
  max_members INTEGER DEFAULT 10,
  checkin_type checkin_type DEFAULT 'photo',
  require_evidence BOOLEAN DEFAULT true,
  invite_code TEXT UNIQUE,
  is_public BOOLEAN DEFAULT false,
  member_count INTEGER DEFAULT 0 CHECK (member_count >= 0),
  current_streak INTEGER DEFAULT 0 CHECK (current_streak >= 0),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  created_by UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  CONSTRAINT valid_date_range CHECK (end_date > start_date),
  CONSTRAINT valid_duration CHECK (duration_days <= 365)
);

-- HABITS
CREATE TABLE public.habits (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  icon TEXT,
  description TEXT,
  category TEXT,
  is_system BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  created_by UUID REFERENCES auth.users(id) ON DELETE SET NULL
);

-- CHALLENGE HABITS
CREATE TABLE public.challenge_habits (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  challenge_id UUID NOT NULL REFERENCES challenges(id) ON DELETE CASCADE,
  habit_id UUID NOT NULL REFERENCES habits(id) ON DELETE CASCADE,
  display_order INTEGER DEFAULT 0,
  custom_name TEXT,
  custom_icon TEXT,
  custom_description TEXT,
  total_checkins INTEGER DEFAULT 0,
  completion_rate DECIMAL(5,2) DEFAULT 0.00,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(challenge_id, habit_id)
);

-- CHALLENGE MEMBERS
CREATE TABLE public.challenge_members (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  challenge_id UUID NOT NULL REFERENCES challenges(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  role member_role DEFAULT 'member',
  status member_status DEFAULT 'pending',
  current_streak INTEGER DEFAULT 0 CHECK (current_streak >= 0),
  longest_streak INTEGER DEFAULT 0 CHECK (longest_streak >= 0),
  total_checkins INTEGER DEFAULT 0 CHECK (total_checkins >= 0),
  points_earned INTEGER DEFAULT 0 CHECK (points_earned >= 0),
  hitch_count INTEGER DEFAULT 2 CHECK (hitch_count >= 0),
  joined_at TIMESTAMPTZ DEFAULT NOW(),
  left_at TIMESTAMPTZ,
  last_checkin_at TIMESTAMPTZ,
  UNIQUE(challenge_id, user_id)
);

-- CHECK-INS
CREATE TABLE public.check_ins (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  challenge_id UUID NOT NULL REFERENCES challenges(id) ON DELETE CASCADE,
  habit_id UUID NOT NULL REFERENCES habits(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  checkin_date DATE NOT NULL DEFAULT CURRENT_DATE,
  status checkin_status DEFAULT 'completed',
  photo_url TEXT,
  video_url TEXT,
  caption TEXT,
  is_on_time BOOLEAN DEFAULT true,
  verified_by UUID REFERENCES auth.users(id),
  verified_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  CONSTRAINT one_checkin_per_day UNIQUE(challenge_id, habit_id, user_id, checkin_date)
);

-- FRIENDSHIPS
CREATE TABLE public.friendships (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  requester_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  addressee_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  status friendship_status DEFAULT 'pending',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  CHECK (requester_id != addressee_id),
  UNIQUE(requester_id, addressee_id)
);

-- NOTIFICATIONS
CREATE TABLE public.notifications (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  type notification_type NOT NULL,
  title TEXT NOT NULL,
  body TEXT NOT NULL,
  data JSONB DEFAULT '{}',
  action_url TEXT,
  is_read BOOLEAN DEFAULT false,
  read_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  expires_at TIMESTAMPTZ
);

-- HITCH LOG
CREATE TABLE public.hitch_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  challenge_id UUID NOT NULL REFERENCES challenges(id) ON DELETE CASCADE,
  habit_id UUID NOT NULL REFERENCES habits(id) ON DELETE CASCADE,
  sender_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  target_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  CONSTRAINT one_hitch_per_habit_per_day UNIQUE(habit_id, sender_id, target_id, created_at::date)
);

-- PROGRAMS (B2B)
CREATE TABLE public.programs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  description TEXT,
  organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  period program_period DEFAULT 'week',
  difficulty program_difficulty DEFAULT 'medium',
  challenges_per_cycle INTEGER DEFAULT 3 CHECK (challenges_per_cycle BETWEEN 1 AND 10),
  checkin_type checkin_type DEFAULT 'photo',
  start_date DATE,
  end_date DATE,
  participant_count INTEGER DEFAULT 0,
  completion_rate DECIMAL(5,2) DEFAULT 0.00,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  created_by UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE
);

-- Add FK after programs table exists
ALTER TABLE user_profiles 
  ADD CONSTRAINT fk_organization 
  FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE SET NULL;

ALTER TABLE challenges 
  ADD CONSTRAINT fk_program 
  FOREIGN KEY (program_id) REFERENCES programs(id) ON DELETE SET NULL;
```

### Step 4: Create Indexes (004_indexes.sql)

```sql
-- User Profiles
CREATE INDEX idx_user_profiles_org ON user_profiles(organization_id) WHERE organization_id IS NOT NULL;
CREATE INDEX idx_user_profiles_mode ON user_profiles(account_type);

-- Organizations
CREATE INDEX idx_organizations_slug ON organizations(slug);
CREATE INDEX idx_organizations_created_by ON organizations(created_by);

-- Challenges
CREATE INDEX idx_challenges_creator ON challenges(created_by);
CREATE INDEX idx_challenges_org ON challenges(organization_id) WHERE organization_id IS NOT NULL;
CREATE INDEX idx_challenges_status ON challenges(status);
CREATE INDEX idx_challenges_invite ON challenges(invite_code) WHERE invite_code IS NOT NULL;
CREATE INDEX idx_challenges_dates ON challenges(start_date, end_date);

-- Challenge Habits
CREATE INDEX idx_challenge_habits_challenge ON challenge_habits(challenge_id);
CREATE INDEX idx_challenge_habits_habit ON challenge_habits(habit_id);

-- Challenge Members
CREATE INDEX idx_challenge_members_challenge ON challenge_members(challenge_id);
CREATE INDEX idx_challenge_members_user ON challenge_members(user_id);
CREATE INDEX idx_challenge_members_status ON challenge_members(status);

-- Check-ins
CREATE INDEX idx_checkins_challenge ON check_ins(challenge_id);
CREATE INDEX idx_checkins_user ON check_ins(user_id);
CREATE INDEX idx_checkins_habit ON check_ins(habit_id);
CREATE INDEX idx_checkins_date ON check_ins(checkin_date DESC);
CREATE INDEX idx_checkins_user_date ON check_ins(user_id, checkin_date DESC);

-- Friendships
CREATE INDEX idx_friendships_requester ON friendships(requester_id);
CREATE INDEX idx_friendships_addressee ON friendships(addressee_id);
CREATE INDEX idx_friendships_status ON friendships(status);

-- Notifications
CREATE INDEX idx_notifications_user ON notifications(user_id);
CREATE INDEX idx_notifications_unread ON notifications(user_id, is_read) WHERE is_read = false;
CREATE INDEX idx_notifications_created ON notifications(created_at DESC);

-- Hitch Log
CREATE INDEX idx_hitch_log_target ON hitch_log(target_id, created_at DESC);
CREATE INDEX idx_hitch_log_sender ON hitch_log(sender_id);

-- Habits
CREATE INDEX idx_habits_system ON habits(is_system) WHERE is_system = true;
CREATE INDEX idx_habits_category ON habits(category) WHERE category IS NOT NULL;

-- Programs
CREATE INDEX idx_programs_org ON programs(organization_id);
CREATE INDEX idx_programs_creator ON programs(created_by);
```

### Step 5: Apply Migrations

```bash
# Via Supabase Dashboard:
# 1. Go to SQL Editor
# 2. Copy-paste each migration file
# 3. Execute in order (001, 002, 003, 004, 005)

# Or via Supabase CLI:
supabase db push
```

---

## 📦 Files to Create

```
darezone-backend/
├── migrations/
│   ├── 001_initial_schema.sql      # Tables, enums, constraints
│   ├── 002_rls_policies.sql        # RLS policies (separate story)
│   ├── 003_seed_habits.sql         # System habits seed data
│   ├── 004_indexes.sql             # Performance indexes
│   └── 005_triggers.sql            # Auto-update triggers
└── README.md                       # Migration instructions
```

---

## 🧪 Testing Checklist

### Manual Tests

```sql
-- Test 1: Create user profile
INSERT INTO user_profiles (id, email, display_name)
VALUES ('00000000-0000-0000-0000-000000000001', 'test@example.com', 'Test User');

-- Test 2: Create challenge
INSERT INTO challenges (name, start_date, end_date, created_by, invite_code)
VALUES ('Test Challenge', CURRENT_DATE, CURRENT_DATE + 30, '00000000-0000-0000-0000-000000000001', 'ABC123');

-- Test 3: Verify constraints
-- Should fail (end_date before start_date):
INSERT INTO challenges (name, start_date, end_date, created_by)
VALUES ('Bad Challenge', '2025-12-01', '2025-11-01', '00000000-0000-0000-0000-000000000001');

-- Test 4: Verify unique constraint
-- Should fail (duplicate check-in):
INSERT INTO check_ins (challenge_id, habit_id, user_id, checkin_date)
VALUES ('[challenge-id]', '[habit-id]', '[user-id]', CURRENT_DATE);
-- Run again → should fail

-- Test 5: Check system habits
SELECT COUNT(*) FROM habits WHERE is_system = true;
-- Should return 10
```

### Automated Tests (Phase 2)

```python
# tests/test_database.py
def test_user_profile_creation():
    # Test user creation with constraints
    pass

def test_challenge_constraints():
    # Test date validation, duration limits
    pass

def test_checkin_unique_constraint():
    # Test one check-in per day enforcement
    pass
```

---

## 📝 Notes

### Important Considerations

1. **Supabase Region**: Choose closest to users (Singapore for Vietnam)
2. **Password Security**: Use strong DB password, store in password manager
3. **Backup**: Enable automatic daily backups in Supabase
4. **Connection Pooling**: Supabase handles this automatically

### Common Issues

**Issue**: Foreign key errors
```sql
-- Solution: Create tables in correct order (parents before children)
-- Order: user → organizations → challenges → challenge_habits/members
```

**Issue**: RLS blocks everything
```sql
-- Solution: Use service_role key for admin operations
-- Or temporarily disable RLS for testing (NOT in production!)
```

### Reference Links

- [Supabase SQL Editor](https://app.supabase.com/project/_/sql)
- [PostgreSQL Constraints](https://www.postgresql.org/docs/current/ddl-constraints.html)
- [RLS Documentation](https://supabase.com/docs/guides/auth/row-level-security)

---

## ✅ Definition of Done

- [ ] All SQL scripts committed to `/migrations/`
- [ ] Migrations applied successfully on Supabase
- [ ] All tables visible in Table Editor
- [ ] Manual tests passed
- [ ] RLS enabled on all tables
- [ ] System habits seeded (10 habits)
- [ ] `.env.example` updated with Supabase credentials format
- [ ] README.md documents migration process
- [ ] Peer review completed
- [ ] No SQL errors in Supabase logs

---

**Next Story:** [Story 2: FastAPI Project Structure](./story-2-project-structure.md)
