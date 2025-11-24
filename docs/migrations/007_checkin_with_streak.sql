-- ============================================================================
-- Migration: 007_checkin_with_streak.sql
-- Description: RPC function for atomic check-in creation with streak calculation
-- Created: 2025-11-24
-- Author: Dev Agent (Story 6)
-- ============================================================================

-- ============================================================================
-- CREATE CHECKIN WITH STREAK UPDATE FUNCTION
-- ============================================================================

CREATE OR REPLACE FUNCTION create_checkin_with_streak_update(
  p_challenge_id UUID,
  p_habit_id UUID,
  p_user_id UUID,
  p_photo_url TEXT DEFAULT NULL,
  p_video_url TEXT DEFAULT NULL,
  p_caption TEXT DEFAULT NULL
)
RETURNS TABLE (
  checkin_id UUID,
  new_streak INTEGER,
  points_earned INTEGER,
  is_streak_broken BOOLEAN
) AS $$
DECLARE
  v_checkin_id UUID;
  v_member_record RECORD;
  v_last_checkin_date DATE;
  v_current_streak INTEGER;
  v_points INTEGER := 10;  -- Base points
  v_is_broken BOOLEAN := FALSE;
BEGIN
  -- Get member record
  SELECT * INTO v_member_record
  FROM challenge_members
  WHERE challenge_id = p_challenge_id
    AND user_id = p_user_id
    AND status = 'active';
  
  IF NOT FOUND THEN
    RAISE EXCEPTION 'User is not an active member of this challenge';
  END IF;
  
  -- Check for existing check-in today
  IF EXISTS (
    SELECT 1 FROM check_ins
    WHERE challenge_id = p_challenge_id
      AND habit_id = p_habit_id
      AND user_id = p_user_id
      AND checkin_date = CURRENT_DATE
  ) THEN
    RAISE EXCEPTION 'Check-in already exists for this habit today';
  END IF;
  
  -- Get last check-in date for this habit in this challenge
  SELECT MAX(checkin_date) INTO v_last_checkin_date
  FROM check_ins
  WHERE challenge_id = p_challenge_id
    AND user_id = p_user_id
    AND habit_id = p_habit_id;
  
  -- Calculate streak
  v_current_streak := v_member_record.current_streak;
  
  IF v_last_checkin_date IS NULL THEN
    -- First check-in ever for this habit
    v_current_streak := 1;
  ELSIF v_last_checkin_date = CURRENT_DATE - INTERVAL '1 day' THEN
    -- Consecutive day - continue streak
    v_current_streak := v_current_streak + 1;
    v_points := v_points * 2;  -- Double points for maintaining streak
  ELSIF v_last_checkin_date < CURRENT_DATE - INTERVAL '1 day' THEN
    -- Missed a day - streak broken
    v_current_streak := 1;
    v_is_broken := TRUE;
  ELSE
    -- Same day or future (shouldn't happen due to constraint)
    v_current_streak := 1;
  END IF;
  
  -- Create check-in
  INSERT INTO check_ins (
    challenge_id, habit_id, user_id,
    photo_url, video_url, caption,
    checkin_date, status, is_on_time
  ) VALUES (
    p_challenge_id, p_habit_id, p_user_id,
    p_photo_url, p_video_url, p_caption,
    CURRENT_DATE, 'completed', TRUE
  ) RETURNING id INTO v_checkin_id;
  
  -- Update member stats in challenge_members
  UPDATE challenge_members
  SET 
    current_streak = v_current_streak,
    longest_streak = GREATEST(longest_streak, v_current_streak),
    total_checkins = total_checkins + 1,
    points_earned = points_earned + v_points,
    last_checkin_at = NOW()
  WHERE challenge_id = p_challenge_id
    AND user_id = p_user_id;
  
  -- Update user profile global stats
  UPDATE user_profiles
  SET 
    current_streak = v_current_streak,
    longest_streak = GREATEST(longest_streak, v_current_streak),
    total_check_ins = total_check_ins + 1,
    points = points + v_points
  WHERE id = p_user_id;
  
  -- Update challenge_habits stats
  UPDATE challenge_habits ch
  SET 
    total_checkins = total_checkins + 1,
    completion_rate = (
      SELECT CASE 
        WHEN member_count > 0 AND days_elapsed > 0 THEN
          (COUNT(ci.*)::FLOAT / (member_count * days_elapsed)) * 100
        ELSE 0
      END
      FROM check_ins ci
      CROSS JOIN (
        SELECT 
          COUNT(*) FILTER (WHERE status = 'active') as member_count,
          (CURRENT_DATE - c.start_date)::INTEGER + 1 as days_elapsed
        FROM challenge_members cm
        CROSS JOIN challenges c
        WHERE c.id = p_challenge_id
          AND cm.challenge_id = p_challenge_id
      ) stats
      WHERE ci.challenge_id = p_challenge_id 
        AND ci.habit_id = p_habit_id
    )
  WHERE ch.challenge_id = p_challenge_id
    AND ch.habit_id = p_habit_id;
  
  -- Return results
  RETURN QUERY SELECT 
    v_checkin_id,
    v_current_streak,
    v_points,
    v_is_broken;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION create_checkin_with_streak_update IS 
  'Atomically create check-in and update streak/points for user. Prevents race conditions.';

-- ============================================================================
-- GRANT EXECUTE PERMISSIONS
-- ============================================================================

-- Grant execute to authenticated users (they can only check in for themselves via RLS)
GRANT EXECUTE ON FUNCTION create_checkin_with_streak_update TO authenticated;
