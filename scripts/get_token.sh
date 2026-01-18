#!/bin/bash
# Quick token getter for Swagger UI testing
# Usage: ./get_token.sh [1|2]

source .env

if [ "$1" == "1" ] || [ "$1" == "" ]; then
    EMAIL="test1@example.com"
    echo "🔑 Getting token for User 1 (test1@example.com)..."
elif [ "$1" == "2" ]; then
    EMAIL="test2@example.com"
    echo "🔑 Getting token for User 2 (test2@example.com)..."
else
    echo "Usage: ./get_token.sh [1|2]"
    echo "  1 = test1@example.com"
    echo "  2 = test2@example.com"
    exit 1
fi

TOKEN=$(curl -s -X POST "$SUPABASE_URL/auth/v1/token?grant_type=password" \
  -H "apikey: $SUPABASE_SERVICE_ROLE_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"12345678\"}" \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)

if [ -z "$TOKEN" ]; then
    echo "❌ Failed to get token"
    exit 1
fi

echo ""
echo "✅ Token for $EMAIL:"
echo ""
echo "$TOKEN"
echo ""
echo "📋 Instructions for Swagger UI:"
echo "1. Open http://localhost:8000/docs"
echo "2. Click 'Authorize' button (green lock icon)"
echo "3. Paste the token above"
echo "4. Click 'Authorize' then 'Close'"
echo ""
