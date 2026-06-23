#!/bin/bash
# 🛡️ Aegis Box - Day 2 Infrastructure Setup
# Run this script to verify all Day 2 infrastructure is properly configured

set -e

echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                              ║"
echo "║          🛡️  Aegis Box - Day 2 Infrastructure Verification               ║"
echo "║                                                                              ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""

# ==========================================
# Check GitHub Infrastructure
# ==========================================
echo "📋 Checking GitHub Infrastructure..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

files_to_check=(
    ".github/workflows/ci.yml"
    ".github/ISSUE_TEMPLATE/bug_report.md"
    ".github/ISSUE_TEMPLATE/feature_request.md"
    ".github/ISSUE_TEMPLATE/documentation.md"
    ".github/ISSUE_TEMPLATE/config.yml"
    ".github/PULL_REQUEST_TEMPLATE.md"
    ".github/CODEOWNERS"
)

all_present=true

for file in "${files_to_check[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file (MISSING)"
        all_present=false
    fi
done

echo ""

# ==========================================
# Check Documentation
# ==========================================
echo "📚 Checking Documentation..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

docs_to_check=(
    "ROADMAP.md"
    "SECURITY.md"
    "CONTRIBUTING.md"
    "README.md"
    "CHANGELOG.md"
)

for doc in "${docs_to_check[@]}"; do
    if [ -f "$doc" ]; then
        echo "✅ $doc"
    else
        echo "⚠️  $doc (missing, but may not be critical)"
    fi
done

echo ""

# ==========================================
# Check Project Structure
# ==========================================
echo "🏗️  Checking Project Structure..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

dirs_to_check=(
    "aegis"
    "tests"
    "docs"
    "scripts"
    ".github"
)

for dir in "${dirs_to_check[@]}"; do
    if [ -d "$dir" ]; then
        echo "✅ $dir/"
    else
        echo "⚠️  $dir/ (missing)"
    fi
done

echo ""

# ==========================================
# Verify CI/CD Configuration
# ==========================================
echo "🔧 Verifying CI/CD Configuration..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ -f ".github/workflows/ci.yml" ]; then
    echo "✅ CI workflow configured"

    # Check if workflow has required jobs
    if grep -q "test:" .github/workflows/ci.yml; then
        echo "  ✅ Test job configured"
    else
        echo "  ❌ Test job missing"
    fi

    if grep -q "critical-modules:" .github/workflows/ci.yml; then
        echo "  ✅ Critical modules test configured"
    else
        echo "  ❌ Critical modules test missing"
    fi

    if grep -q "build:" .github/workflows/ci.yml; then
        echo "  ✅ Build job configured"
    else
        echo "  ❌ Build job missing"
    fi
else
    echo "❌ CI workflow not found"
fi

echo ""

# ==========================================
# Check Issue Templates
# ==========================================
echo "🎫 Verifying Issue Templates..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ -f ".github/ISSUE_TEMPLATE/bug_report.md" ]; then
    echo "✅ Bug report template"
else
    echo "❌ Bug report template missing"
fi

if [ -f ".github/ISSUE_TEMPLATE/feature_request.md" ]; then
    echo "✅ Feature request template"
else
    echo "❌ Feature request template missing"
fi

if [ -f ".github/ISSUE_TEMPLATE/documentation.md" ]; then
    echo "✅ Documentation issue template"
else
    echo "❌ Documentation issue template missing"
fi

echo ""

# ==========================================
# Check Security Configuration
# ==========================================
echo "🔒 Verifying Security Configuration..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ -f "SECURITY.md" ]; then
    echo "✅ Security policy documented"
else
    echo "❌ SECURITY.md missing"
fi

if [ -f ".github/CODEOWNERS" ]; then
    echo "✅ Code owners configured"
else
    echo "⚠️  CODEOWNERS missing (recommended for review automation)"
fi

echo ""

# ==========================================
# Summary
# ==========================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ "$all_present" = true ]; then
    echo "✅ All critical Day 2 infrastructure is in place!"
    echo ""
    echo "🚀 Next Steps:"
    echo "   1. Push these changes to GitHub"
    echo "   2. Enable GitHub Actions in repository settings"
    echo "   3. Configure branch protection rules for 'main'"
    echo "   4. Set up Codecov (optional but recommended)"
    echo ""
    exit 0
else
    echo "⚠️  Some files are missing. Please review the checklist above."
    echo ""
    echo "📚 Refer to docs/INFRASTRUCTURE.md for setup instructions."
    echo ""
    exit 1
fi
