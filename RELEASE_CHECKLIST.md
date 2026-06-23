# ✅ Aegis Box v0.1.0 发布前检查清单

## 📋 必须完成（Pre-flight Checklist）

### 代码质量

- [ ] 所有测试通过 (`pytest tests/`)
- [ ] 代码格式化完成 (`black . && ruff check .`)
- [ ] 类型检查通过 (`mypy aegis/`)
- [ ] 没有未处理的 TODO/FIXME

### 文档完整性

- [ ] README.md 包含 "The Ouroboros Protocol" 章节
- [ ] CHANGELOG.md 已更新
- [ ] QUICKSTART.md 已更新
- [ ] docs/LAUNCH_POST.md 已创建
- [ ] docs/RELEASE_GUIDE.md 已创建
- [ ] API 文档完整

### 版本信息

- [ ] pyproject.toml: version = "0.1.0"
- [ ] aegis/**init**.py: **version** = "0.1.0"
- [ ] README.md 徽章版本正确

### Git 状态

- [ ] 所有更改已提交
- [ ] 所有更改已推送到 GitHub
- [ ] 没有未解决的 merge conflicts

### 配置文件

- [ ] aegis.yaml.example 已更新
- [ ] .gitignore 完整
- [ ] LICENSE 文件存在

### PyPI 准备

- [ ] PyPI 账号已注册
- [ ] PyPI Token 已生成并配置在 ~/.pypirc
- [ ] 包名 "aegis-box" 在 PyPI 上可用（或已拥有）

---

## 🚀 一键复制命令（发布当天）

### 检查状态

```bash
# 检查 Git 状态
git status

# 检查版本号
grep 'version = ' pyproject.toml
grep '__version__' aegis/__init__.py

# 运行测试（可选，如果已在 CI 中运行）
pytest tests/ -v
```

---

### 🎯 三条发布命令（复制粘贴）

```bash
# ============================================
# 命令 1: 创建并推送 Git Tag
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
# 命令 2: 清理并构建分发包
# ============================================
rm -rf dist/ build/ *.egg-info/ && python3 -m build


# ============================================
# 命令 3: 上传到 PyPI
# ============================================
python3 -m twine upload dist/*
```

---

### 验证发布

```bash
# 等待 PyPI 索引更新
sleep 30

# 在新的虚拟环境中安装
python3 -m venv /tmp/test_aegis
source /tmp/test_aegis/bin/activate
pip install aegis-box

# 验证版本
aegis version

# 清理测试环境
deactivate
rm -rf /tmp/test_aegis
```

---

## 📢 发布后宣传（Post-launch Promotion）

### 1. GitHub Release

- [ ] 访问 https://github.com/nexo/aegis-box/releases/new?tag=v0.1.0
- [ ] 标题: 🛡️ Aegis Box v0.1.0 - Initial Public Release
- [ ] 内容: 使用 docs/LAUNCH_POST.md（简化版）
- [ ] 上传构建产物: dist/aegis_box-0.1.0.tar.gz

### 2. Hacker News

- [ ] 访问 https://news.ycombinator.com/submit
- [ ] 标题: "I built an AI audit engine, then let it audit and refactor itself"
- [ ] URL: https://github.com/nexo/aegis-box

### 3. Reddit r/Python

- [ ] 访问 https://reddit.com/r/Python/submit
- [ ] 标题: "Aegis Box: Full-stack intelligent audit engine for Claude Code / Cursor"
- [ ] 内容: docs/LAUNCH_POST.md

### 4. Twitter/X

- [ ] 发推特（示例见下方）
- [ ] 标签: #AI #LLM #ClaudeCode #Cursor #Python

**Twitter 文案:**

```
🛡️ Aegis Box v0.1.0 发布！

一个专为 Claude Code / Cursor 设计的智能审计引擎：
• 🧹 清理垃圾文件
• 🔍 AST 压缩审计
• 🩹 自动生成补丁
• 🔄 IDE 规则同步

最疯狂的是：它能审计自己，然后让自己变得更好 🤯

pip install aegis-box

GitHub: https://github.com/nexo/aegis-box

#AI #LLM #ClaudeCode #Cursor #Python #OpenSource
```

### 5. LinkedIn

- [ ] 发布 docs/LAUNCH_POST.md 的专业版
- [ ] 标签: #AI #SoftwareEngineering #Security

### 6. Dev.to / Medium

- [ ] 发布技术深度文章（可选）
- [ ] 标题: "Building Aegis Box: An AI That Audits Itself"

---

## 📊 发布后监控（Post-launch Monitoring）

### 第一天

- [ ] 监控 PyPI 下载量: https://pypistats.org/packages/aegis-box
- [ ] 监控 GitHub Stars: https://github.com/nexo/aegis-box
- [ ] 监控 GitHub Issues: https://github.com/nexo/aegis-box/issues
- [ ] 回复所有 Issues 和 PR

### 第一周

- [ ] 收集用户反馈
- [ ] 修复紧急 bug
- [ ] 更新文档（根据用户反馈）
- [ ] 准备 v0.1.1 热修复（如果需要）

### 第一个月

- [ ] 分析使用数据
- [ ] 规划 v0.2.0 功能
- [ ] 扩展语言支持（Rust, Go, Java 等）
- [ ] 优化性能

---

## 🎉 发布成功标志

当你看到以下指标时，说明发布成功：

- ✅ PyPI 页面可访问: https://pypi.org/project/aegis-box/
- ✅ `pip install aegis-box` 可以正常安装
- ✅ `aegis version` 显示正确版本
- ✅ GitHub Release 已创建
- ✅ 至少 10 个 GitHub Stars（首日）
- ✅ 至少 100 次 PyPI 下载（首周）
- ✅ 至少 1 个社区 Issue 或 PR

---

## 🛠️ 应急预案（Emergency Rollback）

### 如果发现严重 bug

```bash
# 1. 从 PyPI 撤回版本（不推荐，但可以）
# 联系 PyPI 支持: https://pypi.org/help/

# 2. 发布热修复版本 v0.1.1
# 在 CHANGELOG.md 中说明问题
# 快速修复并发布新版本

# 3. 在 GitHub Release 中标注警告
# 添加 "⚠️ Known Issues" 部分
```

### 如果 Tag 错误

```bash
# 删除本地 Tag
git tag -d v0.1.0

# 删除远程 Tag
git push origin :refs/tags/v0.1.0

# 重新创建
git tag -a v0.1.0 -m "..."
git push origin v0.1.0
```

---

## 📝 发布日志模板

记录发布过程中的关键信息：

```markdown
# Aegis Box v0.1.0 发布日志

**发布日期**: 2026-06-23
**发布人**: Nexo
**Git Commit**: [commit hash]
**PyPI URL**: https://pypi.org/project/aegis-box/0.1.0/

## 发布时间线

- [ ] 14:00 - 创建 Git Tag
- [ ] 14:05 - 构建分发包
- [ ] 14:10 - 上传到 PyPI
- [ ] 14:15 - 验证安装
- [ ] 14:30 - GitHub Release
- [ ] 15:00 - Hacker News
- [ ] 15:30 - Reddit
- [ ] 16:00 - Twitter/X

## 发布指标（首日）

- PyPI 下载: [填写]
- GitHub Stars: [填写]
- GitHub Issues: [填写]
- 社区反馈: [填写]

## 遇到的问题

[记录发布过程中遇到的问题和解决方案]

## 经验教训

[记录经验教训，供下次发布参考]
```

---

## 🚀 准备好了吗？

**如果上述所有复选框都打勾了，你就可以发布了！**

```bash
# 复制并执行三条发布命令（见上方）
```

**祝你发布顺利！🎉**

---

🛡️ **Aegis Box - 让 AI 辅助开发更安全、更高效！**
