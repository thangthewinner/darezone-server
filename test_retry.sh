#!/bin/bash
# Retry test until schema cache refreshes

echo "⏳ Waiting for Supabase to resume..."
sleep 60

cd darezone-server
source .venv/bin/activate

echo "🧪 Testing challenge creation..."
for i in {1..10}; do
    echo ""
    echo "=== Attempt $i/10 ==="
    
    python -m pytest tests/test_comprehensive_features.py::TestChallengeFeatures::test_user1_create_individual_challenge -v --tb=line 2>&1 | tail -20
    
    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        echo ""
        echo "✅ SUCCESS! Schema cache refreshed. Test passed!"
        echo ""
        echo "Running full test suite..."
        python -m pytest tests/test_comprehensive_features.py -v
        exit 0
    fi
    
    if [ $i -lt 10 ]; then
        echo "⏳ Waiting 30s before retry..."
        sleep 30
    fi
done

echo ""
echo "❌ Test still failing after 10 attempts. Manual intervention needed."
exit 1
