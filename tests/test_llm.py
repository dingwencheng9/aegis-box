"""
测试 LLM 客户端的核心功能
"""

import pytest
import asyncio
from typing import List
from pydantic import BaseModel
from unittest.mock import AsyncMock, MagicMock, patch

from aegis.core.llm import (
    LLMClient,
    LLMClientFactory,
    CircuitBreakerOpenError,
    LLMTimeoutError,
    LLMAPIError,
    CircuitState,
)
from aegis.core.rate_limiter import RateLimiter
from aegis.cli import ModelTierConfig, AegisConfig


# ==========================================
# 测试用 Pydantic 模型
# ==========================================
class TestSummary(BaseModel):
    """测试用的结构化输出模型"""
    title: str
    points: List[str]
    score: int


# ==========================================
# Fixtures
# ==========================================
@pytest.fixture
def mock_rate_limiter():
    """Mock RateLimiter"""
    limiter = MagicMock(spec=RateLimiter)
    limiter.acquire = AsyncMock()
    return limiter


@pytest.fixture
def mock_model_config():
    """Mock ModelTierConfig"""
    return ModelTierConfig(
        provider="openai",
        model="gpt-4o-mini",
        api_key_env_var="OPENAI_API_KEY",
    )


@pytest.fixture
def llm_client(mock_model_config, mock_rate_limiter):
    """创建测试用的 LLMClient"""
    return LLMClient(
        config=mock_model_config,
        rate_limiter=mock_rate_limiter,
        max_retries=2,
        timeout=10.0,
    )


@pytest.fixture
def mock_aegis_config():
    """Mock AegisConfig"""
    return AegisConfig(
        llm={
            "tier1_fast": ModelTierConfig(
                provider="openai",
                model="gpt-4o-mini",
                api_key_env_var="OPENAI_API_KEY",
            ),
            "tier2_reasoning": ModelTierConfig(
                provider="anthropic",
                model="claude-3-5-haiku-20241022",
                api_key_env_var="ANTHROPIC_API_KEY",
            ),
            "tier3_patching": ModelTierConfig(
                provider="anthropic",
                model="claude-3-5-sonnet-20241022",
                api_key_env_var="ANTHROPIC_API_KEY",
            ),
        }
    )


# ==========================================
# 单元测试
# ==========================================
def test_llm_client_initialization(llm_client):
    """测试 LLMClient 初始化"""
    assert llm_client.model_id == "openai/gpt-4o-mini"
    assert llm_client.max_retries == 2
    assert llm_client._circuit_state == CircuitState.CLOSED
    assert llm_client._failure_count == 0


def test_estimate_tokens(llm_client):
    """测试 Token 估算"""
    # 短提示
    tokens = llm_client._estimate_tokens("Hello", None, 100)
    assert tokens > 100  # 应该包含输入和输出

    # 长提示
    long_prompt = "A" * 3000  # 3000 字符
    tokens = llm_client._estimate_tokens(long_prompt, None, 500)
    assert tokens > 1000  # 3000/3 + 500 = 1500

    # 带 system_prompt
    tokens = llm_client._estimate_tokens("Hello", "You are a helpful assistant", 100)
    assert tokens > 100


def test_get_api_key(llm_client, monkeypatch):
    """测试 API Key 获取"""
    # 设置环境变量
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-123")
    api_key = llm_client._get_api_key()
    assert api_key == "test-key-123"

    # 未设置环境变量
    monkeypatch.delenv("OPENAI_API_KEY")
    api_key = llm_client._get_api_key()
    assert api_key is None


def test_circuit_breaker_closed(llm_client):
    """测试熔断器关闭状态"""
    assert not llm_client._is_circuit_open()
    assert llm_client._circuit_state == CircuitState.CLOSED


def test_circuit_breaker_open(llm_client):
    """测试熔断器打开"""
    # 记录 3 次失败（达到阈值）
    for _ in range(3):
        llm_client._record_failure()

    assert llm_client._circuit_state == CircuitState.OPEN
    assert llm_client._is_circuit_open()


def test_circuit_breaker_recovery(llm_client):
    """测试熔断器恢复"""
    # 先打开熔断器
    for _ in range(3):
        llm_client._record_failure()
    assert llm_client._circuit_state == CircuitState.OPEN

    # 模拟时间过去（超过恢复时间）
    import time
    llm_client._last_failure_time = time.time() - 61  # 61 秒前

    # 检查是否切换到 HALF_OPEN
    assert not llm_client._is_circuit_open()
    assert llm_client._circuit_state == CircuitState.HALF_OPEN

    # 记录成功，恢复到 CLOSED
    llm_client._record_success()
    assert llm_client._circuit_state == CircuitState.CLOSED


def test_record_success_resets_failure_count(llm_client):
    """测试成功调用重置失败计数"""
    llm_client._failure_count = 2
    llm_client._record_success()
    assert llm_client._failure_count == 0


def test_get_stats(llm_client):
    """测试统计信息获取"""
    llm_client._stats["total_calls"] = 10
    llm_client._stats["success_calls"] = 8
    llm_client._stats["failed_calls"] = 2

    stats = llm_client.get_stats()
    assert stats["total_calls"] == 10
    assert stats["success_calls"] == 8
    assert stats["failed_calls"] == 2
    assert stats["success_rate"] == "80.0%"
    assert stats["circuit_state"] == "closed"


@pytest.mark.asyncio
async def test_chat_circuit_breaker_open(llm_client):
    """测试熔断器打开时拒绝请求"""
    # 先打开熔断器
    for _ in range(3):
        llm_client._record_failure()

    # 尝试调用应该抛出异常
    with pytest.raises(CircuitBreakerOpenError):
        await llm_client.chat("Hello")


@pytest.mark.asyncio
async def test_chat_with_mock_litellm(llm_client, monkeypatch):
    """测试普通文本调用（Mock LiteLLM）"""
    # Mock litellm.acompletion
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Hello, I'm an AI assistant."
    mock_response.usage = MagicMock()
    mock_response.usage.total_tokens = 50

    async def mock_acompletion(*args, **kwargs):
        return mock_response

    monkeypatch.setattr("litellm.acompletion", mock_acompletion)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    # 调用
    response = await llm_client.chat("Hello")

    # 验证
    assert response == "Hello, I'm an AI assistant."
    assert llm_client._stats["success_calls"] == 1
    assert llm_client._stats["total_tokens"] == 50


@pytest.mark.asyncio
async def test_chat_structured_output_fallback(llm_client, monkeypatch):
    """测试结构化输出的 fallback 机制"""
    # Mock litellm.acompletion 第一次抛出异常，第二次成功
    call_count = 0

    async def mock_acompletion(*args, **kwargs):
        nonlocal call_count
        call_count += 1

        if call_count == 1:
            # 第一次调用（原生结构化输出）失败
            raise AttributeError("response_format not supported")
        else:
            # 第二次调用（fallback）成功
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = '''
            {
                "title": "Test Summary",
                "points": ["Point 1", "Point 2"],
                "score": 85
            }
            '''
            return mock_response

    monkeypatch.setattr("litellm.acompletion", mock_acompletion)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    # 调用
    response = await llm_client.chat(
        "Summarize this",
        response_model=TestSummary
    )

    # 验证
    assert isinstance(response, TestSummary)
    assert response.title == "Test Summary"
    assert len(response.points) == 2
    assert response.score == 85
    assert call_count == 2  # 第一次失败，第二次成功


# ==========================================
# LLMClientFactory 测试
# ==========================================
def test_factory_initialization(mock_aegis_config):
    """测试工厂初始化"""
    factory = LLMClientFactory(mock_aegis_config)
    assert factory.rate_limiter is not None


def test_factory_create_tier1_client(mock_aegis_config):
    """测试创建 Tier-1 客户端"""
    factory = LLMClientFactory(mock_aegis_config)
    client = factory.create_tier1_client()

    assert client.model_id == "openai/gpt-4o-mini"
    assert client.max_retries == 2
    assert client.timeout == 30.0


def test_factory_create_tier2_client(mock_aegis_config):
    """测试创建 Tier-2 客户端"""
    factory = LLMClientFactory(mock_aegis_config)
    client = factory.create_tier2_client()

    assert client.model_id == "anthropic/claude-3-5-haiku-20241022"
    assert client.max_retries == 3
    assert client.timeout == 60.0


def test_factory_create_tier3_client(mock_aegis_config):
    """测试创建 Tier-3 客户端"""
    factory = LLMClientFactory(mock_aegis_config)
    client = factory.create_tier3_client()

    assert client.model_id == "anthropic/claude-3-5-sonnet-20241022"
    assert client.max_retries == 3
    assert client.timeout == 120.0


def test_factory_shared_rate_limiter(mock_aegis_config):
    """测试工厂创建的客户端共享同一个 RateLimiter"""
    factory = LLMClientFactory(mock_aegis_config)
    client1 = factory.create_tier1_client()
    client2 = factory.create_tier2_client()
    client3 = factory.create_tier3_client()

    # 所有客户端应该共享同一个 RateLimiter 实例
    assert client1.rate_limiter is client2.rate_limiter
    assert client2.rate_limiter is client3.rate_limiter
    assert client1.rate_limiter is factory.rate_limiter
