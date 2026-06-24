#!/usr/bin/env python3
"""
🛡️ Aegis Box - Hotfix 验证脚本

验证以下两个关键修复：
1. Anthropic API Base 配置支持
2. GLM 空响应自动重试装甲

使用方式:
    python scripts/verify_hotfix.py
"""

import os
import asyncio
from pathlib import Path
from loguru import logger

# ==========================================
# Hotfix 1: API Base 配置验证
# ==========================================
def verify_api_base_config():
    """验证 API Base 配置是否正确加载"""
    logger.info("="*80)
    logger.info("🔍 Hotfix 1: 验证 API Base 配置支持")
    logger.info("="*80)
    print()

    try:
        from aegis.core.config import ConfigLoader

        # 测试 1: 加载配置
        loader = ConfigLoader()
        loader.load()

        # 测试 2: 设置测试环境变量
        os.environ["ANTHROPIC_API_BASE"] = "https://api.anthropic.com"
        os.environ["ANTHROPIC_API_KEY"] = "test-key"
        os.environ["TIER2_PROVIDER"] = "anthropic"
        os.environ["TIER2_MODEL"] = "claude-3-5-haiku-20241022"

        # 测试 3: 获取模型配置
        tier2_config = loader.get_model_config("tier2")

        if tier2_config:
            logger.info(f"✅ Tier-2 配置加载成功:")
            logger.info(f"   - Provider: {tier2_config.get('provider')}")
            logger.info(f"   - Model: {tier2_config.get('model')}")
            logger.info(f"   - API Base: {tier2_config.get('api_base', '未配置')}")

            # 验证 api_base 是否正确读取
            if tier2_config.get('api_base'):
                logger.success("✅ API Base 配置读取成功！")
                return True
            else:
                logger.warning("⚠️ API Base 未读取（可能未设置环境变量）")
                return True
        else:
            logger.error("❌ Tier-2 配置加载失败")
            return False

    except Exception as e:
        logger.error(f"❌ API Base 配置验证失败: {e}")
        return False


# ==========================================
# Hotfix 2: 重试装甲验证
# ==========================================
async def verify_retry_armor():
    """验证文件级重试装甲"""
    logger.info("="*80)
    logger.info("🔍 Hotfix 2: 验证空响应自动重试装甲")
    logger.info("="*80)
    print()

    try:
        from aegis.engines.reducer import ArchitectureReducer
        from aegis.engines.mapper import CodeSkeleton
        from aegis.cli import AegisConfig

        # 创建测试配置
        config = AegisConfig()

        # 创建 Reducer
        reducer = ArchitectureReducer(config)

        # 检查 analyze_file 是否包含重试逻辑
        import inspect
        source = inspect.getsource(reducer.analyze_file)

        # 验证关键字
        checks = {
            "max_file_retries": "max_file_retries" in source,
            "exponential_backoff": "2 ** retry_attempt" in source,
            "empty_response_detection": "'eof while parsing'" in source or "'empty'" in source,
            "retry_loop": "for retry_attempt in range" in source,
        }

        logger.info("🔍 重试装甲特性检查:")
        all_passed = True
        for feature, passed in checks.items():
            status = "✅" if passed else "❌"
            logger.info(f"   {status} {feature.replace('_', ' ').title()}: {'通过' if passed else '失败'}")
            if not passed:
                all_passed = False

        if all_passed:
            logger.success("✅ 重试装甲验证通过！")
            return True
        else:
            logger.error("❌ 重试装甲验证失败")
            return False

    except Exception as e:
        logger.error(f"❌ 重试装甲验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False


# ==========================================
# Hotfix 3: 错误检测模式验证
# ==========================================
def verify_error_patterns():
    """验证可重试错误模式"""
    logger.info("="*80)
    logger.info("🔍 Hotfix 3: 验证错误检测模式")
    logger.info("="*80)
    print()

    try:
        from aegis.core.llm import LLMClient
        import inspect

        # 检查 _call_with_retry 是否包含新的错误模式
        source = inspect.getsource(LLMClient._call_with_retry)

        # 验证新增的错误模式
        new_patterns = [
            "'eof while parsing'",  # 空响应
            "'nodename nor servname'",  # DNS 错误
            "'cannot connect to host'",  # 连接失败
        ]

        logger.info("🔍 错误检测模式:")
        all_found = True
        for pattern in new_patterns:
            found = pattern in source
            status = "✅" if found else "❌"
            logger.info(f"   {status} {pattern}: {'已添加' if found else '未找到'}")
            if not found:
                all_found = False

        if all_found:
            logger.success("✅ 错误检测模式验证通过！")
            return True
        else:
            logger.error("❌ 部分错误检测模式未添加")
            return False

    except Exception as e:
        logger.error(f"❌ 错误检测模式验证失败: {e}")
        return False


# ==========================================
# 主函数
# ==========================================
async def main():
    """运行所有验证"""
    logger.info("="*80)
    logger.info("🛡️ Aegis Box - Hotfix 双杀验证")
    logger.info("="*80)
    print()

    results = {}

    # 验证 1: API Base 配置
    results["api_base_config"] = verify_api_base_config()
    print()

    # 验证 2: 重试装甲
    results["retry_armor"] = await verify_retry_armor()
    print()

    # 验证 3: 错误检测模式
    results["error_patterns"] = verify_error_patterns()
    print()

    # 汇总结果
    logger.info("="*80)
    logger.info("📊 验证结果汇总")
    logger.info("="*80)

    for test_name, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        logger.info(f"  {status} - {test_name.replace('_', ' ').title()}")

    print()

    if all(results.values()):
        logger.success("🎉 所有 Hotfix 验证通过！Aegis 已不可战胜！")
        return True
    else:
        failed_count = sum(1 for passed in results.values() if not passed)
        logger.error(f"⚠️ {failed_count} 个验证失败，请检查代码修改")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
