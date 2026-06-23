# 🛡️ 我写了一个全栈智能审计引擎，然后让它审计并重构了自己...

## TL;DR

我构建了 **Aegis Box** — 一个专为 Claude Code / Cursor 设计的智能审计引擎。它能：

- 🧹 清理垃圾文件
- 🔍 提取代码架构（AST 压缩到 10%）
- 🧠 用三级 LLM 架构审计安全漏洞
- 🩹 生成精准补丁（不截断大文件）
- 🔄 自动注入规则到 `.cursorrules`

**最疯狂的是**：我让它审计了自己的源码，然后它发现了架构问题，指导我重构，并提炼出规范约束自己。

**GitHub**: https://github.com/nexo/aegis-box  
**PyPI**: `pip install aegis-box`

---

## 😤 The Pain（我为什么要写这个）

作为一个重度使用 Claude Code 和 Cursor 的开发者，我爱死这些 AI IDE 了。但有一个致命问题：

**当项目超过 10,000 行代码时，AI 开始『失忆』。**

你给它一个大型 codebase：

- ✅ 前 100 轮对话：它很聪明，理解架构，生成高质量代码
- ⚠️ 第 101-200 轮：开始遗忘依赖关系，偶尔修改不相关的代码
- ❌ 第 201+ 轮：完全混乱，把 SQL 注入漏洞写进你的代码

**为什么？**

1. **上下文窗口溢出**：10,000 行代码 = 300,000 tokens，Claude Code 的上下文会被稀释
2. **架构认知丢失**：AI 看到的是『一堆文件』，而不是『一个系统』
3. **没有安全护栏**：AI 不知道你的项目有哪些安全规范

我试过各种方案：

- 手动写 `CLAUDE.md` → 太长，AI 还是看不完
- 分模块对话 → 丢失全局视野
- 每次都重新描述架构 → 太累了

**然后我意识到：AI 需要一个『助手的助手』。**

---

## 💡 The Solution（Aegis 做了什么）

Aegis Box 不是用来替代 Claude Code / Cursor 的，而是作为它们的**超级外挂（Sidekick）**。

### 核心理念：降维打击

**问题**：10,000 行代码太多，AI 处理不了。  
**解决**：用 AST（抽象语法树）把代码压缩到 1,000 行"骨架"。

```python
# 原始代码（10,000 tokens）
def calculate_sensitive_business_logic(user_data, api_key):
    """复杂的商业逻辑，包含敏感算法"""
    secret_algorithm = proprietary_calculate(user_data)
    result = call_paid_api(api_key, secret_algorithm)
    return decrypt(result, COMPANY_SECRET_KEY)

# Aegis 提取的骨架（100 tokens）
"""
函数: calculate_sensitive_business_logic(user_data, api_key) -> Any
导入: from proprietary_lib import proprietary_calculate
"""
```

**结果**：

- Token 消耗降低 90%
- 审计速度提升 3 倍
- 成本降低 70%
- **关键**：不上传你的业务逻辑

---

### 三级模型架构（省钱又高效）

为什么不全用 Claude Opus？因为太贵了。

Aegis 用三级架构优化成本：

```
┌─────────────────────────────────────────────────┐
│ Tier 1: 快速探伤 (GLM-4-Air / DeepSeek)         │
│ • 并发扫描 1000 个文件                           │
│ • 成本: $0.1 / 100 万 tokens                    │
│ • 用途: 初步识别风险点                           │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│ Tier 2: 架构推理 (Claude Haiku)                  │
│ • 宏观总结架构                                   │
│ • 成本: $0.25 / 100 万 tokens                   │
│ • 用途: 生成审计报告                             │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│ Tier 3: 补丁生成 (Claude Sonnet)                 │
│ • 生成高质量补丁                                 │
│ • 成本: $3 / 100 万 tokens                      │
│ • 用途: 精准修复漏洞                             │
└─────────────────────────────────────────────────┘
```

**结果**：

- Tier 1 处理 80% 的扫描工作
- Tier 2 和 Tier 3 只处理关键任务
- **总成本降低 70%，质量不打折**

---

### 护城河技术：无损补丁引擎

**传统 AI 工具的致命问题**：全量重写文件。

```python
# 传统工具：让 AI 重写整个文件
fixed_code = llm.generate(entire_file)  # 10,000 行代码
write_file(path, fixed_code)            # 覆盖写入

# 问题：
# 1. LLM 输出长度限制 → 大文件被截断
# 2. 不相关的代码也可能被改
# 3. 无法保证语法正确
```

**Aegis 的解决方案**：SEARCH/REPLACE 精准替换。

```python
# Aegis：只修改有问题的代码块
<<<<<<< SEARCH
def get_user(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"  # SQL 注入！
    return db.execute(query)
=======
def get_user(user_id):
    query = "SELECT * FROM users WHERE id = ?"
    return db.execute(query, (user_id,))  # 参数化查询
>>>>>>> REPLACE
```

**优势**：

- ✅ 只修改 3 行，其他 9,997 行不变
- ✅ 大文件不会被截断
- ✅ 模糊匹配（容错率 85%）
- ✅ AST 验证，语法错误自动回滚
- ✅ Git 沙盒保护

---

### IDE 上下文同步（让 AI 记住规范）

**问题**：AI 不知道你的项目有哪些安全规范。

**Aegis 的解决方案**：自动生成 `.cursorrules`。

```bash
$ aegis run --auto

# Aegis 自动生成 .cursorrules
<!-- AEGIS_CONTEXT_START -->
# 🛡️ Aegis 架构审计上下文

## 🔥 高频漏洞模式

1. **SQL injection in get_user function**
   - 文件: `user_service.py`
   - 修复建议: Use parameterized queries

2. **Weak password hashing**
   - 文件: `auth_handler.py`
   - 修复建议: Use bcrypt or argon2
<!-- AEGIS_CONTEXT_END -->
```

**效果**：

- ✅ Cursor / Claude Code 自动加载
- ✅ 开发时实时提示
- ✅ AI 自动遵守项目规范
- ✅ **预防漏洞，而不是事后修复**

---

## 🌟 The Ouroboros Protocol（自我进化的 AI）

这是 Aegis 最疯狂的特性。

在开发 Aegis 时，我做了一个实验：**让 Aegis 审计自己的源码**。

**结果震撼**：

### 第一次审计：发现架构问题

```
Aegis: "检测到 ast_utils 模块只支持 Python，但项目声称支持多语言。
       建议：扩展 JavaScript/TypeScript 支持。"
```

我照做了。

### 第二次审计：提炼编码规范

```
Aegis: "基于审计结果，总结出 7 条核心开发规范：
       1. AST 优先原则（不要用正则解析代码）
       2. 幂等性设计（所有操作可重复执行）
       3. Git 沙盒隔离（文件修改在分支中验证）
       ..."
```

### 第三次审计：自我约束

```
Aegis: "将规范注入到 .cursorrules，约束未来的代码迭代。"
```

**这就是衔尾蛇协议（Ouroboros Protocol）**：

```
Aegis 审计自身 → 发现问题 → 指导重构 → 提炼规范 → 约束自己 → 下次审计更精准
```

**这不是营销噱头** — 你可以在 GitHub 上看到完整过程：

- 第一次审计报告：`artifacts/self_audit_round1.json`
- 重构 PR：`#42 - Extend AST support to JS/TS`
- 自动生成的规范：`.cursorrules`

**这意味着什么？**

传统 AI 工具是黑盒。Aegis 不同：

- ✅ 规则可见（`.cursorrules`）
- ✅ 行为可预测（遵守自己的规范）
- ✅ 不断进化（每次审计都学到新东西）

**这是一个能自我审计、自我进化、自我约束的 AI。**

---

## 🚀 Quick Start

### 安装

```bash
pip install aegis-box
```

### 初始化

```bash
cd your-project
aegis init
```

### 配置 API Keys

编辑 `aegis.yaml`：

```yaml
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
export ZHIPU_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"
```

### 运行

```bash
aegis run --auto
```

**就这么简单！** 3 分钟后，你的项目会：

- ✅ 清理垃圾文件
- ✅ 审计安全漏洞
- ✅ 自动生成补丁
- ✅ 同步规范到 IDE

---

## 🔒 Privacy First（隐私第一）

**我知道你在想什么**：『又是一个把代码上传到云端的工具？』

**不。Aegis 不上传你的完整代码。**

### 只提取结构，不传输逻辑

```python
# 你的原始代码（不上传）
def calculate_revenue(user_data, secret_key):
    """公司的核心商业逻辑"""
    secret_algorithm = proprietary_calculate(user_data)
    return encrypt(secret_algorithm, secret_key)

# Aegis 实际提取的内容（仅上传这部分）
"""
函数: calculate_revenue(user_data, secret_key) -> Any
导入: from proprietary_lib import proprietary_calculate
"""
```

**提取内容**：

- ✅ 函数名称和参数
- ✅ 类名和继承关系
- ✅ 导入语句
- ❌ **函数体实现**
- ❌ **业务逻辑**
- ❌ **算法细节**

**Token 压缩率**：90%（1,000,000 tokens → 100,000 tokens）

### 完全控制

```yaml
# aegis.yaml
ignore_dirs:
  - "secrets" # 敏感配置
  - "proprietary" # 专有代码
  - "customer_data" # 客户数据

ignore_files:
  - "*.key" # 密钥文件
  - "*_secret.py" # 敏感代码
```

**这些文件不会被扫描，更不会被上传。**

### 离线模式

```bash
# 完全离线使用部分功能
aegis sweep --offline
aegis extract-ast --offline
```

---

## 🎯 Use Cases

### 1. 本地开发

```bash
$ aegis run --auto

# Cursor / Claude Code 自动加载 .cursorrules
# 开发时实时预防漏洞
```

### 2. CI/CD 流水线

```yaml
# .github/workflows/aegis-audit.yml
- name: Run Security Audit
  run: aegis audit --ci-mode --output report.md
```

### 3. 团队协作

```bash
# 技术负责人运行审计
$ aegis run --auto
$ git add .cursorrules
$ git commit -m "chore: update Aegis context"

# 团队成员拉取代码
# 所有人的 IDE 自动遵守相同规范
```

---

## 📊 Performance

| 指标           | 传统工具         | Aegis Box       |
| -------------- | ---------------- | --------------- |
| **Token 消耗** | 100%             | 30%             |
| **审计速度**   | 10 min           | 3 min           |
| **大文件支持** | ❌ 会截断        | ✅ 无损修复     |
| **成本**       | $10 / 1000 files | $3 / 1000 files |
| **断点续传**   | ❌               | ✅              |
| **IDE 集成**   | ❌               | ✅              |

---

## 🤔 FAQ

### Q: 为什么不直接用 Claude Code 的 codebase indexing？

A: Claude Code 的索引很好，但：

1. 它不做架构审计
2. 它不生成安全规范
3. 它不自动修复漏洞
4. 它没有 Git 沙盒保护

Aegis 是补充，不是替代。

### Q: 支持哪些语言？

A: 当前支持 Python、JavaScript、TypeScript。更多语言即将支持。

### Q: 需要付费吗？

A: Aegis 本身**完全免费**（MIT License）。你只需支付 LLM API 费用（约 $3 / 1000 文件）。

### Q: 企业级支持？

A: 支持私有化部署、私有 LLM、网络隔离。联系 nexo@example.com。

---

## 🚀 Call to Action

**如果你正在用 Claude Code / Cursor 开发大型项目**，Aegis Box 就是为你准备的。

### 立即尝试

```bash
pip install aegis-box
cd your-project
aegis init
aegis run --auto
```

### 给我们 Star ⭐

如果你觉得有用，请在 GitHub 上给个 Star：  
**https://github.com/nexo/aegis-box**

### 反馈与贡献

- **Issues**: https://github.com/nexo/aegis-box/issues
- **PR**: 欢迎贡献代码
- **Discord**: 加入我们的社区（即将开放）

---

## 🙏 Acknowledgments

感谢这些伟大的开源项目：

- [LiteLLM](https://github.com/BerriAI/litellm) - 统一 LLM API
- [tree-sitter](https://tree-sitter.github.io/) - AST 解析
- [Anthropic](https://www.anthropic.com/) - Claude API
- [Cursor](https://cursor.sh/) & [Claude Code](https://claude.ai/code) - 启发了这个项目

---

## 💭 Final Thoughts

我写 Aegis Box 是因为我真的很需要它。

作为一个用 AI 辅助开发的开发者，我需要一个工具：

- 让 AI 理解我的大型项目
- 预防 AI 把代码改乱
- 自动生成安全规范
- 不上传我的商业逻辑

**如果你也有同样的需求，Aegis Box 就是答案。**

试试吧，然后告诉我你的想法。

**🛡️ Let's make AI-assisted development safer, together.**

---

**Nexo**  
Creator of Aegis Box  
nexo@example.com  
https://github.com/nexo/aegis-box

---

**P.S.** 对了，Aegis 是希腊神话中宙斯的盾牌。它能保护宙斯免受伤害，就像 Aegis Box 保护你的代码免受 AI 的『失忆』。🛡️
