#!/bin/bash
# 🛡️ Aegis Box - 智谱 AI 原生 SDK 安装和验证脚本

set -e  # 遇到错误立即退出

echo "========================================"
echo "🛡️ Aegis Box - 智谱 AI SDK 安装"
echo "========================================"
echo ""

# ==========================================
# Step 1: 检查 Python 环境
# ==========================================
echo "📋 Step 1: 检查 Python 环境..."

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 未安装"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | awk '{print $2}')
echo "✅ Python 版本: $PYTHON_VERSION"
echo ""

# ==========================================
# Step 2: 安装依赖
# ==========================================
echo "📦 Step 2: 安装 zai-sdk..."

pip install zai-sdk==0.2.3 || {
    echo "❌ zai-sdk 安装失败"
    exit 1
}

echo "✅ zai-sdk 安装成功"
echo ""

# ==========================================
# Step 3: 验证安装
# ==========================================
echo "🔍 Step 3: 验证安装..."

python3 << EOF
try:
    import zai
    print(f"✅ zai-sdk 版本: {zai.__version__}")
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    exit(1)
EOF

echo ""

# ==========================================
# Step 4: 检查 API Key
# ==========================================
echo "🔑 Step 4: 检查 API Key..."

if [ -z "$ZHIPU_API_KEY" ]; then
    echo "⚠️ 未设置 ZHIPU_API_KEY 环境变量"
    echo ""
    echo "请执行以下命令之一："
    echo "  1. export ZHIPU_API_KEY=your-api-key"
    echo "  2. 在 .env 文件中添加: ZHIPU_API_KEY=your-api-key"
    echo ""
else
    # 脱敏显示
    MASKED_KEY="${ZHIPU_API_KEY:0:8}...${ZHIPU_API_KEY: -4}"
    echo "✅ API Key 已配置: $MASKED_KEY"
    echo ""
fi

# ==========================================
# Step 5: 运行测试
# ==========================================
echo "🧪 Step 5: 运行测试（可选）..."
echo ""
echo "运行以下命令测试功能："
echo "  python examples/test_zhipu_client.py"
echo ""
echo "运行性能对比："
echo "  python scripts/benchmark_llm.py"
echo ""

# ==========================================
# 完成
# ==========================================
echo "========================================"
echo "✅ 安装完成！"
echo "========================================"
echo ""
echo "📚 下一步："
echo "  1. 阅读文档: docs/ZHIPU_OPTIMIZATION.md"
echo "  2. 运行示例: python examples/test_zhipu_client.py"
echo "  3. 集成到 Aegis: 参考文档 Phase 1"
echo ""
