-- ============================================================================
-- Migration: 003_seed_habits.sql
-- Description: Seed system habits for challenges
-- Created: 2025-11-23
-- Author: Dev Agent (Story 1)
-- ============================================================================

-- ============================================================================
-- SYSTEM HABITS SEED DATA
-- ============================================================================

INSERT INTO public.habits (id, name, icon, description, category, is_system) VALUES
(
  '00000000-0000-0000-0000-000000000001',
  'Morning Exercise',
  '🏃',
  'Start your day with 15-30 minutes of physical activity',
  'health',
  true
),
(
  '00000000-0000-0000-0000-000000000002',
  'Drink Water',
  '💧',
  'Drink at least 8 glasses (2 liters) of water daily',
  'health',
  true
),
(
  '00000000-0000-0000-0000-000000000003',
  'Read Books',
  '📚',
  'Read at least 20 pages of a book every day',
  'learning',
  true
),
(
  '00000000-0000-0000-0000-000000000004',
  'Meditation',
  '🧘',
  'Practice mindfulness or meditation for 10-15 minutes',
  'mental_health',
  true
),
(
  '00000000-0000-0000-0000-000000000005',
  'Healthy Eating',
  '🥗',
  'Eat at least one healthy meal with vegetables and fruits',
  'health',
  true
),
(
  '00000000-0000-0000-0000-000000000006',
  'Learn Something New',
  '🎓',
  'Spend 30 minutes learning a new skill or language',
  'learning',
  true
),
(
  '00000000-0000-0000-0000-000000000007',
  'Sleep Early',
  '😴',
  'Go to bed before 11 PM for better rest',
  'health',
  true
),
(
  '00000000-0000-0000-0000-000000000008',
  'Gratitude Journal',
  '📝',
  'Write down 3 things you are grateful for today',
  'mental_health',
  true
),
(
  '00000000-0000-0000-0000-000000000009',
  'No Social Media',
  '📱',
  'Avoid social media for at least 2 hours before bed',
  'productivity',
  true
),
(
  '00000000-0000-0000-0000-000000000010',
  'Connect with Loved Ones',
  '❤️',
  'Call or meet with family/friends for meaningful connection',
  'social',
  true
)
ON CONFLICT (id) DO NOTHING;

-- ============================================================================
-- VERIFICATION
-- ============================================================================

DO $$
DECLARE
  habit_count INTEGER;
BEGIN
  SELECT COUNT(*) INTO habit_count 
  FROM public.habits 
  WHERE is_system = true;
  
  RAISE NOTICE 'Seeded % system habits', habit_count;
  
  IF habit_count != 10 THEN
    RAISE EXCEPTION 'Expected 10 system habits, but found %', habit_count;
  END IF;
END $$;

-- ============================================================================
-- DISPLAY SEEDED HABITS
-- ============================================================================

SELECT 
  name,
  icon,
  category,
  description
FROM public.habits
WHERE is_system = true
ORDER BY name;
