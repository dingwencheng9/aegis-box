#!/usr/bin/env python3
"""
🛡️ Aegis Box - 智谱 AI 客户端使用示例

演示如何使用优化后的原生客户端
"""

import asyncio
import os
from pathlib import Path
from loguru import logger

from aegis.core.llm_zhipu import create_zhipu_client


# ==========================================
# 示例 1: 基础对话
# ==========================================
async def example_basic_chat():
    """基础对话示例"""
    logger.info("🔹 示例 1: 基础对话")

    client = create_zhipu_client()

    response = await client.chat(
        messages=[
            {"role": "user", "content": "请用一句话介绍智谱 AI"}
        ],
        temperature=0.7
    )

    logger.success(f"AI 回复: {response}")


# ==========================================
# 示例 2: 推理模式（Thinking）
# ==========================================
async def example_thinking_mode():
    """推理模式示例"""
    logger.info("🔹 示例 2: 推理模式（Thinking）")

    client = create_zhipu_client(enable_thinking=True)

    response = await client.chat(
        messages=[
            {"role": "user", "content": "计算 123 * 456 + 789"}
        ],
        enable_thinking=True
    )

    logger.success(f"AI 回复: {response}")


# ==========================================
# 示例 3: 结构化输出
# ==========================================
async def example_structured_output():
    """结构化输出示例"""
    logger.info("🔹 示例 3: 结构化输出")

    client = create_zhipu_client()

    # 定义 schema
    schema = {
        "type": "object",
        "properties": {
            "file_path": {"type": "string"},
            "responsibility": {"type": "string"},
            "vulnerabilities": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "level": {"type": "string"},
                        "description": {"type": "string"},
                        "suggestion": {"type": "string"}
                    },
                    "required": ["level", "description", "suggestion"]
                }
            }
        },
        "required": ["file_path", "responsibility", "vulnerabilities"]
    }

    # 调用
    result = await client.structured_output(
        messages=[
            {"role": "user", "content": """
分析以下 Python 代码的安全问题：

```python
def execute_command(cmd):
    os.system(cmd)  # 直接执行用户命令
```

请以 JSON 格式返回分析结果。
"""}
        ],
        schema=schema
    )

    logger.success(f"结构化输出: {result}")


# ==========================================
# 示例 4: 流式输出
# ==========================================
async def example_streaming():
    """流式输出示例"""
    logger.info("🔹 示例 4: 流式输出")

    client = create_zhipu_client()

    logger.info("AI 回复（流式）:")
    async for chunk in await client.chat(
        messages=[
            {"role": "user", "content": "讲一个关于 AI 安全的故事，30 字以内"}
        ],
        stream=True
    ):
        if chunk["type"] == "content":
            print(chunk["content"], end="", flush=True)
        elif chunk["type"] == "complete":
            print()  # 换行
            logger.success(f"\n完整内容: {chunk['full_content']}")


# ==========================================
# 示例 5: 错误处理和重试
# ==========================================
async def example_error_handling():
    """错误处理示例"""
    logger.info("🔹 示例 5: 错误处理和重试")

    try:
        client = create_zhipu_client(api_key="invalid-key")

        response = await client.chat(
            messages=[
                {"role": "user", "content": "测试"}
            ]
        )

        logger.success(f"AI 回复: {response}")

    except Exception as e:
        logger.error(f"❌ 预期的错误: {type(e).__name__} - {e}")


# ==========================================
# 主函数
# ==========================================
async def main():
    """运行所有示例"""
    logger.info("="*80)
    logger.info("🛡️ Aegis Box - 智谱 AI 客户端使用示例")
    logger.info("="*80)

    # 检查 API Key
    if not os.getenv("ZHIPU_API_KEY"):
        logger.warning("⚠️ 未设置 ZHIPU_API_KEY 环境变量")
        logger.info("请设置: export ZHIPU_API_KEY=your-api-key")
        return

    # 运行示例
    examples = [
        example_basic_chat,
        example_thinking_mode,
        example_structured_output,
        example_streaming,
        example_error_handling
    ]

    for example_func in examples:
        try:
            await example_func()
            print()
        except Exception as e:
            logger.error(f"❌ 示例失败: {e}")
            print()

    logger.success("✅ 所有示例运行完成！")


if __name__ == "__main__":
    asyncio.run(main())
