#!/usr/bin/env python3
"""
Aegis Box - 改进的 API 连接测试

改进内容:
1. Anthropic API 模型自动降级
2. 更友好的错误处理
3. 智谱 AI 余额检查提示
"""

import os
import sys

# 加载 .env 文件
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ .env 文件加载成功")
except ImportError:
    print("⚠️  python-dotenv 未安装，尝试从环境变量读取")

print("=" * 80)
print("🛡️  Aegis Box - API 连接测试 (改进版)")
print("=" * 80)
print()

# ==========================================
# 环境变量验证
# ==========================================
print("[1/3] 验证环境变量...")
print()

api_keys = {
    "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY"),
    "ZHIPU_API_KEY": os.getenv("ZHIPU_API_KEY"),
    "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
}

found_keys = []
for key, value in api_keys.items():
    if value and value != f"your-{key.lower().replace('_', '-')}-here":
        masked = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "***"
        print(f"    ✅ {key}: {masked}")
        found_keys.append(key)
    else:
        print(f"    ⚠️  {key}: 未设置")

if not found_keys:
    print()
    print("❌ 未找到任何有效的 API Key")
    sys.exit(1)

print()

# ==========================================
# 测试 Anthropic API (带模型降级)
# ==========================================
anthropic_success = False
anthropic_model_used = None

if "ANTHROPIC_API_KEY" in found_keys:
    print("[2/3] 测试 Anthropic API (带模型自动降级)...")
    print()

    try:
        import httpx

        api_key = api_keys["ANTHROPIC_API_KEY"]
        api_url = os.getenv("ANTHROPIC_API_URL", "https://api.anthropic.com")
        api_url = api_url.rstrip('/')
        url = f"{api_url}/v1/messages"

        print(f"    API 端点: {url}")
        print()

        # 从环境变量读取模型配置，如果未设置则使用降级列表
        configured_models = []

        # 检查 Tier 2 和 Tier 3 配置
        tier2_model = os.getenv("ANTHROPIC_MODEL_TIER2")
        tier3_model = os.getenv("ANTHROPIC_MODEL_TIER3")

        if tier2_model:
            configured_models.append((tier2_model, f"Configured Tier 2: {tier2_model}"))
        if tier3_model and tier3_model != tier2_model:
            configured_models.append((tier3_model, f"Configured Tier 3: {tier3_model}"))

        # 如果有配置的模型，先尝试配置的模型
        if configured_models:
            print("    使用配置的模型:")
            for model_id, model_name in configured_models:
                print(f"    • {model_name}")
            print()

        # 模型降级列表（从新到旧）
        fallback_models = [
            ("claude-3-5-sonnet-20240620", "Claude 3.5 Sonnet"),
            ("claude-3-sonnet-20240229", "Claude 3 Sonnet"),
            ("claude-3-haiku-20240307", "Claude 3 Haiku"),
        ]

        # 合并配置的模型和降级模型（去重）
        all_models = configured_models.copy()
        for model_id, model_name in fallback_models:
            if not any(m[0] == model_id for m in all_models):
                all_models.append((model_id, f"Fallback: {model_name}"))

        if not configured_models:
            print("    未配置模型，使用默认降级列表")
            print()

        success = False

        for model_id, model_name in all_models:
            print(f"    尝试模型: {model_name}")
            print(f"    模型 ID: {model_id}")

            try:
                response = httpx.post(
                    url,
                    headers={
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json"
                    },
                    json={
                        "model": model_id,
                        "max_tokens": 100,
                        "messages": [
                            {"role": "user", "content": "请用一句话回复：Aegis Anthropic 连接成功。"}
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
                    print(f"    📝 使用模型: {model_name}")
                    print(f"    📝 模型响应: {message}")
                    print("    " + "=" * 76)
                    print()
                    anthropic_success = True
                    anthropic_model_used = model_name
                    break
                else:
                    error_data = response.json()
                    error_msg = error_data.get("error", {}).get("message", "Unknown error")
                    print(f"    ⚠️  HTTP {response.status_code}: {error_msg}")
                    print()

            except httpx.HTTPStatusError as e:
                print(f"    ⚠️  HTTP 错误: {e.response.status_code}")
                print()
            except httpx.TimeoutException:
                print(f"    ⚠️  连接超时")
                print()
            except Exception as e:
                print(f"    ⚠️  异常: {str(e)[:100]}")
                print()

        if not anthropic_success:
            print("    ❌ 所有模型均失败")
            print()
            print("    💡 解决建议:")
            print()
            print("       方案 1: 联系代理服务商")
            print("          • 询问支持的模型列表")
            print("          • 确认 API 兼容性")
            print()
            print("       方案 2: 切换到官方 API")
            print("          • 编辑 .env 文件")
            print("          • 修改: ANTHROPIC_API_URL=https://api.anthropic.com")
            print("          • 或注释掉此行使用默认官方端点")
            print()
            print("       方案 3: 查看详细文档")
            print("          • cat docs/API_TEST_ANALYSIS.md")
            print()

    except ImportError:
        print("    ❌ httpx 未安装")
        print("    安装: uv pip install httpx")
        print()
    except Exception as e:
        print(f"    ❌ 未预期错误: {e}")
        print()
else:
    print("[2/3] 跳过 Anthropic API 测试（未配置 API Key）")
    print()

# ==========================================
# 测试 Zhipu AI (带余额提示)
# ==========================================
zhipu_success = False
zhipu_model_used = None

if "ZHIPU_API_KEY" in found_keys:
    print("[3/3] 测试 Zhipu AI API...")
    print()

    try:
        from zai import ZaiClient

        api_key = api_keys["ZHIPU_API_KEY"]

        # 从环境变量读取模型配置
        model = os.getenv("ZHIPU_MODEL_TIER1", "glm-4-air")

        print(f"    使用模型: {model}")
        print("    正在初始化 ZAI 客户端...")
        client = ZaiClient(api_key=api_key)

        print("    正在连接 Zhipu AI API...")
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": "请用一句话回复：Aegis Zhipu 连接成功。"}
            ],
            max_tokens=100
        )

        message = response.choices[0].message.content

        print("    ✅ 成功！")
        print()
        print("    " + "=" * 76)
        print(f"    📝 GLM 响应: {message}")
        print("    " + "=" * 76)
        print()
        zhipu_success = True
        zhipu_model_used = model

    except ImportError:
        print("    ❌ zai-sdk 未安装")
        print("    安装: uv pip install zai-sdk")
        print()
    except Exception as e:
        error_str = str(e)

        # 检查是否是余额不足错误
        if "1113" in error_str or "Insufficient balance" in error_str:
            print("    ❌ 余额不足或资源包已用尽")
            print()
            print("    💡 解决方案:")
            print()
            print("       方案 1: 充值账户 (推荐)")
            print("          • 访问: https://open.bigmodel.cn/")
            print("          • 导航: 账户管理 → 余额管理")
            print("          • 推荐充值: ¥50-100")
            print("          • GLM-4-Air 价格: ¥0.001/1k tokens (非常便宜)")
            print("          • ¥50 可用约 5000 万 tokens")
            print()
            print("       方案 2: 领取免费额度")
            print("          • 检查账户优惠券")
            print("          • 新用户注册送 1800 万 tokens")
            print("          • 完成实名认证获取额外额度")
            print()
            print("       方案 3: 临时只用 Anthropic API")
            print("          • Aegis Box 可以只用一个 API 工作")
            print("          • 确保 Anthropic API 配置正确")
            print()
        else:
            print(f"    ❌ 错误: {error_str[:200]}")
            print()
            import traceback
            print("    详细错误信息:")
            traceback.print_exc()
            print()
else:
    print("[3/3] 跳过 Zhipu AI API 测试（未配置 API Key）")
    print()

# ==========================================
# 测试总结
# ==========================================
print("=" * 80)
print("📊 测试总结")
print("=" * 80)
print()

# 统计测试结果
total_configured = len(found_keys)
total_success = 0
total_failed = 0

if "ANTHROPIC_API_KEY" in found_keys:
    if anthropic_success:
        print(f"✅ Anthropic API - 测试通过")
        print(f"   使用模型: {anthropic_model_used}")
        total_success += 1
    else:
        print(f"❌ Anthropic API - 测试失败")
        total_failed += 1
else:
    print("⚠️  Anthropic API - 未配置")

if "ZHIPU_API_KEY" in found_keys:
    if zhipu_success:
        print(f"✅ Zhipu AI API - 测试通过")
        print(f"   使用模型: {zhipu_model_used}")
        total_success += 1
    else:
        print(f"❌ Zhipu AI API - 测试失败")
        total_failed += 1
else:
    print("⚠️  Zhipu AI API - 未配置")

print()
print(f"📈 配置的 API: {total_configured}")
print(f"✅ 测试通过: {total_success}")
print(f"❌ 测试失败: {total_failed}")

print()
if total_success > 0:
    print(f"🎉 {total_success}/{total_configured} API 测试通过！Aegis Box 可以正常工作。")
    print()
    print("💡 下一步:")
    print("   • 查看模型配置指南: cat docs/MODEL_CONFIG.md")
    print("   • 开始使用 Aegis Box")
elif total_failed > 0:
    print("⚠️  所有 API 测试失败，请根据上述错误提示解决问题。")
    print()
    print("💡 下一步:")
    print("   1. 根据上述错误提示解决问题")
    print("   2. 重新运行测试: .venv/bin/python test_api_improved.py")
    print("   3. 查看详细分析: cat docs/API_TEST_ANALYSIS.md")
else:
    print("⚠️  未配置任何 API Key，请先配置。")
    print()
    print("💡 下一步:")
    print("   1. 复制配置模板: cp .env.example .env")
    print("   2. 编辑配置文件: nano .env")
    print("   3. 查看配置指南: cat docs/API_KEY_SETUP.md")

print()
print("=" * 80)
