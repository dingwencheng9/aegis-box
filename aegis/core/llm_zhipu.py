#!/usr/bin/env python3
"""
🛡️ Aegis Box - 智谱 AI 原生客户端

优化亮点：
1. 使用 zai-sdk 原生客户端（无 LiteLLM 转换开销）
2. 支持 thinking 模式（推理能力增强）
3. 更好的错误处理和重试机制
4. 支持 Function Calling 和网络搜索
"""

import os
import json
import asyncio
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass
from loguru import logger

try:
    from zai import ZhipuAiClient
    import zai.core
    ZHIPU_AVAILABLE = True
except ImportError:
    ZHIPU_AVAILABLE = False
    logger.warning("zai-sdk 未安装，GLM 功能不可用。请运行: pip install zai-sdk")


# ==========================================
# 配置模型
# ==========================================
@dataclass
class ZhipuConfig:
    """智谱 AI 配置"""
    api_key: str
    model: str = "glm-4.5-air"
    base_url: str = "https://open.bigmodel.cn/api/paas/v4/"
    timeout: float = 120.0
    max_retries: int = 3
    enable_thinking: bool = False  # 推理模式


# ==========================================
# 智谱 AI 客户端（原生）
# ==========================================
class AegisZhipuClient:
    """
    Aegis 专用智谱 AI 客户端

    特性：
    - ✅ 原生 SDK（无 LiteLLM 开销）
    - ✅ 自动重试（指数退避）
    - ✅ 精细错误处理
    - ✅ Thinking 模式支持
    - ✅ 结构化输出容错
    """

    def __init__(self, config: ZhipuConfig):
        """
        初始化客户端

        Args:
            config: 智谱 AI 配置
        """
        if not ZHIPU_AVAILABLE:
            raise ImportError("zai-sdk 未安装，请运行: pip install zai-sdk")

        self.config = config
        self.client = ZhipuAiClient(
            api_key=config.api_key,
            base_url=config.base_url,
            timeout=config.timeout,
            max_retries=config.max_retries
        )

        logger.info(f"✅ ZhipuAiClient 初始化: {config.model}")

    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 4096,
        stream: bool = False,
        enable_thinking: bool = False,
        tools: Optional[List[Dict]] = None
    ) -> Union[str, Dict[str, Any]]:
        """
        聊天接口（支持同步和流式）

        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大 token 数
            stream: 是否流式输出
            enable_thinking: 是否启用推理模式
            tools: Function Calling 工具列表

        Returns:
            文本响应或完整响应对象
        """
        # 构建请求参数
        kwargs = {
            "model": self.config.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream
        }

        # 推理模式
        if enable_thinking or self.config.enable_thinking:
            kwargs["thinking"] = {"type": "enabled"}

        # Function Calling
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        # 重试逻辑
        for attempt in range(self.config.max_retries):
            try:
                response = self.client.chat.completions.create(**kwargs)

                # 流式输出
                if stream:
                    return self._handle_stream(response)

                # 同步输出
                return self._handle_response(response)

            except zai.core.APIStatusError as e:
                logger.warning(f"⚠️ API 状态错误（第 {attempt + 1}/{self.config.max_retries} 次）: {e}")
                if attempt == self.config.max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)  # 指数退避

            except zai.core.APITimeoutError as e:
                logger.warning(f"⚠️ 请求超时（第 {attempt + 1}/{self.config.max_retries} 次）: {e}")
                if attempt == self.config.max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)

            except Exception as e:
                logger.error(f"❌ 未知错误: {e}")
                raise

    def _handle_response(self, response) -> str:
        """
        处理同步响应

        Args:
            response: API 响应

        Returns:
            文本内容
        """
        choice = response.choices[0]

        # Function Calling
        if choice.message.tool_calls:
            logger.debug(f"🔧 检测到 Function Calling: {len(choice.message.tool_calls)} 个")
            return {
                "content": choice.message.content,
                "tool_calls": choice.message.tool_calls
            }

        # 普通响应
        return choice.message.content

    def _handle_stream(self, response):
        """
        处理流式响应

        Args:
            response: 流式响应迭代器

        Yields:
            文本片段
        """
        full_content = []
        reasoning_content = []

        for chunk in response:
            delta = chunk.choices[0].delta

            # 推理内容
            if hasattr(delta, 'reasoning_content') and delta.reasoning_content:
                reasoning_content.append(delta.reasoning_content)
                yield {
                    "type": "reasoning",
                    "content": delta.reasoning_content
                }

            # 普通内容
            if delta.content:
                full_content.append(delta.content)
                yield {
                    "type": "content",
                    "content": delta.content
                }

        # 最终结果
        yield {
            "type": "complete",
            "full_content": "".join(full_content),
            "reasoning": "".join(reasoning_content) if reasoning_content else None
        }

    async def structured_output(
        self,
        messages: List[Dict[str, str]],
        schema: Dict[str, Any],
        temperature: float = 0.3,
        max_tokens: int = 4096
    ) -> Dict[str, Any]:
        """
        结构化输出（带容错）

        Args:
            messages: 消息列表
            schema: JSON Schema
            temperature: 温度参数
            max_tokens: 最大 token 数

        Returns:
            解析后的结构化数据
        """
        # 在 system prompt 中注入 schema
        schema_prompt = f"""
你必须以标准 JSON 格式返回，严格遵循以下 schema：

{json.dumps(schema, indent=2, ensure_ascii=False)}

注意事项：
1. 使用 null 而非 None
2. 使用 true/false 而非 True/False
3. 确保所有必需字段都存在
4. 不要添加任何 Markdown 标记
"""

        # 添加 schema 到 messages
        enhanced_messages = [
            {"role": "system", "content": schema_prompt}
        ] + messages

        # 调用 API
        response = await self.chat(
            messages=enhanced_messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False
        )

        # 解析 JSON（带容错）
        return self._parse_json_with_fallback(response)

    def _parse_json_with_fallback(self, text: str) -> Dict[str, Any]:
        """
        解析 JSON（容错处理）

        Args:
            text: 文本内容

        Returns:
            解析后的字典
        """
        # 清理 Markdown 标记
        cleaned = text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        # 修复 Python 字面量
        cleaned = cleaned.replace(": None", ": null")
        cleaned = cleaned.replace(":None", ":null")
        cleaned = cleaned.replace(": True", ": true")
        cleaned = cleaned.replace(": False", ": false")

        # 解析
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON 解析失败: {e}")
            logger.debug(f"原始文本: {text[:500]}...")
            raise


# ==========================================
# 便捷工厂函数
# ==========================================
def create_zhipu_client(
    api_key: Optional[str] = None,
    model: str = "glm-4.5-air",
    enable_thinking: bool = False
) -> AegisZhipuClient:
    """
    创建智谱 AI 客户端

    Args:
        api_key: API Key（默认从环境变量读取）
        model: 模型名称
        enable_thinking: 是否启用推理模式

    Returns:
        客户端实例
    """
    config = ZhipuConfig(
        api_key=api_key or os.getenv("ZHIPU_API_KEY"),
        model=model,
        enable_thinking=enable_thinking
    )

    return AegisZhipuClient(config)
