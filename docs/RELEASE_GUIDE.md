# 🚀 Aegis Box v0.1.0 发布命令清单

## 快速发布（三条命令）

如果你已经确认：

- ✅ 所有代码已提交
- ✅ 版本号正确（pyproject.toml: version = "0.1.0"）
- ✅ PyPI Token 已配置（~/.pypirc）

**直接执行以下命令：**

```bash
# 命令 1: 创建并推送 Git Tag
git tag -a v0.1.0 -m "🚀 Release v0.1.0: Initial public release" && git push origin v0.1.0

# 命令 2: 构建分发包
python3 -m build

# 命令 3: 上传到 PyPI
python3 -m twine upload dist/*
```

---

## 完整发布流程（推荐）

### 前置准备

1. **检查未提交的更改**

   ```bash
   git status
   ```

2. **确认版本号**

   ```bash
   grep 'version = ' pyproject.toml
   # 应该显示: version = "0.1.0"
   ```

3. **安装构建工具**（如果未安装）

   ```bash
   pip install build twine
   ```

4. **配置 PyPI Token**（首次发布）
   ```bash
   # 访问 https://pypi.org/manage/account/token/ 生成 Token
   # 然后创建 ~/.pypirc
   cat > ~/.pypirc << 'EOF'
   [pypi]
   username = __token__
   password = pypi-AgEIcHlwaS5vcmcC...  # 你的 Token
   EOF
   chmod 600 ~/.pypirc
   ```

---

### 发布步骤

#### 步骤 1: 创建 Git Tag

```bash
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

---
Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

**推送 Tag 到 GitHub:**

```bash
git push origin v0.1.0
```

---

#### 步骤 2: 构建分发包

```bash
# 清理旧的构建产物
rm -rf dist/ build/ *.egg-info/

# 构建 wheel 和 source distribution
python3 -m build
```

**验证构建产物:**

```bash
ls -lh dist/
# 应该看到:
# aegis_box-0.1.0-py3-none-any.whl
# aegis_box-0.1.0.tar.gz
```

---

#### 步骤 3: 上传到 PyPI

```bash
# 上传到 PyPI
python3 -m twine upload dist/*
```

**或者先上传到 TestPyPI 测试:**

```bash
# 上传到 TestPyPI
python3 -m twine upload --repository testpypi dist/*

# 从 TestPyPI 安装测试
pip install --index-url https://test.pypi.org/simple/ aegis-box
```

---

### 发布后验证

```bash
# 等待 PyPI 索引更新（约 30 秒）
sleep 30

# 从 PyPI 安装
pip install --upgrade aegis-box

# 验证版本
aegis version
# 应该显示: 🛡️ Aegis Box v0.1.0
```

---

## 发布后任务

### 1. 在 GitHub 上创建 Release

访问: https://github.com/nexo/aegis-box/releases/new?tag=v0.1.0

**Release 标题:** 🛡️ Aegis Box v0.1.0 - Initial Public Release

**描述:** 使用 `docs/LAUNCH_POST.md` 的内容（简化版）

---

### 2. 发布新闻稿

#### Hacker News

- URL: https://news.ycombinator.com/submit
- 标题: "I built an AI audit engine, then let it audit and refactor itself"
- 链接: GitHub 项目地址

#### Reddit r/Python

- URL: https://reddit.com/r/Python/submit
- 标题: "Aegis Box: Full-stack intelligent audit engine for Claude Code / Cursor"
- 内容: 使用 `docs/LAUNCH_POST.md`

#### Twitter/X

```
🛡️ Aegis Box v0.1.0 发布！

一个专为 Claude Code / Cursor 设计的智能审计引擎：
• 🧹 清理垃圾
• 🔍 AST 审计
• 🩹 自动修复
• 🔄 IDE 集成

最疯狂的是：它能审计自己，然后让自己变得更好 🤯

pip install aegis-box

#AI #LLM #ClaudeCode #Cursor
```

#### LinkedIn

使用 `docs/LAUNCH_POST.md` 的完整内容

---

### 3. 监控指标

- **PyPI 下载量**: https://pypistats.org/packages/aegis-box
- **GitHub Stars**: https://github.com/nexo/aegis-box
- **GitHub Issues**: https://github.com/nexo/aegis-box/issues

---

## 常见问题

### Q: Twine 上传失败怎么办？

```bash
# 检查 Token 是否正确
cat ~/.pypirc

# 重新生成 Token
# 访问 https://pypi.org/manage/account/token/
```

---

### Q: Tag 已经存在怎么办？

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

### Q: 构建失败怎么办？

```bash
# 检查 pyproject.toml 语法
python3 -c "import tomllib; tomllib.load(open('pyproject.toml', 'rb'))"

# 检查依赖是否正确
python3 -m pip check
```

---

## 一键发布脚本

如果你想用自动化脚本：

```bash
./scripts/release.sh
```

这个脚本会：

1. ✅ 检查未提交的更改
2. ✅ 创建并推送 Git Tag
3. ✅ 构建分发包
4. ✅ 上传到 PyPI
5. ✅ 验证发布

---

## 🎉 发布成功！

恭喜！Aegis Box v0.1.0 已经发布到 PyPI！

现在全世界的开发者都可以通过 `pip install aegis-box` 安装你的工具了！

**下一步：**

- 关注 GitHub Issues 反馈
- 准备 v0.2.0 的新特性
- 持续改进文档

🛡️ **Let's make AI-assisted development safer, together!**
