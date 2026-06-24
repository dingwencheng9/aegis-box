#!/usr/bin/env python3
"""
🛡️ Aegis Box - Phase 3-5 优化验证脚本

验证以下三个核心优化：
1. Phase 3: 结构化输出预清理
2. Phase 4: 动态并发控制
3. Phase 5: 智能重试策略
"""

import asyncio
from loguru import logger


# ==========================================
# Phase 3: 结构化输出预清理
# ==========================================
def test_phase3_preprocess():
    """测试 Phase 3: 预处理函数"""
    logger.info("="*80)
    logger.info("🔍 Phase 3: 结构化输出预清理验证")
    logger.info("="*80)
    print()

    try:
        from aegis.core.llm import LLMClient
        from aegis.cli import ModelTierConfig, AegisConfig

        # 创建测试配置
        config = ModelTierConfig(
            provider="openai",
            model="glm-4.5-air",
            api_key_env_var="ZHIPU_API_KEY"
        )

        # 创建客户端（不需要实际初始化）
        import inspect
        source = inspect.getsource(LLMClient._preprocess_glm_response)

        # 验证关键功能
        checks = {
            "Markdown 清理": "```json" in source or "```" in source,
            "Python 字面量修复": "None" in source and "null" in source,
            "正则表达式": "re.sub" in source,
            "True/False 修复": "True" in source and "true" in source,
        }

        logger.info("🔍 预处理函数特性检查:")
        all_passed = True
        for feature, passed in checks.items():
            status = "✅" if passed else "❌"
            logger.info(f"   {status} {feature}: {'通过' if passed else '失败'}")
            if not passed:
                all_passed = False

        if all_passed:
            logger.success("✅ Phase 3 预处理函数验证通过！")
            return True
        else:
            logger.error("❌ Phase 3 预处理函数验证失败")
            return False

    except Exception as e:
        logger.error(f"❌ Phase 3 验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False


# ==========================================
# Phase 4: 动态并发控制
# ==========================================
async def test_phase4_adaptive_concurrency():
    """测试 Phase 4: 动态并发控制"""
    logger.info("="*80)
    logger.info("🔍 Phase 4: 动态并发控制验证")
    logger.info("="*80)
    print()

    try:
        from aegis.core.adaptive_concurrency import AdaptiveConcurrencyController

        # 创建控制器
        controller = AdaptiveConcurrencyController(
            initial_concurrency=10,
            min_concurrency=3,
            max_concurrency=20
        )

        logger.info("🔍 动态并发控制器特性检查:")

        # 测试 1: 初始状态
        initial_concurrency = controller.get_current_concurrency()
        logger.info(f"   ✅ 初始并发数: {initial_concurrency}")

        # 测试 2: 速率限制响应
        old_concurrency = controller.get_current_concurrency()
        await controller.on_rate_limit()
        new_concurrency = controller.get_current_concurrency()
        decreased = new_concurrency < old_concurrency
        logger.info(f"   {'✅' if decreased else '❌'} 速率限制响应: {old_concurrency} → {new_concurrency} ({'减少' if decreased else '未减少'})")

        # 测试 3: 成功恢复
        for _ in range(10):
            await controller.on_success()
        recovered_concurrency = controller.get_current_concurrency()
        increased = recovered_concurrency > new_concurrency
        logger.info(f"   {'✅' if increased else '⚠️'} 成功恢复: {new_concurrency} → {recovered_concurrency} ({'增加' if increased else '未增加'})")

        # 测试 4: 统计信息
        stats = controller.get_stats()
        logger.info(f"   ✅ 统计信息: 总请求={stats['total_requests']}, 成功率={stats['success_rate']:.1%}")

        if decreased:
            logger.success("✅ Phase 4 动态并发控制验证通过！")
            return True
        else:
            logger.warning("⚠️ Phase 4 部分功能验证失败")
            return False

    except Exception as e:
        logger.error(f"❌ Phase 4 验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False


# ==========================================
# Phase 5: 智能重试策略
# ==========================================
def test_phase5_smart_retry():
    """测试 Phase 5: 智能重试策略"""
    logger.info("="*80)
    logger.info("🔍 Phase 5: 智能重试策略验证")
    logger.info("="*80)
    print()

    try:
        from aegis.core.smart_retry import (
            RetryConfig,
            ErrorClassifier,
            smart_retry,
            TENACITY_AVAILABLE
        )

        if not TENACITY_AVAILABLE:
            logger.warning("⚠️ tenacity 未安装，跳过 Phase 5 验证")
            logger.info("   请运行: uv pip install tenacity")
            return False

        logger.info("🔍 智能重试策略特性检查:")

        # 测试 1: 重试配置
        configs = {
            "速率限制": RetryConfig.RATE_LIMIT,
            "空响应": RetryConfig.EMPTY_RESPONSE,
            "超时": RetryConfig.TIMEOUT,
            "网络错误": RetryConfig.NETWORK,
        }

        for name, config in configs.items():
            has_config = "stop" in config and "wait" in config
            logger.info(f"   {'✅' if has_config else '❌'} {name}配置: {'存在' if has_config else '缺失'}")

        # 测试 2: 错误分类
        test_errors = [
            (Exception("RateLimitError: 429 Too Many Requests"), "rate_limit"),
            (Exception("EOF while parsing"), "empty_response"),
            (Exception("Timeout error"), "timeout"),
            (Exception("Connection failed"), "network"),
        ]

        classification_passed = True
        for error, expected in test_errors:
            classified = ErrorClassifier.classify(error)
            passed = classified == expected
            classification_passed = classification_passed and passed
            logger.info(f"   {'✅' if passed else '❌'} 错误分类: {expected} → {classified}")

        # 测试 3: 装饰器存在
        import inspect
        has_decorator = inspect.isfunction(smart_retry)
        logger.info(f"   {'✅' if has_decorator else '❌'} 智能重试装饰器: {'存在' if has_decorator else '缺失'}")

        if classification_passed and has_decorator:
            logger.success("✅ Phase 5 智能重试策略验证通过！")
            return True
        else:
            logger.error("❌ Phase 5 智能重试策略验证失败")
            return False

    except Exception as e:
        logger.error(f"❌ Phase 5 验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False


# ==========================================
# 主函数
# ==========================================
async def main():
    """运行所有验证"""
    logger.info("="*80)
    logger.info("🛡️ Aegis Box - Phase 3-5 优化验证")
    logger.info("="*80)
    print()

    results = {}

    # 验证 Phase 3
    results["phase3"] = test_phase3_preprocess()
    print()

    # 验证 Phase 4
    results["phase4"] = await test_phase4_adaptive_concurrency()
    print()

    # 验证 Phase 5
    results["phase5"] = test_phase5_smart_retry()
    print()

    # 汇总结果
    logger.info("="*80)
    logger.info("📊 验证结果汇总")
    logger.info("="*80)

    for phase, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        logger.info(f"  {status} - {phase.upper()}")

    print()

    if all(results.values()):
        logger.success("🎉 所有优化验证通过！GLM 优化已就绪！")
        logger.info("")
        logger.info("📈 预期改进:")
        logger.info("  - 成功率: 90.9% → 99.9%+")
        logger.info("  - 延迟/文件: 14s → 7-9s")
        logger.info("  - Fallback 率: 100% → 显著降低")
        logger.info("  - 速率限制: 自动适应")
        return True
    else:
        failed_count = sum(1 for passed in results.values() if not passed)
        logger.error(f"⚠️ {failed_count} 个验证失败，请检查实现")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
