"""
Structured logging system for JobHunter.

Provides centralized logging with multiple output destinations,
log levels, and metrics tracking for monitoring scraper health.
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime
import json


class StructuredLogger:
    """
    Centralized logger with support for console and file outputs.
    Tracks metrics for monitoring scraper performance.
    """

    def __init__(
        self,
        name: str = "jobhunter",
        level: str = "INFO",
        log_dir: Optional[Path] = None,
        enable_file: bool = True,
        enable_console: bool = True,
    ):
        """
        Initialize the structured logger.

        Args:
            name: Logger name
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_dir: Directory for log files (default: logs/)
            enable_file: Write logs to file
            enable_console: Output logs to console
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        self.logger.handlers.clear()  # Remove existing handlers

        # Metrics tracking
        self.metrics = {
            "api_calls": 0,
            "scrapes_attempted": 0,
            "scrapes_successful": 0,
            "scrapes_failed": 0,
            "errors_by_type": {},
            "platform_success_rate": {},
        }

        # Console handler
        if enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(getattr(logging, level.upper()))
            console_formatter = logging.Formatter(
                fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)

        # File handler
        if enable_file:
            if log_dir is None:
                log_dir = Path("logs")
            log_dir.mkdir(parents=True, exist_ok=True)

            log_file = log_dir / f"jobhunter_{datetime.now().strftime('%Y%m%d')}.log"
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)  # Always log everything to file
            file_formatter = logging.Formatter(
                fmt='%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)

    def debug(self, message: str, **kwargs):
        """Log debug message with optional context."""
        self._log(logging.DEBUG, message, kwargs)

    def info(self, message: str, **kwargs):
        """Log info message with optional context."""
        self._log(logging.INFO, message, kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message with optional context."""
        self._log(logging.WARNING, message, kwargs)

    def error(self, message: str, **kwargs):
        """Log error message with optional context."""
        self._log(logging.ERROR, message, kwargs)

    def critical(self, message: str, **kwargs):
        """Log critical message with optional context."""
        self._log(logging.CRITICAL, message, kwargs)

    def _log(self, level: int, message: str, context: dict):
        """Internal logging method with context."""
        if context:
            message = f"{message} | Context: {json.dumps(context)}"
        self.logger.log(level, message)

    # Metric tracking methods

    def record_api_call(self):
        """Increment API call counter."""
        self.metrics["api_calls"] += 1

    def record_scrape_attempt(self, platform: str):
        """Record scraping attempt for a platform."""
        self.metrics["scrapes_attempted"] += 1
        if platform not in self.metrics["platform_success_rate"]:
            self.metrics["platform_success_rate"][platform] = {
                "attempts": 0,
                "successes": 0
            }
        self.metrics["platform_success_rate"][platform]["attempts"] += 1

    def record_scrape_success(self, platform: str):
        """Record successful scrape."""
        self.metrics["scrapes_successful"] += 1
        if platform in self.metrics["platform_success_rate"]:
            self.metrics["platform_success_rate"][platform]["successes"] += 1

    def record_scrape_failure(self, platform: str, error_type: str):
        """Record scraping failure."""
        self.metrics["scrapes_failed"] += 1

        # Track error types
        if error_type not in self.metrics["errors_by_type"]:
            self.metrics["errors_by_type"][error_type] = 0
        self.metrics["errors_by_type"][error_type] += 1

    def get_metrics(self) -> dict:
        """Return current metrics."""
        # Calculate success rates
        metrics_copy = self.metrics.copy()
        for platform, stats in metrics_copy["platform_success_rate"].items():
            if stats["attempts"] > 0:
                stats["success_rate"] = round(
                    stats["successes"] / stats["attempts"], 3
                )

        return metrics_copy

    def log_metrics_summary(self):
        """Log a summary of current metrics."""
        metrics = self.get_metrics()

        total_attempts = metrics["scrapes_attempted"]
        total_successes = metrics["scrapes_successful"]
        overall_rate = 0
        if total_attempts > 0:
            overall_rate = round(total_successes / total_attempts * 100, 1)

        self.info("=== Scraping Session Metrics ===")
        self.info(f"API Calls: {metrics['api_calls']}")
        self.info(f"Scrapes: {total_successes}/{total_attempts} ({overall_rate}% success)")

        if metrics["platform_success_rate"]:
            self.info("Platform Success Rates:")
            for platform, stats in metrics["platform_success_rate"].items():
                rate = stats.get("success_rate", 0) * 100
                self.info(f"  {platform}: {stats['successes']}/{stats['attempts']} ({rate:.1f}%)")

        if metrics["errors_by_type"]:
            self.info("Error Types:")
            for error_type, count in metrics["errors_by_type"].items():
                self.info(f"  {error_type}: {count}")


# Global logger instance
_global_logger: Optional[StructuredLogger] = None


def get_logger(
    name: str = "jobhunter",
    level: str = "INFO",
    **kwargs
) -> StructuredLogger:
    """
    Get or create the global logger instance.

    Args:
        name: Logger name
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        **kwargs: Additional arguments passed to StructuredLogger

    Returns:
        StructuredLogger instance
    """
    global _global_logger

    if _global_logger is None:
        _global_logger = StructuredLogger(name=name, level=level, **kwargs)

    return _global_logger


def reset_logger():
    """Reset the global logger (useful for testing)."""
    global _global_logger
    _global_logger = None
