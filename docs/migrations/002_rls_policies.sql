-- ============================================================================
-- Migration: 002_rls_policies.sql
-- Description: Row Level Security policies for data access control
-- Created: 2025-11-23
-- Author: Dev Agent (Story 1)
-- ============================================================================

-- ============================================================================
-- USER PROFILES POLICIES
-- ============================================================================

-- Users can view their own profile
CREATE POLICY "Users can view own profile"
  ON public.user_profiles
  FOR SELECT
  USING (auth.uid() = id);

-- Users can view profiles of their friends
CREATE POLICY "Users can view friends' profiles"
  ON public.user_profiles
  FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.friendships
      WHERE status = 'accepted'
        AND (
          (requester_id = auth.uid() AND addressee_id = user_profiles.id)
          OR (addressee_id = auth.uid() AND requester_id = user_profiles.id)
        )
    )
  );

-- Users can view profiles of challenge members in their challenges
CREATE POLICY "Users can view challenge members' profiles"
  ON public.user_profiles
  FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.challenge_members cm1
      JOIN public.challenge_members cm2 ON cm1.challenge_id = cm2.challenge_id
      WHERE cm1.user_id = auth.uid()
        AND cm2.user_id = user_profiles.id
        AND cm1.status = 'active'
        AND cm2.status = 'active'
    )
  );

-- Users can update their own profile
CREATE POLICY "Users can update own profile"
  ON public.user_profiles
  FOR UPDATE
  USING (auth.uid() = id)
  WITH CHECK (auth.uid() = id);

-- Users can insert their own profile (during signup)
CREATE POLICY "Users can insert own profile"
  ON public.user_profiles
  FOR INSERT
  WITH CHECK (auth.uid() = id);

-- ============================================================================
-- ORGANIZATIONS POLICIES
-- ============================================================================

-- Organization members can view their organization
CREATE POLICY "Members can view their organization"
  ON public.organizations
  FOR SELECT
  USING (
    id IN (
      SELECT organization_id FROM public.user_profiles
      WHERE id = auth.uid()
    )
  );

-- Organization creators can update their organization
CREATE POLICY "Creators can update organization"
  ON public.organizations
  FOR UPDATE
  USING (created_by = auth.uid())
  WITH CHECK (created_by = auth.uid());

-- Authenticated users can create organizations
CREATE POLICY "Authenticated users can create organizations"
  ON public.organizations
  FOR INSERT
  WITH CHECK (auth.uid() = created_by);

-- ============================================================================
-- CHALLENGES POLICIES
-- ============================================================================

-- Challenge members can view their challenges
CREATE POLICY "Members can view their challenges"
  ON public.challenges
  FOR SELECT
  USING (
    id IN (
      SELECT challenge_id FROM public.challenge_members
      WHERE user_id = auth.uid()
        AND status IN ('pending', 'active')
    )
  );

-- Users can view public challenges
CREATE POLICY "Anyone can view public challenges"
  ON public.challenges
  FOR SELECT
  USING (is_public = true);

-- Challenge creators can update their challenges
CREATE POLICY "Creators can update their challenges"
  ON public.challenges
  FOR UPDATE
  USING (created_by = auth.uid())
  WITH CHECK (created_by = auth.uid());

-- Authenticated users can create challenges
CREATE POLICY "Authenticated users can create challenges"
  ON public.challenges
  FOR INSERT
  WITH CHECK (auth.uid() = created_by);

-- ============================================================================
-- CHALLENGE MEMBERS POLICIES
-- ============================================================================

-- Users can view members of challenges they're in
CREATE POLICY "Members can view challenge members"
  ON public.challenge_members
  FOR SELECT
  USING (
    challenge_id IN (
      SELECT challenge_id FROM public.challenge_members
      WHERE user_id = auth.uid()
        AND status IN ('pending', 'active')
    )
  );

-- Challenge creators can insert members
CREATE POLICY "Creators can add members"
  ON public.challenge_members
  FOR INSERT
  WITH CHECK (
    challenge_id IN (
      SELECT id FROM public.challenges
      WHERE created_by = auth.uid()
    )
  );

-- Users can join challenges (self-insert)
CREATE POLICY "Users can join challenges"
  ON public.challenge_members
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- Users can update their own membership
CREATE POLICY "Users can update own membership"
  ON public.challenge_members
  FOR UPDATE
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- Challenge creators can update members
CREATE POLICY "Creators can update members"
  ON public.challenge_members
  FOR UPDATE
  USING (
    challenge_id IN (
      SELECT id FROM public.challenges
      WHERE created_by = auth.uid()
    )
  );

-- ============================================================================
-- CHALLENGE HABITS POLICIES
-- ============================================================================

-- Members can view habits of challenges they're in
CREATE POLICY "Members can view challenge habits"
  ON public.challenge_habits
  FOR SELECT
  USING (
    challenge_id IN (
      SELECT challenge_id FROM public.challenge_members
      WHERE user_id = auth.uid()
        AND status IN ('pending', 'active')
    )
  );

-- Challenge creators can manage habits
CREATE POLICY "Creators can manage challenge habits"
  ON public.challenge_habits
  FOR ALL
  USING (
    challenge_id IN (
      SELECT id FROM public.challenges
      WHERE created_by = auth.uid()
    )
  );

-- ============================================================================
-- HABITS POLICIES
-- ============================================================================

-- Everyone can view system habits
CREATE POLICY "Anyone can view system habits"
  ON public.habits
  FOR SELECT
  USING (is_system = true);

-- Users can view their own custom habits
CREATE POLICY "Users can view own custom habits"
  ON public.habits
  FOR SELECT
  USING (created_by = auth.uid() AND is_system = false);

-- Users can create custom habits
CREATE POLICY "Users can create custom habits"
  ON public.habits
  FOR INSERT
  WITH CHECK (
    auth.uid() = created_by 
    AND is_system = false
  );

-- ============================================================================
-- CHECK-INS POLICIES
-- ============================================================================

-- Users can view check-ins of challenges they're in
CREATE POLICY "Members can view challenge check-ins"
  ON public.check_ins
  FOR SELECT
  USING (
    challenge_id IN (
      SELECT challenge_id FROM public.challenge_members
      WHERE user_id = auth.uid()
        AND status = 'active'
    )
  );

-- Users can create their own check-ins
CREATE POLICY "Users can create own check-ins"
  ON public.check_ins
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- Users can update their own check-ins (within same day)
CREATE POLICY "Users can update own check-ins"
  ON public.check_ins
  FOR UPDATE
  USING (
    auth.uid() = user_id 
    AND checkin_date = CURRENT_DATE
  )
  WITH CHECK (
    auth.uid() = user_id
  );

-- ============================================================================
-- FRIENDSHIPS POLICIES
-- ============================================================================

-- Users can view friendships where they're involved
CREATE POLICY "Users can view own friendships"
  ON public.friendships
  FOR SELECT
  USING (
    auth.uid() = requester_id 
    OR auth.uid() = addressee_id
  );

-- Users can create friend requests
CREATE POLICY "Users can send friend requests"
  ON public.friendships
  FOR INSERT
  WITH CHECK (auth.uid() = requester_id);

-- Users can update friendships where they're addressee (accept/reject)
CREATE POLICY "Users can respond to friend requests"
  ON public.friendships
  FOR UPDATE
  USING (auth.uid() = addressee_id)
  WITH CHECK (auth.uid() = addressee_id);

-- Users can delete their friendships
CREATE POLICY "Users can delete own friendships"
  ON public.friendships
  FOR DELETE
  USING (
    auth.uid() = requester_id 
    OR auth.uid() = addressee_id
  );

-- ============================================================================
-- NOTIFICATIONS POLICIES
-- ============================================================================

-- Users can view their own notifications
CREATE POLICY "Users can view own notifications"
  ON public.notifications
  FOR SELECT
  USING (auth.uid() = user_id);

-- Users can update their own notifications (mark as read)
CREATE POLICY "Users can update own notifications"
  ON public.notifications
  FOR UPDATE
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- System can create notifications (via service_role)
-- No INSERT policy - only backend with service_role can insert

-- ============================================================================
-- HITCH LOG POLICIES
-- ============================================================================

-- Users can view hitches they sent or received
CREATE POLICY "Users can view their hitches"
  ON public.hitch_log
  FOR SELECT
  USING (
    auth.uid() = sender_id 
    OR auth.uid() = target_id
  );

-- Users can create hitches (send reminders)
CREATE POLICY "Users can send hitches"
  ON public.hitch_log
  FOR INSERT
  WITH CHECK (auth.uid() = sender_id);

-- ============================================================================
-- PROGRAMS POLICIES (B2B)
-- ============================================================================

-- Organization members can view their programs
CREATE POLICY "Members can view organization programs"
  ON public.programs
  FOR SELECT
  USING (
    organization_id IN (
      SELECT organization_id FROM public.user_profiles
      WHERE id = auth.uid()
    )
  );

-- Organization admins can manage programs
CREATE POLICY "Admins can manage programs"
  ON public.programs
  FOR ALL
  USING (
    organization_id IN (
      SELECT id FROM public.organizations
      WHERE created_by = auth.uid()
    )
  );

-- ============================================================================
-- SERVICE ROLE BYPASS
-- ============================================================================

-- Service role can bypass RLS for all tables (for backend operations)
-- This is automatic in Supabase when using service_role key

-- ============================================================================
-- VERIFICATION
-- ============================================================================

DO $$
DECLARE
  policy_count INTEGER;
BEGIN
  SELECT COUNT(*) INTO policy_count 
  FROM pg_policies 
  WHERE schemaname = 'public';
  
  RAISE NOTICE 'Created % RLS policies', policy_count;
END $$;
