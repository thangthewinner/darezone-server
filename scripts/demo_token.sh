#!/bin/bash
# Demo: How JWT Token Works

echo "🔐 JWT Token Demo"
echo "================="
echo ""

source .env

echo "1️⃣ Login User 1 (first time)..."
TOKEN1=$(curl -s -X POST "$SUPABASE_URL/auth/v1/token?grant_type=password" \
  -H "apikey: $SUPABASE_SERVICE_ROLE_KEY" \
  -H "Content-Type: application/json" \
  -d '{"email":"test1@example.com","password":"12345678"}' \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)

echo "   Token 1: ${TOKEN1:0:50}..."
echo ""

sleep 1

echo "2️⃣ Login User 1 (second time)..."
TOKEN2=$(curl -s -X POST "$SUPABASE_URL/auth/v1/token?grant_type=password" \
  -H "apikey: $SUPABASE_SERVICE_ROLE_KEY" \
  -H "Content-Type: application/json" \
  -d '{"email":"test1@example.com","password":"12345678"}' \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)

echo "   Token 2: ${TOKEN2:0:50}..."
echo ""

echo "3️⃣ Comparing tokens..."
if [ "$TOKEN1" == "$TOKEN2" ]; then
    echo "   ❌ Tokens are SAME (unexpected)"
else
    echo "   ✅ Tokens are DIFFERENT (each login creates unique token)"
fi
echo ""

echo "4️⃣ Test Token 1 with API..."
RESPONSE=$(curl -s -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer $TOKEN1")

if echo "$RESPONSE" | grep -q "test1@example.com"; then
    echo "   ✅ Token 1 is VALID"
    echo "   User: $(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['email'])" 2>/dev/null)"
else
    echo "   ❌ Token 1 is INVALID"
fi
echo ""

echo "5️⃣ Test Token 2 with API..."
RESPONSE=$(curl -s -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer $TOKEN2")

if echo "$RESPONSE" | grep -q "test1@example.com"; then
    echo "   ✅ Token 2 is VALID"
    echo "   User: $(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['email'])" 2>/dev/null)"
else
    echo "   ❌ Token 2 is INVALID"
fi
echo ""

echo "📝 Summary:"
echo "   - Each login creates a NEW unique token"
echo "   - Both tokens are valid (until expiry)"
echo "   - You can use either token to authenticate"
echo "   - Token expires after 1 hour"
echo ""

echo "🎯 For Swagger UI:"
echo "   1. Copy any token above"
echo "   2. Go to http://localhost:8000/docs"
echo "   3. Click 'Authorize'"
echo "   4. Paste token in 'Value' field"
echo "   5. Click 'Authorize' then 'Close'"
echo ""
