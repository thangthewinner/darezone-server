# Scripts Directory

Helper scripts for development and testing.

## Test Users Setup

### 1. Create Test Users in Supabase Auth

```bash
./create_test_users.sh
```

This creates two test users:
- `test1@example.com` / Password: `12345678`
- `test2@example.com` / Password: `12345678`

### 2. Create User Profiles in Database

Run `create_test_profiles.sql` in Supabase SQL Editor:

1. Go to Supabase Dashboard → SQL Editor
2. Copy content from `create_test_profiles.sql`
3. Run the SQL

Or use psql:
```bash
psql $DATABASE_URL < scripts/create_test_profiles.sql
```

## Usage

After setup, you can use these test users for:
- Manual testing via API
- Automated tests (see `tests/fixtures_test_users.py`)
- Development and debugging

## Test User IDs

- Test User 1: `8ef3a396-d9fe-4f80-a8d3-437e75dd3248`
- Test User 2: `627f319d-ee76-4acb-8f80-be1df138130a`

**Note:** These IDs are generated when you run `create_test_users.sh`. Update `create_test_profiles.sql` if IDs are different.
