"""设备端MCP工具执行器"""

from typing import Dict, Any
from ..base import ToolType, ToolDefinition, ToolResult, ToolExecutor, ToolAction
from .mcp_handler import call_mcp_tool


class DeviceMCPExecutor(ToolExecutor):
    """设备端MCP工具执行器"""

    def __init__(self, conn):
        self.conn = conn

    async def execute(
        self, conn, tool_name: str, arguments: Dict[str, Any]
    ) -> ToolResult:
        """执行设备端MCP工具"""
        if not hasattr(conn, "mcp_client") or not conn.mcp_client:
            return ToolResult(
                action=ToolAction.ERROR,
                content="设备端MCP客户端未初始化",
                error="设备端MCP客户端未初始化",
            )

        if not await conn.mcp_client.is_ready():
            return ToolResult(
                action=ToolAction.ERROR,
                content="设备端MCP客户端未准备就绪",
                error="设备端MCP客户端未准备就绪",
            )

        try:
            # 转换参数为JSON字符串
            import json

            args_str = json.dumps(arguments) if arguments else "{}"

            # 调用设备端MCP工具
            result = await call_mcp_tool(conn, conn.mcp_client, tool_name, args_str)

            return ToolResult(action=ToolAction.RESPONSE, content=str(result))

        except ValueError as e:
            return ToolResult(action=ToolAction.NOT_FOUND, content=str(e), error=str(e))
        except Exception as e:
            return ToolResult(action=ToolAction.ERROR, content=str(e), error=str(e))

    def get_tools(self) -> Dict[str, ToolDefinition]:
        """获取所有设备端MCP工具"""
        if not hasattr(self.conn, "mcp_client") or not self.conn.mcp_client:
            return {}

        tools = {}
        mcp_tools = self.conn.mcp_client.get_available_tools()

        for tool in mcp_tools:
            func_def = tool.get("function", {})
            tool_name = func_def.get("name", "")

            if tool_name:
                tools[tool_name] = ToolDefinition(
                    name=tool_name, description=tool, tool_type=ToolType.DEVICE_MCP
                )

        return tools

    def has_tool(self, tool_name: str) -> bool:
        """检查是否有指定的设备端MCP工具"""
        if not hasattr(self.conn, "mcp_client") or not self.conn.mcp_client:
            return False

        return self.conn.mcp_client.has_tool(tool_name)
