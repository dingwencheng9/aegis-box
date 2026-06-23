#!/usr/bin/env python3
"""
🛡️ Aegis Box - Unified Configuration Loader

统一配置加载器：支持 .env + aegis.yaml 的分层配置策略

优先级：环境变量 > aegis.yaml > 默认值
设计原则：幂等性、零破坏性、向后兼容
"""

import os
import re
from pathlib import Path
from typing import Optional, Any, Dict
import yaml
from dotenv import load_dotenv
from loguru import logger


class ConfigLoader:
    """
    统一配置加载器

    职责：
    1. 加载 .env 文件到环境变量
    2. 加载 aegis.yaml 配置
    3. 解析 ${VAR} 格式的环境变量引用
    4. 提供配置访问接口

    特性：
    - 幂等性：多次调用 load() 结果一致
    - 零破坏性：完全兼容现有 Pydantic 模型
    - 优先级：环境变量 > YAML 配置 > 默认值
    """

    # 环境变量引用的正则模式
    ENV_VAR_PATTERN = re.compile(r'\$\{([^}]+)\}')

    def __init__(self, project_root: Optional[Path] = None):
        """
        初始化配置加载器

        Args:
            project_root: 项目根目录，默认为当前工作目录
        """
        self.project_root = project_root or Path.cwd()
        self.config_data: Dict[str, Any] = {}
        self._loaded = False

    def load(self) -> Dict[str, Any]:
        """
        加载配置（幂等性）

        Returns:
            解析后的配置字典
        """
        if self._loaded:
            return self.config_data

        # Step 1: 加载 .env 文件
        self._load_dotenv()

        # Step 2: 加载 aegis.yaml
        self._load_yaml()

        # Step 3: 解析环境变量引用
        self._resolve_env_vars()

        self._loaded = True
        logger.debug(f"✅ 配置加载完成: {self.project_root}")

        return self.config_data

    def _load_dotenv(self):
        """加载 .env 文件到环境变量"""
        env_file = self.project_root / ".env"

        if env_file.exists():
            load_dotenv(dotenv_path=env_file, override=False)
            logger.debug(f"📄 加载 .env: {env_file}")
        else:
            logger.debug(f"⚠️  未找到 .env 文件: {env_file}")

    def _load_yaml(self):
        """加载 aegis.yaml 配置文件"""
        yaml_file = self.project_root / "aegis.yaml"

        if not yaml_file.exists():
            logger.debug(f"⚠️  未找到 aegis.yaml: {yaml_file}")
            self.config_data = {}
            return

        try:
            with open(yaml_file, "r", encoding="utf-8") as f:
                self.config_data = yaml.safe_load(f) or {}
            logger.debug(f"📄 加载 aegis.yaml: {yaml_file}")
        except Exception as e:
            logger.warning(f"⚠️  加载 aegis.yaml 失败: {e}")
            self.config_data = {}

    def _resolve_env_vars(self):
        """
        递归解析配置中的 ${VAR} 环境变量引用

        支持格式：
        - ${API_KEY}
        - ${ANTHROPIC_MODEL_TIER2}
        """
        self.config_data = self._resolve_value(self.config_data)

    def _resolve_value(self, value: Any) -> Any:
        """
        递归解析单个值

        Args:
            value: 待解析的值（可能是 str, dict, list, 或其他类型）

        Returns:
            解析后的值
        """
        if isinstance(value, str):
            return self._resolve_string(value)
        elif isinstance(value, dict):
            return {k: self._resolve_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._resolve_value(item) for item in value]
        else:
            return value

    def _resolve_string(self, text: str) -> str:
        """
        解析字符串中的环境变量引用

        Args:
            text: 可能包含 ${VAR} 的字符串

        Returns:
            解析后的字符串
        """
        def replacer(match):
            env_var = match.group(1)
            value = os.getenv(env_var)

            if value is None:
                logger.warning(f"⚠️  环境变量未设置: {env_var}")
                return match.group(0)  # 保持原样

            return value

        return self.ENV_VAR_PATTERN.sub(replacer, text)

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值

        Args:
            key: 配置键（支持点号分隔的嵌套路径，如 "llm.tier1_fast.model"）
            default: 默认值

        Returns:
            配置值或默认值
        """
        if not self._loaded:
            self.load()

        keys = key.split(".")
        value = self.config_data

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def get_model_config(self, tier: str) -> Optional[Dict[str, Any]]:
        """
        获取指定 tier 的模型配置

        优先级：
        1. 直接环境变量（TIER1_FAST_MODEL, TIER1_FAST_PROVIDER）
        2. aegis.yaml 中的配置
        3. None（由 Pydantic 默认值填充）

        Args:
            tier: 模型层级名称（如 "tier1_fast"）

        Returns:
            模型配置字典或 None
        """
        if not self._loaded:
            self.load()

        # 优先级 1: 直接从环境变量构建配置
        env_prefix = tier.upper()
        env_model = os.getenv(f"{env_prefix}_MODEL")
        env_provider = os.getenv(f"{env_prefix}_PROVIDER")

        if env_model or env_provider:
            config = {}
            if env_provider:
                config["provider"] = env_provider
            if env_model:
                config["model"] = env_model

            # 尝试推断 provider
            if "model" in config and "provider" not in config:
                config["provider"] = self._infer_provider(config["model"])

            # API Key 环境变量
            if "provider" in config:
                config["api_key_env_var"] = f"{config['provider'].upper()}_API_KEY"

            logger.debug(f"🔧 从环境变量构建 {tier} 配置: {config}")
            return config

        # 优先级 2: 从 aegis.yaml 读取
        yaml_config = self.get(f"llm.{tier}")
        if yaml_config:
            logger.debug(f"📄 从 aegis.yaml 读取 {tier} 配置")
            return yaml_config

        # 优先级 3: 返回 None，由 Pydantic 使用默认值
        logger.debug(f"⚪ {tier} 未配置，使用默认值")
        return None

    def _infer_provider(self, model: str) -> str:
        """
        从模型名推断 provider

        Args:
            model: 模型名称

        Returns:
            推断的 provider 名称
        """
        model_lower = model.lower()

        if "claude" in model_lower:
            return "anthropic"
        elif "glm" in model_lower or "chatglm" in model_lower:
            return "zhipu"
        elif "gpt" in model_lower:
            return "openai"
        elif "llama" in model_lower or "qwen" in model_lower or "mistral" in model_lower:
            return "ollama"

        logger.warning(f"⚠️  无法推断 provider from model: {model}")
        return "unknown"

    def reload(self):
        """重新加载配置（清除缓存）"""
        self._loaded = False
        self.config_data = {}
        return self.load()


# 全局单例（可选，用于简化调用）
_global_loader: Optional[ConfigLoader] = None


def get_config_loader(project_root: Optional[Path] = None) -> ConfigLoader:
    """
    获取全局配置加载器单例

    Args:
        project_root: 项目根目录

    Returns:
        ConfigLoader 实例
    """
    global _global_loader

    if _global_loader is None or project_root is not None:
        _global_loader = ConfigLoader(project_root)
        _global_loader.load()

    return _global_loader
