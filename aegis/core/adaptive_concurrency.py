"""
🛡️ Aegis - 自适应并发控制器

Phase 4: 动态并发控制（消灭 429 速率限制）

基于 AIMD（加性增、乘性减）算法，类似 TCP 拥塞控制：
- 遇到速率限制 → 快速减半并发
- 连续成功 → 缓慢增加并发
"""

import asyncio
from typing import Optional
from loguru import logger


class AdaptiveConcurrencyController:
    """
    自适应并发控制器

    特性：
    - ✅ AIMD 算法（Additive Increase, Multiplicative Decrease）
    - ✅ 速率限制快速响应（乘性减半）
    - ✅ 成功时缓慢恢复（加性增长）
    - ✅ 最小/最大并发保护
    - ✅ 线程安全

    Example:
        >>> controller = AdaptiveConcurrencyController(initial=10)
        >>> semaphore = controller.get_semaphore()
        >>> async with semaphore:
        ...     try:
        ...         await api_call()
        ...         controller.on_success()
        ...     except RateLimitError:
        ...         controller.on_rate_limit()
    """

    def __init__(
        self,
        initial_concurrency: int = 10,
        min_concurrency: int = 3,
        max_concurrency: int = 20,
        increase_step: int = 1,  # 加性增长步长
        decrease_factor: float = 0.5,  # 乘性减半因子
    ):
        """
        初始化控制器

        Args:
            initial_concurrency: 初始并发数
            min_concurrency: 最小并发数
            max_concurrency: 最大并发数
            increase_step: 成功时增加的步长
            decrease_factor: 速率限制时的减小因子
        """
        self.current = initial_concurrency
        self.min = min_concurrency
        self.max = max_concurrency
        self.increase_step = increase_step
        self.decrease_factor = decrease_factor

        # 统计信息
        self.rate_limit_count = 0
        self.success_count = 0
        self.consecutive_successes = 0
        self.total_requests = 0

        # 信号量（动态调整）
        self._semaphore = asyncio.Semaphore(initial_concurrency)
        self._lock = asyncio.Lock()

        logger.info(f"🎯 自适应并发控制器初始化: {initial_concurrency} (范围: {min_concurrency}-{max_concurrency})")

    def get_semaphore(self) -> asyncio.Semaphore:
        """获取当前信号量"""
        return self._semaphore

    async def on_rate_limit(self):
        """
        速率限制回调（乘性减）

        触发条件：捕获到 429 Too Many Requests

        策略：
        - 并发 = max(min, current * decrease_factor)
        - 快速响应，避免持续触发速率限制
        """
        async with self._lock:
            old_concurrency = self.current
            self.current = max(self.min, int(self.current * self.decrease_factor))
            self.rate_limit_count += 1
            self.consecutive_successes = 0  # 重置连续成功计数

            # 重新创建信号量
            if self.current != old_concurrency:
                self._semaphore = asyncio.Semaphore(self.current)
                logger.warning(
                    f"🔻 速率限制触发！降低并发: {old_concurrency} → {self.current} "
                    f"(累计触发 {self.rate_limit_count} 次)"
                )

    async def on_success(self):
        """
        成功回调（加性增）

        触发条件：请求成功完成

        策略：
        - 每 N 次连续成功，增加 1 个并发
        - 缓慢恢复，避免过快触发速率限制
        """
        async with self._lock:
            self.success_count += 1
            self.consecutive_successes += 1
            self.total_requests += 1

            # 每 10 次连续成功，增加 1 个并发
            if self.consecutive_successes >= 10:
                old_concurrency = self.current
                self.current = min(self.max, self.current + self.increase_step)
                self.consecutive_successes = 0  # 重置

                # 重新创建信号量
                if self.current != old_concurrency:
                    self._semaphore = asyncio.Semaphore(self.current)
                    logger.info(
                        f"🔺 恢复并发: {old_concurrency} → {self.current} "
                        f"(成功率: {self.get_success_rate():.1%})"
                    )

    async def on_error(self, error_type: str = "unknown"):
        """
        通用错误回调

        Args:
            error_type: 错误类型（rate_limit, timeout, network 等）
        """
        async with self._lock:
            self.total_requests += 1

            # 速率限制错误特殊处理
            if error_type == "rate_limit":
                await self.on_rate_limit()

    def get_current_concurrency(self) -> int:
        """获取当前并发数"""
        return self.current

    def get_success_rate(self) -> float:
        """获取成功率"""
        if self.total_requests == 0:
            return 1.0
        return self.success_count / self.total_requests

    def get_stats(self) -> dict:
        """获取统计信息"""
        return {
            "current_concurrency": self.current,
            "total_requests": self.total_requests,
            "success_count": self.success_count,
            "rate_limit_count": self.rate_limit_count,
            "success_rate": self.get_success_rate(),
        }

    def reset(self, initial_concurrency: Optional[int] = None):
        """
        重置控制器

        Args:
            initial_concurrency: 新的初始并发数（可选）
        """
        if initial_concurrency:
            self.current = initial_concurrency
        else:
            self.current = 10  # 默认值

        self._semaphore = asyncio.Semaphore(self.current)
        self.rate_limit_count = 0
        self.success_count = 0
        self.consecutive_successes = 0
        self.total_requests = 0

        logger.info(f"🔄 并发控制器已重置: {self.current}")
