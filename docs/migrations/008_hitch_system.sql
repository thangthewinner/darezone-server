-- =====================================================
-- Migration: 008 - Hitch Reminder System
-- Story: Story 11 - Hitch Reminder System
-- Purpose: RPC function for atomic hitch sending with rate limiting
-- =====================================================

-- =====================================================
-- 1. Send Hitch Reminder Function
-- =====================================================

CREATE OR REPLACE FUNCTION send_hitch_reminder(
  p_challenge_id UUID,
  p_habit_id UUID,
  p_sender_id UUID,
  p_target_ids UUID[]
)
RETURNS TABLE (
  hitches_sent INTEGER,
  remaining_hitches INTEGER
) AS $$
DECLARE
  v_sender_record RECORD;
  v_target_id UUID;
  v_hitches_sent INTEGER := 0;
  v_habit_name TEXT;
  v_challenge_name TEXT;
BEGIN
  -- =====================================================
  -- Validation: Sender membership and hitch count
  -- =====================================================
  
  SELECT 
    cm.hitch_count,
    cm.status,
    cm.user_id
  INTO v_sender_record
  FROM challenge_members cm
  WHERE cm.challenge_id = p_challenge_id
    AND cm.user_id = p_sender_id;
  
  -- Check if sender is a member
  IF NOT FOUND THEN
    RAISE EXCEPTION 'Sender is not a member of this challenge';
  END IF;
  
  -- Check if sender is active
  IF v_sender_record.status != 'active' THEN
    RAISE EXCEPTION 'Sender is not an active member';
  END IF;
  
  -- Check if sender has hitches remaining
  IF v_sender_record.hitch_count <= 0 THEN
    RAISE EXCEPTION 'No hitches remaining';
  END IF;
  
  -- =====================================================
  -- Get habit and challenge names for notification
  -- =====================================================
  
  SELECT name INTO v_habit_name
  FROM habits 
  WHERE id = p_habit_id;
  
  IF NOT FOUND THEN
    RAISE EXCEPTION 'Habit not found';
  END IF;
  
  SELECT name INTO v_challenge_name
  FROM challenges
  WHERE id = p_challenge_id;
  
  -- =====================================================
  -- Send hitch to each target
  -- =====================================================
  
  FOREACH v_target_id IN ARRAY p_target_ids
  LOOP
    -- Validate target is member of challenge
    IF NOT EXISTS (
      SELECT 1 
      FROM challenge_members
      WHERE challenge_id = p_challenge_id
        AND user_id = v_target_id
        AND status = 'active'
    ) THEN
      -- Skip invalid targets silently
      CONTINUE;
    END IF;
    
    -- Check if already sent hitch today (rate limiting)
    -- Uses unique constraint: one_hitch_per_habit_per_day
    IF NOT EXISTS (
      SELECT 1 
      FROM hitch_log
      WHERE habit_id = p_habit_id
        AND sender_id = p_sender_id
        AND target_id = v_target_id
        AND hitch_date = CURRENT_DATE
    ) THEN
      
      -- =====================================================
      -- Create hitch log entry
      -- =====================================================
      
      INSERT INTO hitch_log (
        challenge_id,
        habit_id,
        sender_id,
        target_id,
        hitch_date
      ) VALUES (
        p_challenge_id,
        p_habit_id,
        p_sender_id,
        v_target_id,
        CURRENT_DATE
      );
      
      -- =====================================================
      -- Send notification to target
      -- =====================================================
      
      INSERT INTO notifications (
        user_id,
        type,
        title,
        body,
        data,
        action_url,
        is_read
      ) VALUES (
        v_target_id,
        'hitch_reminder',
        'Reminder: Check-in needed! 🔔',
        format('Your friend reminded you to check in for "%s" in "%s"', 
          v_habit_name, 
          COALESCE(v_challenge_name, 'your challenge')
        ),
        jsonb_build_object(
          'challenge_id', p_challenge_id,
          'habit_id', p_habit_id,
          'sender_id', p_sender_id,
          'habit_name', v_habit_name
        ),
        format('/challenges/%s', p_challenge_id),
        false
      );
      
      -- Increment counter
      v_hitches_sent := v_hitches_sent + 1;
      
    END IF;
  END LOOP;
  
  -- =====================================================
  -- Decrement sender's hitch count (only if hitches sent)
  -- =====================================================
  
  IF v_hitches_sent > 0 THEN
    UPDATE challenge_members
    SET hitch_count = hitch_count - 1
    WHERE challenge_id = p_challenge_id
      AND user_id = p_sender_id;
  ELSE
    -- No hitches sent (all targets already received or invalid)
    RAISE EXCEPTION 'No valid targets or all targets already received hitch today';
  END IF;
  
  -- =====================================================
  -- Return results
  -- =====================================================
  
  RETURN QUERY SELECT 
    v_hitches_sent,
    v_sender_record.hitch_count - 1;  -- New remaining count
    
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =====================================================
-- 2. Comments
-- =====================================================

COMMENT ON FUNCTION send_hitch_reminder(UUID, UUID, UUID, UUID[]) IS
'Send hitch reminders to challenge members. Validates sender membership, decrements hitch_count, logs hitches, and sends notifications. Rate limit: 1 hitch per habit per target per day.';

-- =====================================================
-- 3. Verification Query
-- =====================================================

-- Test if function exists
SELECT 
  proname as function_name,
  pg_get_function_arguments(oid) as arguments,
  pg_get_function_result(oid) as returns
FROM pg_proc
WHERE proname = 'send_hitch_reminder';