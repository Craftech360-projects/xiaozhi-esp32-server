"""工具系统的类型定义"""

from enum import Enum
from dataclasses import dataclass
from typing import Any, Dict, Optional, Callable, Awaitable
from abc import ABC, abstractmethod


class ToolType(Enum):
    """工具类型枚举"""

    SERVER_PLUGIN = "server_plugin"  # 服务端插件
    SERVER_MCP = "server_mcp"  # 服务端MCP
    DEVICE_IOT = "device_iot"  # 设备端IoT
    DEVICE_MCP = "device_mcp"  # 设备端MCP


class ToolAction(Enum):
    """工具执行后的动作类型"""

    ERROR = "error"  # 错误
    NOT_FOUND = "not_found"  # 工具未找到
    RESPONSE = "response"  # 直接回复
    REQUEST_LLM = "request_llm"  # 需要LLM处理
    NONE = "none"  # 无需特殊处理


@dataclass
class ToolResult:
    """工具执行结果"""

    action: ToolAction
    content: str  # 结果内容
    response: Optional[str] = None  # 直接回复内容
    error: Optional[str] = None  # 错误信息


@dataclass
class ToolDefinition:
    """工具定义"""

    name: str  # 工具名称
    description: Dict[str, Any]  # 工具描述（OpenAI函数调用格式）
    tool_type: ToolType  # 工具类型
    parameters: Optional[Dict[str, Any]] = None  # 额外参数
