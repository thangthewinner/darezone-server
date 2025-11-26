-- =====================================================
-- Migration: 009 - Statistics & History Views (FIXED)
-- Story: Story 12 - History & Stats API
-- Purpose: Materialized views + Stats API with numeric casts
-- =====================================================


-- =====================================================
-- 1. Challenge Member Stats Materialized View
-- =====================================================

DROP MATERIALIZED VIEW IF EXISTS challenge_member_stats;

CREATE MATERIALIZED VIEW challenge_member_stats AS
SELECT 
  cm.challenge_id,
  cm.user_id,
  up.display_name,
  up.avatar_url,
  cm.current_streak,
  cm.longest_streak,
  cm.total_checkins,
  cm.points_earned,
  cm.status,
  cm.joined_at,
  
  -- Challenge info
  c.name AS challenge_name,
  c.start_date,
  c.end_date,
  c.duration_days,
  c.status AS challenge_status,
  
  -- Completion rate (cast to numeric for ROUND)
  ROUND(
    (
      CASE 
        WHEN (c.duration_days + 1) * habit_count.count > 0 
        THEN (cm.total_checkins::float / ((c.duration_days + 1) * habit_count.count)) * 100
        ELSE 0
      END
    )::numeric,
    2
  ) AS completion_rate,
  
  -- Total possible checkins
  (c.duration_days + 1) * habit_count.count AS total_possible_checkins,
  
  -- Rank by points
  RANK() OVER (
    PARTITION BY cm.challenge_id 
    ORDER BY cm.points_earned DESC, cm.current_streak DESC
  ) AS points_rank,
  
  -- Rank by completion
  RANK() OVER (
    PARTITION BY cm.challenge_id 
    ORDER BY (cm.total_checkins::float / NULLIF((c.duration_days + 1) * habit_count.count, 0)) DESC
  ) AS completion_rank
  
FROM challenge_members cm
JOIN challenges c ON c.id = cm.challenge_id
JOIN user_profiles up ON up.id = cm.user_id
CROSS JOIN LATERAL (
  SELECT COUNT(*) AS count
  FROM challenge_habits
  WHERE challenge_id = cm.challenge_id
) AS habit_count
WHERE cm.status IN ('active', 'left', 'kicked');


-- =====================================================
-- 1.1 Indexes for MV
-- =====================================================

CREATE UNIQUE INDEX IF NOT EXISTS idx_challenge_member_stats_pk 
  ON challenge_member_stats(challenge_id, user_id);

CREATE INDEX IF NOT EXISTS idx_challenge_member_stats_user 
  ON challenge_member_stats(user_id);

CREATE INDEX IF NOT EXISTS idx_challenge_member_stats_challenge 
  ON challenge_member_stats(challenge_id);

CREATE INDEX IF NOT EXISTS idx_challenge_member_stats_points_rank 
  ON challenge_member_stats(challenge_id, points_rank);


-- =====================================================
-- 2. Refresh Function
-- =====================================================

CREATE OR REPLACE FUNCTION refresh_challenge_stats()
RETURNS void AS $$
BEGIN
  REFRESH MATERIALIZED VIEW CONCURRENTLY challenge_member_stats;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION refresh_challenge_stats() IS 
  'Refresh challenge member statistics materialized view.';


-- =====================================================
-- 3. RPC Function: Get Challenge Stats
-- =====================================================

CREATE OR REPLACE FUNCTION get_challenge_stats(p_challenge_id UUID)
RETURNS JSON AS $$
DECLARE
  v_result JSON;
BEGIN
  SELECT json_build_object(
    'challenge_id', p_challenge_id,
    'total_members', COUNT(*),
    'active_members', COUNT(*) FILTER (WHERE status = 'active'),
    'avg_completion_rate', ROUND(AVG(completion_rate)::numeric, 2),
    'avg_points', ROUND(AVG(points_earned)::numeric, 2),
    'avg_streak', ROUND(AVG(current_streak)::numeric, 2),
    'total_checkins', SUM(total_checkins),
    'challenge_info', (
      SELECT json_build_object(
        'name', name,
        'start_date', start_date,
        'end_date', end_date,
        'duration_days', duration_days,
        'status', status
      )
      FROM challenges WHERE id = p_challenge_id
    ),
    'top_performers', (
      SELECT json_agg(
        json_build_object(
          'user_id', user_id,
          'display_name', display_name,
          'avatar_url', avatar_url,
          'points_earned', points_earned,
          'completion_rate', completion_rate,
          'rank', points_rank
        )
        ORDER BY points_rank
      )
      FROM challenge_member_stats
      WHERE challenge_id = p_challenge_id
        AND points_rank <= 10
    ),
    'habit_stats', (
      SELECT json_agg(
        json_build_object(
          'habit_id', ch.habit_id,
          'habit_name', h.name,
          'total_checkins', COUNT(ci.id),
          'completion_rate',
            ROUND(
              (
                COUNT(ci.id)::float
                / NULLIF(
                    (SELECT duration_days + 1 FROM challenges WHERE id = p_challenge_id)
                    * (SELECT COUNT(*) FROM challenge_members WHERE challenge_id = p_challenge_id AND status='active'),
                  0
                ) * 100
              )::numeric,
              2
            )
        )
      )
      FROM challenge_habits ch
      JOIN habits h ON h.id = ch.habit_id
      LEFT JOIN check_ins ci ON ci.challenge_id = p_challenge_id 
                              AND ci.habit_id = ch.habit_id
      WHERE ch.challenge_id = p_challenge_id
      GROUP BY ch.habit_id, h.name
    )
  ) INTO v_result
  FROM challenge_member_stats
  WHERE challenge_id = p_challenge_id;

  RETURN v_result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION get_challenge_stats(UUID) IS 
  'Get full challenge statistics including habits and performers.';


-- =====================================================
-- 4. RPC Function: Get User Dashboard
-- =====================================================

CREATE OR REPLACE FUNCTION get_user_dashboard(p_user_id UUID)
RETURNS JSON AS $$
DECLARE
  v_result JSON;
BEGIN
  SELECT json_build_object(
    'user_stats', (
      SELECT json_build_object(
        'current_streak', current_streak,
        'longest_streak', longest_streak,
        'total_check_ins', total_check_ins,
        'total_challenges_completed', total_challenges_completed,
        'points', points
      )
      FROM user_profiles WHERE id = p_user_id
    ),
    'active_challenges', (
      SELECT json_agg(
        json_build_object(
          'challenge_id', cms.challenge_id,
          'challenge_name', cms.challenge_name,
          'current_streak', cms.current_streak,
          'points_earned', cms.points_earned,
          'completion_rate', cms.completion_rate,
          'rank', cms.points_rank,
          'end_date', cms.end_date
        )
        ORDER BY cms.end_date DESC
      )
      FROM challenge_member_stats cms
      WHERE cms.user_id = p_user_id
        AND cms.status = 'active'
        AND cms.challenge_status = 'active'
    ),
    'recent_completions', (
      SELECT json_agg(
        json_build_object(
          'challenge_id', cms.challenge_id,
          'challenge_name', cms.challenge_name,
          'completion_rate', cms.completion_rate,
          'points_earned', cms.points_earned,
          'rank', cms.points_rank,
          'end_date', cms.end_date
        )
        ORDER BY cms.end_date DESC
      )
      FROM challenge_member_stats cms
      WHERE cms.user_id = p_user_id
        AND cms.status IN ('active', 'left')
        AND cms.challenge_status IN ('completed', 'failed')
      LIMIT 5
    ),
    'achievements', json_build_array()
  ) INTO v_result;

  RETURN v_result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION get_user_dashboard(UUID) IS 
  'Get user dashboard including stats, challenges, and recent completions.';


-- =====================================================
-- 5. Populate Initial Data
-- =====================================================

REFRESH MATERIALIZED VIEW challenge_member_stats;


-- =====================================================
-- 6. Verification Queries
-- =====================================================

SELECT matviewname FROM pg_matviews WHERE matviewname = 'challenge_member_stats';

SELECT proname FROM pg_proc 
WHERE proname IN ('refresh_challenge_stats', 'get_challenge_stats', 'get_user_dashboard')
ORDER BY proname;