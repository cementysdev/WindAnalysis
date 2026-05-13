"""CLI-aware logger with rich formatting."""

import logging
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from datetime import datetime


class CLILogger:
    """
    Logger that integrates with Rich console for beautiful log output.

    Features:
    - Colored log levels
    - Timestamped messages
    - Panel formatting for important messages
    - Integration with standard Python logging
    """

    def __init__(self, console: Optional[Console] = None):
        """
        Initialize CLI logger.

        Args:
            console: Rich Console instance (creates new if None)
        """
        self.console = console or Console()

    def _format_message(self, level: str, message: str, color: str) -> Text:
        """Format a log message with timestamp and color."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        text = Text()
        text.append(f"[{timestamp}] ", style="dim")
        text.append(f"{level} ", style=f"bold {color}")
        text.append(message, style=color)
        return text

    def debug(self, message: str):
        """Log debug message."""
        text = self._format_message("DEBUG", message, "cyan")
        self.console.print(text)

    def info(self, message: str):
        """Log info message."""
        text = self._format_message("INFO", message, "blue")
        self.console.print(text)

    def success(self, message: str):
        """Log success message."""
        text = self._format_message("SUCCESS", message, "green")
        self.console.print(text)

    def warning(self, message: str):
        """Log warning message."""
        text = self._format_message("WARNING", message, "yellow")
        self.console.print(text)

    def error(self, message: str, exc: Optional[Exception] = None):
        """
        Log error message.

        Args:
            message: Error message
            exc: Optional exception to display
        """
        text = self._format_message("ERROR", message, "red")
        self.console.print(text)

        if exc:
            self.console.print_exception(show_locals=False)

    def critical(self, message: str):
        """Log critical message."""
        text = self._format_message("CRITICAL", message, "red bold")
        self.console.print(text)

    def panel(self, message: str, title: str = "Info", style: str = "blue"):
        """
        Display message in a panel.

        Args:
            message: Message content
            title: Panel title
            style: Border style/color
        """
        panel = Panel(
            message,
            title=f"[bold]{title}[/bold]",
            border_style=style,
            padding=(1, 2),
        )
        self.console.print(panel)


class RichLogHandler(logging.Handler):
    """
    Logging handler that forwards to CLILogger.

    This allows standard Python logging to integrate with Rich console.
    """

    def __init__(self, cli_logger: CLILogger):
        """
        Initialize handler.

        Args:
            cli_logger: CLILogger instance
        """
        super().__init__()
        self.cli_logger = cli_logger

    def emit(self, record: logging.LogRecord):
        """Emit a log record."""
        try:
            message = self.format(record)

            if record.levelno >= logging.ERROR:
                self.cli_logger.error(message)
            elif record.levelno >= logging.WARNING:
                self.cli_logger.warning(message)
            elif record.levelno >= logging.INFO:
                self.cli_logger.info(message)
            else:
                self.cli_logger.debug(message)

        except Exception:
            self.handleError(record)


def setup_cli_logging(cli_logger: CLILogger, level: int = logging.ERROR):
    """
    Configure Python logging to use CLILogger.

    Args:
        cli_logger: CLILogger instance
        level: Logging level
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add Rich handler
    rich_handler = RichLogHandler(cli_logger)
    rich_handler.setLevel(level)
    root_logger.addHandler(rich_handler)
