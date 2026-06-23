#!/bin/bash
# 🚀 Aegis Box v0.1.0 正式发布脚本
# 请在执行前确认：
# 1. 所有代码已提交到 Git
# 2. CHANGELOG.md 已更新
# 3. pyproject.toml 版本号正确
# 4. PyPI 账号已配置（~/.pypirc）

set -e  # 遇到错误立即退出

echo "🛡️  Aegis Box v0.1.0 发布准备..."
echo ""

# ==========================================
# 步骤 1: 创建 Git Tag
# ==========================================
echo "📌 步骤 1: 创建 Git Tag"
echo "----------------------------------------"

# 检查是否有未提交的更改
if [[ -n $(git status -s) ]]; then
    echo "⚠️  警告: 检测到未提交的更改"
    git status -s
    echo ""
    read -p "是否继续？(y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ 发布已取消"
        exit 1
    fi
fi

# 创建 Tag
echo "创建 Tag: v0.1.0"
git tag -a v0.1.0 -m "🚀 Release v0.1.0: Initial public release

🎯 核心功能:
- 🧹 Asset Sweeper: 资产清扫与垃圾清理
- 🔍 Architecture Reducer: AST 提取与架构审计
- 🛠️  Smart Patcher: 智能补丁生成与 Git 沙盒
- 🔄 Context Injector: IDE 上下文同步
- 🤖 三级模型路由: Tier1 (快速) → Tier2 (推理) → Tier3 (修复)

🌟 特色:
- The Ouroboros Protocol: 自我审计与进化能力
- 无损补丁引擎: SEARCH/REPLACE 精准替换
- AST 压缩: Token 消耗降低 90%
- 隐私保护: 只提取结构，不上传业务逻辑

📚 文档:
- README: 完整使用指南
- QUICKSTART: 3 分钟快速开始
- LAUNCH_POST: 首发新闻稿

🙏 致谢:
感谢所有测试者和早期用户的反馈！

---
Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"

echo "✅ Tag 创建成功"
echo ""

# 推送 Tag 到远程
echo "推送 Tag 到 GitHub..."
git push origin v0.1.0

echo "✅ Tag 已推送"
echo ""

# ==========================================
# 步骤 2: 构建分发包
# ==========================================
echo "📦 步骤 2: 构建分发包"
echo "----------------------------------------"

# 清理旧的构建产物
echo "清理旧的构建产物..."
rm -rf dist/ build/ *.egg-info/

# 使用 Python 3.13+ 构建
echo "构建 wheel 和 sdist..."
python3 -m build

echo "✅ 构建完成"
echo ""

# 显示构建产物
echo "构建产物:"
ls -lh dist/
echo ""

# ==========================================
# 步骤 3: 上传到 PyPI
# ==========================================
echo "🚀 步骤 3: 上传到 PyPI"
echo "----------------------------------------"

# 检查 PyPI 配置
if [[ ! -f ~/.pypirc ]]; then
    echo "⚠️  警告: 未找到 ~/.pypirc 配置文件"
    echo "请先配置 PyPI 凭证:"
    echo ""
    echo "cat > ~/.pypirc << EOF"
    echo "[pypi]"
    echo "username = __token__"
    echo "password = pypi-AgEIcHlwaS5vcmcC..."
    echo "EOF"
    echo ""
    read -p "配置完成后按回车继续，或按 Ctrl+C 取消..."
fi

# 上传到 PyPI
echo "上传到 PyPI..."
python3 -m twine upload dist/*

echo ""
echo "✅ 上传完成！"
echo ""

# ==========================================
# 步骤 4: 验证发布
# ==========================================
echo "🔍 步骤 4: 验证发布"
echo "----------------------------------------"

echo "等待 PyPI 索引更新（约 30 秒）..."
sleep 30

echo "尝试从 PyPI 安装..."
pip install --upgrade aegis-box

echo ""
echo "验证版本..."
aegis version

echo ""
echo "✅ 发布验证成功！"
echo ""

# ==========================================
# 完成
# ==========================================
echo "=========================================="
echo "🎉 Aegis Box v0.1.0 发布成功！"
echo "=========================================="
echo ""
echo "接下来的步骤:"
echo ""
echo "1. 在 GitHub 上创建 Release:"
echo "   https://github.com/nexo/aegis-box/releases/new?tag=v0.1.0"
echo ""
echo "2. 发布新闻稿:"
echo "   - Hacker News: https://news.ycombinator.com/submit"
echo "   - Reddit r/Python: https://reddit.com/r/Python/submit"
echo "   - Twitter/X: 分享 docs/LAUNCH_POST.md"
echo ""
echo "3. 更新项目主页:"
echo "   - PyPI 项目页面已自动更新"
echo "   - 检查 README 渲染是否正确"
echo ""
echo "4. 监控反馈:"
echo "   - GitHub Issues: https://github.com/nexo/aegis-box/issues"
echo "   - PyPI 下载量: https://pypistats.org/packages/aegis-box"
echo ""
echo "🛡️  Aegis Box - 让 AI 辅助开发更安全、更高效！"
echo ""
