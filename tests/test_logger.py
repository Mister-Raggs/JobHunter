"""
Tests for logger functionality.
"""

import pytest
from pathlib import Path
from jobhunter.logger import StructuredLogger, get_logger, reset_logger


class TestStructuredLogger:
    """Test structured logging functionality."""

    def test_logger_creation(self, tmp_path):
        """Logger should be created with default settings."""
        logger = StructuredLogger(
            name="test",
            level="INFO",
            log_dir=tmp_path,
            enable_console=False,
        )

        assert logger.logger.name == "test"
        assert logger.metrics["api_calls"] == 0

    def test_log_methods(self, tmp_path):
        """All log level methods should work."""
        logger = StructuredLogger(
            name="test",
            log_dir=tmp_path,
            enable_console=False,
        )

        # Should not raise exceptions
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        logger.critical("Critical message")

    def test_log_with_context(self, tmp_path):
        """Logging with context should include extra data."""
        logger = StructuredLogger(
            name="test",
            log_dir=tmp_path,
            enable_console=False,
        )

        # Should not raise exceptions
        logger.info("Message with context", url="https://example.com", count=5)

    def test_metrics_tracking(self, tmp_path):
        """Metrics should be tracked correctly."""
        logger = StructuredLogger(
            name="test",
            log_dir=tmp_path,
            enable_console=False,
        )

        # Track API calls
        logger.record_api_call()
        logger.record_api_call()
        assert logger.metrics["api_calls"] == 2

        # Track scrapes
        logger.record_scrape_attempt("greenhouse")
        logger.record_scrape_success("greenhouse")

        logger.record_scrape_attempt("lever")
        logger.record_scrape_failure("lever", "TimeoutError")

        metrics = logger.get_metrics()

        assert metrics["scrapes_attempted"] == 2
        assert metrics["scrapes_successful"] == 1
        assert metrics["scrapes_failed"] == 1
        assert metrics["errors_by_type"]["TimeoutError"] == 1

        # Check platform stats
        assert "greenhouse" in metrics["platform_success_rate"]
        assert metrics["platform_success_rate"]["greenhouse"]["attempts"] == 1
        assert metrics["platform_success_rate"]["greenhouse"]["successes"] == 1
        assert metrics["platform_success_rate"]["greenhouse"]["success_rate"] == 1.0

    def test_success_rate_calculation(self, tmp_path):
        """Success rate should be calculated correctly."""
        logger = StructuredLogger(
            name="test",
            log_dir=tmp_path,
            enable_console=False,
        )

        # 3 attempts, 2 successes = 66.7% success rate
        for _ in range(3):
            logger.record_scrape_attempt("lever")

        logger.record_scrape_success("lever")
        logger.record_scrape_success("lever")

        metrics = logger.get_metrics()
        success_rate = metrics["platform_success_rate"]["lever"]["success_rate"]

        assert success_rate == pytest.approx(0.667, rel=0.01)

    def test_log_file_creation(self, tmp_path):
        """Log file should be created in specified directory."""
        logger = StructuredLogger(
            name="test",
            log_dir=tmp_path,
            enable_console=False,
        )

        logger.info("Test message")

        # Check that a log file was created
        log_files = list(tmp_path.glob("*.log"))
        assert len(log_files) == 1

        # Check that message was written
        log_content = log_files[0].read_text()
        assert "Test message" in log_content


class TestGlobalLogger:
    """Test global logger singleton."""

    def test_get_logger_singleton(self, tmp_path):
        """get_logger should return same instance."""
        reset_logger()  # Start fresh

        logger1 = get_logger(log_dir=tmp_path, enable_console=False)
        logger2 = get_logger()

        assert logger1 is logger2

    def test_reset_logger(self, tmp_path):
        """reset_logger should create new instance."""
        reset_logger()

        logger1 = get_logger(log_dir=tmp_path, enable_console=False)
        logger1.record_api_call()

        reset_logger()

        logger2 = get_logger(log_dir=tmp_path, enable_console=False)

        # Should be different instance with fresh metrics
        assert logger2.metrics["api_calls"] == 0
