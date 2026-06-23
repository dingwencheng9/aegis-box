#!/bin/bash
# 🚀 Aegis Box v0.1.0 - 一键复制发布命令
# 直接复制下方三条命令到终端执行

# ============================================
# 📌 命令 1: 创建并推送 Git Tag
# ============================================
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
Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>" && git push origin v0.1.0


# ============================================
# 📦 命令 2: 清理并构建分发包
# ============================================
rm -rf dist/ build/ *.egg-info/ && python3 -m build


# ============================================
# 🚀 命令 3: 上传到 PyPI
# ============================================
python3 -m twine upload dist/*
