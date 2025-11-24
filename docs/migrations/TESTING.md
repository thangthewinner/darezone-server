# Database Migration Testing Guide

Complete testing guide to verify database migrations work correctly.

## 🎯 Testing Objectives

1. ✅ All tables created successfully
2. ✅ Constraints and validations work
3. ✅ RLS policies protect data properly
4. ✅ Triggers auto-update fields
5. ✅ Indexes improve query performance
6. ✅ System habits seeded correctly

---

## 📋 Pre-Test Checklist

Before running tests, ensure:

- [ ] All 5 migrations applied successfully
- [ ] No SQL errors in Supabase logs
- [ ] Supabase project is active
- [ ] You have service_role key for testing

---

## 🧪 Test Suite

### Test 1: Table Creation Verification

**Purpose:** Verify all tables exist with correct columns

```sql
-- Check all tables exist
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_type = 'BASE TABLE'
ORDER BY table_name;
```

**Expected Result:**
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

**✅ Pass Criteria:** All 11 tables present

---

### Test 2: Enum Types Verification

**Purpose:** Verify custom enums created

```sql
SELECT typname 
FROM pg_type 
WHERE typnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
  AND typtype = 'e'
ORDER BY typname;
```

**Expected Result:** 10 enum types

**✅ Pass Criteria:** All enums present (challenge_status, challenge_type, etc.)

---

### Test 3: System Habits Seeded

**Purpose:** Verify 10 system habits inserted

```sql
-- Count system habits
SELECT COUNT(*) as total_system_habits 
FROM habits 
WHERE is_system = true;

-- View all system habits
SELECT name, icon, category, description 
FROM habits 
WHERE is_system = true 
ORDER BY name;
```

**Expected Result:** 10 system habits

**Habits:**
1. Connect with Loved Ones ❤️
2. Drink Water 💧
3. Gratitude Journal 📝
4. Healthy Eating 🥗
5. Learn Something New 🎓
6. Meditation 🧘
7. Morning Exercise 🏃
8. No Social Media 📱
9. Read Books 📚
10. Sleep Early 😴

**✅ Pass Criteria:** COUNT = 10, all habits have name, icon, category

---

### Test 4: User Profile Creation

**Purpose:** Test user profile CRUD with constraints

```sql
-- Create test user profile
INSERT INTO user_profiles (
  id, 
  email, 
  display_name, 
  account_type,
  current_streak,
  longest_streak
) VALUES (
  '11111111-1111-1111-1111-111111111111',
  'testuser@darezone.com',
  'Test User',
  'b2c',
  0,
  0
);

-- Verify
SELECT id, email, display_name, account_type, current_streak 
FROM user_profiles 
WHERE email = 'testuser@darezone.com';

-- Test constraint: negative streak should fail
INSERT INTO user_profiles (
  id, 
  email, 
  display_name,
  current_streak
) VALUES (
  '22222222-2222-2222-2222-222222222222',
  'invalid@darezone.com',
  'Invalid User',
  -5
);
-- Expected: ERROR constraint violation
```

**✅ Pass Criteria:**
- Valid insert succeeds
- Negative streak insert fails with constraint error

---

### Test 5: Challenge Creation with Auto-Generated Invite Code

**Purpose:** Test challenge creation and invite code trigger

```sql
-- Create group challenge (should auto-generate invite_code)
INSERT INTO challenges (
  name,
  description,
  type,
  start_date,
  end_date,
  created_by
) VALUES (
  '30-Day Fitness Challenge',
  'Get fit with friends',
  'group',
  CURRENT_DATE,
  CURRENT_DATE + 30,
  '11111111-1111-1111-1111-111111111111'
);

-- Verify invite code generated
SELECT 
  id, 
  name, 
  type,
  invite_code,
  duration_days,
  member_count
FROM challenges 
WHERE name = '30-Day Fitness Challenge';

-- Test date constraint: end_date before start_date should fail
INSERT INTO challenges (
  name,
  start_date,
  end_date,
  created_by
) VALUES (
  'Invalid Challenge',
  '2025-12-31',
  '2025-01-01',
  '11111111-1111-1111-1111-111111111111'
);
-- Expected: ERROR check constraint "valid_date_range"
```

**✅ Pass Criteria:**
- Valid challenge created
- invite_code is 6 characters (e.g., "ABC123")
- duration_days = 30
- Invalid date range rejected

---

### Test 6: Add Habits to Challenge

**Purpose:** Test challenge_habits junction table

```sql
-- Get challenge ID
SELECT id FROM challenges WHERE name = '30-Day Fitness Challenge';
-- Let's say it's: aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa

-- Get system habit ID
SELECT id FROM habits WHERE name = 'Morning Exercise';
-- Let's say it's: 00000000-0000-0000-0000-000000000001

-- Add habit to challenge
INSERT INTO challenge_habits (challenge_id, habit_id, display_order)
VALUES (
  'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
  '00000000-0000-0000-0000-000000000001',
  1
);

-- Verify
SELECT 
  ch.id,
  c.name as challenge_name,
  h.name as habit_name,
  ch.display_order,
  ch.total_checkins
FROM challenge_habits ch
JOIN challenges c ON ch.challenge_id = c.id
JOIN habits h ON ch.habit_id = h.id;

-- Test unique constraint: duplicate should fail
INSERT INTO challenge_habits (challenge_id, habit_id)
VALUES (
  'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
  '00000000-0000-0000-0000-000000000001'
);
-- Expected: ERROR unique violation
```

**✅ Pass Criteria:**
- Habit added to challenge
- Duplicate habit rejected

---

### Test 7: Challenge Member Join & Member Count Trigger

**Purpose:** Test member join and auto-increment member_count

```sql
-- Before: member_count should be 0
SELECT name, member_count FROM challenges 
WHERE name = '30-Day Fitness Challenge';

-- User joins challenge
INSERT INTO challenge_members (challenge_id, user_id, role, status)
VALUES (
  'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
  '11111111-1111-1111-1111-111111111111',
  'creator',
  'active'
);

-- After: member_count should be 1
SELECT name, member_count FROM challenges 
WHERE name = '30-Day Fitness Challenge';

-- Verify member details
SELECT 
  cm.id,
  up.display_name,
  cm.role,
  cm.status,
  cm.current_streak,
  cm.total_checkins,
  cm.hitch_count
FROM challenge_members cm
JOIN user_profiles up ON cm.user_id = up.id;
```

**✅ Pass Criteria:**
- member_count incremented from 0 to 1
- hitch_count defaults to 2

---

### Test 8: Check-in Creation & Counter Triggers

**Purpose:** Test check-in and auto-update counters

```sql
-- Before: check counters
SELECT 
  total_check_ins 
FROM user_profiles 
WHERE id = '11111111-1111-1111-1111-111111111111';

SELECT 
  total_checkins 
FROM challenge_members 
WHERE user_id = '11111111-1111-1111-1111-111111111111';

-- Create check-in
INSERT INTO check_ins (
  challenge_id,
  habit_id,
  user_id,
  checkin_date,
  caption
) VALUES (
  'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
  '00000000-0000-0000-0000-000000000001',
  '11111111-1111-1111-1111-111111111111',
  CURRENT_DATE,
  'First check-in! Feeling great!'
);

-- After: counters should increment
SELECT 
  total_check_ins 
FROM user_profiles 
WHERE id = '11111111-1111-1111-1111-111111111111';
-- Expected: 1

SELECT 
  total_checkins,
  last_checkin_at
FROM challenge_members 
WHERE user_id = '11111111-1111-1111-1111-111111111111';
-- Expected: total_checkins = 1, last_checkin_at = NOW()

SELECT 
  total_checkins 
FROM challenge_habits 
WHERE challenge_id = 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa';
-- Expected: 1

-- Test unique constraint: duplicate check-in same day should fail
INSERT INTO check_ins (
  challenge_id,
  habit_id,
  user_id,
  checkin_date
) VALUES (
  'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
  '00000000-0000-0000-0000-000000000001',
  '11111111-1111-1111-1111-111111111111',
  CURRENT_DATE
);
-- Expected: ERROR unique constraint "one_checkin_per_day"
```

**✅ Pass Criteria:**
- All 3 counters incremented (user, member, habit)
- last_checkin_at updated
- Duplicate check-in rejected

---

### Test 9: Friendship Request

**Purpose:** Test friendships table and constraints

```sql
-- Create second user
INSERT INTO user_profiles (id, email, display_name)
VALUES (
  '33333333-3333-3333-3333-333333333333',
  'friend@darezone.com',
  'Friend User'
);

-- Send friend request
INSERT INTO friendships (requester_id, addressee_id, status)
VALUES (
  '11111111-1111-1111-1111-111111111111',
  '33333333-3333-3333-3333-333333333333',
  'pending'
);

-- Verify
SELECT 
  f.id,
  u1.display_name as requester,
  u2.display_name as addressee,
  f.status,
  f.created_at
FROM friendships f
JOIN user_profiles u1 ON f.requester_id = u1.id
JOIN user_profiles u2 ON f.addressee_id = u2.id;

-- Test self-friend constraint: should fail
INSERT INTO friendships (requester_id, addressee_id)
VALUES (
  '11111111-1111-1111-1111-111111111111',
  '11111111-1111-1111-1111-111111111111'
);
-- Expected: ERROR check constraint violation
```

**✅ Pass Criteria:**
- Friend request created
- Self-friending rejected

---

### Test 10: Hitch Log (Reminder System)

**Purpose:** Test hitch logging and daily unique constraint

```sql
-- Send hitch reminder
INSERT INTO hitch_log (
  challenge_id,
  habit_id,
  sender_id,
  target_id
) VALUES (
  'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
  '00000000-0000-0000-0000-000000000001',
  '11111111-1111-1111-1111-111111111111',
  '33333333-3333-3333-3333-333333333333'
);

-- Verify
SELECT 
  hl.id,
  u1.display_name as sender,
  u2.display_name as target,
  h.name as habit,
  hl.created_at
FROM hitch_log hl
JOIN user_profiles u1 ON hl.sender_id = u1.id
JOIN user_profiles u2 ON hl.target_id = u2.id
JOIN habits h ON hl.habit_id = h.id;

-- Test: second hitch same day should fail
INSERT INTO hitch_log (
  challenge_id,
  habit_id,
  sender_id,
  target_id
) VALUES (
  'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
  '00000000-0000-0000-0000-000000000001',
  '11111111-1111-1111-1111-111111111111',
  '33333333-3333-3333-3333-333333333333'
);
-- Expected: ERROR unique constraint "one_hitch_per_habit_per_day"
```

**✅ Pass Criteria:**
- Hitch logged
- Duplicate hitch same day rejected

---

### Test 11: RLS Policy Verification

**Purpose:** Ensure RLS is enabled on all tables

```sql
-- Check RLS status
SELECT 
  tablename,
  rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public'
  AND tablename IN (
    'user_profiles',
    'challenges',
    'challenge_members',
    'check_ins',
    'friendships',
    'notifications',
    'habits',
    'hitch_log',
    'organizations',
    'programs',
    'challenge_habits'
  )
ORDER BY tablename;
```

**✅ Pass Criteria:** All tables have `rowsecurity = t` (true)

---

### Test 12: Index Performance Test

**Purpose:** Verify indexes exist for common queries

```sql
-- Check indexes created
SELECT 
  schemaname,
  tablename,
  indexname
FROM pg_indexes 
WHERE schemaname = 'public' 
  AND indexname LIKE 'idx_%'
ORDER BY tablename, indexname;
```

**✅ Pass Criteria:** 50+ custom indexes exist

---

### Test 13: Trigger Verification

**Purpose:** Verify all triggers attached

```sql
-- List all triggers
SELECT 
  trigger_name,
  event_object_table,
  action_statement
FROM information_schema.triggers 
WHERE trigger_schema = 'public'
ORDER BY event_object_table, trigger_name;
```

**Expected Triggers:**
- `trigger_set_challenge_invite_code` on challenges
- `trigger_update_*_updated_at` on multiple tables
- `trigger_update_challenge_member_count` on challenge_members
- `trigger_update_user_checkin_count` on check_ins
- `trigger_update_member_checkin_count` on check_ins
- `trigger_update_challenge_habit_stats` on check_ins

**✅ Pass Criteria:** All expected triggers present

---

## 🧹 Cleanup After Testing

```sql
-- Delete test data (in reverse dependency order)
DELETE FROM hitch_log WHERE sender_id IN ('11111111-1111-1111-1111-111111111111', '33333333-3333-3333-3333-333333333333');
DELETE FROM check_ins WHERE user_id = '11111111-1111-1111-1111-111111111111';
DELETE FROM friendships WHERE requester_id = '11111111-1111-1111-1111-111111111111' OR addressee_id = '33333333-3333-3333-3333-333333333333';
DELETE FROM challenge_members WHERE user_id IN ('11111111-1111-1111-1111-111111111111', '33333333-3333-3333-3333-333333333333');
DELETE FROM challenge_habits WHERE challenge_id IN (SELECT id FROM challenges WHERE created_by = '11111111-1111-1111-1111-111111111111');
DELETE FROM challenges WHERE created_by = '11111111-1111-1111-1111-111111111111';
DELETE FROM user_profiles WHERE id IN ('11111111-1111-1111-1111-111111111111', '33333333-3333-3333-3333-333333333333');

-- Verify cleanup
SELECT COUNT(*) FROM user_profiles WHERE email LIKE '%@darezone.com';
-- Expected: 0
```

---

## 📊 Final Checklist

After all tests pass:

- [ ] All 11 tables created
- [ ] 10 system habits seeded
- [ ] RLS enabled on all tables
- [ ] 50+ indexes created
- [ ] 10+ triggers working
- [ ] Constraints validated (dates, negatives, duplicates)
- [ ] Auto-counters incrementing
- [ ] Invite codes generating
- [ ] Test data cleaned up

---

## 🎉 Success Criteria

**All tests passed = Story 1 Complete!**

You can now proceed to **Story 2: FastAPI Project Structure**

---

**Testing Version:** 1.0  
**Last Updated:** 2025-11-23
