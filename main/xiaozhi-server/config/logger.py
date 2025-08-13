import os
import sys
from loguru import logger
from config.config_loader import load_config
from config.settings import check_config_file
from datetime import datetime

SERVER_VERSION = "0.6.2"
_logger_initialized = False


def get_module_abbreviation(module_name, module_dict):
    """Get module name abbreviation, return 00 if empty
    If name contains underscore, return first two characters after the underscore
    """
    module_value = module_dict.get(module_name, "")
    if not module_value:
        return "00"
    if "_" in module_value:
        parts = module_value.split("_")
        return parts[-1][:2] if parts[-1] else "00"
    return module_value[:2]


def build_module_string(selected_module):
    """Build module string"""
    return (
        get_module_abbreviation("VAD", selected_module)
        + get_module_abbreviation("ASR", selected_module)
        + get_module_abbreviation("LLM", selected_module)
        + get_module_abbreviation("TTS", selected_module)
        + get_module_abbreviation("Memory", selected_module)
        + get_module_abbreviation("Intent", selected_module)
    )


def formatter(record):
    """Add default value for logs without tag"""
    record["extra"].setdefault("tag", record["name"])
    return record["message"]


def setup_logging():
    check_config_file()
    """Read log configuration from config file and set log output format and level"""
    config = load_config()
    log_config = config["log"]
    global _logger_initialized

    # Configure logging on first initialization
    if not _logger_initialized:
        logger.configure(
            extra={
                "selected_module": log_config.get("selected_module", "00000000000000")
            }
        )  # New configuration
        log_format = log_config.get(
            "log_format",
            "<green>{time:YYMMDD HH:mm:ss}</green>[{version}_{extra[selected_module]}][<light-blue>{extra[tag]}</light-blue>]-<level>{level}</level>-<light-green>{message}</light-green>",
        )
        log_format_file = log_config.get(
            "log_format_file",
            "{time:YYYY-MM-DD HH:mm:ss} - {version}_{extra[selected_module]} - {name} - {level} - {extra[tag]} - {message}",
        )
        selected_module_str = logger._core.extra["selected_module"]

        log_format = log_format.replace("{version}", SERVER_VERSION)
        log_format = log_format.replace(
            "{selected_module}", selected_module_str)
        log_format_file = log_format_file.replace("{version}", SERVER_VERSION)
        log_format_file = log_format_file.replace(
            "{selected_module}", selected_module_str
        )

        log_level = log_config.get("log_level", "INFO")
        log_dir = log_config.get("log_dir", "tmp")
        log_file = log_config.get("log_file", "server.log")
        data_dir = log_config.get("data_dir", "data")

        os.makedirs(log_dir, exist_ok=True)
        os.makedirs(data_dir, exist_ok=True)

        # Configure log output
        logger.remove()

        # Output to console
        logger.add(sys.stdout, format=log_format,
                   level=log_level, filter=formatter)

        # Output to file - unified directory, rotate by size
        # Complete log file path
        log_file_path = os.path.join(log_dir, log_file)

        # Add log handler
        logger.add(
            log_file_path,
            format=log_format_file,
            level=log_level,
            filter=formatter,
            rotation="10 MB",  # Maximum 10MB per file
            retention="30 days",  # Keep for 30 days
            compression=None,
            encoding="utf-8",
            enqueue=True,  # Async safe
            backtrace=True,
            diagnose=True,
        )
        _logger_initialized = True  # Mark as initialized

    return logger


def update_module_string(selected_module_str):
    """Update module string and reconfigure log handlers"""
    logger.debug(f"Updating log configuration components")
    current_module = logger._core.extra["selected_module"]

    if current_module == selected_module_str:
        logger.debug(f"Components unchanged, no update needed")
        return

    try:
        logger.configure(extra={"selected_module": selected_module_str})

        config = load_config()
        log_config = config["log"]

        log_format = log_config.get(
            "log_format",
            "<green>{time:YYMMDD HH:mm:ss}</green>[{version}_{extra[selected_module]}][<light-blue>{extra[tag]}</light-blue>]-<level>{level}</level>-<light-green>{message}</light-green>",
        )
        log_format_file = log_config.get(
            "log_format_file",
            "{time:YYYY-MM-DD HH:mm:ss} - {version}_{extra[selected_module]} - {name} - {level} - {extra[tag]} - {message}",
        )

        log_format = log_format.replace("{version}", SERVER_VERSION)
        log_format = log_format.replace(
            "{selected_module}", selected_module_str)
        log_format_file = log_format_file.replace("{version}", SERVER_VERSION)
        log_format_file = log_format_file.replace(
            "{selected_module}", selected_module_str
        )

        logger.remove()
        logger.add(
            sys.stdout,
            format=log_format,
            level=log_config.get("log_level", "INFO"),
            filter=formatter,
        )

        # Update file log configuration - unified directory, rotate by size
        log_dir = log_config.get("log_dir", "tmp")
        log_file = log_config.get("log_file", "server.log")

        # Complete log file path
        log_file_path = os.path.join(log_dir, log_file)

        logger.add(
            log_file_path,
            format=log_format_file,
            level=log_config.get("log_level", "INFO"),
            filter=formatter,
            rotation="10 MB",  # Maximum 10MB per file
            retention="30 days",  # Keep for 30 days
            compression=None,
            encoding="utf-8",
            enqueue=True,  # Async safe
            backtrace=True,
            diagnose=True,
        )

    except Exception as e:
        logger.error(f"Log configuration update failed: {str(e)}")
        raise
