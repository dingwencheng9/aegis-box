# 🚀 LLM 客户端使用指南

## 📋 概述

`aegis/core/llm.py` 提供了统一的大语言模型调用接口，支持：

- ✅ 多提供商（OpenAI, Anthropic, Zhipu, Ollama）
- ✅ 结构化输出（Pydantic 模型）
- ✅ 三层速率限制
- ✅ 熔断与降级机制
- ✅ 自动重试
- ✅ Token 估算

---

## 🎯 快速开始

### 1. 基础文本调用

```python
from aegis.cli import ConfigManager
from aegis.core.llm import LLMClientFactory

# 加载配置
config = ConfigManager.load()

# 创建工厂
factory = LLMClientFactory(config)

# 创建 Tier-1 客户端（快速探伤）
tier1 = factory.create_tier1_client()

# 调用
response = await tier1.chat("请用一句话介绍 Python")
print(response)
# 输出: "Python 是一门简洁优雅的解释型高级编程语言。"
```

### 2. 结构化输出（Pydantic）

```python
from pydantic import BaseModel
from typing import List

# 定义输出结构
class CodeSummary(BaseModel):
    responsibility: str
    code_smells: List[str]
    priority_todos: List[str]

# 调用（强制返回 JSON）
summary = await tier1.chat(
    prompt="分析以下代码骨架...",
    response_model=CodeSummary,
    system_prompt="你是一个代码审查专家"
)

# 类型安全的访问
print(summary.responsibility)  # ✅ IDE 自动补全
print(summary.code_smells)      # ✅ 类型检查
```

### 3. 三个层级的客户端

```python
# Tier-1: 快速探伤（GLM-4-Air）
tier1 = factory.create_tier1_client()
result1 = await tier1.chat("快速分析")

# Tier-2: 架构推理（Claude-3.5-Haiku）
tier2 = factory.create_tier2_client()
result2 = await tier2.chat("深度分析架构")

# Tier-3: 补丁生成（Claude-3.5-Sonnet）
tier3 = factory.create_tier3_client()
result3 = await tier3.chat("生成高质量补丁")
```

---

## 📊 核心特性详解

### 1. 自动速率限制

```python
# 三层速率限制自动生效
# Layer 1: 全局 QPS（每秒 10 请求）
# Layer 2: Provider 限制（Anthropic 40/分钟）
# Layer 3: Token 桶（平滑突发流量）

# 无需手动管理，自动阻塞等待
response = await tier1.chat("...")  # 自动等待配额
```

### 2. 熔断与降级

```python
# 连续失败 3 次后自动熔断
try:
    response = await tier1.chat("...")
except CircuitBreakerOpenError as e:
    print(f"服务熔断: {e}")
    # 可以切换到备用模型
    response = await tier2.chat("...")
```

### 3. 统计信息

```python
# 获取客户端统计
stats = tier1.get_stats()
print(stats)
# {
#     "total_calls": 100,
#     "success_calls": 95,
#     "failed_calls": 5,
#     "success_rate": "95.0%",
#     "total_tokens": 50000,
#     "circuit_state": "closed",
#     "model_id": "zhipu/glm-4-air"
# }

# 获取速率限制器统计
limiter_stats = factory.get_rate_limiter_stats()
print(limiter_stats)
# {
#     "total_requests": 100,
#     "total_tokens": 50000,
#     "provider_counts": {
#         "zhipu": 50,
#         "anthropic": 50
#     }
# }
```

---

## 🛠️ 高级用法

### 1. 自定义参数

```python
response = await tier1.chat(
    prompt="你的问题",
    system_prompt="你是一个专家",
    temperature=0.3,     # 更确定性的输出
    max_tokens=2000,     # 限制输出长度
)
```

### 2. 处理错误

```python
from aegis.core.llm import (
    CircuitBreakerOpenError,
    LLMTimeoutError,
    LLMAPIError,
)

try:
    response = await tier1.chat("...")
except CircuitBreakerOpenError:
    # 熔断器打开，切换模型
    print("模型熔断，使用备用方案")
except LLMTimeoutError:
    # 超时，重试或放弃
    print("请求超时")
except LLMAPIError as e:
    # API 调用失败
    print(f"API 错误: {e}")
```

### 3. 批量并发调用

```python
import asyncio

# 并发分析多个文件（Tier-1）
tasks = [
    tier1.chat(f"分析文件 {i}")
    for i in range(100)
]

# 速率限制自动控制并发
results = await asyncio.gather(*tasks)
```

---

## 🔧 配置示例

### aegis.yaml

```yaml
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

# 速率限制
rate_limit:
  global_qps: 10
  provider_limits:
    zhipu: 100
    anthropic: 40
```

### 环境变量

```bash
export ZHIPU_API_KEY="your-zhipu-key"
export ANTHROPIC_API_KEY="your-anthropic-key"
export OPENAI_API_KEY="your-openai-key"  # 可选
```

---

## 📖 完整示例：Reducer 集成

```python
from aegis.core.llm import LLMClientFactory
from aegis.cli import ConfigManager
from pydantic import BaseModel
from typing import List

# 定义输出结构
class FileSummary(BaseModel):
    """单文件摘要"""
    file_path: str
    responsibility: str
    code_smells: List[str]
    priority_todos: List[str]

async def analyze_file(skeleton: CodeSkeleton) -> FileSummary:
    """使用 Tier-1 分析单个文件"""

    # 初始化
    config = ConfigManager.load()
    factory = LLMClientFactory(config)
    tier1 = factory.create_tier1_client()

    # 构建 Prompt
    prompt = f"""
请分析以下代码骨架：

{skeleton.to_markdown()}

要求：
1. 这个文件的核心职责是什么？（1 句话）
2. 有哪些潜在的代码异味或漏洞？（列表）
3. 有哪些 TODO/FIXME 需要优先处理？（列表）
"""

    # 调用（结构化输出）
    try:
        summary = await tier1.chat(
            prompt=prompt,
            response_model=FileSummary,
            system_prompt="你是一个代码审查专家，专注于发现潜在问题",
            temperature=0.3,  # 更确定性
        )

        return summary

    except Exception as e:
        logger.error(f"分析失败: {e}")
        # 返回默认值
        return FileSummary(
            file_path=str(skeleton.file_path),
            responsibility="分析失败",
            code_smells=[],
            priority_todos=[]
        )

async def analyze_project(skeletons: List[CodeSkeleton]):
    """并发分析整个项目"""

    # 创建任务列表
    tasks = [analyze_file(skeleton) for skeleton in skeletons]

    # 并发执行（速率限制自动控制）
    summaries = await asyncio.gather(*tasks)

    # 过滤失败的
    valid_summaries = [s for s in summaries if s.responsibility != "分析失败"]

    print(f"成功分析: {len(valid_summaries)}/{len(skeletons)} 个文件")
    return valid_summaries
```

---

## 🐛 故障排查

### 问题 1: `API Key not found`

**解决方案**：

```bash
# 检查环境变量
echo $ANTHROPIC_API_KEY

# 设置环境变量
export ANTHROPIC_API_KEY="your-key"
```

### 问题 2: `熔断器打开`

**原因**：连续失败 3 次

**解决方案**：

```python
# 查看统计信息
stats = client.get_stats()
print(stats["failure_count"])

# 等待 60 秒后自动恢复
# 或手动切换到备用模型
```

### 问题 3: `Rate limit exceeded`

**原因**：并发过高

**解决方案**：

```yaml
# 降低 aegis.yaml 中的速率限制
rate_limit:
  global_qps: 5 # 从 10 降低到 5
```

---

## ✅ 最佳实践

### 1. 选择合适的 Tier

```python
# Tier-1: 快速、便宜，用于并发扫描
tier1 = factory.create_tier1_client()
for file in files:
    summary = await tier1.chat(f"分析 {file}")

# Tier-2: 中等推理，用于架构总结
tier2 = factory.create_tier2_client()
report = await tier2.chat("生成架构报告")

# Tier-3: 最强，用于补丁生成（不可逆操作）
tier3 = factory.create_tier3_client()
patch = await tier3.chat("生成补丁")
```

### 2. 使用结构化输出

```python
# ✅ 好：强制返回 JSON
class Output(BaseModel):
    result: str

output = await client.chat("...", response_model=Output)

# ❌ 坏：手动解析字符串
text = await client.chat("请以 JSON 格式输出...")
data = json.loads(text)  # 可能失败
```

### 3. 监控统计信息

```python
# 定期检查统计
stats = client.get_stats()
if stats["success_rate"] < "80.0%":
    logger.warning("成功率过低，检查配置")
```

---

## 📚 相关文档

- [PHASE2_PLAN.md](../PHASE2_PLAN.md) - Phase 2 开发计划
- [ARCHITECTURE_REVIEW.md](../ARCHITECTURE_REVIEW.md) - 架构审查报告
- [LiteLLM 文档](https://docs.litellm.ai/) - LiteLLM 官方文档

---

**🛡️ Aegis Box - 企业级 LLM 客户端封装**
