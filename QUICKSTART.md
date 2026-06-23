# 🚀 Aegis Box - 快速开始指南

从零到运行，**3 分钟**看到效果。

---

## 📋 前置要求

- Python 3.9+
- pip 或 uv
- Git（可选，用于沙盒保护）
- API Keys（至少一个）:
  - Anthropic API Key（推荐）
  - OpenAI API Key
  - Zhipu API Key

---

## ⚡ 3 分钟快速上手

### Step 1: 安装（30 秒）

```bash
pip install aegis-box
```

或使用 uv（更快）：

```bash
uv pip install aegis-box
```

---

### Step 2: 初始化配置（60 秒）

```bash
# 进入你的项目目录
cd your-project

# 初始化配置
aegis init
```

这会在项目根目录生成 `aegis.yaml` 配置文件。

---

### Step 3: 配置 API Keys（60 秒）

编辑 `aegis.yaml`：

```yaml
version: "1.0"

# 三级模型配置
llm:
  tier1_fast:
    provider: "zhipu"
    model: "glm-4-air"
    api_key_env_var: "ZHIPU_API_KEY"

  tier2_reasoning:
    provider: "anthropic"
    model: "claude-3-5-haiku-20241022"
    api_key_env_var: "ANTHROPIC_API_KEY"

  tier3_patching:
    provider: "anthropic"
    model: "claude-3-5-sonnet-20241022"
    api_key_env_var: "ANTHROPIC_API_KEY"
```

设置环境变量：

```bash
export ANTHROPIC_API_KEY="sk-ant-xxx"
export ZHIPU_API_KEY="xxx"
```

**提示**：你可以只配置一个 API Key，Aegis 会自动使用该模型。

---

### Step 4: 一键运行（30 秒）

```bash
aegis run --auto
```

**就这么简单！** Aegis 会自动：

1. 🧹 清扫垃圾文件
2. 🔍 提取代码架构
3. 🏛️ 审计安全漏洞
4. 🩹 自动生成修复补丁
5. 🔄 同步上下文到 IDE

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

## 🔧 常见问题

### Q1: 没有 API Key 怎么办？

**A**: Aegis 支持多个 LLM 提供商，你至少需要一个：

- **Anthropic** (推荐): https://console.anthropic.com/
- **OpenAI**: https://platform.openai.com/
- **Zhipu**: https://open.bigmodel.cn/

如果你只有一个 API Key，可以配置所有三级模型使用同一个：

```yaml
llm:
  tier1_fast:
    provider: "anthropic"
    model: "claude-3-5-haiku-20241022"
    api_key_env_var: "ANTHROPIC_API_KEY"

  tier2_reasoning:
    provider: "anthropic"
    model: "claude-3-5-haiku-20241022"
    api_key_env_var: "ANTHROPIC_API_KEY"

  tier3_patching:
    provider: "anthropic"
    model: "claude-3-5-sonnet-20241022"
    api_key_env_var: "ANTHROPIC_API_KEY"
```

---

### Q2: 运行很慢怎么办？

**A**: 可能的原因：

1. **网络问题**: 检查是否能访问 LLM API
2. **Token 过多**: 项目太大，考虑调整忽略规则
3. **速率限制**: 降低 `rate_limit.global_qps`

**优化建议**：

```yaml
# 忽略大文件/目录
ignore_dirs:
  - "node_modules"
  - "venv"
  - ".git"
  - "dist"
  - "build"

ignore_extensions:
  - ".pyc"
  - ".log"
  - ".lock"

# 降低速率限制
rate_limit:
  global_qps: 5 # 降低到 5
```

---

### Q3: 补丁应用失败怎么办？

**A**: Aegis 有自动回滚机制，不会损坏源文件。

失败原因：

1. **代码上下文不匹配**: 文件已被修改
2. **语法错误**: LLM 生成的补丁有问题

**解决方案**：

```bash
# 重新运行（会自动重试）
aegis run --continue

# 或者手动修复
aegis patch --review  # 查看 diff
```

---

### Q4: 如何在 CI/CD 中使用？

**A**: 参考 GitHub Actions 示例：

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

      - name: Run Security Audit
        run: aegis audit --ci-mode --output audit-report.md
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

---

### Q5: 如何自定义忽略规则？

**A**: 编辑 `aegis.yaml`：

```yaml
ignore_dirs:
  - ".git"
  - "node_modules"
  - "venv"
  - "my-custom-dir" # 自定义目录

ignore_extensions:
  - ".pyc"
  - ".log"
  - ".custom" # 自定义扩展名

ignore_patterns:
  - "*.min.js" # 忽略压缩文件
  - "*.generated.*" # 忽略生成的文件
```

---

## 📚 更多资源

- **完整文档**: [README.md](../README.md)
- **CLI 命令手册**: [docs/COMMANDS.md](COMMANDS.md)
- **发布检查清单**: [RELEASE.md](../RELEASE.md)
- **架构文档**: [docs/ARCHITECTURE_REVIEW.md](ARCHITECTURE_REVIEW.md)
- **GitHub**: https://github.com/nexo/aegis-box
- **Issues**: https://github.com/nexo/aegis-box/issues

---

## 🎉 完成！

恭喜！你已经成功运行了 Aegis Box。

**接下来**：

1. ✅ 查看审计报告
2. ✅ 在 IDE 中验证
3. ✅ 集成到 CI/CD
4. ✅ 分享给团队

**有问题？** 欢迎在 GitHub Issues 提问：https://github.com/nexo/aegis-box/issues

---

**🛡️ Aegis Box - 让 AI 辅助开发更安全、更高效！**
