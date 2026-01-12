-- Create user profiles for test users
INSERT INTO user_profiles (id, email, display_name, full_name, account_type, created_at)
VALUES (
    '8ef3a396-d9fe-4f80-a8d3-437e75dd3248',
    'test1@example.com',
    'Test User 1',
    'Test User One',
    'b2c',
    NOW()
) ON CONFLICT (id) DO UPDATE SET
    email = EXCLUDED.email,
    display_name = EXCLUDED.display_name;

INSERT INTO user_profiles (id, email, display_name, full_name, account_type, created_at)
VALUES (
    '627f319d-ee76-4acb-8f80-be1df138130a',
    'test2@example.com',
    'Test User 2',
    'Test User Two',
    'b2c',
    NOW()
) ON CONFLICT (id) DO UPDATE SET
    email = EXCLUDED.email,
    display_name = EXCLUDED.display_name;

SELECT id, email, display_name FROM user_profiles 
WHERE email IN ('test1@example.com', 'test2@example.com');
