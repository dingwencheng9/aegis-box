#!/usr/bin/env python3
"""
Aegis Box - 完整的 API 连接测试

测试内容：
1. 环境变量加载
2. Anthropic API 连接
3. Zhipu AI (ZAI) API 连接
"""

import os
import sys
from pathlib import Path

# 加载 .env 文件
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ .env 文件加载成功")
except ImportError:
    print("⚠️  python-dotenv 未安装，尝试从环境变量读取")

print("=" * 80)
print("🛡️  Aegis Box - API 连接测试")
print("=" * 80)
print()

# ==========================================
# 测试 1: 环境变量验证
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
    print()
    print("请按以下步骤设置：")
    print()
    print("1. 复制 .env.example 为 .env:")
    print("   cp .env.example .env")
    print()
    print("2. 编辑 .env 文件，填入真实的 API Key")
    print()
    print("3. 重新运行此脚本:")
    print("   .venv/bin/python test_api_complete.py")
    sys.exit(1)

print()

# ==========================================
# 测试 2: Anthropic API
# ==========================================
if "ANTHROPIC_API_KEY" in found_keys:
    print("[2/3] 测试 Anthropic API...")
    print()

    try:
        import httpx

        api_key = api_keys["ANTHROPIC_API_KEY"]

        # 支持自定义 API 端点
        api_url = os.getenv("ANTHROPIC_API_URL", "https://api.anthropic.com")
        # 确保 URL 不以斜杠结尾
        api_url = api_url.rstrip('/')
        url = f"{api_url}/v1/messages"

        print(f"    API 端点: {url}")

        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        payload = {
            "model": "claude-3-5-haiku-20241022",
            "max_tokens": 100,
            "messages": [
                {
                    "role": "user",
                    "content": "请用一句话回复：Aegis Anthropic 连接成功。"
                }
            ]
        }

        print("    正在连接 Anthropic API...")
        response = httpx.post(url, headers=headers, json=payload, timeout=30.0)

        if response.status_code == 200:
            result = response.json()
            message = result.get("content", [{}])[0].get("text", "")

            print("    ✅ 连接成功！")
            print()
            print("    " + "=" * 76)
            print(f"    📝 Claude 响应: {message}")
            print("    " + "=" * 76)
            print()
        else:
            print(f"    ❌ 请求失败: HTTP {response.status_code}")
            print(f"    响应: {response.text[:200]}")
            print()

    except httpx.HTTPStatusError as e:
        print(f"    ❌ HTTP 错误: {e.response.status_code}")
        print(f"    响应: {e.response.text[:200]}")
        print()
    except httpx.TimeoutException:
        print("    ❌ 连接超时")
        print()
    except Exception as e:
        print(f"    ❌ 错误: {e}")
        print()
else:
    print("[2/3] 跳过 Anthropic API 测试（未配置 API Key）")
    print()

# ==========================================
# 测试 3: Zhipu AI (ZAI) API
# ==========================================
if "ZHIPU_API_KEY" in found_keys:
    print("[3/3] 测试 Zhipu AI API...")
    print()

    try:
        from zai import ZaiClient

        api_key = api_keys["ZHIPU_API_KEY"]

        print("    正在初始化 ZAI 客户端...")
        client = ZaiClient(api_key=api_key)

        print("    正在连接 Zhipu AI API...")
        response = client.chat.completions.create(
            model="glm-4-air",
            messages=[
                {
                    "role": "user",
                    "content": "请用一句话回复：Aegis Zhipu 连接成功。"
                }
            ],
            max_tokens=100
        )

        message = response.choices[0].message.content

        print("    ✅ 连接成功！")
        print()
        print("    " + "=" * 76)
        print(f"    📝 GLM 响应: {message}")
        print("    " + "=" * 76)
        print()

    except ImportError:
        print("    ❌ zai-sdk 未安装")
        print("    安装: uv pip install zai-sdk")
        print()
    except Exception as e:
        print(f"    ❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        print()
else:
    print("[3/3] 跳过 Zhipu AI API 测试（未配置 API Key）")
    print()

# ==========================================
# 总结
# ==========================================
print("=" * 80)
print("📊 测试总结")
print("=" * 80)
print()

if "ANTHROPIC_API_KEY" in found_keys:
    print("✅ Anthropic API (Claude) - 已配置并测试")
else:
    print("⚠️  Anthropic API (Claude) - 未配置")

if "ZHIPU_API_KEY" in found_keys:
    print("✅ Zhipu AI API (GLM) - 已配置并测试")
else:
    print("⚠️  Zhipu AI API (GLM) - 未配置")

print()

if len(found_keys) >= 1:
    print("🎉 至少有一个 API 配置成功！Aegis Box 可以正常工作。")
else:
    print("⚠️  建议至少配置一个 API Key 以使用 Aegis Box。")

print()
print("=" * 80)
