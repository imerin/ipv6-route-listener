"""Logging module for the route listener."""

import datetime
from dataclasses import dataclass

@dataclass
class LoggerConfig:
    """Configuration for the logger."""
    log_ignored: bool = False

class Logger:
    """Handles logging for the route listener."""

    def __init__(self, config: LoggerConfig):
        """Initialize the logger with configuration."""
        self.config = config

    def _log(self, message: str, prefix: str = "", level: str = "info") -> None:
        """Log a message with timestamp and prefix."""
        if level == "ignored" and not self.config.log_ignored:
            return

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {prefix}{message}")

    def info(self, message: str, prefix: str = "") -> None:
        """Log an info message."""
        self._log(message, prefix, "info")

    def error(self, message: str, prefix: str = "") -> None:
        """Log an error message."""
        self._log(message, prefix, "error")

    def ignored(self, message: str, prefix: str = "") -> None:
        """Log an ignored route message."""
        self._log(message, prefix, "ignored")

    def banner(self, message: str) -> None:
        """Log a banner message."""
        self._log(message) 