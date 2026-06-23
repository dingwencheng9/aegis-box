#!/usr/bin/env python3
"""
🛡️ Aegis Box - LiteLLM vs 原生 SDK 性能对比测试

对比指标：
1. 成功率
2. 平均延迟
3. Token 消耗
4. 错误类型分布
"""

import asyncio
import time
from typing import Dict, Any, List
from dataclasses import dataclass, field
from loguru import logger

# ==========================================
# 测试数据
# ==========================================
TEST_CASES = [
    {
        "name": "简单对话",
        "messages": [{"role": "user", "content": "用一句话介绍 Python"}]
    },
    {
        "name": "代码分析",
        "messages": [{"role": "user", "content": """
分析以下代码的安全问题：

```python
def execute_command(cmd):
    os.system(cmd)
```
"""}]
    },
    {
        "name": "结构化输出",
        "messages": [{"role": "user", "content": """
返回 JSON 格式：

{
  "vulnerabilities": [
    {"level": "P0", "description": "命令注入"}
  ]
}
"""}]
    }
]


# ==========================================
# 结果数据类
# ==========================================
@dataclass
class TestResult:
    """单次测试结果"""
    success: bool
    latency: float  # 秒
    error_type: str = None
    response_length: int = 0


@dataclass
class BenchmarkResult:
    """基准测试结果"""
    name: str
    total_tests: int = 0
    successful_tests: int = 0
    failed_tests: int = 0
    total_latency: float = 0.0
    results: List[TestResult] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        """成功率"""
        return (self.successful_tests / self.total_tests * 100) if self.total_tests > 0 else 0.0

    @property
    def avg_latency(self) -> float:
        """平均延迟"""
        return (self.total_latency / self.successful_tests) if self.successful_tests > 0 else 0.0


# ==========================================
# LiteLLM 测试
# ==========================================
async def test_litellm(test_cases: List[Dict]) -> BenchmarkResult:
    """
    测试 LiteLLM 方案

    Args:
        test_cases: 测试用例列表

    Returns:
        基准测试结果
    """
    logger.info("🔹 开始测试 LiteLLM...")

    result = BenchmarkResult(name="LiteLLM")

    try:
        import litellm
        import os

        for idx, case in enumerate(test_cases, 1):
            logger.info(f"  [{idx}/{len(test_cases)}] {case['name']}")

            start_time = time.time()
            test_result = TestResult(success=False, latency=0.0)

            try:
                response = await litellm.acompletion(
                    model="openai/glm-4.5-air",
                    api_base="https://open.bigmodel.cn/api/paas/v4/",
                    api_key=os.getenv("ZHIPU_API_KEY"),
                    messages=case["messages"],
                    timeout=120.0
                )

                latency = time.time() - start_time
                content = response.choices[0].message.content

                test_result = TestResult(
                    success=True,
                    latency=latency,
                    response_length=len(content)
                )

                result.successful_tests += 1
                result.total_latency += latency

                logger.success(f"    ✅ 成功 | 延迟: {latency:.2f}s | 长度: {len(content)}")

            except Exception as e:
                latency = time.time() - start_time
                test_result = TestResult(
                    success=False,
                    latency=latency,
                    error_type=type(e).__name__
                )
                result.failed_tests += 1
                logger.error(f"    ❌ 失败 | 错误: {type(e).__name__}")

            result.results.append(test_result)
            result.total_tests += 1

    except ImportError:
        logger.warning("⚠️ litellm 未安装，跳过测试")

    return result


# ==========================================
# 原生 SDK 测试
# ==========================================
async def test_native_sdk(test_cases: List[Dict]) -> BenchmarkResult:
    """
    测试原生 SDK 方案

    Args:
        test_cases: 测试用例列表

    Returns:
        基准测试结果
    """
    logger.info("🔹 开始测试原生 SDK...")

    result = BenchmarkResult(name="原生 SDK")

    try:
        from aegis.core.llm_zhipu import create_zhipu_client

        client = create_zhipu_client()

        for idx, case in enumerate(test_cases, 1):
            logger.info(f"  [{idx}/{len(test_cases)}] {case['name']}")

            start_time = time.time()
            test_result = TestResult(success=False, latency=0.0)

            try:
                response = await client.chat(
                    messages=case["messages"],
                    temperature=0.3,
                    max_tokens=4096
                )

                latency = time.time() - start_time

                test_result = TestResult(
                    success=True,
                    latency=latency,
                    response_length=len(response)
                )

                result.successful_tests += 1
                result.total_latency += latency

                logger.success(f"    ✅ 成功 | 延迟: {latency:.2f}s | 长度: {len(response)}")

            except Exception as e:
                latency = time.time() - start_time
                test_result = TestResult(
                    success=False,
                    latency=latency,
                    error_type=type(e).__name__
                )
                result.failed_tests += 1
                logger.error(f"    ❌ 失败 | 错误: {type(e).__name__}")

            result.results.append(test_result)
            result.total_tests += 1

    except ImportError as e:
        logger.warning(f"⚠️ 原生 SDK 未安装或配置错误: {e}")

    return result


# ==========================================
# 结果对比
# ==========================================
def print_comparison(litellm_result: BenchmarkResult, native_result: BenchmarkResult):
    """
    打印对比结果

    Args:
        litellm_result: LiteLLM 结果
        native_result: 原生 SDK 结果
    """
    logger.info("="*80)
    logger.info("📊 性能对比结果")
    logger.info("="*80)

    print()
    print(f"{'指标':<20} {'LiteLLM':<20} {'原生 SDK':<20} {'提升':<15}")
    print("-"*80)

    # 成功率
    litellm_success = litellm_result.success_rate
    native_success = native_result.success_rate
    success_diff = native_success - litellm_success

    print(f"{'成功率':<20} {litellm_success:<19.1f}% {native_success:<19.1f}% {success_diff:+.1f}%")

    # 平均延迟
    litellm_latency = litellm_result.avg_latency
    native_latency = native_result.avg_latency
    latency_improvement = ((litellm_latency - native_latency) / litellm_latency * 100) if litellm_latency > 0 else 0

    print(f"{'平均延迟':<20} {litellm_latency:<19.2f}s {native_latency:<19.2f}s {latency_improvement:+.1f}%")

    # 总测试数
    print(f"{'总测试数':<20} {litellm_result.total_tests:<20} {native_result.total_tests:<20}")

    # 失败数
    print(f"{'失败数':<20} {litellm_result.failed_tests:<20} {native_result.failed_tests:<20}")

    print()
    logger.info("="*80)


# ==========================================
# 主函数
# ==========================================
async def main():
    """运行基准测试"""
    import os

    logger.info("="*80)
    logger.info("🛡️ Aegis Box - LiteLLM vs 原生 SDK 性能对比")
    logger.info("="*80)
    print()

    # 检查 API Key
    if not os.getenv("ZHIPU_API_KEY"):
        logger.error("❌ 未设置 ZHIPU_API_KEY 环境变量")
        logger.info("请设置: export ZHIPU_API_KEY=your-api-key")
        return

    # 运行测试
    logger.info(f"📋 测试用例数: {len(TEST_CASES)}")
    print()

    # LiteLLM
    litellm_result = await test_litellm(TEST_CASES)
    print()

    # 原生 SDK
    native_result = await test_native_sdk(TEST_CASES)
    print()

    # 对比结果
    print_comparison(litellm_result, native_result)

    logger.success("✅ 基准测试完成！")


if __name__ == "__main__":
    asyncio.run(main())
