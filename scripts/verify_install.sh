#!/bin/bash
# 🛡️ Aegis Box - Global Installation Verification Script
# 验证全局安装后的包完整性和可用性

set -e

echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                              ║"
echo "║           🛡️  Aegis Box - Global Installation Verification               ║"
echo "║                                                                              ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""

# ==========================================
# Step 1: 创建干净的测试环境
# ==========================================
echo "📦 Step 1: 创建干净的测试环境"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

TEST_DIR="/tmp/aegis_test_env_$(date +%s)"
echo "创建测试目录: $TEST_DIR"
mkdir -p "$TEST_DIR"
cd "$TEST_DIR"

echo "✅ 测试环境已创建"
echo ""

# ==========================================
# Step 2: 验证 CLI 命令可用
# ==========================================
echo "🔍 Step 2: 验证 CLI 命令可用"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if command -v aegis &> /dev/null; then
    echo "✅ aegis 命令已安装"
else
    echo "❌ aegis 命令未找到"
    echo ""
    echo "请确保你已经运行了:"
    echo "  pip install aegis-box"
    echo ""
    exit 1
fi

echo ""

# ==========================================
# Step 3: 测试 --version
# ==========================================
echo "📌 Step 3: 测试 aegis --version"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

VERSION_OUTPUT=$(aegis --version 2>&1 || echo "FAILED")

if [[ "$VERSION_OUTPUT" == *"0.1.0"* ]]; then
    echo "✅ 版本检查通过"
    echo "输出: $VERSION_OUTPUT"
else
    echo "❌ 版本检查失败"
    echo "输出: $VERSION_OUTPUT"
    exit 1
fi

echo ""

# ==========================================
# Step 4: 测试 aegis init
# ==========================================
echo "🔧 Step 4: 测试 aegis init"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

INIT_OUTPUT=$(aegis init 2>&1 || echo "FAILED")

if [[ "$INIT_OUTPUT" == *"FAILED"* ]]; then
    echo "❌ aegis init 执行失败"
    echo "输出: $INIT_OUTPUT"
    exit 1
fi

echo "✅ aegis init 执行成功"
echo ""

# ==========================================
# Step 5: 验证生成的配置文件
# ==========================================
echo "📝 Step 5: 验证生成的配置文件"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ -f "aegis.yaml" ]; then
    echo "✅ aegis.yaml 已生成"
    echo ""
    echo "文件内容预览:"
    head -n 20 aegis.yaml
    echo ""
else
    echo "❌ aegis.yaml 未生成"
    exit 1
fi

# ==========================================
# Step 6: 验证帮助文档
# ==========================================
echo "📚 Step 6: 验证帮助文档"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

HELP_OUTPUT=$(aegis --help 2>&1 || echo "FAILED")

if [[ "$HELP_OUTPUT" == *"FAILED"* ]]; then
    echo "❌ aegis --help 执行失败"
    exit 1
fi

# 检查关键命令是否存在
REQUIRED_COMMANDS=("init" "run" "audit" "sweep" "patch")
ALL_FOUND=true

for cmd in "${REQUIRED_COMMANDS[@]}"; do
    if [[ "$HELP_OUTPUT" == *"$cmd"* ]]; then
        echo "✅ 命令存在: $cmd"
    else
        echo "❌ 命令缺失: $cmd"
        ALL_FOUND=false
    fi
done

if [ "$ALL_FOUND" = false ]; then
    echo ""
    echo "❌ 部分命令缺失"
    exit 1
fi

echo ""

# ==========================================
# Step 7: 清理测试环境
# ==========================================
echo "🧹 Step 7: 清理测试环境"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

cd /tmp
rm -rf "$TEST_DIR"

echo "✅ 测试环境已清理"
echo ""

# ==========================================
# 总结
# ==========================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 全局安装验证成功！"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Aegis Box 全局安装验证通过所有测试："
echo "  ✅ CLI 命令可用"
echo "  ✅ 版本信息正确"
echo "  ✅ init 命令工作正常"
echo "  ✅ 配置文件正常生成"
echo "  ✅ 帮助文档完整"
echo "  ✅ 所有核心命令存在"
echo ""
echo "🛡️  Aegis Box 已准备好投入使用！"
echo ""
