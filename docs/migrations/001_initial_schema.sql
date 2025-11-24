-- ============================================================================
-- Migration: 001_initial_schema.sql
-- Description: Core database schema for DareZone
-- Created: 2025-11-23
-- Author: Dev Agent (Story 1)
-- ============================================================================

-- ============================================================================
-- ENUMS
-- ============================================================================

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

-- ============================================================================
-- ORGANIZATIONS TABLE (B2B)
-- ============================================================================

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

COMMENT ON TABLE public.organizations IS 'B2B organizations for team challenges and programs';
COMMENT ON COLUMN public.organizations.slug IS 'Unique URL-friendly identifier';
COMMENT ON COLUMN public.organizations.plan IS 'Subscription tier: starter, growth, enterprise';
COMMENT ON COLUMN public.organizations.feature_flags IS 'JSON object for feature toggles';

-- ============================================================================
-- USER PROFILES TABLE
-- ============================================================================

CREATE TABLE public.user_profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email TEXT NOT NULL UNIQUE,
  full_name TEXT,
  display_name TEXT,
  avatar_url TEXT,
  bio TEXT,
  account_type TEXT DEFAULT 'b2c' CHECK (account_type IN ('b2c', 'b2b')),
  forced_mode TEXT CHECK (forced_mode IN ('b2c', 'b2b')),
  organization_id UUID REFERENCES organizations(id) ON DELETE SET NULL,
  current_streak INTEGER DEFAULT 0 CHECK (current_streak >= 0),
  longest_streak INTEGER DEFAULT 0 CHECK (longest_streak >= 0),
  total_check_ins INTEGER DEFAULT 0 CHECK (total_check_ins >= 0),
  total_challenges_completed INTEGER DEFAULT 0 CHECK (total_challenges_completed >= 0),
  points INTEGER DEFAULT 0 CHECK (points >= 0),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  last_seen_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE public.user_profiles IS 'Extended user profile data beyond Supabase Auth';
COMMENT ON COLUMN public.user_profiles.account_type IS 'User mode: b2c (individual) or b2b (organization member)';
COMMENT ON COLUMN public.user_profiles.forced_mode IS 'Admin can force user into specific mode';
COMMENT ON COLUMN public.user_profiles.current_streak IS 'Current consecutive check-in days';
COMMENT ON COLUMN public.user_profiles.longest_streak IS 'Personal best streak record';

-- ============================================================================
-- HABITS TABLE
-- ============================================================================

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

COMMENT ON TABLE public.habits IS 'System and custom habits available for challenges';
COMMENT ON COLUMN public.habits.is_system IS 'System habits are pre-defined, custom habits are user-created';
COMMENT ON COLUMN public.habits.category IS 'Grouping: health, productivity, learning, social, etc.';

-- ============================================================================
-- PROGRAMS TABLE (B2B)
-- ============================================================================

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

COMMENT ON TABLE public.programs IS 'B2B structured programs with recurring challenges';
COMMENT ON COLUMN public.programs.period IS 'Challenge generation period: week, month, quarter';
COMMENT ON COLUMN public.programs.challenges_per_cycle IS 'How many challenges to auto-create per period';

-- ============================================================================
-- CHALLENGES TABLE
-- ============================================================================

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
  program_id UUID REFERENCES programs(id) ON DELETE SET NULL,
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

COMMENT ON TABLE public.challenges IS 'Individual or group challenges with habits to complete';
COMMENT ON COLUMN public.challenges.duration_days IS 'Auto-calculated from date range';
COMMENT ON COLUMN public.challenges.invite_code IS '6-char code for joining challenge';
COMMENT ON COLUMN public.challenges.member_count IS 'Cached count for performance';

-- ============================================================================
-- CHALLENGE HABITS TABLE
-- ============================================================================

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

COMMENT ON TABLE public.challenge_habits IS 'Junction table linking challenges to habits';
COMMENT ON COLUMN public.challenge_habits.custom_name IS 'Override habit name for this challenge';
COMMENT ON COLUMN public.challenge_habits.completion_rate IS 'Percentage of members who completed this habit';

-- ============================================================================
-- CHALLENGE MEMBERS TABLE
-- ============================================================================

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

COMMENT ON TABLE public.challenge_members IS 'Users participating in challenges with their stats';
COMMENT ON COLUMN public.challenge_members.hitch_count IS 'Remaining hitch reminders (resets daily)';
COMMENT ON COLUMN public.challenge_members.role IS 'creator: challenge owner, admin: co-admin, member: participant';

-- ============================================================================
-- CHECK-INS TABLE
-- ============================================================================

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

COMMENT ON TABLE public.check_ins IS 'Daily habit check-ins with evidence';
COMMENT ON COLUMN public.check_ins.is_on_time IS 'True if checked in on same day, false if backdated';
COMMENT ON CONSTRAINT one_checkin_per_day ON public.check_ins IS 'Enforce one check-in per habit per user per day';

-- ============================================================================
-- FRIENDSHIPS TABLE
-- ============================================================================

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

COMMENT ON TABLE public.friendships IS 'Friend connections between users';
COMMENT ON COLUMN public.friendships.requester_id IS 'User who sent friend request';
COMMENT ON COLUMN public.friendships.addressee_id IS 'User who received friend request';

-- ============================================================================
-- NOTIFICATIONS TABLE
-- ============================================================================

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

COMMENT ON TABLE public.notifications IS 'In-app and push notifications';
COMMENT ON COLUMN public.notifications.data IS 'JSON payload for app-specific data';
COMMENT ON COLUMN public.notifications.action_url IS 'Deep link URL when notification clicked';

-- ============================================================================
-- HITCH LOG TABLE
-- ============================================================================

CREATE TABLE public.hitch_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  challenge_id UUID NOT NULL REFERENCES challenges(id) ON DELETE CASCADE,
  habit_id UUID NOT NULL REFERENCES habits(id) ON DELETE CASCADE,
  sender_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  target_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  
  -- Ngày dùng để giới hạn 1 hitch / habit / target / ngày
  hitch_date DATE NOT NULL DEFAULT CURRENT_DATE,

  CONSTRAINT one_hitch_per_habit_per_day
    UNIQUE(habit_id, sender_id, target_id, hitch_date)
);

COMMENT ON TABLE public.hitch_log IS 'Hitch reminder history for accountability';
COMMENT ON CONSTRAINT one_hitch_per_habit_per_day ON public.hitch_log
  IS 'Prevent spam: one hitch per habit per target per day';


-- ============================================================================
-- ENABLE ROW LEVEL SECURITY (RLS)
-- ============================================================================

ALTER TABLE public.organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.habits ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.programs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.challenges ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.challenge_habits ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.challenge_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.check_ins ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.friendships ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.hitch_log ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

-- Verify table creation
DO $$
DECLARE
  table_count INTEGER;
BEGIN
  SELECT COUNT(*) INTO table_count 
  FROM information_schema.tables 
  WHERE table_schema = 'public' 
    AND table_type = 'BASE TABLE';
  
  RAISE NOTICE 'Created % tables in public schema', table_count;
END $$;
