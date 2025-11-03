#!/bin/bash
# Test script to verify mode logging works correctly

echo "========================================="
echo "Testing Mode Logging"
echo "========================================="
echo ""

cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

echo "Test 1: Production Mode (no WG_MOCK_MODE set)"
echo "-----------------------------------------"
timeout 3 python3 app.py 2>&1 | grep -E "(MOCK MODE|PRODUCTION MODE|Database:|Scenario:)" || true
echo ""

echo "Test 2: Mock Mode with mixed scenario"
echo "-----------------------------------------"
WG_MOCK_MODE=true WG_MOCK_SCENARIO=mixed timeout 3 python3 app.py 2>&1 | grep -E "(MOCK MODE|PRODUCTION MODE|Database:|Scenario:)" || true
echo ""

echo "Test 3: Mock Mode with empty scenario"
echo "-----------------------------------------"
WG_MOCK_MODE=true WG_MOCK_SCENARIO=empty timeout 3 python3 app.py 2>&1 | grep -E "(MOCK MODE|PRODUCTION MODE|Database:|Scenario:)" || true
echo ""

echo "========================================="
echo "Test complete!"
echo "========================================="
