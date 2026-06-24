"""
🛡️ Aegis - 智能重试策略

Phase 5: 细粒度智能重试（Smart Retry）

基于 tenacity 实现差异化重试策略：
- rate_limit: 5 次重试，基准延迟 2s
- empty_response: 4 次重试，基准延迟 1.5s
- timeout: 3 次重试，基准延迟 1s
- network: 3 次重试，基准延迟 2s
"""

from typing import Callable, Any, Optional
from functools import wraps
from loguru import logger

try:
    from tenacity import (
        retry,
        stop_after_attempt,
        wait_exponential,
        retry_if_exception_type,
        before_sleep_log,
    )
    TENACITY_AVAILABLE = True
except ImportError:
    TENACITY_AVAILABLE = False
    logger.warning("tenacity 未安装，智能重试不可用。请运行: uv pip install tenacity")


# ==========================================
# 重试配置
# ==========================================
class RetryConfig:
    """重试配置枚举"""

    # 速率限制（最激进）
    RATE_LIMIT = {
        "stop": stop_after_attempt(5),
        "wait": wait_exponential(multiplier=2, min=2, max=30),
        "retry": retry_if_exception_type(Exception),  # 匹配所有异常，由装饰器内部过滤
    }

    # 空响应
    EMPTY_RESPONSE = {
        "stop": stop_after_attempt(4),
        "wait": wait_exponential(multiplier=1.5, min=1.5, max=20),
        "retry": retry_if_exception_type(Exception),
    }

    # 超时
    TIMEOUT = {
        "stop": stop_after_attempt(3),
        "wait": wait_exponential(multiplier=1, min=1, max=10),
        "retry": retry_if_exception_type(Exception),
    }

    # 网络错误
    NETWORK = {
        "stop": stop_after_attempt(3),
        "wait": wait_exponential(multiplier=2, min=2, max=20),
        "retry": retry_if_exception_type(Exception),
    }

    # 默认策略
    DEFAULT = {
        "stop": stop_after_attempt(3),
        "wait": wait_exponential(multiplier=1, min=1, max=10),
        "retry": retry_if_exception_type(Exception),
    }


# ==========================================
# 错误分类器
# ==========================================
class ErrorClassifier:
    """错误分类器"""

    @staticmethod
    def classify(error: Exception) -> str:
        """
        分类错误类型

        Args:
            error: 异常对象

        Returns:
            错误类型（rate_limit, empty_response, timeout, network, unknown）
        """
        error_str = str(error).lower()
        error_type = type(error).__name__.lower()

        # 速率限制
        if 'ratelimiterror' in error_type or 'rate limit' in error_str or '速率限制' in error_str or '429' in error_str:
            return "rate_limit"

        # 空响应
        if 'eof while parsing' in error_str or 'empty' in error_str:
            return "empty_response"

        # 超时
        if 'timeout' in error_type or 'timeout' in error_str:
            return "timeout"

        # 网络错误
        if 'connection' in error_str or 'network' in error_str or 'nodename nor servname' in error_str:
            return "network"

        return "unknown"

    @staticmethod
    def should_retry(error: Exception) -> bool:
        """
        判断是否应该重试

        Args:
            error: 异常对象

        Returns:
            是否应该重试
        """
        error_type = ErrorClassifier.classify(error)
        return error_type in ["rate_limit", "empty_response", "timeout", "network"]


# ==========================================
# 智能重试装饰器
# ==========================================
def smart_retry(func: Optional[Callable] = None, *, enable: bool = True):
    """
    智能重试装饰器

    根据错误类型动态选择重试策略

    Args:
        func: 被装饰的函数
        enable: 是否启用（用于开关）

    Example:
        >>> @smart_retry
        ... async def api_call():
        ...     return await client.chat(...)
    """
    if not TENACITY_AVAILABLE:
        # tenacity 未安装，返回原函数
        if func is None:
            return lambda f: f
        return func

    def decorator(f: Callable) -> Callable:
        if not enable:
            return f

        @wraps(f)
        async def wrapper(*args, **kwargs) -> Any:
            """
            包装函数，动态选择重试策略
            """
            # 首次尝试
            try:
                return await f(*args, **kwargs)
            except Exception as first_error:
                # 分类错误
                error_type = ErrorClassifier.classify(first_error)

                # 不可重试错误，直接抛出
                if not ErrorClassifier.should_retry(first_error):
                    logger.error(f"❌ 不可重试错误: {error_type} - {first_error}")
                    raise

                # 选择重试配置
                if error_type == "rate_limit":
                    config = RetryConfig.RATE_LIMIT
                    logger.warning(f"⚠️ 检测到速率限制，使用激进重试策略（最多 5 次）")
                elif error_type == "empty_response":
                    config = RetryConfig.EMPTY_RESPONSE
                    logger.warning(f"⚠️ 检测到空响应，使用标准重试策略（最多 4 次）")
                elif error_type == "timeout":
                    config = RetryConfig.TIMEOUT
                    logger.warning(f"⚠️ 检测到超时，使用快速重试策略（最多 3 次）")
                elif error_type == "network":
                    config = RetryConfig.NETWORK
                    logger.warning(f"⚠️ 检测到网络错误，使用标准重试策略（最多 3 次）")
                else:
                    config = RetryConfig.DEFAULT
                    logger.warning(f"⚠️ 未知错误类型，使用默认重试策略")

                # 创建动态重试器
                retryer = retry(
                    stop=config["stop"],
                    wait=config["wait"],
                    retry=config["retry"],
                    before_sleep=before_sleep_log(logger, "warning"),
                    reraise=True,
                )

                # 应用重试
                retry_func = retryer(f)
                return await retry_func(*args, **kwargs)

        return wrapper

    if func is None:
        return decorator
    return decorator(func)


# ==========================================
# 辅助函数
# ==========================================
def get_retry_stats(func: Callable) -> dict:
    """
    获取函数的重试统计

    Args:
        func: 被装饰的函数

    Returns:
        统计信息字典
    """
    if not TENACITY_AVAILABLE:
        return {}

    if hasattr(func, "retry"):
        statistics = func.retry.statistics
        return {
            "attempt_number": statistics.get("attempt_number", 0),
            "delay_since_first_attempt": statistics.get("delay_since_first_attempt", 0),
        }

    return {}
