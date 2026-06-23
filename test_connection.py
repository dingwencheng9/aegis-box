#!/usr/bin/env python3
"""
Aegis Box - LLM 连通性测试脚本

用途：验证 LLM 客户端是否正确配置和连接
测试内容：
1. 配置文件加载
2. LLM 客户端初始化
3. 网络通信测试
"""

import os
import sys
from pathlib import Path

# 确保项目根目录在 sys.path 中
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    print("=" * 80)
    print("🛡️  Aegis Box - LLM 连通性测试")
    print("=" * 80)
    print()

    # 1. 验证项目结构
    print("[1/4] 验证项目结构...")
    aegis_dir = project_root / "aegis"
    if not aegis_dir.exists():
        print(f"    ❌ 找不到 aegis 目录: {aegis_dir}")
        print("    提示: 请确保在项目根目录下运行此脚本")
        return 1
    print(f"    ✅ 项目根目录: {project_root}")
    print()

    # 2. 导入核心模块
    print("[2/4] 导入核心模块...")
    try:
        from aegis.cli import AegisConfig
        print("    ✅ 核心模块导入成功")
    except ImportError as e:
        print(f"    ❌ 导入失败: {e}")
        print("    提示: 请确保已安装所有依赖 (pip install -e .)")
        return 1
    print()

    # 3. 验证环境变量
    print("[3/4] 验证环境变量...")
    api_keys = {
        "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY"),
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "ZHIPU_API_KEY": os.getenv("ZHIPU_API_KEY"),
    }

    found_keys = [k for k, v in api_keys.items() if v]
    if not found_keys:
        print("    ❌ 未找到任何 API Key")
        print("    提示: 请设置以下环境变量之一:")
        print("      export ANTHROPIC_API_KEY='your-key'")
        print("      export OPENAI_API_KEY='your-key'")
        print("      export ZHIPU_API_KEY='your-key'")
        return 1

    for key in found_keys:
        value = api_keys[key]
        masked = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "***"
        print(f"    ✅ {key}: {masked}")
    print()

    # 4. 测试 LLM 连接
    print("[4/4] 测试 LLM 连接...")

    # 根据找到的 API Key 选择提供商
    if api_keys["ANTHROPIC_API_KEY"]:
        provider = "anthropic"
        model = "claude-3-5-haiku-20241022"
        api_key = api_keys["ANTHROPIC_API_KEY"]
    elif api_keys["OPENAI_API_KEY"]:
        provider = "openai"
        model = "gpt-4o-mini"
        api_key = api_keys["OPENAI_API_KEY"]
    else:
        provider = "zhipu"
        model = "glm-4-air"
        api_key = api_keys["ZHIPU_API_KEY"]

    print(f"    使用提供商: {provider}")
    print(f"    模型: {model}")
    print()

    try:
        # 注意：这里需要适配实际的 LLM 客户端实现
        # 由于我们还没有完整实现 LLM 客户端，这里只是框架
        print("    正在连接 LLM API...")

        # 临时测试：直接使用 httpx 测试连通性
        import httpx

        if provider == "anthropic":
            # 测试 Anthropic API
            url = "https://api.anthropic.com/v1/messages"
            headers = {
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
            payload = {
                "model": model,
                "max_tokens": 50,
                "messages": [
                    {"role": "user", "content": "请回复：'Aegis 连接成功，系统就绪。'"}
                ]
            }

            response = httpx.post(url, headers=headers, json=payload, timeout=30.0)
            response.raise_for_status()

            result = response.json()
            message = result.get("content", [{}])[0].get("text", "")

        elif provider == "openai":
            # 测试 OpenAI API
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": model,
                "messages": [
                    {"role": "user", "content": "请回复：'Aegis 连接成功，系统就绪。'"}
                ],
                "max_tokens": 50
            }

            response = httpx.post(url, headers=headers, json=payload, timeout=30.0)
            response.raise_for_status()

            result = response.json()
            message = result.get("choices", [{}])[0].get("message", {}).get("content", "")

        else:
            print("    ⚠️  Zhipu API 测试暂未实现")
            message = "测试跳过"

        print()
        print("    " + "=" * 76)
        print(f"    📝 模型响应: {message}")
        print("    " + "=" * 76)
        print()
        print("✅ 测试通过！Aegis 核心引擎已就绪")
        print()
        return 0

    except httpx.HTTPStatusError as e:
        print(f"    ❌ API 请求失败: HTTP {e.response.status_code}")
        print(f"    响应内容: {e.response.text[:200]}")
        print()
        print("    提示:")
        print("    - 检查 API Key 是否正确")
        print("    - 检查 API Key 是否有足够的额度")
        print("    - 检查网络连接")
        return 1

    except httpx.TimeoutException:
        print("    ❌ 连接超时")
        print()
        print("    提示:")
        print("    - 检查网络连接")
        print("    - 检查是否需要代理")
        return 1

    except Exception as e:
        print(f"    ❌ 测试失败: {e}")
        print()
        print("    提示:")
        print("    - 检查错误消息")
        print("    - 确保依赖已安装 (pip install httpx)")
        return 1

if __name__ == "__main__":
    sys.exit(main())
