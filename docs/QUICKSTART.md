# 🚀 Quick Start Guide - Story 1: Database Setup

Get your database up and running in **10 minutes**.

---

## ✅ What You'll Achieve

By the end of this guide:
- ✅ Database schema deployed on Supabase
- ✅ 11 tables created with constraints
- ✅ 40+ RLS policies protecting data
- ✅ 50+ performance indexes
- ✅ 10 system habits seeded
- ✅ Ready for Story 2 (FastAPI)

---

## 📋 Prerequisites

- ✅ Supabase project created
- ✅ `.env` file with Supabase credentials
- ✅ 10 minutes of your time

**Check:** Open `.env` - should have:
```env
SUPABASE_URL=https://fvadyrhrqrqzxgyztyss.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_ROLE_KEY=eyJ...
```

---

## 🎯 Step-by-Step (3 Steps)

### Step 1: Open Supabase SQL Editor (1 min)

1. Go to https://app.supabase.com
2. Select your project (should see `fvadyrhrqrqzxgyztyss`)
3. Click **SQL Editor** in left sidebar
4. Click **New query** button

---

### Step 2: Apply Migrations (5 min)

**Run these 5 SQL files in ORDER:**

#### 2.1. Initial Schema (Tables & Enums)

```bash
# Open in your code editor:
darezone-server/migrations/001_initial_schema.sql
```

- Copy entire file content
- Paste into Supabase SQL Editor
- Click **Run** (bottom right)
- Wait for "Success. No rows returned" ✅

#### 2.2. RLS Policies (Security)

```bash
# Open:
darezone-server/migrations/002_rls_policies.sql
```

- Copy → Paste → Run
- Wait for success ✅

#### 2.3. Seed Habits

```bash
# Open:
darezone-server/migrations/003_seed_habits.sql
```

- Copy → Paste → Run
- Should see 10 habits displayed ✅

#### 2.4. Performance Indexes

```bash
# Open:
darezone-server/migrations/004_indexes.sql
```

- Copy → Paste → Run
- Wait for success ✅

#### 2.5. Triggers & Automation

```bash
# Open:
darezone-server/migrations/005_triggers.sql
```

- Copy → Paste → Run
- Wait for success ✅

---

### Step 3: Verify Setup (4 min)

#### 3.1. Check Tables Created

In Supabase SQL Editor, run:

```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_type = 'BASE TABLE'
ORDER BY table_name;
```

**Expected:** 11 tables
```
challenge_habits
challenge_members
challenges
check_ins
friendships
habits
hitch_log
notifications
organizations
programs
user_profiles
```

✅ **Pass:** All 11 present

---

#### 3.2. Check System Habits

```sql
SELECT name, icon, category 
FROM habits 
WHERE is_system = true 
ORDER BY name;
```

**Expected:** 10 habits

```
Connect with Loved Ones | ❤️  | social
Drink Water             | 💧  | health
Gratitude Journal       | 📝  | mental_health
Healthy Eating          | 🥗  | health
Learn Something New     | 🎓  | learning
Meditation              | 🧘  | mental_health
Morning Exercise        | 🏃  | health
No Social Media         | 📱  | productivity
Read Books              | 📚  | learning
Sleep Early             | 😴  | health
```

✅ **Pass:** COUNT = 10

---

#### 3.3. Quick Functional Test

```sql
-- Create test user
INSERT INTO user_profiles (
  id, 
  email, 
  display_name
) VALUES (
  '11111111-1111-1111-1111-111111111111',
  'test@quickstart.com',
  'Quick Test'
);

-- Create test challenge (invite_code should auto-generate!)
INSERT INTO challenges (
  name,
  type,
  start_date,
  end_date,
  created_by
) VALUES (
  'Test Challenge',
  'group',
  CURRENT_DATE,
  CURRENT_DATE + 30,
  '11111111-1111-1111-1111-111111111111'
);

-- Check invite code was generated
SELECT name, invite_code, duration_days 
FROM challenges;
```

**Expected:**
- `invite_code` = 6-char code (e.g., "K3M9Q2")
- `duration_days` = 30

✅ **Pass:** Invite code auto-generated

---

#### 3.4. Cleanup Test Data

```sql
DELETE FROM challenges WHERE name = 'Test Challenge';
DELETE FROM user_profiles WHERE email = 'test@quickstart.com';
```

---

## 🎉 Success Checklist

- [x] 5 migrations applied without errors
- [x] 11 tables visible in Table Editor
- [x] 10 system habits seeded
- [x] Invite code auto-generation working
- [x] Test data created and cleaned up

**✅ YOU'RE DONE!** Database is ready.

---

## 🚀 What's Next?

**Story 2: FastAPI Project Structure**

You'll create:
- FastAPI app structure
- Health check endpoint
- Supabase client connection
- Basic CRUD operations

**Time estimate:** 2 days

See [stories/phase-1/story-2-project-structure.md](./stories/phase-1/story-2-project-structure.md)

---

## 🆘 Troubleshooting

### Error: "relation already exists"

**Cause:** Migration was already applied

**Solution:** Skip that migration, continue to next one

---

### Error: "permission denied"

**Cause:** Wrong credentials in SQL Editor

**Solution:** 
1. Make sure you're logged into correct Supabase project
2. Try refreshing browser
3. Check project is not paused

---

### Error: "syntax error"

**Cause:** Incomplete copy-paste

**Solution:** 
1. Open migration file again
2. Select All (Ctrl+A / Cmd+A)
3. Copy
4. Paste into **fresh** SQL Editor tab
5. Run

---

### Tables not showing in Table Editor

**Solution:**
1. Click **Database** → **Tables** in left sidebar
2. Refresh browser
3. Should see all 11 tables

---

### Need help?

See detailed guides:
- [migrations/README.md](./migrations/README.md) - Full migration guide
- [migrations/TESTING.md](./migrations/TESTING.md) - Comprehensive tests

---

## 📸 Visual Verification

After completing, your Supabase project should look like:

**Table Editor:**
```
📁 public
  📄 challenge_habits
  📄 challenge_members
  📄 challenges
  📄 check_ins
  📄 friendships
  📄 habits (10 rows)
  📄 hitch_log
  📄 notifications
  📄 organizations
  📄 programs
  📄 user_profiles
```

**Database → Policies:**
```
🔒 40+ policies visible
✅ All tables have RLS enabled
```

---

**Time Spent:** ~10 minutes  
**Story Status:** ✅ COMPLETED  
**Next Story:** Story 2 - FastAPI Project Structure

Happy coding! 🚀
