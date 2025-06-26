"""服务端插件工具执行器"""

from typing import Dict, Any
from ..base import ToolType, ToolDefinition, ToolResult, ToolExecutor, ToolAction
from plugins_func.register import all_function_registry, Action, ActionResponse


class ServerPluginExecutor(ToolExecutor):
    """服务端插件工具执行器"""

    def __init__(self, conn):
        self.conn = conn
        self.config = conn.config

    async def execute(
        self, conn, tool_name: str, arguments: Dict[str, Any]
    ) -> ToolResult:
        """执行服务端插件工具"""
        func_item = all_function_registry.get(tool_name)
        if not func_item:
            return ToolResult(
                action=ToolAction.NOT_FOUND, content=f"插件函数 {tool_name} 不存在"
            )

        try:
            # 根据工具类型决定如何调用
            if hasattr(func_item, "type"):
                func_type = func_item.type
                if func_type.code in [4, 5]:  # SYSTEM_CTL, IOT_CTL (需要conn参数)
                    result = func_item.func(conn, **arguments)
                elif func_type.code == 2:  # WAIT
                    result = func_item.func(**arguments)
                elif func_type.code == 3:  # CHANGE_SYS_PROMPT
                    result = func_item.func(conn, **arguments)
                else:
                    result = func_item.func(**arguments)
            else:
                # 默认不传conn参数
                result = func_item.func(**arguments)

            # 转换ActionResponse到ToolResult
            if isinstance(result, ActionResponse):
                if result.action == Action.ERROR:
                    return ToolResult(
                        action=ToolAction.ERROR,
                        content=result.result,
                        error=result.response,
                    )
                elif result.action == Action.RESPONSE:
                    return ToolResult(
                        action=ToolAction.RESPONSE,
                        content=result.result,
                        response=result.response,
                    )
                elif result.action == Action.REQLLM:
                    return ToolResult(
                        action=ToolAction.REQUEST_LLM,
                        content=result.result,
                        response=result.response,
                    )
                else:
                    return ToolResult(
                        action=ToolAction.NONE,
                        content=result.result,
                        response=result.response,
                    )
            else:
                # 直接返回结果
                return ToolResult(action=ToolAction.RESPONSE, content=str(result))

        except Exception as e:
            return ToolResult(action=ToolAction.ERROR, content=str(e), error=str(e))

    def get_tools(self) -> Dict[str, ToolDefinition]:
        """获取所有注册的服务端插件工具"""
        tools = {}

        # 获取必要的函数
        necessary_functions = ["handle_exit_intent", "get_time", "get_lunar"]

        # 获取配置中的函数
        config_functions = self.config["Intent"][
            self.config["selected_module"]["Intent"]
        ].get("functions", [])

        # 合并所有需要的函数
        all_required_functions = list(set(necessary_functions + config_functions))

        for func_name in all_required_functions:
            func_item = all_function_registry.get(func_name)
            if func_item:
                tools[func_name] = ToolDefinition(
                    name=func_name,
                    description=func_item.description,
                    tool_type=ToolType.SERVER_PLUGIN,
                )

        return tools

    def has_tool(self, tool_name: str) -> bool:
        """检查是否有指定的服务端插件工具"""
        return tool_name in all_function_registry
