# 🔍 API 连接测试深度分析报告

## 📊 测试结果总览

**执行时间**: 2026-06-23
**测试状态**: ⚠️ 部分失败

```
✅ 环境变量验证: 通过 (2/3 API Keys 已配置)
❌ Anthropic API: 失败 (HTTP 400 - 模型不支持)
❌ Zhipu AI API: 失败 (429 - 余额不足)
```

---

## 🚨 问题 1: Anthropic API - 模型不支持

### 错误详情

```json
{
  "type": "error",
  "error": {
    "type": "invalid_request_error",
    "message": "Unsupported model: claude-3-5-haiku-20241022"
  }
}
```

**API 端点**: `https://cdn1.yunyi.yun/claude/v1/messages`

### 根本原因分析

你的代理服务 **不支持** `claude-3-5-haiku-20241022` 模型。

**可能的原因**:

1. 代理服务使用的是旧版本的 Anthropic API
2. 代理服务只支持部分模型
3. 模型名称需要特殊映射

### 解决方案

#### 方案 1: 使用代理服务支持的模型 (推荐)

**Step 1: 查询代理服务支持的模型列表**

```bash
# 联系你的代理服务提供商，询问支持的模型列表
# 或查看他们的文档
```

**常见的支持模型**:

- `claude-3-haiku-20240307` (Claude 3 Haiku)
- `claude-3-sonnet-20240229` (Claude 3 Sonnet)
- `claude-3-opus-20240229` (Claude 3 Opus)
- `claude-3-5-sonnet-20240620` (Claude 3.5 Sonnet)

**Step 2: 更新测试脚本使用支持的模型**

创建一个新的测试脚本 `test_api_with_fallback.py`:

```python
#!/usr/bin/env python3
"""带模型降级的 API 测试"""

import os
from dotenv import load_dotenv

load_dotenv()

# 定义模型降级策略
ANTHROPIC_MODELS = [
    "claude-3-5-sonnet-20240620",  # 最新
    "claude-3-sonnet-20240229",    # 降级 1
    "claude-3-haiku-20240307",     # 降级 2
]

import httpx

api_key = os.getenv("ANTHROPIC_API_KEY")
api_url = os.getenv("ANTHROPIC_API_URL", "https://api.anthropic.com")
url = f"{api_url.rstrip('/')}/v1/messages"

for model in ANTHROPIC_MODELS:
    print(f"尝试模型: {model}")

    try:
        response = httpx.post(
            url,
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            json={
                "model": model,
                "max_tokens": 50,
                "messages": [{"role": "user", "content": "hi"}]
            },
            timeout=30.0
        )

        if response.status_code == 200:
            print(f"✅ 成功！支持的模型: {model}")
            print(f"响应: {response.json()['content'][0]['text']}")
            break
        else:
            print(f"❌ 失败: {response.status_code}")
            print(f"错误: {response.text[:200]}")
    except Exception as e:
        print(f"❌ 异常: {e}")
```

#### 方案 2: 切换到官方 Anthropic API

如果代理服务限制太多，建议切换到官方 API。

**Step 1: 修改 .env 文件**

```bash
# 方法 1: 注释掉自定义端点
# ANTHROPIC_API_URL=https://cdn1.yunyi.yun/claude

# 方法 2: 改为官方端点
ANTHROPIC_API_URL=https://api.anthropic.com
```

**优势**:

- ✅ 支持所有最新模型
- ✅ 更稳定的服务
- ✅ 完整的功能支持

**劣势**:

- ⚠️ 可能需要科学上网
- ⚠️ 可能速度较慢

#### 方案 3: 动态模型选择 (最佳)

修改 Aegis Box 核心代码，支持自动降级：

```python
# aegis/core/llm.py

class AnthropicClient:
    # 定义模型优先级（从新到旧）
    MODEL_FALLBACK = {
        "haiku": [
            "claude-3-5-haiku-20241022",
            "claude-3-haiku-20240307",
        ],
        "sonnet": [
            "claude-3-5-sonnet-20240620",
            "claude-3-sonnet-20240229",
        ],
        "opus": [
            "claude-3-opus-20240229",
        ]
    }

    async def complete_with_fallback(self, tier: str, prompt: str):
        """使用模型降级策略"""
        models = self.MODEL_FALLBACK.get(tier, [])

        for model in models:
            try:
                response = await self.complete(model, prompt)
                logger.info(f"成功使用模型: {model}")
                return response
            except HTTPError as e:
                if e.status_code == 400:
                    logger.warning(f"模型 {model} 不支持，尝试降级")
                    continue
                raise

        raise Exception(f"所有 {tier} 级别模型均不可用")
```

---

## 🚨 问题 2: Zhipu AI - 余额不足

### 错误详情

```json
{
  "error": {
    "code": "1113",
    "message": "Insufficient balance or no resource package. Please recharge."
  }
}
```

### 根本原因

**你的智谱 AI 账户余额不足或资源包已用尽。**

### 解决方案

#### 方案 1: 充值账户 (推荐)

**Step 1: 访问智谱 AI 控制台**

```
https://open.bigmodel.cn/
```

**Step 2: 充值**

1. 导航到 **账户管理** → **余额管理**
2. 选择充值金额
3. 完成支付

**推荐充值金额**:

- ¥50 - 个人开发测试（约 5000 万 tokens）
- ¥100 - 小型项目（约 1 亿 tokens）
- ¥500+ - 生产环境

**GLM-4-Air 价格**:

- ¥0.001 / 1k tokens
- 非常便宜，适合大规模使用

#### 方案 2: 申请免费额度

**智谱 AI 新用户福利**:

1. 注册即送 **1800 万 tokens** 免费额度
2. 实名认证后额外送免费额度
3. 参与活动可获得更多

**Step: 检查是否有未领取的额度**

1. 访问控制台
2. 查看 **优惠券** 或 **活动中心**
3. 领取可用额度

#### 方案 3: 使用 Anthropic API (备选)

如果智谱 AI 暂时无法使用，可以临时只用 Anthropic API。

**修改测试脚本**，跳过智谱 AI 测试：

```python
# test_api_complete.py

# 在测试前添加
if "ZHIPU_API_KEY" in found_keys:
    # 检查余额
    print("[3/3] 测试 Zhipu AI API...")
    print("    ⚠️  如果余额不足，请充值后再测试")
    print("    充值地址: https://open.bigmodel.cn/")
    print()

    # 询问是否继续
    # 或直接跳过
    print("    ⏭️  跳过 Zhipu AI 测试（余额不足）")
else:
    print("[3/3] 跳过 Zhipu AI API 测试（未配置 API Key）")
```

---

## 🎯 优化方案总结

### 立即行动项

#### 1. 解决 Anthropic API 模型问题

**选项 A: 查询并使用支持的模型** (5 分钟)

```bash
# 联系代理服务商
# 或运行模型探测脚本
.venv/bin/python test_api_with_fallback.py
```

**选项 B: 切换到官方 API** (1 分钟)

```bash
# 编辑 .env
nano .env

# 注释掉或改为官方端点
ANTHROPIC_API_URL=https://api.anthropic.com
```

#### 2. 解决智谱 AI 余额问题

**选项 A: 充值** (5 分钟 + 支付时间)

```
1. 访问: https://open.bigmodel.cn/
2. 充值 ¥50-100
3. 等待到账（通常立即到账）
```

**选项 B: 领取免费额度** (2 分钟)

```
1. 检查账户优惠券
2. 领取未使用的额度
3. 完成实名认证获取额外额度
```

---

## 🔧 优化测试脚本

创建一个改进版的测试脚本，包含：

- 模型自动降级
- 更友好的错误处理
- 余额检查提示

```python
#!/usr/bin/env python3
"""改进的 API 测试脚本"""

import os
import httpx
from dotenv import load_dotenv

load_dotenv()

print("="*80)
print("🛡️  Aegis Box - API 连接测试 (改进版)")
print("="*80)
print()

# ==========================================
# 测试 Anthropic API (带模型降级)
# ==========================================
anthropic_key = os.getenv("ANTHROPIC_API_KEY")
anthropic_url = os.getenv("ANTHROPIC_API_URL", "https://api.anthropic.com")

if anthropic_key:
    print("[1/2] 测试 Anthropic API (带模型降级)...")
    print()

    # 模型降级列表（从新到旧）
    models = [
        ("claude-3-5-sonnet-20240620", "Claude 3.5 Sonnet"),
        ("claude-3-sonnet-20240229", "Claude 3 Sonnet"),
        ("claude-3-haiku-20240307", "Claude 3 Haiku"),
    ]

    url = f"{anthropic_url.rstrip('/')}/v1/messages"
    success = False

    for model_id, model_name in models:
        print(f"    尝试模型: {model_name} ({model_id})")

        try:
            response = httpx.post(
                url,
                headers={
                    "x-api-key": anthropic_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": model_id,
                    "max_tokens": 100,
                    "messages": [
                        {"role": "user", "content": "请回复：Aegis 连接成功。"}
                    ]
                },
                timeout=30.0
            )

            if response.status_code == 200:
                result = response.json()
                message = result.get("content", [{}])[0].get("text", "")

                print(f"    ✅ 成功！")
                print()
                print("    " + "=" * 76)
                print(f"    📝 模型: {model_name}")
                print(f"    📝 响应: {message}")
                print("    " + "=" * 76)
                print()
                success = True
                break
            else:
                print(f"    ⚠️  HTTP {response.status_code}: {response.json().get('error', {}).get('message', 'Unknown error')}")

        except Exception as e:
            print(f"    ⚠️  异常: {str(e)[:100]}")

    if not success:
        print("    ❌ 所有模型均失败")
        print()
        print("    💡 建议:")
        print("       1. 联系代理服务商确认支持的模型")
        print("       2. 或切换到官方 API: ANTHROPIC_API_URL=https://api.anthropic.com")
        print()

# ==========================================
# 测试 Zhipu AI (带余额提示)
# ==========================================
zhipu_key = os.getenv("ZHIPU_API_KEY")

if zhipu_key:
    print("[2/2] 测试 Zhipu AI API...")
    print()

    try:
        from zai import ZaiClient

        client = ZaiClient(api_key=zhipu_key)

        response = client.chat.completions.create(
            model="glm-4-air",
            messages=[
                {"role": "user", "content": "请回复：Aegis 连接成功。"}
            ],
            max_tokens=100
        )

        message = response.choices[0].message.content

        print("    ✅ 成功！")
        print()
        print("    " + "=" * 76)
        print(f"    📝 响应: {message}")
        print("    " + "=" * 76)
        print()

    except Exception as e:
        error_str = str(e)

        if "1113" in error_str or "Insufficient balance" in error_str:
            print("    ❌ 余额不足")
            print()
            print("    💡 解决方案:")
            print("       1. 充值: https://open.bigmodel.cn/")
            print("       2. 推荐充值 ¥50-100 (约 5000 万 - 1 亿 tokens)")
            print("       3. GLM-4-Air 价格: ¥0.001/1k tokens (非常便宜)")
            print("       4. 或检查账户优惠券是否有未领取额度")
            print()
        else:
            print(f"    ❌ 错误: {error_str[:200]}")
            print()

print("="*80)
print("📊 测试完成")
print("="*80)
```

保存为 `test_api_improved.py` 并运行：

```bash
.venv/bin/python test_api_improved.py
```

---

## 📋 行动检查清单

### 短期（今天完成）

- [ ] **Anthropic API**: 联系代理服务商确认支持的模型
- [ ] 或切换到官方 API: 修改 `.env` 中的 `ANTHROPIC_API_URL`
- [ ] **Zhipu AI**: 充值 ¥50-100 到账户
- [ ] 或领取未使用的免费额度
- [ ] 运行改进的测试脚本验证

### 中期（本周完成）

- [ ] 在 Aegis Box 中实现模型自动降级机制
- [ ] 添加余额检查功能（启动时警告）
- [ ] 优化错误处理和重试逻辑
- [ ] 更新文档说明支持的模型列表

### 长期（持续优化）

- [ ] 监控 API 使用量和成本
- [ ] 定期更新模型列表
- [ ] 实现智能模型选择（根据任务复杂度）
- [ ] 添加成本预估功能

---

## 💡 最佳实践建议

### 1. 模型选择策略

```python
# Aegis Box 三级架构建议
TIER_CONFIG = {
    "tier1": {  # 快速探伤
        "primary": "glm-4-air",           # 首选
        "fallback": "glm-4-flash"         # 备选
    },
    "tier2": {  # 架构推理
        "primary": "claude-3-haiku-20240307",      # 首选（支持广泛）
        "fallback": "claude-3-sonnet-20240229"     # 备选
    },
    "tier3": {  # 补丁生成
        "primary": "claude-3-5-sonnet-20240620",   # 首选
        "fallback": "claude-3-sonnet-20240229"     # 备选
    }
}
```

### 2. 成本优化

```python
# 智谱 AI 成本（便宜）
GLM_4_AIR_COST = 0.001 / 1000  # ¥0.001 per 1k tokens

# Anthropic 成本（贵但质量高）
CLAUDE_HAIKU_COST = 0.25 / 1_000_000  # $0.25 per 1M input tokens
CLAUDE_SONNET_COST = 3.00 / 1_000_000  # $3.00 per 1M input tokens

# 建议：Tier 1 用 GLM-4-Air，Tier 2/3 用 Claude
```

### 3. 错误处理

```python
# 添加完善的错误处理
try:
    response = await client.complete(prompt)
except ModelNotSupportedError:
    # 自动降级到支持的模型
    response = await client.complete_with_fallback(prompt)
except InsufficientBalanceError:
    # 提示用户充值
    logger.error("余额不足，请充值: https://open.bigmodel.cn/")
    raise
except APIError as e:
    # 记录错误并重试
    logger.error(f"API 错误: {e}")
    retry_with_backoff()
```

---

## 🎯 推荐配置（生产环境）

```bash
# .env 配置

# Anthropic API (使用官方端点，支持所有模型)
ANTHROPIC_API_KEY=your-key
ANTHROPIC_API_URL=https://api.anthropic.com

# Zhipu AI (确保余额充足)
ZHIPU_API_KEY=your-key

# 成本控制
MAX_TOKENS_PER_REQUEST=4000
DAILY_TOKEN_BUDGET=1000000  # 每天最多 100 万 tokens
```

**预估成本**:

- 每天 100 万 tokens
- GLM-4-Air: ¥1/天
- Claude Haiku: $0.25/天
- **总计**: ~¥2-3/天

---

**需要我帮你创建这些优化脚本吗？或者你想先解决哪个问题？**
