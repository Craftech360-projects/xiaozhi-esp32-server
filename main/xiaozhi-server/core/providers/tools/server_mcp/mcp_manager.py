"""服务端MCP管理器"""

import asyncio
import os
import json
from typing import Dict, Any, List
from config.config_loader import get_project_dir
from config.logger import setup_logging

TAG = __name__
logger = setup_logging()


class ServerMCPManager:
    """管理多个服务端MCP服务的集中管理器"""

    def __init__(self, conn) -> None:
        """初始化MCP管理器"""
        self.conn = conn
        self.config_path = get_project_dir() + "data/.mcp_server_settings.json"
        if not os.path.exists(self.config_path):
            self.config_path = ""
            logger.bind(tag=TAG).warning(
                f"请检查mcp服务配置文件：data/.mcp_server_settings.json"
            )
        self.clients: Dict[str, Any] = {}
        self.tools = []

    def load_config(self) -> Dict[str, Any]:
        """加载MCP服务配置"""
        if len(self.config_path) == 0:
            return {}

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            return config.get("mcpServers", {})
        except Exception as e:
            logger.bind(tag=TAG).error(
                f"Error loading MCP config from {self.config_path}: {e}"
            )
            return {}

    async def initialize_servers(self) -> None:
        """初始化所有MCP服务"""
        config = self.load_config()
        for name, srv_config in config.items():
            if not srv_config.get("command") and not srv_config.get("url"):
                logger.bind(tag=TAG).warning(
                    f"Skipping server {name}: neither command nor url specified"
                )
                continue

            try:
                # 这里可以添加真正的MCP客户端初始化逻辑
                # 暂时使用简化版本
                logger.bind(tag=TAG).info(f"初始化服务端MCP客户端: {name}")
                # client = MCPClient(srv_config)
                # await client.initialize()
                # self.clients[name] = client
                # client_tools = client.get_available_tools()
                # self.tools.extend(client_tools)

            except Exception as e:
                logger.bind(tag=TAG).error(
                    f"Failed to initialize MCP server {name}: {e}"
                )

    def get_all_tools(self) -> List[Dict[str, Any]]:
        """获取所有服务的工具function定义"""
        return self.tools

    def is_mcp_tool(self, tool_name: str) -> bool:
        """检查是否是MCP工具"""
        for tool in self.tools:
            if (
                tool.get("function") is not None
                and tool["function"].get("name") == tool_name
            ):
                return True
        return False

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """执行工具调用"""
        logger.bind(tag=TAG).info(f"执行服务端MCP工具 {tool_name}，参数: {arguments}")

        # 这里可以添加真正的工具执行逻辑
        # 暂时返回模拟结果
        return f"服务端MCP工具 {tool_name} 执行结果"

    async def cleanup_all(self) -> None:
        """关闭所有 MCP客户端"""
        for name, client in list(self.clients.items()):
            try:
                if hasattr(client, "cleanup"):
                    await asyncio.wait_for(client.cleanup(), timeout=20)
                logger.bind(tag=TAG).info(f"服务端MCP客户端已关闭: {name}")
            except (asyncio.TimeoutError, Exception) as e:
                logger.bind(tag=TAG).error(f"关闭服务端MCP客户端 {name} 时出错: {e}")
        self.clients.clear()
