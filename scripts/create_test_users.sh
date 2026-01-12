#!/bin/bash
# Create Test Users in Supabase
echo "🔧 Creating test users..."
source .env

# Test user 1
echo "Creating test1@example.com..."
curl -X POST "$SUPABASE_URL/auth/v1/admin/users" \
  -H "apikey: $SUPABASE_SERVICE_ROLE_KEY" \
  -H "Authorization: Bearer $SUPABASE_SERVICE_ROLE_KEY" \
  -H "Content-Type: application/json" \
  -d '{"email":"test1@example.com","password":"12345678","email_confirm":true,"user_metadata":{"display_name":"Test User 1"}}'

echo ""

# Test user 2
echo "Creating test2@example.com..."
curl -X POST "$SUPABASE_URL/auth/v1/admin/users" \
  -H "apikey: $SUPABASE_SERVICE_ROLE_KEY" \
  -H "Authorization: Bearer $SUPABASE_SERVICE_ROLE_KEY" \
  -H "Content-Type: application/json" \
  -d '{"email":"test2@example.com","password":"12345678","email_confirm":true,"user_metadata":{"display_name":"Test User 2"}}'

echo ""
echo "✅ Done! Credentials: test1@example.com / test2@example.com | Password: 12345678"
