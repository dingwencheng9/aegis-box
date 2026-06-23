"""
🛡️ Aegis - LLM 客户端封装
统一的大语言模型调用接口，支持多提供商、结构化输出、熔断降级
"""

import os
import time
import asyncio
from typing import Optional, Type, Union, TypeVar, Dict, Any
from enum import Enum
from pydantic import BaseModel, ValidationError
from loguru import logger
import litellm

from aegis.cli import ModelTierConfig, AegisConfig
from aegis.core.rate_limiter import RateLimiter, ExponentialBackoff


# 泛型：支持类型安全的结构化输出
T = TypeVar('T', bound=BaseModel)


# ==========================================
# 自定义异常
# ==========================================
class CircuitBreakerOpenError(Exception):
    """熔断器打开异常"""
    pass


class LLMTimeoutError(Exception):
    """LLM 请求超时"""
    pass


class LLMAPIError(Exception):
    """LLM API 调用失败"""
    pass


# ==========================================
# 熔断器状态
# ==========================================
class CircuitState(str, Enum):
    """熔断器状态"""
    CLOSED = "closed"       # 正常
    OPEN = "open"           # 熔断
    HALF_OPEN = "half_open" # 尝试恢复


# ==========================================
# LLM 客户端
# ==========================================
class LLMClient:
    """
    统一的 LLM 调用客户端

    职责：
    1. 封装单个模型配置（provider + model）
    2. 集成 RateLimiter 进行速率控制
    3. 支持 Pydantic 结构化输出（原生 LiteLLM）
    4. 熔断与降级机制
    5. 自动重试和错误处理

    Example:
        >>> client = LLMClient(config, rate_limiter)
        >>> response = await client.chat("你好")
        >>> print(response)  # 字符串
        >>>
        >>> # 结构化输出
        >>> class Summary(BaseModel):
        ...     title: str
        ...     points: List[str]
        >>> summary = await client.chat("总结这篇文章", response_model=Summary)
        >>> print(summary.title)  # Pydantic 对象
    """

    def __init__(
        self,
        config: ModelTierConfig,
        rate_limiter: RateLimiter,
        max_retries: int = 3,
        timeout: float = 60.0,
        circuit_breaker_threshold: int = 3,
        circuit_breaker_timeout: float = 60.0,
    ):
        """
        初始化 LLM 客户端

        Args:
            config: 模型配置（来自 aegis.yaml）
            rate_limiter: 速率限制器（依赖注入）
            max_retries: 最大重试次数
            timeout: 超时时间（秒）
            circuit_breaker_threshold: 熔断阈值（连续失败次数）
            circuit_breaker_timeout: 熔断后恢复尝试的等待时间（秒）
        """
        self.config = config
        self.rate_limiter = rate_limiter
        self.max_retries = max_retries
        self.timeout = timeout
        self.circuit_breaker_threshold = circuit_breaker_threshold
        self.circuit_breaker_timeout = circuit_breaker_timeout

        # 熔断器状态
        self._failure_count = 0
        self._last_failure_time: Optional[float] = None
        self._circuit_state = CircuitState.CLOSED

        # 统计信息
        self._stats = {
            "total_calls": 0,
            "success_calls": 0,
            "failed_calls": 0,
            "total_tokens": 0,
        }

        # 构建完整的模型标识符（用于 LiteLLM）
        self.model_id = f"{self.config.provider}/{self.config.model}"

        logger.info(f"LLMClient 初始化: {self.model_id}")

    async def chat(
        self,
        prompt: str,
        response_model: Optional[Type[T]] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> Union[str, T]:
        """
        统一的聊天接口

        Args:
            prompt: 用户输入
            response_model: 如果提供，强制模型输出结构化 JSON
            system_prompt: 系统提示（可选）
            temperature: 采样温度（0-2）
            max_tokens: 最大生成 token 数

        Returns:
            - 如果 response_model 为 None：返回字符串
            - 如果 response_model 提供：返回解析后的 Pydantic 对象

        Raises:
            CircuitBreakerOpenError: 熔断器打开，服务不可用
            LLMTimeoutError: 请求超时
            LLMAPIError: API 调用失败

        Example:
            >>> # 普通文本
            >>> text = await client.chat("你好，介绍一下自己")
            >>>
            >>> # 结构化输出
            >>> class UserInfo(BaseModel):
            ...     name: str
            ...     age: int
            >>> info = await client.chat(
            ...     "提取用户信息：张三，25岁",
            ...     response_model=UserInfo
            ... )
            >>> print(info.name)  # "张三"
        """
        # 1. 检查熔断器
        if self._is_circuit_open():
            raise CircuitBreakerOpenError(
                f"熔断器打开: {self.model_id} (连续失败 {self._failure_count} 次)"
            )

        # 2. 构建消息
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # 3. 动态估算 Token 数量
        estimated_tokens = self._estimate_tokens(prompt, system_prompt, max_tokens)

        # 4. 速率限制
        logger.debug(f"请求速率限制: provider={self.config.provider}, tokens={estimated_tokens}")
        await self.rate_limiter.acquire(self.config.provider, estimated_tokens)

        # 5. 实际调用（带重试）
        try:
            self._stats["total_calls"] += 1
            response = await self._call_with_retry(
                messages=messages,
                response_model=response_model,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            # 6. 记录成功
            self._record_success()
            return response

        except asyncio.TimeoutError as e:
            self._record_failure()
            logger.error(f"LLM 请求超时: {self.model_id}")
            raise LLMTimeoutError(f"请求超时: {self.model_id}") from e

        except Exception as e:
            self._record_failure()
            # Security: 过滤敏感信息
            error_msg = str(e)
            # 移除可能包含 API Key 的模式
            import re
            error_msg = re.sub(r'(api[_-]?key|authorization|bearer|token)[=:\s]+[^\s,\)]+',
                             r'\1=***REDACTED***',
                             error_msg,
                             flags=re.IGNORECASE)
            logger.error(f"LLM API 错误: {self.model_id} - {error_msg}")
            raise LLMAPIError(f"API 调用失败: {self.model_id}") from e

    async def _call_with_retry(
        self,
        messages: list,
        response_model: Optional[Type[T]],
        temperature: float,
        max_tokens: int,
    ) -> Union[str, T]:
        """
        带重试的实际调用逻辑

        Args:
            messages: 消息列表
            response_model: Pydantic 模型（可选）
            temperature: 温度
            max_tokens: 最大 token 数

        Returns:
            字符串或 Pydantic 对象
        """
        backoff = ExponentialBackoff(
            base_delay=1.0,
            max_delay=10.0,
            max_retries=self.max_retries
        )

        last_error = None

        for attempt in range(self.max_retries):
            try:
                # 获取 API Key
                api_key = self._get_api_key()

                # 准备调用参数
                call_params = {
                    "model": self.model_id,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "timeout": self.timeout,
                }

                # 如果有 API Key，显式传递
                if api_key:
                    call_params["api_key"] = api_key

                # 如果有自定义端点
                if self.config.endpoint:
                    call_params["api_base"] = self.config.endpoint

                # 如果需要结构化输出
                if response_model:
                    try:
                        # 尝试原生 LiteLLM 结构化输出
                        call_params["response_format"] = response_model
                        response = await litellm.acompletion(**call_params)
                        content = response.choices[0].message.content

                        # 解析为 Pydantic 对象
                        return response_model.model_validate_json(content)

                    except (ValidationError, AttributeError, KeyError) as e:
                        # Fallback: 手动在 system_prompt 中要求 JSON
                        logger.warning(
                            f"原生结构化输出失败，使用 fallback: {e}"
                        )
                        return await self._fallback_structured_output(
                            messages=messages,
                            response_model=response_model,
                            call_params=call_params,
                        )
                else:
                    # 普通文本输出
                    response = await litellm.acompletion(**call_params)
                    content = response.choices[0].message.content

                    # 更新 Token 统计
                    if hasattr(response, "usage") and response.usage:
                        self._stats["total_tokens"] += response.usage.total_tokens

                    return content

            except asyncio.TimeoutError:
                logger.warning(f"第 {attempt + 1} 次调用超时: {self.model_id}")
                last_error = asyncio.TimeoutError()
                if attempt < self.max_retries - 1:
                    await backoff.wait()
                    backoff.attempt += 1

            except Exception as e:
                error_str = str(e).lower()
                # 判断是否为可重试错误
                is_retryable = any(pattern in error_str for pattern in [
                    '429', 'rate limit', 'too many requests',
                    '503', 'service unavailable',
                    '502', 'bad gateway',
                    'timeout', 'connection', 'network'
                ])

                if is_retryable:
                    logger.warning(f"第 {attempt + 1} 次调用失败（可重试）: {self.model_id} - {e}")
                else:
                    logger.error(f"第 {attempt + 1} 次调用失败（不可重试）: {self.model_id} - {e}")
                    # 不可重试错误直接抛出
                    raise e

                last_error = e
                if attempt < self.max_retries - 1:
                    await backoff.wait()
                    backoff.attempt += 1

        # 所有重试都失败
        raise last_error or LLMAPIError("未知错误")

    async def _fallback_structured_output(
        self,
        messages: list,
        response_model: Type[T],
        call_params: Dict[str, Any],
    ) -> T:
        """
        Fallback 机制：在 system_prompt 中要求 JSON 输出

        Args:
            messages: 原始消息
            response_model: Pydantic 模型
            call_params: 调用参数

        Returns:
            解析后的 Pydantic 对象
        """
        # 构建 JSON Schema 提示
        schema_str = response_model.model_json_schema()
        json_instruction = f"""
你必须严格按照以下 JSON Schema 格式输出，不要包含任何其他文字：

{schema_str}

只返回有效的 JSON，不要添加任何解释或 markdown 代码块标记。
"""

        # 在 system_prompt 中追加 JSON 要求
        modified_messages = messages.copy()
        if modified_messages[0]["role"] == "system":
            modified_messages[0]["content"] += "\n\n" + json_instruction
        else:
            modified_messages.insert(0, {"role": "system", "content": json_instruction})

        # 移除 response_format（避免重复）
        call_params_copy = call_params.copy()
        call_params_copy.pop("response_format", None)
        call_params_copy["messages"] = modified_messages

        # 调用
        response = await litellm.acompletion(**call_params_copy)
        content = response.choices[0].message.content

        # 清理可能的 markdown 代码块标记
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        # 解析 JSON
        try:
            return response_model.model_validate_json(content)
        except ValidationError as e:
            logger.error(f"Fallback JSON 解析失败: {e}\n原始输出: {content}")
            raise LLMAPIError(f"结构化输出解析失败: {e}")

    def _estimate_tokens(
        self,
        prompt: str,
        system_prompt: Optional[str],
        max_tokens: int
    ) -> int:
        """
        动态估算 Token 数量

        使用简单的启发式规则：
        - 输入 token ≈ (prompt + system_prompt) 字符数 / 4
        - 输出 token ≈ max_tokens
        - 总计 = 输入 + 输出

        Args:
            prompt: 用户提示
            system_prompt: 系统提示
            max_tokens: 最大输出 token

        Returns:
            估算的总 token 数
        """
        total_chars = len(prompt)
        if system_prompt:
            total_chars += len(system_prompt)

        # 粗略估算：1 token ≈ 4 字符（英文）或 1.5 字符（中文）
        # 这里取保守值 3
        estimated_input_tokens = total_chars // 3
        estimated_total_tokens = estimated_input_tokens + max_tokens

        logger.debug(
            f"Token 估算: 输入 ~{estimated_input_tokens}, "
            f"输出 ~{max_tokens}, 总计 ~{estimated_total_tokens}"
        )

        return estimated_total_tokens

    def _get_api_key(self) -> Optional[str]:
        """
        动态读取 API Key

        从环境变量中读取 API Key，如果未配置则返回 None

        Returns:
            API Key 或 None
        """
        if not self.config.api_key_env_var:
            return None

        api_key = os.environ.get(self.config.api_key_env_var)
        if not api_key:
            logger.warning(
                f"API Key 环境变量未设置: {self.config.api_key_env_var}"
            )
        return api_key

    def _is_circuit_open(self) -> bool:
        """
        检查熔断器是否打开

        状态机：
        CLOSED (正常)
           ↓ (连续失败 >= threshold)
        OPEN (熔断)
           ↓ (等待 circuit_breaker_timeout 秒)
        HALF_OPEN (尝试恢复)
           ↓ (成功 1 次)
        CLOSED

        Returns:
            True 如果熔断器打开，False 否则
        """
        if self._circuit_state == CircuitState.CLOSED:
            return False

        if self._circuit_state == CircuitState.OPEN:
            # 检查是否可以尝试恢复
            if self._last_failure_time:
                elapsed = time.time() - self._last_failure_time
                if elapsed >= self.circuit_breaker_timeout:
                    logger.info(f"熔断器尝试恢复: {self.model_id}")
                    self._circuit_state = CircuitState.HALF_OPEN
                    return False
            return True

        # HALF_OPEN 状态允许请求通过
        return False

    def _record_failure(self):
        """记录失败，更新熔断器状态"""
        self._failure_count += 1
        self._last_failure_time = time.time()
        self._stats["failed_calls"] += 1

        logger.warning(
            f"LLM 调用失败: {self.model_id} "
            f"(连续失败 {self._failure_count}/{self.circuit_breaker_threshold})"
        )

        # 修复：只有当连续失败次数达到或超过阈值时，才打开熔断器
        if self._failure_count >= self.circuit_breaker_threshold:
            logger.error(f"🚨 触发熔断阈值！{self.model_id} 熔断器已打开。")
            self._circuit_state = CircuitState.OPEN

    def _record_success(self):
        """记录成功，重置失败计数"""
        self._stats["success_calls"] += 1

        # 如果在 HALF_OPEN 状态，恢复到 CLOSED
        if self._circuit_state == CircuitState.HALF_OPEN:
            logger.info(f"熔断器恢复正常: {self.model_id}")
            self._circuit_state = CircuitState.CLOSED

        # 重置失败计数
        if self._failure_count > 0:
            logger.info(
                f"LLM 调用成功，重置失败计数: {self.model_id} "
                f"(之前失败 {self._failure_count} 次)"
            )
            self._failure_count = 0
            self._last_failure_time = None

    def get_stats(self) -> Dict[str, Any]:
        """
        获取客户端统计信息

        Returns:
            统计信息字典，包含：
            - total_calls: 总调用次数
            - success_calls: 成功次数
            - failed_calls: 失败次数
            - total_tokens: 总 token 消耗
            - success_rate: 成功率
            - circuit_state: 熔断器状态
        """
        total = self._stats["total_calls"]
        success = self._stats["success_calls"]
        success_rate = (success / total * 100) if total > 0 else 0

        return {
            **self._stats,
            "success_rate": f"{success_rate:.1f}%",
            "circuit_state": self._circuit_state.value,
            "failure_count": self._failure_count,
            "model_id": self.model_id,
        }


# ==========================================
# LLM 客户端工厂
# ==========================================
class LLMClientFactory:
    """
    LLM 客户端工厂

    职责：
    1. 创建并管理 RateLimiter（单例）
    2. 为 Tier-1/2/3 创建专用客户端
    3. 确保所有客户端共享同一个 RateLimiter

    Example:
        >>> config = ConfigManager.load()
        >>> factory = LLMClientFactory(config)
        >>>
        >>> tier1 = factory.create_tier1_client()
        >>> tier2 = factory.create_tier2_client()
        >>>
        >>> # 两个客户端共享同一个速率限制器
        >>> response1 = await tier1.chat("...")
        >>> response2 = await tier2.chat("...")
    """

    def __init__(self, config: AegisConfig):
        """
        初始化工厂

        Args:
            config: Aegis 全局配置
        """
        self.config = config

        # 创建共享的 RateLimiter（单例）
        self.rate_limiter = RateLimiter(
            global_qps=config.rate_limit.global_qps,
            provider_limits=config.rate_limit.provider_limits,
            token_bucket_capacity=config.rate_limit.token_bucket_capacity,
            token_bucket_refill_rate=config.rate_limit.token_bucket_refill_rate,
        )

        logger.info("LLMClientFactory 初始化完成")

    def create_tier1_client(self) -> LLMClient:
        """
        创建 Tier-1 客户端（快速探伤）

        配置：
        - 快速失败（max_retries=2）
        - 较短超时（30 秒）
        - 适用于并发扫描大量文件

        Returns:
            Tier-1 LLMClient 实例
        """
        return LLMClient(
            config=self.config.llm["tier1_fast"],
            rate_limiter=self.rate_limiter,
            max_retries=2,
            timeout=30.0,
            circuit_breaker_threshold=5,  # Tier-1 允许更多失败
        )

    def create_tier2_client(self) -> LLMClient:
        """
        创建 Tier-2 客户端（架构推理）

        配置：
        - 中等重试（max_retries=3）
        - 标准超时（60 秒）
        - 适用于宏观架构总结

        Returns:
            Tier-2 LLMClient 实例
        """
        return LLMClient(
            config=self.config.llm["tier2_reasoning"],
            rate_limiter=self.rate_limiter,
            max_retries=3,
            timeout=60.0,
            circuit_breaker_threshold=3,
        )

    def create_tier3_client(self) -> LLMClient:
        """
        创建 Tier-3 客户端（补丁生成）

        配置：
        - 最大重试（max_retries=3）
        - 较长超时（120 秒）
        - 适用于生成高质量代码补丁

        Returns:
            Tier-3 LLMClient 实例
        """
        return LLMClient(
            config=self.config.llm["tier3_patching"],
            rate_limiter=self.rate_limiter,
            max_retries=3,
            timeout=120.0,
            circuit_breaker_threshold=2,  # Tier-3 严格，快速熔断
        )

    def get_rate_limiter_stats(self) -> Dict[str, Any]:
        """
        获取共享的 RateLimiter 统计信息

        Returns:
            速率限制器统计信息
        """
        return self.rate_limiter.get_stats()
