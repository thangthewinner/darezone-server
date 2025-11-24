-- ============================================================================
-- Migration: 005_triggers.sql
-- Description: Database triggers for automatic updates and validations
-- Created: 2025-11-23
-- Author: Dev Agent (Story 1)
-- ============================================================================

-- ============================================================================
-- HELPER FUNCTION: Update updated_at timestamp
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION update_updated_at_column() IS 'Auto-update updated_at timestamp on row modification';

-- ============================================================================
-- HELPER FUNCTION: Generate invite code
-- ============================================================================

CREATE OR REPLACE FUNCTION generate_invite_code()
RETURNS TEXT AS $$
DECLARE
  chars TEXT := 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
  code TEXT := '';
  i INTEGER;
BEGIN
  FOR i IN 1..6 LOOP
    code := code || substr(chars, floor(random() * length(chars) + 1)::int, 1);
  END LOOP;
  RETURN code;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION generate_invite_code() IS 'Generate 6-character alphanumeric invite code (excludes confusing chars)';

-- ============================================================================
-- TRIGGER: Auto-generate invite code for challenges
-- ============================================================================

CREATE OR REPLACE FUNCTION set_challenge_invite_code()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.invite_code IS NULL AND NEW.type IN ('group', 'program') THEN
    LOOP
      NEW.invite_code := generate_invite_code();
      EXIT WHEN NOT EXISTS (
        SELECT 1 FROM public.challenges 
        WHERE invite_code = NEW.invite_code
      );
    END LOOP;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_set_challenge_invite_code
  BEFORE INSERT ON public.challenges
  FOR EACH ROW
  EXECUTE FUNCTION set_challenge_invite_code();

COMMENT ON TRIGGER trigger_set_challenge_invite_code ON public.challenges 
  IS 'Auto-generate unique invite code for group/program challenges';

-- ============================================================================
-- TRIGGER: Update challenge.member_count
-- ============================================================================

CREATE OR REPLACE FUNCTION update_challenge_member_count()
RETURNS TRIGGER AS $$
BEGIN
  IF TG_OP = 'INSERT' THEN
    UPDATE public.challenges 
    SET member_count = member_count + 1
    WHERE id = NEW.challenge_id;

  ELSIF TG_OP = 'DELETE' THEN
    UPDATE public.challenges 
    SET member_count = member_count - 1
    WHERE id = OLD.challenge_id;

  END IF;

  RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_challenge_member_count
  AFTER INSERT OR DELETE ON public.challenge_members
  FOR EACH ROW
  EXECUTE FUNCTION update_challenge_member_count();

COMMENT ON TRIGGER trigger_update_challenge_member_count ON public.challenge_members 
  IS 'Keep challenge.member_count in sync on join/leave';

-- ============================================================================
-- TRIGGER: Update program participant_count
-- ============================================================================

CREATE OR REPLACE FUNCTION update_program_participant_count()
RETURNS TRIGGER AS $$
DECLARE
  v_program_id UUID;
BEGIN
  -- Lấy program_id từ challenges
  SELECT program_id 
  INTO v_program_id
  FROM public.challenges
  WHERE id = COALESCE(NEW.challenge_id, OLD.challenge_id);

  IF v_program_id IS NULL THEN
    RETURN COALESCE(NEW, OLD);
  END IF;

  -- Chỉ quan tâm nếu INSERT hoặc status thay đổi
  IF TG_OP = 'INSERT' THEN
    IF NEW.status = 'active' THEN
      UPDATE public.programs 
      SET participant_count = (
        SELECT COUNT(DISTINCT cm.user_id)
        FROM public.challenge_members cm
        JOIN public.challenges c ON c.id = cm.challenge_id
        WHERE c.program_id = v_program_id
          AND cm.status = 'active'
      )
      WHERE id = v_program_id;
    END IF;

  ELSIF TG_OP = 'UPDATE' THEN
    IF OLD.status IS DISTINCT FROM NEW.status THEN
      UPDATE public.programs 
      SET participant_count = (
        SELECT COUNT(DISTINCT cm.user_id)
        FROM public.challenge_members cm
        JOIN public.challenges c ON c.id = cm.challenge_id
        WHERE c.program_id = v_program_id
          AND cm.status = 'active'
      )
      WHERE id = v_program_id;
    END IF;

  END IF;

  RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_program_participant_count
  AFTER INSERT OR UPDATE ON public.challenge_members
  FOR EACH ROW
  EXECUTE FUNCTION update_program_participant_count();

COMMENT ON TRIGGER trigger_update_program_participant_count ON public.challenge_members 
  IS 'Recalculate program participant_count when members join/leave or status changes';

-- ============================================================================
-- TRIGGER: Update user total_check_ins
-- ============================================================================

CREATE OR REPLACE FUNCTION update_user_checkin_count()
RETURNS TRIGGER AS $$
BEGIN
  IF TG_OP = 'INSERT' THEN
    UPDATE public.user_profiles
    SET total_check_ins = total_check_ins + 1
    WHERE id = NEW.user_id;

  ELSIF TG_OP = 'DELETE' THEN
    UPDATE public.user_profiles
    SET total_check_ins = total_check_ins - 1
    WHERE id = OLD.user_id;

  END IF;

  RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_user_checkin_count
  AFTER INSERT OR DELETE ON public.check_ins
  FOR EACH ROW
  EXECUTE FUNCTION update_user_checkin_count();

COMMENT ON TRIGGER trigger_update_user_checkin_count ON public.check_ins 
  IS 'Increment user total_check_ins on check-in';

-- ============================================================================
-- TRIGGER: Update challenge_members.total_checkins
-- ============================================================================

CREATE OR REPLACE FUNCTION update_member_checkin_count()
RETURNS TRIGGER AS $$
BEGIN
  IF TG_OP = 'INSERT' THEN
    UPDATE public.challenge_members 
    SET 
      total_checkins = total_checkins + 1,
      last_checkin_at = NOW()
    WHERE challenge_id = NEW.challenge_id
      AND user_id = NEW.user_id;

  ELSIF TG_OP = 'DELETE' THEN
    UPDATE public.challenge_members 
    SET total_checkins = total_checkins - 1
    WHERE challenge_id = OLD.challenge_id
      AND user_id = OLD.user_id;

  END IF;

  RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_member_checkin_count
  AFTER INSERT OR DELETE ON public.check_ins
  FOR EACH ROW
  EXECUTE FUNCTION update_member_checkin_count();

COMMENT ON TRIGGER trigger_update_member_checkin_count ON public.check_ins 
  IS 'Update per-member check-in statistics';

-- ============================================================================
-- TRIGGER: Update challenge_habits.total_checkins
-- ============================================================================

CREATE OR REPLACE FUNCTION update_challenge_habit_stats()
RETURNS TRIGGER AS $$
BEGIN
  IF TG_OP = 'INSERT' THEN
    UPDATE public.challenge_habits
    SET total_checkins = total_checkins + 1
    WHERE challenge_id = NEW.challenge_id
      AND habit_id = NEW.habit_id;

  ELSIF TG_OP = 'DELETE' THEN
    UPDATE public.challenge_habits
    SET total_checkins = total_checkins - 1
    WHERE challenge_id = OLD.challenge_id
      AND habit_id = OLD.habit_id;

  END IF;

  RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_challenge_habit_stats
  AFTER INSERT OR DELETE ON public.check_ins
  FOR EACH ROW
  EXECUTE FUNCTION update_challenge_habit_stats();

COMMENT ON TRIGGER trigger_update_challenge_habit_stats ON public.check_ins 
  IS 'Update per-habit stats inside challenge';

-- ============================================================================
-- ATTACH updated_at TRIGGERS TO TABLES
-- ============================================================================

CREATE TRIGGER trigger_update_user_profiles_updated_at
  BEFORE UPDATE ON public.user_profiles
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_update_organizations_updated_at
  BEFORE UPDATE ON public.organizations
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_update_challenges_updated_at
  BEFORE UPDATE ON public.challenges
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_update_programs_updated_at
  BEFORE UPDATE ON public.programs
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_update_check_ins_updated_at
  BEFORE UPDATE ON public.check_ins
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_update_friendships_updated_at
  BEFORE UPDATE ON public.friendships
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- VERIFICATION
-- ============================================================================

DO $$
DECLARE
  trigger_count INTEGER;
  function_count INTEGER;
BEGIN
  SELECT COUNT(*) 
  INTO trigger_count
  FROM pg_trigger 
  WHERE tgname LIKE 'trigger_%';

  SELECT COUNT(*) 
  INTO function_count
  FROM pg_proc p
  JOIN pg_namespace n ON p.pronamespace = n.oid
  WHERE n.nspname = 'public'
    AND p.proname IN (
      'update_updated_at_column',
      'generate_invite_code',
      'set_challenge_invite_code',
      'update_challenge_member_count',
      'update_program_participant_count',
      'update_user_checkin_count',
      'update_member_checkin_count',
      'update_challenge_habit_stats'
    );

  RAISE NOTICE 'Created % triggers and % helper functions', trigger_count, function_count;
END $$;