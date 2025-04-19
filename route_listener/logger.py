"""Logging module for the route listener."""

import logging
import sys
from datetime import datetime
from typing import Optional

class Logger:
    """Custom logger for the route listener application."""
    
    def __init__(self, log_ignored: bool = False):
        """Initialize the logger.
        
        Args:
            log_ignored: Whether to log ignored routes
        """
        self.log_ignored = log_ignored
        self._setup_logging()
        
    def _setup_logging(self):
        """Set up the logging configuration."""
        # Create a formatter
        formatter = logging.Formatter('[%(asctime)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        
        # Create a console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        
        # Create a logger
        self._logger = logging.getLogger('route_listener')
        self._logger.setLevel(logging.INFO)
        self._logger.addHandler(console_handler)
        
    def info(self, message: str) -> None:
        """Log an info message.
        
        Args:
            message: The message to log
        """
        self._logger.info(message)
        
    def error(self, message: str) -> None:
        """Log an error message.
        
        Args:
            message: The message to log
        """
        self._logger.error(message)
        
    def debug(self, message: str) -> None:
        """Log a debug message.
        
        Args:
            message: The message to log
        """
        self._logger.debug(message)
        
    def ignored(self, message: str) -> None:
        """Log an ignored route message.
        
        Args:
            message: The message to log
        """
        if self.log_ignored:
            self._logger.info(message)
            
    def isEnabledFor(self, level: int) -> bool:
        """Check if the logger is enabled for the given level.
        
        Args:
            level: The logging level to check
            
        Returns:
            True if the logger is enabled for the given level, False otherwise
        """
        return self._logger.isEnabledFor(level)

    def banner(self, message: str) -> None:
        """Log a banner message."""
        self._logger.info(message) 