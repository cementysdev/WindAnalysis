"""
Centralized logging configuration for Wind Turbine Analytics.
Provides colored console output with timestamps for better developer experience.
"""

import logging
import sys
from typing import Optional
from colorama import Fore, Style, init

# Initialize colorama for cross-platform colored output
init(autoreset=True)


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for different log levels."""

    # Color mapping for log levels
    COLORS = {
        logging.DEBUG: Fore.CYAN,
        logging.INFO: Fore.GREEN,
        logging.WARNING: Fore.YELLOW,
        logging.ERROR: Fore.RED,
        logging.CRITICAL: Fore.RED + Style.BRIGHT,
    }

    def __init__(self, fmt: Optional[str] = None, datefmt: Optional[str] = None):
        super().__init__(fmt, datefmt)

    def format(self, record: logging.LogRecord) -> str:
        # Get color for the log level
        log_color = self.COLORS.get(record.levelno, Fore.WHITE)

        # Color the level name
        record.levelname = f"{log_color}{record.levelname}{Style.RESET_ALL}"

        # Color the message based on level
        record.msg = f"{log_color}{record.msg}{Style.RESET_ALL}"

        return super().format(record)


def setup_logger(
    name: str, level: int = logging.DEBUG, log_file: Optional[str] = None
) -> logging.Logger:
    """
    Configure and return a logger with colored console output.

    Args:
        name: Logger name (typically __name__)
        level: Logging level (default: INFO)
        log_file: Optional file path for file logging

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger

    logger.setLevel(level)

    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    # Format: [timestamp] [LEVEL] [logger_name] message
    console_format = "[%(asctime)s] [%(levelname)s] %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    colored_formatter = ColoredFormatter(console_format, datefmt=date_format)
    console_handler.setFormatter(colored_formatter)
    logger.addHandler(console_handler)

    # Optional file handler (without colors)
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)

        file_format = "[%(asctime)s] [%(levelname)s] %(message)s"
        file_formatter = logging.Formatter(file_format, datefmt=date_format)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get or create a logger with default configuration.

    Args:
        name: Logger name (use __name__ from calling module)

    Returns:
        Configured logger instance

    Example:
        >>> from src.logger_config import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.debug("Processing started")
        >>> logger.warning("Low data quality detected")
        >>> logger.error("Failed to load file")
    """
    return setup_logger(name)


# Example usage and testing
if __name__ == "__main__":
    # Demo logger
    demo_logger = get_logger(__name__)

    demo_logger.debug("This is a DEBUG message")
    demo_logger.debug("This is an INFO message")
    demo_logger.warning("This is a WARNING message")
    demo_logger.error("This is an ERROR message")
    demo_logger.critical("This is a CRITICAL message")
