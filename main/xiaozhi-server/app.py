import sys
import uuid
import signal
import asyncio
from aioconsole import ainput
from config.settings import load_config
from config.logger import setup_logging
from core.utils.util import get_local_ip
from core.http_server import SimpleHttpServer
from core.websocket_server import WebSocketServer
from core.utils.util import check_ffmpeg_installed

TAG = __name__
logger = setup_logging()


async def wait_for_exit() -> None:
    """
    Blocks until Ctrl-C / SIGTERM is received.
    - Unix: Uses add_signal_handler
    - Windows: Relies on KeyboardInterrupt
    """
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    if sys.platform != "win32":  # Unix / macOS
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, stop_event.set)
        await stop_event.wait()
    else:
        # Windows: await a future that is always pending,
        # allowing KeyboardInterrupt to bubble up to asyncio.run,
        # thus eliminating the problem of legacy normal threads blocking process exit.
        try:
            await asyncio.Future()
        except KeyboardInterrupt:  # Ctrl-C
            pass


async def monitor_stdin():
    """Monitors standard input, consumes the Enter key"""
    while True:
        await ainput()  # Asynchronously waits for input, consumes Enter


async def main():
    check_ffmpeg_installed()
    config = load_config()

    # By default, use the manager-api's secret as the auth_key
    # If the secret is empty, generate a random key
    # auth_key is used for JWT authentication, e.g., for the visual analysis interface's JWT authentication
    auth_key = config.get("manager-api", {}).get("secret", "")
    # "你" means "you" or "your"
    if not auth_key or len(auth_key) == 0 or "your" in auth_key:
        auth_key = str(uuid.uuid4().hex)
    config["server"]["auth_key"] = auth_key

    # Add stdin monitoring task
    stdin_task = asyncio.create_task(monitor_stdin())

    # Start the WebSocket server
    ws_server = WebSocketServer(config)
    ws_task = asyncio.create_task(ws_server.start())
    # Start the Simple HTTP server
    ota_server = SimpleHttpServer(config)
    ota_task = asyncio.create_task(ota_server.start())

    read_config_from_api = config.get("read_config_from_api", False)
    port = int(config["server"].get("http_port", 8003))
    if not read_config_from_api:
        logger.bind(tag=TAG).info(
            "The OTA interface is\t\thttp://{}:{}/xiaozhi/ota/",
            get_local_ip(),
            port,
        )
    logger.bind(tag=TAG).info(
        "The visual analysis interface is\thttp://{}:{}/mcp/vision/explain",
        get_local_ip(),
        port,
    )

    # Get WebSocket configuration, use safe default values
    websocket_port = 8000
    server_config = config.get("server", {})
    if isinstance(server_config, dict):
        websocket_port = int(server_config.get("port", 8000))

    logger.bind(tag=TAG).info(
        "The Websocket address is\tws://{}:{}/xiaozhi/v1/",
        get_local_ip(),
        websocket_port,
    )

    logger.bind(tag=TAG).info(
        "=======The address above is a WebSocket protocol address, please do not access it with a browser======="
    )
    logger.bind(tag=TAG).info(
        "To test the WebSocket, please open test_page.html in the test directory with Google Chrome"
    )
    logger.bind(tag=TAG).info(
        "=============================================================\n"
    )

    try:
        await wait_for_exit()  # Blocks until an exit signal is received
    except asyncio.CancelledError:
        print("Task was cancelled, cleaning up resources...")
    finally:
        # Cancel all tasks (key fix point)
        stdin_task.cancel()
        ws_task.cancel()
        if ota_task:
            ota_task.cancel()

        # Wait for tasks to terminate (must add a timeout)
        await asyncio.wait(
            [stdin_task, ws_task, ota_task] if ota_task else [stdin_task, ws_task],
            timeout=3.0,
            return_when=asyncio.ALL_COMPLETED,
        )
        print("Server has been shut down, program exiting.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Manual interruption, program terminating.")
