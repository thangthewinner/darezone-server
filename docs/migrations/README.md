# DareZone Database Migrations

Database schema migrations for DareZone backend using Supabase PostgreSQL.

## 📋 Migration Files

| File | Description | Dependencies |
|------|-------------|--------------|
| `001_initial_schema.sql` | Core tables, enums, constraints | None |
| `002_rls_policies.sql` | Row Level Security policies | 001 |
| `003_seed_habits.sql` | 10 system habits seed data | 001 |
| `004_indexes.sql` | Performance indexes | 001 |
| `005_triggers.sql` | Auto-update triggers | 001 |

## 🚀 How to Apply Migrations

### Method 1: Supabase Dashboard (Recommended for First Setup)

1. **Go to SQL Editor**
   ```
   https://app.supabase.com/project/YOUR_PROJECT_ID/sql/new
   ```

2. **Run migrations in order:**
   - Copy content of `001_initial_schema.sql`
   - Paste into SQL Editor
   - Click "Run"
   - Wait for success message
   - Repeat for 002, 003, 004, 005

3. **Verify**
   - Check "Table Editor" tab
   - Should see 11 tables created
   - Check "Database" → "Policies" → Should see RLS policies

### Method 2: Supabase CLI

```bash
# Install Supabase CLI (if not already)
npm install -g supabase

# Login
supabase login

# Link to your project
supabase link --project-ref YOUR_PROJECT_REF

# Apply all migrations
supabase db push

# Or apply specific migration
psql $DATABASE_URL < migrations/001_initial_schema.sql
```

### Method 3: Direct SQL Connection

```bash
# Get connection string from Supabase Dashboard
# Settings → Database → Connection string → URI

psql "postgresql://postgres:PASSWORD@db.PROJECT_REF.supabase.co:5432/postgres" \
  -f migrations/001_initial_schema.sql

# Repeat for each file in order
```

## ✅ Verification Checklist

After applying all migrations, verify:

### 1. Tables Created
```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_type = 'BASE TABLE'
ORDER BY table_name;
```

**Expected tables (11):**
- challenge_habits
- challenge_members
- challenges
- check_ins
- friendships
- habits
- hitch_log
- notifications
- organizations
- programs
- user_profiles

### 2. Enums Created
```sql
SELECT typname 
FROM pg_type 
WHERE typname IN (
  'challenge_status', 
  'challenge_type', 
  'checkin_type',
  'member_role',
  'member_status',
  'friendship_status',
  'notification_type',
  'checkin_status',
  'program_period',
  'program_difficulty'
);
```

### 3. RLS Enabled
```sql
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY tablename;
```

All tables should have `rowsecurity = true`

### 4. Policies Created
```sql
SELECT schemaname, tablename, policyname 
FROM pg_policies 
WHERE schemaname = 'public'
ORDER BY tablename, policyname;
```

Should see ~40+ policies

### 5. Indexes Created
```sql
SELECT indexname, tablename 
FROM pg_indexes 
WHERE schemaname = 'public' 
  AND indexname LIKE 'idx_%'
ORDER BY tablename, indexname;
```

Should see 50+ custom indexes

### 6. Triggers Created
```sql
SELECT trigger_name, event_object_table 
FROM information_schema.triggers 
WHERE trigger_schema = 'public'
ORDER BY event_object_table, trigger_name;
```

Should see triggers for updated_at, counts, etc.

### 7. System Habits Seeded
```sql
SELECT COUNT(*) FROM habits WHERE is_system = true;
-- Should return 10

SELECT name, icon, category 
FROM habits 
WHERE is_system = true 
ORDER BY name;
```

## 🧪 Manual Testing

### Test 1: Create User Profile
```sql
-- Insert test user (replace UUID with real auth.users id)
INSERT INTO user_profiles (id, email, display_name, account_type)
VALUES (
  '00000000-0000-0000-0000-000000000001',
  'test@darezone.com',
  'Test User',
  'b2c'
);

-- Verify
SELECT * FROM user_profiles WHERE email = 'test@darezone.com';
```

### Test 2: Create Challenge
```sql
INSERT INTO challenges (
  name, 
  description,
  type,
  start_date, 
  end_date, 
  created_by
) VALUES (
  'Morning Routine Challenge',
  'Wake up early and exercise',
  'group',
  CURRENT_DATE,
  CURRENT_DATE + INTERVAL '30 days',
  '00000000-0000-0000-0000-000000000001'
);

-- Verify invite_code was auto-generated
SELECT id, name, invite_code FROM challenges;
```

### Test 3: Add Habit to Challenge
```sql
-- Get challenge and habit IDs first
SELECT id, name FROM challenges LIMIT 1;
SELECT id, name FROM habits WHERE is_system = true LIMIT 1;

-- Add habit to challenge
INSERT INTO challenge_habits (challenge_id, habit_id)
VALUES (
  'CHALLENGE_ID_HERE',
  'HABIT_ID_HERE'
);
```

### Test 4: Join Challenge
```sql
INSERT INTO challenge_members (challenge_id, user_id, role)
VALUES (
  'CHALLENGE_ID_HERE',
  '00000000-0000-0000-0000-000000000001',
  'creator'
);

-- Verify member_count incremented
SELECT name, member_count FROM challenges;
```

### Test 5: Check-in
```sql
-- Get habit from challenge
SELECT ch.id, h.name 
FROM challenge_habits ch
JOIN habits h ON ch.habit_id = h.id
LIMIT 1;

INSERT INTO check_ins (
  challenge_id,
  habit_id,
  user_id,
  checkin_date,
  caption
) VALUES (
  'CHALLENGE_ID_HERE',
  'HABIT_ID_HERE',
  '00000000-0000-0000-0000-000000000001',
  CURRENT_DATE,
  'First check-in!'
);

-- Verify total_checkins incremented
SELECT total_checkins FROM user_profiles 
WHERE id = '00000000-0000-0000-0000-000000000001';
```

### Test 6: Constraint Validation
```sql
-- This should FAIL (duplicate check-in):
INSERT INTO check_ins (
  challenge_id,
  habit_id,
  user_id,
  checkin_date
) VALUES (
  'SAME_CHALLENGE_ID',
  'SAME_HABIT_ID',
  'SAME_USER_ID',
  CURRENT_DATE
);
-- Expected: ERROR: duplicate key value violates unique constraint

-- This should FAIL (end_date before start_date):
INSERT INTO challenges (
  name,
  start_date,
  end_date,
  created_by
) VALUES (
  'Bad Challenge',
  '2025-12-31',
  '2025-01-01',
  '00000000-0000-0000-0000-000000000001'
);
-- Expected: ERROR: new row violates check constraint "valid_date_range"
```

## 🔧 Troubleshooting

### Issue: "relation already exists"

**Cause:** Migration was already applied

**Solution:**
```sql
-- Drop and recreate (CAUTION: Deletes all data!)
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO public;

-- Then reapply migrations
```

### Issue: "permission denied for schema public"

**Cause:** Wrong database role

**Solution:** Use service_role key or database password, not anon key

### Issue: Foreign key constraint errors

**Cause:** Wrong migration order

**Solution:** Always apply in numerical order (001 → 002 → 003 → 004 → 005)

### Issue: RLS blocks all queries

**Cause:** Using anon key without proper RLS policies

**Solutions:**
1. Use service_role key for backend operations
2. Temporarily disable RLS for testing:
   ```sql
   ALTER TABLE table_name DISABLE ROW LEVEL SECURITY;
   ```
3. Check RLS policies are correctly applied

## 📝 Next Steps

After migrations are applied:

1. ✅ Verify all tables exist
2. ✅ Test RLS policies with different user contexts
3. ✅ Move to **Story 2**: FastAPI Project Structure
4. 🚀 Connect backend to database and test CRUD operations

## 🔗 References

- [Supabase SQL Editor](https://supabase.com/docs/guides/database/overview)
- [PostgreSQL Migrations](https://www.postgresql.org/docs/current/sql-commands.html)
- [Row Level Security](https://supabase.com/docs/guides/auth/row-level-security)
- [Supabase CLI](https://supabase.com/docs/guides/cli)

---

**Migration Version:** 1.0  
**Last Updated:** 2025-11-23  
**Story:** Phase 1 - Story 1
