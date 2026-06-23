# 🚀 Aegis Box - Quick Start Guide

From zero to results in **3 minutes**.

---

## 📋 Prerequisites

- Python 3.9+
- pip or uv
- **One API Key** (choose one):
  - **Anthropic** (recommended): Free credits at [console.anthropic.com](https://console.anthropic.com/)
  - **智谱 AI** (cost-effective): Free tier at [open.bigmodel.cn](https://open.bigmodel.cn/)
  - **OpenAI** (alternative): Credits at [platform.openai.com](https://platform.openai.com/)

---

## ⚡ 3-Minute Setup

### Step 1: Install (30 seconds)

```bash
pip install aegis-box
```

Or with uv (faster):

```bash
uv pip install aegis-box
```

---

### Step 2: Get Your API Key (60 seconds)

#### Option A: Anthropic (Recommended)

1. Visit [console.anthropic.com](https://console.anthropic.com/)
2. Sign up (free credits included)
3. Go to **API Keys** → **Create Key**
4. Copy your key (starts with `sk-ant-`)

#### Option B: 智谱 AI (Cost-Effective)

1. Visit [open.bigmodel.cn](https://open.bigmodel.cn/)
2. 注册账号（免费额度）
3. 进入 **API 管理** → **创建 API Key**
4. 复制密钥

#### Option C: OpenAI

1. Visit [platform.openai.com](https://platform.openai.com/)
2. Sign up and add credits
3. Go to **API Keys** → **Create new secret key**
4. Copy your key (starts with `sk-`)

---

### Step 3: Configure (30 seconds)

```bash
# Copy the example config
cp .env.example .env

# Edit .env with your favorite editor
nano .env  # or vim, code, etc.
```

**Add your API key** (uncomment and fill one):

```bash
# For Anthropic
ANTHROPIC_API_KEY=sk-ant-your-key-here

# For 智谱 AI
ZHIPU_API_KEY=your-zhipu-key-here

# For OpenAI
OPENAI_API_KEY=sk-your-openai-key-here
```

**That's it!** You don't need to edit `aegis.yaml` — it reads from `.env` automatically.

---

### Step 4: Run (30 seconds)

```bash
# Go to your project
cd your-project

# Initialize
aegis init

# Run full audit
aegis run --auto
```

**Done!** Aegis will:

1. 🧹 Sweep garbage files
2. 🔍 Extract code architecture (90% compressed)
3. 🏛️ Audit security vulnerabilities
4. 🩹 Generate and apply fixes
5. 🔄 Sync context to your IDE

---

## 📊 运行效果示例

```bash
$ aegis run --auto

🚀 启动 Aegis 全链路编排...
⚡ 自动批准模式：将跳过所有确认步骤

================================================================================
🧹 资产清扫
================================================================================
[INFO] 扫描文件: 1000
[INFO] 清理文件: 50 (.pyc, .log, __pycache__)
[INFO] 释放空间: 100 MB
✅ 步骤完成: sweep (2.1s)

================================================================================
🔍 架构审计
================================================================================
[INFO] 提取代码骨架: 50 个文件
[INFO] Token 压缩率: 90% (500k → 50k tokens)
[INFO] 发现漏洞: 3
  ├─ 关键: 1 (SQL injection in user_service.py)
  ├─ 高危: 2 (Weak password hashing, XSS vulnerability)
  └─ 中危: 0
✅ 步骤完成: reduce (15.3s)

================================================================================
🛠️  智能修复
================================================================================
[INFO] 生成修复补丁: 3 个
[INFO] 应用补丁:
  ✅ user_service.py (SQL injection → parameterized query)
  ✅ auth_handler.py (MD5 → bcrypt)
  ❌ template.html (XSS → failed to match context)
[INFO] 修复成功: 2
[INFO] 修复失败: 1
[INFO] 成功率: 67%
✅ 步骤完成: patch (8.7s)

================================================================================
🔄 上下文同步
================================================================================
[INFO] 生成 IDE 上下文
[INFO] 目标文件: .cursorrules
[INFO] 注入规则:
  - SQL injection 预防
  - 密码哈希强度要求
  - XSS 预防提示
[INFO] 注入成功: true
✅ 步骤完成: context_sync (1.2s)

================================================================================
📊 执行汇总
================================================================================
会话 ID: 20260623-150000
开始时间: 2026-06-23T15:00:00
结束时间: 2026-06-23T15:00:27
总耗时: 27.3 秒
最终状态: success

步骤详情:
  ✅ sweep: success (2.1s)
  ✅ reduce: success (15.3s)
  ✅ patch: success (8.7s)
  ✅ context_sync: success (1.2s)

汇总统计:
  总步骤数: 4
  成功: 4
  失败: 0

  扫描文件: 1000
  清理文件: 50
  发现漏洞: 3
  修复漏洞: 2
  释放空间: 100 MB
  Token 消耗: 50k
  预估成本: $0.15
================================================================================

✅ Aegis 全链路编排完成！

📝 查看详细报告:
  - 状态文件: artifacts/aegis_state.json
  - IDE 规则: .cursorrules
```

---

## 🎯 下一步

### 1. 查看审计报告

```bash
# 查看状态文件
cat artifacts/aegis_state.json

# 查看 IDE 规则
cat .cursorrules
```

---

### 2. 在 IDE 中验证

**Cursor / Claude Code 会自动加载 `.cursorrules`**

打开项目，尝试写一段有 SQL 注入风险的代码：

```python
def get_user(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return db.execute(query)
```

**IDE 会实时提示**：

```
⚠️  [Aegis] 检测到 SQL 注入风险
建议：使用参数化查询
```

---

### 3. 运行其他命令

```bash
# 仅审计（不修复）
aegis audit

# 仅清扫垃圾
aegis sweep --dry-run  # 预览
aegis sweep --execute  # 执行

# 仅修复指定文件
aegis patch user_service.py auth_handler.py

# 仅同步上下文
aegis context-sync

# 显示配置
aegis config show

# 显示版本
aegis version
```

---

## 🔧 FAQ

### Q1: I don't have an API key yet

**A**: No problem! Get free credits:

- **Anthropic** (recommended): [console.anthropic.com](https://console.anthropic.com/) — Free $5 credits
- **智谱 AI** (cost-effective): [open.bigmodel.cn](https://open.bigmodel.cn/) — Free tier included
- **OpenAI**: [platform.openai.com](https://platform.openai.com/) — $5 free trial

Just pick one, sign up, and you're ready in 60 seconds.

---

### Q2: Can I use only one API key?

**A**: Yes! Aegis works with a single provider. Just set one key in `.env`:

```bash
# Use Anthropic for all tiers (recommended)
ANTHROPIC_API_KEY=sk-ant-xxxxx
```

Aegis will automatically use this key for all operations.

---

### Q3: It's running slowly

**A**: Possible causes:

1. **Network issues**: Check your connection to the LLM API
2. **Large project**: Add more ignore patterns in `.env`
3. **Rate limits**: Reduce request rate

**Quick fix**:

```bash
# In .env, add:
AEGIS_GLOBAL_QPS=5  # Reduce from default 10
```

---

### Q4: Patch failed to apply

**A**: Don't worry! Aegis has auto-rollback — your code is safe.

**Why it happens**:

- Code context mismatch (file was modified)
- LLM generated incorrect patch

**Solution**:

```bash
# Retry automatically
aegis run --continue

# Or review manually
aegis patch --review
```

---

### Q5: How do I use this in CI/CD?

**A**: GitHub Actions example:

```yaml
# .github/workflows/aegis-audit.yml
name: Aegis Security Audit

on: [push, pull_request]

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: "3.9"

      - name: Install Aegis
        run: pip install aegis-box

      - name: Run Audit
        run: aegis audit --ci-mode --output report.md
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

Store your API key in **Settings → Secrets → Actions**.

---

### Q6: Can I use local models (Ollama)?

**A**: Yes! For 100% offline operation:

```bash
# In .env
TIER1_FAST_PROVIDER=ollama
TIER1_FAST_MODEL=llama3:8b

TIER2_REASONING_PROVIDER=ollama
TIER2_REASONING_MODEL=codellama:34b

OLLAMA_BASE_URL=http://localhost:11434
```

See [.env.example](.env.example) for full Ollama config.

---

## 📚 More Resources

- **Full Documentation**: [README.md](README.md)
- **CLI Commands**: Run `aegis --help`
- **Advanced Configuration**: See [.env.example](.env.example)
- **GitHub**: [github.com/dingwencheng9/aegis-box](https://github.com/dingwencheng9/aegis-box)
- **Issues**: [github.com/dingwencheng9/aegis-box/issues](https://github.com/dingwencheng9/aegis-box/issues)

---

## 🎉 You're All Set!

Congrats! You've successfully run Aegis Box.

**Next steps**:

1. ✅ Check the audit report (`artifacts/aegis_state.json`)
2. ✅ Verify in your IDE (`.cursorrules` is auto-loaded)
3. ✅ Integrate into CI/CD
4. ✅ Share with your team

**Questions?** Open an issue on [GitHub](https://github.com/dingwencheng9/aegis-box/issues) — we're here to help!

---

**🛡️ Aegis Box - Making AI-assisted development safer, together.**
