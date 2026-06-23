# 🎯 Aegis Box - 模型配置指南

## 📋 概述

Aegis Box 支持通过环境变量灵活配置 LLM 模型，适应不同的场景和需求。

---

## 🔧 环境变量配置

### Anthropic 模型配置

```bash
# .env 文件

# API Key 和端点
ANTHROPIC_API_KEY=your-api-key
ANTHROPIC_API_URL=https://cdn1.yunyi.yun/claude  # 可选

# 模型配置
ANTHROPIC_MODEL_TIER2=claude-3-haiku-20240307      # Tier 2: 架构推理
ANTHROPIC_MODEL_TIER3=claude-3-5-sonnet-20240620   # Tier 3: 补丁生成
```

### Zhipu AI 模型配置

```bash
# .env 文件

# API Key
ZHIPU_API_KEY=your-api-key

# 模型配置
ZHIPU_MODEL_TIER1=glm-4-air  # Tier 1: 快速探伤
```

---

## 📊 Aegis Box 三级架构

### Tier 1: 快速探伤（切片级并发检查）

**目标**: 快速扫描大量代码切片，识别潜在问题
**要求**: 速度快、成本低
**推荐模型**: GLM-4-Air

```bash
ZHIPU_MODEL_TIER1=glm-4-air
```

**模型选项**:

| 模型          | 速度   | 成本   | 质量       | 适用场景         |
| ------------- | ------ | ------ | ---------- | ---------------- |
| `glm-4-air`   | ⚡⚡⚡ | 💰     | ⭐⭐⭐     | 快速探伤（推荐） |
| `glm-4-flash` | ⚡⚡   | 💰💰   | ⭐⭐⭐⭐   | 平衡选择         |
| `glm-4`       | ⚡     | 💰💰💰 | ⭐⭐⭐⭐⭐ | 高质量探伤       |

### Tier 2: 架构推理（宏观总结）

**目标**: 理解代码架构，生成高层次总结
**要求**: 推理能力强、理解准确
**推荐模型**: Claude 3 Haiku

```bash
ANTHROPIC_MODEL_TIER2=claude-3-haiku-20240307
```

**模型选项**:

| 模型                         | 速度   | 成本     | 质量       | 适用场景             |
| ---------------------------- | ------ | -------- | ---------- | -------------------- |
| `claude-3-haiku-20240307`    | ⚡⚡⚡ | 💰💰     | ⭐⭐⭐⭐   | 快速架构分析（推荐） |
| `claude-3-sonnet-20240229`   | ⚡⚡   | 💰💰💰   | ⭐⭐⭐⭐⭐ | 深度架构分析         |
| `claude-3-5-sonnet-20240620` | ⚡     | 💰💰💰💰 | ⭐⭐⭐⭐⭐ | 最高质量             |

### Tier 3: 补丁生成（精确修复）

**目标**: 生成无损代码补丁
**要求**: 最高质量、精确性
**推荐模型**: Claude 3.5 Sonnet

```bash
ANTHROPIC_MODEL_TIER3=claude-3-5-sonnet-20240620
```

**模型选项**:

| 模型                         | 速度 | 成本       | 质量       | 适用场景             |
| ---------------------------- | ---- | ---------- | ---------- | -------------------- |
| `claude-3-5-sonnet-20240620` | ⚡   | 💰💰💰💰   | ⭐⭐⭐⭐⭐ | 精确补丁生成（推荐） |
| `claude-3-sonnet-20240229`   | ⚡⚡ | 💰💰💰     | ⭐⭐⭐⭐⭐ | 高质量补丁           |
| `claude-3-opus-20240229`     | ⚡   | 💰💰💰💰💰 | ⭐⭐⭐⭐⭐ | 最高质量（最贵）     |

---

## 🎯 推荐配置方案

### 方案 1: 成本优先（个人开发）

**配置**:

```bash
# 全部使用 GLM-4-Air
ZHIPU_MODEL_TIER1=glm-4-air
ANTHROPIC_MODEL_TIER2=claude-3-haiku-20240307
ANTHROPIC_MODEL_TIER3=claude-3-haiku-20240307
```

**成本**: ~¥1-2/天
**适用**: 个人项目、预算有限

### 方案 2: 平衡配置（推荐）

**配置**:

```bash
# Tier 1: GLM-4-Air (快速 + 便宜)
ZHIPU_MODEL_TIER1=glm-4-air

# Tier 2: Claude Haiku (快速 + 高质量)
ANTHROPIC_MODEL_TIER2=claude-3-haiku-20240307

# Tier 3: Claude 3.5 Sonnet (最高质量)
ANTHROPIC_MODEL_TIER3=claude-3-5-sonnet-20240620
```

**成本**: ~¥5-10/天
**适用**: 生产环境、中小型项目

### 方案 3: 质量优先（企业级）

**配置**:

```bash
# Tier 1: GLM-4 (高质量探伤)
ZHIPU_MODEL_TIER1=glm-4

# Tier 2: Claude 3.5 Sonnet
ANTHROPIC_MODEL_TIER2=claude-3-5-sonnet-20240620

# Tier 3: Claude 3.5 Sonnet
ANTHROPIC_MODEL_TIER3=claude-3-5-sonnet-20240620
```

**成本**: ~¥20-50/天
**适用**: 关键项目、安全要求高

### 方案 4: 单 API 配置（极简）

**配置 A - 只用智谱 AI**:

```bash
ZHIPU_MODEL_TIER1=glm-4-air
# 不设置 Anthropic 模型，Tier 2/3 也使用智谱 AI
```

**配置 B - 只用 Anthropic**:

```bash
ANTHROPIC_MODEL_TIER2=claude-3-haiku-20240307
ANTHROPIC_MODEL_TIER3=claude-3-5-sonnet-20240620
# 不设置智谱模型，Tier 1 也使用 Claude
```

---

## 🔄 模型降级策略

### 自动降级

如果配置的模型不可用，Aegis Box 会自动降级：

**Anthropic 降级顺序**:

1. 配置的模型 (ANTHROPIC_MODEL_TIER2/TIER3)
2. claude-3-5-sonnet-20240620
3. claude-3-sonnet-20240229
4. claude-3-haiku-20240307

**Zhipu AI 降级顺序**:

1. 配置的模型 (ZHIPU_MODEL_TIER1)
2. glm-4-air
3. glm-4-flash
4. glm-4

### 手动指定降级

```bash
# 在 .env 中设置多个备选模型
ANTHROPIC_MODEL_TIER2=claude-3-haiku-20240307
ANTHROPIC_MODEL_TIER2_FALLBACK=claude-3-sonnet-20240229

ZHIPU_MODEL_TIER1=glm-4-air
ZHIPU_MODEL_TIER1_FALLBACK=glm-4-flash
```

---

## 💰 成本计算

### 价格表

#### Anthropic (USD)

| 模型              | Input ($/1M tokens) | Output ($/1M tokens) |
| ----------------- | ------------------- | -------------------- |
| Claude 3 Haiku    | $0.25               | $1.25                |
| Claude 3 Sonnet   | $3.00               | $15.00               |
| Claude 3.5 Sonnet | $3.00               | $15.00               |
| Claude 3 Opus     | $15.00              | $75.00               |

#### Zhipu AI (CNY)

| 模型        | Input (¥/1K tokens) | Output (¥/1K tokens) |
| ----------- | ------------------- | -------------------- |
| GLM-4-Air   | ¥0.001              | ¥0.001               |
| GLM-4-Flash | ¥0.001              | ¥0.001               |
| GLM-4       | ¥0.1                | ¥0.1                 |
| GLM-4-Plus  | ¥0.5                | ¥0.5                 |

### 成本估算（中等项目）

**假设**:

- 每天处理 500 个文件
- 平均每个文件 1000 行代码
- Tier 1: 50k tokens/文件
- Tier 2: 10k tokens/文件
- Tier 3: 5k tokens/文件

**方案 2 (平衡配置) 每天成本**:

```
Tier 1 (GLM-4-Air):
  500 文件 × 50k tokens = 25M tokens
  成本: 25M × ¥0.001/1k = ¥25

Tier 2 (Claude Haiku):
  500 文件 × 10k tokens = 5M tokens
  成本: 5M × $0.25/1M = $1.25 ≈ ¥9

Tier 3 (Claude 3.5 Sonnet):
  假设只有 10% 文件需要补丁
  50 文件 × 5k tokens = 0.25M tokens
  成本: 0.25M × $3/1M = $0.75 ≈ ¥5.4

总成本: ¥25 + ¥9 + ¥5.4 = ¥39.4/天
月成本: ¥1182
```

---

## 🧪 测试模型配置

### 测试脚本

```bash
# 测试当前配置
.venv/bin/python test_api_improved.py
```

脚本会：

1. 读取环境变量中的模型配置
2. 优先尝试配置的模型
3. 如果失败，自动降级到备选模型
4. 显示成功的模型和响应

### 预期输出

```
================================================================================
🛡️  Aegis Box - API 连接测试 (改进版)
================================================================================

[1/3] 验证环境变量...
    ✅ ANTHROPIC_API_KEY: DC2Y4WW2...GKR2
    ✅ ZHIPU_API_KEY: ee490e4b...5GeP

[2/3] 测试 Anthropic API (带模型自动降级)...
    API 端点: https://cdn1.yunyi.yun/claude/v1/messages

    使用配置的模型:
    • Configured Tier 2: claude-3-haiku-20240307
    • Configured Tier 3: claude-3-5-sonnet-20240620

    尝试模型: Configured Tier 2: claude-3-haiku-20240307
    模型 ID: claude-3-haiku-20240307
    ✅ 成功！

    ============================================================================
    📝 使用模型: Configured Tier 2: claude-3-haiku-20240307
    📝 模型响应: Aegis Anthropic 连接成功。
    ============================================================================

[3/3] 测试 Zhipu AI API...
    使用模型: glm-4-air
    ✅ 成功！

    ============================================================================
    📝 GLM 响应: Aegis Zhipu 连接成功。
    ============================================================================
```

---

## 📝 配置示例

### 开发环境

```bash
# .env

# Anthropic (使用代理，快速模型)
ANTHROPIC_API_KEY=your-key
ANTHROPIC_API_URL=https://cdn1.yunyi.yun/claude
ANTHROPIC_MODEL_TIER2=claude-3-haiku-20240307
ANTHROPIC_MODEL_TIER3=claude-3-haiku-20240307

# Zhipu AI (最便宜的模型)
ZHIPU_API_KEY=your-key
ZHIPU_MODEL_TIER1=glm-4-air
```

### 生产环境

```bash
# .env

# Anthropic (官方端点，高质量模型)
ANTHROPIC_API_KEY=your-key
ANTHROPIC_API_URL=https://api.anthropic.com
ANTHROPIC_MODEL_TIER2=claude-3-sonnet-20240229
ANTHROPIC_MODEL_TIER3=claude-3-5-sonnet-20240620

# Zhipu AI (快速模型)
ZHIPU_API_KEY=your-key
ZHIPU_MODEL_TIER1=glm-4-air
```

### 测试环境

```bash
# .env

# 只用最便宜的模型
ANTHROPIC_API_KEY=your-key
ANTHROPIC_MODEL_TIER2=claude-3-haiku-20240307
ANTHROPIC_MODEL_TIER3=claude-3-haiku-20240307

ZHIPU_API_KEY=your-key
ZHIPU_MODEL_TIER1=glm-4-air
```

---

## 🔍 如何选择模型

### 决策树

```
需要处理大量文件？
├─ 是 → Tier 1 用 glm-4-air
└─ 否 → Tier 1 用 glm-4 或 glm-4-flash

需要深度架构分析？
├─ 是 → Tier 2 用 claude-3-5-sonnet
└─ 否 → Tier 2 用 claude-3-haiku

补丁质量要求高？
├─ 是 → Tier 3 用 claude-3-5-sonnet
└─ 否 → Tier 3 用 claude-3-haiku

预算有限？
└─ 全部用 glm-4-air 和 claude-3-haiku
```

### 质量 vs 成本权衡

```
最便宜: glm-4-air + claude-3-haiku + claude-3-haiku
平衡:   glm-4-air + claude-3-haiku + claude-3-5-sonnet ⭐ 推荐
高质量: glm-4 + claude-3-5-sonnet + claude-3-5-sonnet
最高:   glm-4-plus + claude-3-opus + claude-3-opus
```

---

## 📚 相关文档

- **API Key 配置**: [API_KEY_SETUP.md](API_KEY_SETUP.md)
- **API 测试分析**: [API_TEST_ANALYSIS.md](API_TEST_ANALYSIS.md)
- **自定义端点**: [CUSTOM_ENDPOINT.md](CUSTOM_ENDPOINT.md)

---

**🎯 通过灵活的模型配置，优化 Aegis Box 的成本和质量！**
