-- ============================================================================
-- Migration: 004_indexes.sql
-- Description: Performance indexes for common queries
-- Created: 2025-11-23
-- Author: Dev Agent (Story 1)
-- ============================================================================

-- ============================================================================
-- USER PROFILES INDEXES
-- ============================================================================

-- Organization lookup
CREATE INDEX idx_user_profiles_org 
  ON public.user_profiles(organization_id) 
  WHERE organization_id IS NOT NULL;

-- Account type filtering
CREATE INDEX idx_user_profiles_mode 
  ON public.user_profiles(account_type);

-- Email lookup (already unique, but explicit index for searches)
CREATE INDEX idx_user_profiles_email 
  ON public.user_profiles(email);

-- Last seen for online status
CREATE INDEX idx_user_profiles_last_seen 
  ON public.user_profiles(last_seen_at DESC);

-- ============================================================================
-- ORGANIZATIONS INDEXES
-- ============================================================================

-- Slug lookup for URL routing
CREATE INDEX idx_organizations_slug 
  ON public.organizations(slug);

-- Creator lookup
CREATE INDEX idx_organizations_created_by 
  ON public.organizations(created_by);

-- Plan filtering for analytics
CREATE INDEX idx_organizations_plan 
  ON public.organizations(plan);

-- ============================================================================
-- CHALLENGES INDEXES
-- ============================================================================

-- Creator lookup
CREATE INDEX idx_challenges_creator 
  ON public.challenges(created_by);

-- Organization challenges
CREATE INDEX idx_challenges_org 
  ON public.challenges(organization_id) 
  WHERE organization_id IS NOT NULL;

-- Status filtering (active challenges)
CREATE INDEX idx_challenges_status 
  ON public.challenges(status);

-- Invite code lookup (joining challenges)
CREATE INDEX idx_challenges_invite 
  ON public.challenges(invite_code) 
  WHERE invite_code IS NOT NULL;

-- Date range queries
CREATE INDEX idx_challenges_dates 
  ON public.challenges(start_date, end_date);

-- Public challenges discovery
CREATE INDEX idx_challenges_public 
  ON public.challenges(is_public) 
  WHERE is_public = true;

-- Program challenges
CREATE INDEX idx_challenges_program 
  ON public.challenges(program_id) 
  WHERE program_id IS NOT NULL;

-- ============================================================================
-- CHALLENGE HABITS INDEXES
-- ============================================================================

-- Challenge habits lookup
CREATE INDEX idx_challenge_habits_challenge 
  ON public.challenge_habits(challenge_id);

-- Habit usage lookup
CREATE INDEX idx_challenge_habits_habit 
  ON public.challenge_habits(habit_id);

-- Display order sorting
CREATE INDEX idx_challenge_habits_order 
  ON public.challenge_habits(challenge_id, display_order);

-- ============================================================================
-- CHALLENGE MEMBERS INDEXES
-- ============================================================================

-- Challenge members lookup
CREATE INDEX idx_challenge_members_challenge 
  ON public.challenge_members(challenge_id);

-- User's challenges lookup
CREATE INDEX idx_challenge_members_user 
  ON public.challenge_members(user_id);

-- Active members filtering
CREATE INDEX idx_challenge_members_status 
  ON public.challenge_members(status);

-- Composite for active members of a challenge
CREATE INDEX idx_challenge_members_active 
  ON public.challenge_members(challenge_id, status) 
  WHERE status = 'active';

-- Last check-in for reminders
CREATE INDEX idx_challenge_members_last_checkin 
  ON public.challenge_members(last_checkin_at DESC NULLS LAST);

-- ============================================================================
-- CHECK-INS INDEXES
-- ============================================================================

-- Challenge check-ins
CREATE INDEX idx_checkins_challenge 
  ON public.check_ins(challenge_id);

-- User check-ins
CREATE INDEX idx_checkins_user 
  ON public.check_ins(user_id);

-- Habit check-ins
CREATE INDEX idx_checkins_habit 
  ON public.check_ins(habit_id);

-- Date filtering (recent check-ins)
CREATE INDEX idx_checkins_date 
  ON public.check_ins(checkin_date DESC);

-- User's recent check-ins
CREATE INDEX idx_checkins_user_date 
  ON public.check_ins(user_id, checkin_date DESC);

-- Challenge habit check-ins (for streak calculation)
CREATE INDEX idx_checkins_challenge_habit_date 
  ON public.check_ins(challenge_id, habit_id, checkin_date DESC);

-- Status filtering
CREATE INDEX idx_checkins_status 
  ON public.check_ins(status);

-- On-time check-ins analytics
CREATE INDEX idx_checkins_on_time 
  ON public.check_ins(is_on_time) 
  WHERE is_on_time = true;

-- ============================================================================
-- FRIENDSHIPS INDEXES
-- ============================================================================

-- Requester lookup
CREATE INDEX idx_friendships_requester 
  ON public.friendships(requester_id);

-- Addressee lookup
CREATE INDEX idx_friendships_addressee 
  ON public.friendships(addressee_id);

-- Status filtering (accepted friendships)
CREATE INDEX idx_friendships_status 
  ON public.friendships(status);

-- Active friendships composite
CREATE INDEX idx_friendships_accepted 
  ON public.friendships(requester_id, addressee_id) 
  WHERE status = 'accepted';

-- ============================================================================
-- NOTIFICATIONS INDEXES
-- ============================================================================

-- User's notifications
CREATE INDEX idx_notifications_user 
  ON public.notifications(user_id);

-- Unread notifications
CREATE INDEX idx_notifications_unread 
  ON public.notifications(user_id, is_read) 
  WHERE is_read = false;

-- Recent notifications
CREATE INDEX idx_notifications_created 
  ON public.notifications(created_at DESC);

-- Type filtering
CREATE INDEX idx_notifications_type 
  ON public.notifications(type);

-- Expired notifications cleanup
CREATE INDEX idx_notifications_expired 
  ON public.notifications(expires_at) 
  WHERE expires_at IS NOT NULL;

-- ============================================================================
-- HITCH LOG INDEXES
-- ============================================================================

-- Target's received hitches
CREATE INDEX idx_hitch_log_target 
  ON public.hitch_log(target_id, created_at DESC);

-- Sender's sent hitches
CREATE INDEX idx_hitch_log_sender 
  ON public.hitch_log(sender_id);

-- Challenge hitches
CREATE INDEX idx_hitch_log_challenge 
  ON public.hitch_log(challenge_id);

-- Recent hitches (for rate limiting)
CREATE INDEX idx_hitch_log_recent 
  ON public.hitch_log(sender_id, created_at DESC);

-- ============================================================================
-- HABITS INDEXES
-- ============================================================================

-- System habits lookup
CREATE INDEX idx_habits_system 
  ON public.habits(is_system) 
  WHERE is_system = true;

-- Category filtering
CREATE INDEX idx_habits_category 
  ON public.habits(category) 
  WHERE category IS NOT NULL;

-- Creator lookup (custom habits)
CREATE INDEX idx_habits_creator 
  ON public.habits(created_by) 
  WHERE created_by IS NOT NULL;

-- ============================================================================
-- PROGRAMS INDEXES (B2B)
-- ============================================================================

-- Organization programs
CREATE INDEX idx_programs_org 
  ON public.programs(organization_id);

-- Creator lookup
CREATE INDEX idx_programs_creator 
  ON public.programs(created_by);

-- Date range
CREATE INDEX idx_programs_dates 
  ON public.programs(start_date, end_date) 
  WHERE start_date IS NOT NULL;

-- Period filtering
CREATE INDEX idx_programs_period 
  ON public.programs(period);

-- ============================================================================
-- VERIFICATION
-- ============================================================================

DO $$
DECLARE
  index_count INTEGER;
BEGIN
  SELECT COUNT(*) INTO index_count 
  FROM pg_indexes 
  WHERE schemaname = 'public'
    AND indexname LIKE 'idx_%';
  
  RAISE NOTICE 'Created % custom indexes', index_count;
END $$;

-- ============================================================================
-- INDEX USAGE NOTES
-- ============================================================================

COMMENT ON INDEX idx_user_profiles_org IS 'Fast lookup for organization members';
COMMENT ON INDEX idx_challenges_status IS 'Filter active/completed challenges efficiently';
COMMENT ON INDEX idx_checkins_user_date IS 'User check-in history queries';
COMMENT ON INDEX idx_friendships_accepted IS 'Quick friend list retrieval';
COMMENT ON INDEX idx_notifications_unread IS 'Show unread notifications badge';
