#!/bin/bash
# Script to check Railway configuration and environment variables
# This helps diagnose why auto-migrations might not be running

echo "========================================================================"
echo "Railway Configuration Checker"
echo "========================================================================"
echo ""

# Check if railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI is not installed"
    echo "Install with: npm install -g @railway/cli"
    exit 1
fi

echo "✅ Railway CLI is installed"
echo ""

# Try to get Railway project info
echo "📋 Checking Railway project configuration..."
echo ""

# Get environment variables (this will require manual review)
echo "🔍 Fetching environment variables from Railway..."
echo "Note: You may need to select your project/environment interactively"
echo ""

railway vars 2>&1

echo ""
echo "========================================================================"
echo "Check for these key variables:"
echo "========================================================================"
echo "  - RUN_MIGRATIONS: Should be 'true' for auto-migrations"
echo "  - DATABASE_URL: Should be set to your PostgreSQL connection string"
echo "  - ENVIRONMENT: Should indicate production/staging/development"
echo ""
echo "If RUN_MIGRATIONS is not set or is 'false', set it with:"
echo "  railway vars set RUN_MIGRATIONS=true"
echo ""
echo "To view logs:"
echo "  railway logs --service backend"
echo ""

