#!/usr/bin/env python3
"""
🧪 LLM 客户端功能测试脚本
测试 LLMClient 的各项功能
"""

import asyncio
from typing import List
from pydantic import BaseModel
from loguru import logger

from aegis.cli import ConfigManager
from aegis.core.llm import LLMClientFactory, CircuitBreakerOpenError


# 定义测试用的 Pydantic 模型
class TestSummary(BaseModel):
    """测试用的结构化输出"""
    title: str
    key_points: List[str]
    score: int


async def test_basic_text_chat():
    """测试 1: 基础文本对话"""
    logger.info("=" * 60)
    logger.info("测试 1: 基础文本对话")
    logger.info("=" * 60)

    config = ConfigManager.load()
    factory = LLMClientFactory(config)
    tier1 = factory.create_tier1_client()

    try:
        response = await tier1.chat(
            prompt="请用一句话介绍 Python 编程语言",
            temperature=0.7,
            max_tokens=100,
        )
        logger.success(f"✅ 响应: {response}")
        return True
    except Exception as e:
        logger.error(f"❌ 失败: {e}")
        return False


async def test_structured_output():
    """测试 2: 结构化输出（Pydantic）"""
    logger.info("=" * 60)
    logger.info("测试 2: 结构化输出")
    logger.info("=" * 60)

    config = ConfigManager.load()
    factory = LLMClientFactory(config)
    tier1 = factory.create_tier1_client()

    try:
        summary = await tier1.chat(
            prompt="""
请总结以下内容：

Python 是一门广泛使用的解释型、高级编程语言。它由 Guido van Rossum 创建。
Python 的设计哲学强调代码的可读性和简洁的语法。
Python 支持多种编程范式，包括面向对象、命令式、函数式和过程式编程。
""",
            response_model=TestSummary,
            system_prompt="你是一个内容总结专家",
            temperature=0.3,
        )

        logger.success("✅ 结构化输出成功:")
        logger.info(f"  - 标题: {summary.title}")
        logger.info(f"  - 关键点数量: {len(summary.key_points)}")
        for i, point in enumerate(summary.key_points, 1):
            logger.info(f"    {i}. {point}")
        logger.info(f"  - 评分: {summary.score}")
        return True

    except Exception as e:
        logger.error(f"❌ 失败: {e}")
        return False


async def test_three_tiers():
    """测试 3: 三个层级的客户端"""
    logger.info("=" * 60)
    logger.info("测试 3: 三层级客户端")
    logger.info("=" * 60)

    config = ConfigManager.load()
    factory = LLMClientFactory(config)

    # Tier-1
    try:
        tier1 = factory.create_tier1_client()
        logger.info(f"Tier-1 模型: {tier1.model_id}")
        response1 = await tier1.chat("用一句话介绍快速探伤", max_tokens=50)
        logger.success(f"✅ Tier-1 响应: {response1[:50]}...")
    except Exception as e:
        logger.error(f"❌ Tier-1 失败: {e}")
        return False

    # Tier-2
    try:
        tier2 = factory.create_tier2_client()
        logger.info(f"Tier-2 模型: {tier2.model_id}")
        response2 = await tier2.chat("用一句话介绍架构推理", max_tokens=50)
        logger.success(f"✅ Tier-2 响应: {response2[:50]}...")
    except Exception as e:
        logger.error(f"❌ Tier-2 失败: {e}")
        return False

    # Tier-3
    try:
        tier3 = factory.create_tier3_client()
        logger.info(f"Tier-3 模型: {tier3.model_id}")
        response3 = await tier3.chat("用一句话介绍补丁生成", max_tokens=50)
        logger.success(f"✅ Tier-3 响应: {response3[:50]}...")
    except Exception as e:
        logger.error(f"❌ Tier-3 失败: {e}")
        return False

    return True


async def test_rate_limiting():
    """测试 4: 速率限制"""
    logger.info("=" * 60)
    logger.info("测试 4: 速率限制")
    logger.info("=" * 60)

    config = ConfigManager.load()
    factory = LLMClientFactory(config)
    tier1 = factory.create_tier1_client()

    try:
        # 连续发送 5 个请求，观察速率限制
        logger.info("发送 5 个并发请求...")
        tasks = [
            tier1.chat(f"请求 #{i}", max_tokens=10)
            for i in range(5)
        ]

        import time
        start = time.time()
        results = await asyncio.gather(*tasks)
        elapsed = time.time() - start

        logger.success(f"✅ 完成 5 个请求，耗时: {elapsed:.2f} 秒")
        logger.info(f"平均延迟: {elapsed / 5:.2f} 秒/请求")

        # 查看速率限制器统计
        limiter_stats = factory.get_rate_limiter_stats()
        logger.info("速率限制器统计:")
        logger.info(f"  - 总请求数: {limiter_stats['total_requests']}")
        logger.info(f"  - 总 Token: {limiter_stats['total_tokens']}")

        return True

    except Exception as e:
        logger.error(f"❌ 失败: {e}")
        return False


async def test_stats():
    """测试 5: 统计信息"""
    logger.info("=" * 60)
    logger.info("测试 5: 统计信息")
    logger.info("=" * 60)

    config = ConfigManager.load()
    factory = LLMClientFactory(config)
    tier1 = factory.create_tier1_client()

    try:
        # 执行几次调用
        for i in range(3):
            await tier1.chat(f"测试请求 #{i}", max_tokens=20)

        # 获取统计
        stats = tier1.get_stats()
        logger.success("✅ 客户端统计信息:")
        logger.info(f"  - 总调用次数: {stats['total_calls']}")
        logger.info(f"  - 成功次数: {stats['success_calls']}")
        logger.info(f"  - 失败次数: {stats['failed_calls']}")
        logger.info(f"  - 成功率: {stats['success_rate']}")
        logger.info(f"  - 总 Token: {stats['total_tokens']}")
        logger.info(f"  - 熔断器状态: {stats['circuit_state']}")

        return True

    except Exception as e:
        logger.error(f"❌ 失败: {e}")
        return False


async def main():
    """运行所有测试"""
    logger.info("🚀 开始 LLM 客户端功能测试")
    logger.info("")

    tests = [
        ("基础文本对话", test_basic_text_chat),
        ("结构化输出", test_structured_output),
        ("三层级客户端", test_three_tiers),
        ("速率限制", test_rate_limiting),
        ("统计信息", test_stats),
    ]

    results = []
    for name, test_func in tests:
        try:
            success = await test_func()
            results.append((name, success))
        except Exception as e:
            logger.error(f"测试 '{name}' 异常: {e}")
            results.append((name, False))

        # 测试之间暂停
        await asyncio.sleep(1)
        logger.info("")

    # 汇总结果
    logger.info("=" * 60)
    logger.info("测试结果汇总")
    logger.info("=" * 60)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status} - {name}")

    logger.info("")
    logger.info(f"总计: {passed}/{total} 通过")

    if passed == total:
        logger.success("🎉 所有测试通过！")
    else:
        logger.warning(f"⚠️ {total - passed} 个测试失败")


if __name__ == "__main__":
    asyncio.run(main())
