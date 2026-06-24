"""
🛡️ Aegis - Log Sanitizer（日志脱敏工具）
防止敏感信息泄露到日志中
"""

import re
from typing import Any, Dict, List, Set


# 敏感字段关键词（大小写不敏感）
SENSITIVE_KEYS: Set[str] = {
    "api_key",
    "apikey",
    "api-key",
    "token",
    "access_token",
    "refresh_token",
    "bearer",
    "authorization",
    "password",
    "passwd",
    "pwd",
    "secret",
    "private_key",
    "privatekey",
    "client_secret",
    "auth",
    "credential",
}

# 敏感值的正则模式
SENSITIVE_PATTERNS = [
    # API Keys
    (re.compile(r'(sk-[a-zA-Z0-9]{32,})', re.IGNORECASE), r'sk-***REDACTED***'),
    (re.compile(r'(glm-[a-zA-Z0-9]{32,})', re.IGNORECASE), r'glm-***REDACTED***'),
    # Bearer tokens
    (re.compile(r'(Bearer\s+[a-zA-Z0-9\-._~+/]+=*)', re.IGNORECASE), r'Bearer ***REDACTED***'),
    # AWS keys
    (re.compile(r'(AKIA[0-9A-Z]{16})', re.IGNORECASE), r'AKIA***REDACTED***'),
    # Generic long alphanumeric strings that look like tokens
    (re.compile(r'([a-f0-9]{32,})', re.IGNORECASE), r'***REDACTED***'),
]


def sanitize_dict(data: Dict[str, Any], redacted_text: str = "***REDACTED***") -> Dict[str, Any]:
    """
    脱敏字典中的敏感字段

    Args:
        data: 要脱敏的字典
        redacted_text: 替换文本

    Returns:
        脱敏后的字典副本
    """
    if not isinstance(data, dict):
        return data

    sanitized = {}
    for key, value in data.items():
        # 检查键名是否为敏感字段
        if any(sensitive in key.lower() for sensitive in SENSITIVE_KEYS):
            sanitized[key] = redacted_text
        # 递归处理嵌套字典
        elif isinstance(value, dict):
            sanitized[key] = sanitize_dict(value, redacted_text)
        # 递归处理列表
        elif isinstance(value, (list, tuple)):
            sanitized[key] = type(value)(
                sanitize_dict(item, redacted_text) if isinstance(item, dict) else item
                for item in value
            )
        else:
            sanitized[key] = value

    return sanitized


def sanitize_string(text: str, redacted_text: str = "***REDACTED***") -> str:
    """
    脱敏字符串中的敏感信息

    Args:
        text: 要脱敏的字符串
        redacted_text: 替换文本

    Returns:
        脱敏后的字符串
    """
    if not isinstance(text, str):
        return text

    result = text
    for pattern, replacement in SENSITIVE_PATTERNS:
        result = pattern.sub(replacement, result)

    return result


def sanitize_log_data(data: Any, redacted_text: str = "***REDACTED***") -> Any:
    """
    智能脱敏任意类型的数据（用于日志记录）

    Args:
        data: 要脱敏的数据（可以是任意类型）
        redacted_text: 替换文本

    Returns:
        脱敏后的数据
    """
    if isinstance(data, dict):
        return sanitize_dict(data, redacted_text)
    elif isinstance(data, str):
        return sanitize_string(data, redacted_text)
    elif isinstance(data, (list, tuple)):
        return type(data)(sanitize_log_data(item, redacted_text) for item in data)
    else:
        # 对于其他类型（数字、布尔等），直接返回
        return data
