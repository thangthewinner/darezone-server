#!/bin/bash
# Get JWT token for Railway production API
# Usage: ./get_token_railway.sh [1|2]

source .env

# Railway API URL
RAILWAY_API="https://darezone.up.railway.app/api/v1"

if [ "$1" == "1" ] || [ "$1" == "" ]; then
    EMAIL="test1@example.com"
    echo "🔑 Getting token for User 1 (test1@example.com) on Railway..."
elif [ "$1" == "2" ]; then
    EMAIL="test2@example.com"
    echo "🔑 Getting token for User 2 (test2@example.com) on Railway..."
else
    echo "Usage: ./get_token_railway.sh [1|2]"
    echo "  1 = test1@example.com"
    echo "  2 = test2@example.com"
    exit 1
fi

# Login via Supabase (same as local)
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

# Test token with Railway API
echo "🧪 Testing token with Railway API..."
RESPONSE=$(curl -s -X GET "$RAILWAY_API/auth/me" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json")

if echo "$RESPONSE" | grep -q "$EMAIL"; then
    echo "✅ Token is VALID on Railway!"
    echo "   User: $(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('email', 'N/A'))" 2>/dev/null)"
else
    echo "⚠️  Could not verify token (API might be down or token invalid)"
    echo "   Response: $RESPONSE"
fi

echo ""
echo "📋 Instructions for Railway Swagger UI:"
echo "1. Open https://darezone.up.railway.app/docs"
echo "2. Click 'Authorize' button (green lock icon)"
echo "3. Paste the token above"
echo "4. Click 'Authorize' then 'Close'"
echo ""
