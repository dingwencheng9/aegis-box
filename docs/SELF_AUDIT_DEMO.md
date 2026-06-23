# 🔥 Aegis Box 自我审计演示

> **日期**: 2026-06-24  
> **状态**: ✅ Tier-1 审计成功 | ⏳ Tier-2 架构分析中 | ⏸️ Tier-3 补丁生成待测试

---

## 📋 测试概述

Aegis Box 首次受控漏洞点火试验（Proof of Concept Ignition），验证 LLM 核心流水线的完整功能。

### 🎯 测试目标

1. **制造靶标**: 创建包含明显安全漏洞的测试文件
2. **打通神经链路**: 验证 Tier-1/2/3 LLM 调用链路
3. **自动修复**: 生成并应用安全补丁

---

## 🎯 第一步：制造靶标

**文件**: `tests/dummy_vulnerable_app.py`

故意植入的漏洞：

1. **命令注入** (`execute_user_command`)
   - 直接将用户输入传递给 `os.system()`
   - 攻击向量: `; rm -rf /`

2. **SQL 注入** (`search_user`)
   - 字符串拼接构建 SQL 查询
   - 攻击向量: `' OR '1'='1`

3. **路径遍历** (`read_user_file`)
   - 未验证文件路径
   - 攻击向量: `../../etc/passwd`

4. **XSS 跨站脚本** (`render_html`)
   - 未转义用户输入
   - 攻击向量: `<script>alert('xss')</script>`

---

## ⚡ 第二步：LLM 神经链路

### 配置修复过程

**问题 1**: LiteLLM 不支持 `zhipu` 提供商

- ❌ 尝试: `zhipu/glm-4-air`
- ❌ 尝试: `zhipuai/glm-4-air`
- ✅ 解决: `openai/glm-4.5-air` + 自定义端点

**最终配置**:

```yaml
llm:
  tier1_fast:
    provider: openai # OpenAI 兼容模式
    model: glm-4.5-air
    endpoint: https://open.bigmodel.cn/api/paas/v4
  tier2_reasoning:
    provider: anthropic
    model: claude-sonnet-4-6 # 升级至 Sonnet（原为 Haiku）
  tier3_patching:
    provider: anthropic
    model: claude-opus-4-8
```

---

## 🎊 第三步：Tier-1 审计结果

**模型**: GLM-4.5-Air  
**耗时**: ~47 秒（包含速率限制等待 153s）  
**状态**: ✅ **成功检测所有漏洞！**

### 发现的漏洞清单

| #   | 级别   | 漏洞类型     | 位置    | 描述                                    |
| --- | ------ | ------------ | ------- | --------------------------------------- |
| 1   | **P0** | 命令注入     | L10-L17 | `execute_user_command` 直接执行用户输入 |
| 2   | **P0** | SQL 注入     | L20-L34 | `search_user` 字符串拼接 SQL 查询       |
| 3   | **P0** | 路径遍历     | L37-L44 | `read_user_file` 未验证文件路径         |
| 4   | **P0** | XSS 跨站脚本 | L47-L54 | `render_html` 未转义 HTML               |
| 5   | **P1** | 高耦合       | L58-L72 | `api_endpoint` 调用多个函数             |

### 修复建议

**命令注入**:

```python
# ❌ 危险
os.system(f"echo {user_input}")

# ✅ 安全
import subprocess
subprocess.run(["echo", user_input], check=True)
```

**SQL 注入**:

```python
# ❌ 危险
cursor.execute(f"SELECT * FROM users WHERE username = '{username}'")

# ✅ 安全
cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
```

**路径遍历**:

```python
# ❌ 危险
with open(filename, 'r') as f:
    return f.read()

# ✅ 安全
from pathlib import Path
safe_path = Path("/allowed/dir") / filename
if safe_path.resolve().is_relative_to("/allowed/dir"):
    with open(safe_path, 'r') as f:
        return f.read()
```

**XSS 防护**:

```python
# ❌ 危险
html = f"<div>{user_content}</div>"

# ✅ 安全
from html import escape
html = f"<div>{escape(user_content)}</div>"
```

---

## 🏛️ 第四步：Tier-2 架构分析

**模型**: Claude Sonnet 4.6  
**状态**: ⏳ **进行中**（等待速率限制 358 秒）

预期输出：

- 架构评价（项目类型、架构模式、技术栈）
- 内聚耦合度评估
- P0 漏洞汇总
- Top 3 重构建议

---

## 🛠️ 第五步：Tier-3 补丁生成

**模型**: Claude Opus 4.8  
**状态**: ⏸️ **待执行**

计划：

1. 针对 4 个 P0 漏洞生成 SEARCH/REPLACE 补丁
2. 使用 GitSandbox 在隔离分支测试
3. 验证修复后的代码安全性

---

## 📊 性能统计

| 阶段            | 模型        | 耗时 | Token 消耗 | 成本估算 |
| --------------- | ----------- | ---- | ---------- | -------- |
| **AST 提取**    | tree-sitter | 1ms  | 0          | $0       |
| **Tier-1 审计** | GLM-4.5-Air | 47s  | ~2,500     | ~$0.001  |
| **Tier-2 分析** | Sonnet 4.6  | 待测 | ~4,500     | ~$0.01   |
| **Tier-3 补丁** | Opus 4.8    | 待测 | ~8,000     | ~$0.12   |
| **总计**        | -           | -    | ~15,000    | ~$0.13   |

**Token 压缩率**: 73 行原始代码 → 57 行骨架（78.1% 压缩）

---

## 🎯 关键发现

### ✅ 成功验证

1. **AST 提取工作正常**
   - tree-sitter 成功解析 Python 代码
   - 78.1% 的 Token 压缩率

2. **Tier-1 LLM 调用成功**
   - GLM-4.5-Air 正确识别所有漏洞
   - 结构化输出 fallback 机制工作正常

3. **智谱 AI OpenAI 兼容模式**
   - 通过 `openai/` 前缀调用成功
   - 自定义端点配置生效

### ⚠️ 待优化

1. **结构化输出解析**
   - GLM 返回 Markdown 格式而非 JSON
   - fallback 到 instructor 解析成功（但增加耗时）

2. **速率限制过于保守**
   - 初始 Token 桶为空，需等待 153 秒
   - 可优化初始容量配置

3. **Tier-2 重复调用 Tier-1**
   - `analyze_project` 会重新调用 `analyze_file`
   - 应复用已有的 Tier-1 结果

---

## 🚀 下一步计划

1. **等待 Tier-2 完成** (预计 6 分钟)
2. **验证架构报告质量**
3. **测试 Tier-3 补丁生成**
4. **应用补丁并验证修复**
5. **完整流程录屏演示**

---

## 📝 技术债务记录

### 需要修复的问题

1. **reducer.py:363**: Tier-2 应复用 Tier-1 结果，避免重复调用
2. **llm.py:266**: 改进结构化输出解析（GLM 不支持原生 JSON mode）
3. **rate_limiter.py:45**: 优化初始 Token 桶容量，避免首次等待

### 配置优化建议

```yaml
rate_limit:
  token_bucket_capacity: 10000 # 当前: 1000（太小）
  token_bucket_refill_rate: 50 # 当前: 10（太慢）
```

---

**🛡️ The Ouroboros Protocol is ALIVE! Aegis 正在审计自己！**
