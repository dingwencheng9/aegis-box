"""
🛡️ Aegis - 多层级速率限制器
实现全局 QPS、Provider 级别、Token 桶三重限流机制
"""

import asyncio
import time
from typing import Dict, Optional
from collections import deque
from loguru import logger
from aiolimiter import AsyncLimiter


class TokenBucket:
    """Token 桶算法实现，用于平滑突发流量"""

    def __init__(self, capacity: int, refill_rate: float):
        """
        Args:
            capacity: 桶容量（最大 token 数量）
            refill_rate: 每秒补充的 token 数量
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill_time = time.monotonic()
        self._lock = asyncio.Lock()

    async def consume(self, tokens: int) -> bool:
        """
        尝试消费指定数量的 token

        Args:
            tokens: 需要消费的 token 数量

        Returns:
            是否成功消费
        """
        async with self._lock:
            # 计算自上次补充以来应该补充的 token
            now = time.monotonic()
            elapsed = now - self.last_refill_time
            refill_amount = elapsed * self.refill_rate

            # 补充 token（不超过容量）
            self.tokens = min(self.capacity, self.tokens + refill_amount)
            self.last_refill_time = now

            # 尝试消费
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            else:
                # Token 不足，等待一段时间
                wait_time = (tokens - self.tokens) / self.refill_rate
                logger.debug(f"Token 桶不足，等待 {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
                self.tokens = 0  # 消费完
                return True


class RateLimiter:
    """
    三层速率限制器
    Layer 1: 全局 QPS 限制（防止被封号）
    Layer 2: 按 Provider 限制（遵守各厂商的 API 限流规则）
    Layer 3: Token 桶（平滑突发流量）
    """

    def __init__(
        self,
        global_qps: int = 10,
        provider_limits: Optional[Dict[str, int]] = None,
        token_bucket_capacity: int = 1000,
        token_bucket_refill_rate: float = 10.0,
    ):
        """
        Args:
            global_qps: 全局每秒请求数
            provider_limits: 各 Provider 的每分钟请求数限制
            token_bucket_capacity: Token 桶容量
            token_bucket_refill_rate: Token 桶每秒补充速率
        """
        # Layer 1: 全局限流
        self.global_limiter = AsyncLimiter(max_rate=global_qps, time_period=1.0)

        # Layer 2: 按 Provider 限流
        self.provider_limits = provider_limits or {
            "openai": 50,
            "anthropic": 40,
            "zhipu": 100,
            "ollama": 10000,  # 本地模型几乎无限制
        }
        self.provider_limiters: Dict[str, AsyncLimiter] = {
            provider: AsyncLimiter(max_rate=limit, time_period=60.0)
            for provider, limit in self.provider_limits.items()
        }

        # Layer 3: Token 桶
        self.token_bucket = TokenBucket(
            capacity=token_bucket_capacity,
            refill_rate=token_bucket_refill_rate
        )

        # 统计信息
        self.stats = {
            "total_requests": 0,
            "total_tokens": 0,
            "provider_counts": {provider: 0 for provider in self.provider_limits},
        }

    async def acquire(self, provider: str, estimated_tokens: int = 1000):
        """
        申请速率限制资源（三层检查）

        Args:
            provider: LLM 提供商名称
            estimated_tokens: 预估的 token 消耗量
        """
        # 确保 provider 存在
        if provider not in self.provider_limiters:
            logger.warning(f"未知 Provider: {provider}，使用默认限流规则")
            self.provider_limiters[provider] = AsyncLimiter(max_rate=50, time_period=60.0)

        # Layer 1: 全局 QPS 限制
        async with self.global_limiter:
            # Layer 2: Provider 级别限制
            async with self.provider_limiters[provider]:
                # Layer 3: Token 桶限流
                await self.token_bucket.consume(estimated_tokens)

                # 更新统计
                self.stats["total_requests"] += 1
                self.stats["total_tokens"] += estimated_tokens
                self.stats["provider_counts"][provider] = self.stats["provider_counts"].get(provider, 0) + 1

                logger.debug(
                    f"速率限制通过: provider={provider}, tokens={estimated_tokens}, "
                    f"total_requests={self.stats['total_requests']}"
                )

    def get_stats(self) -> Dict:
        """获取统计信息"""
        return self.stats.copy()


class ExponentialBackoff:
    """指数退避重试机制"""

    def __init__(
        self,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        max_retries: int = 5,
    ):
        """
        Args:
            base_delay: 初始延迟（秒）
            max_delay: 最大延迟（秒）
            max_retries: 最大重试次数
        """
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.max_retries = max_retries
        self.attempt = 0

    async def wait(self):
        """执行退避等待"""
        if self.attempt >= self.max_retries:
            raise Exception(f"达到最大重试次数 ({self.max_retries})")

        delay = min(self.base_delay * (2 ** self.attempt), self.max_delay)
        logger.warning(f"第 {self.attempt + 1} 次重试，等待 {delay:.2f}s")
        await asyncio.sleep(delay)
        self.attempt += 1

    def reset(self):
        """重置重试计数器"""
        self.attempt = 0
