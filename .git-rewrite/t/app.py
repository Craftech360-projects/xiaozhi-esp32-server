import asyncio
from config.logger import setup_logging
from config.settings import load_config
from core.server import WebSocketServer


async def main():
    setup_logging()  # 最先初始化日志
    config = load_config()

    server = WebSocketServer(config)
    await server.start()


if __name__ == "__main__":
    asyncio.run(main())
