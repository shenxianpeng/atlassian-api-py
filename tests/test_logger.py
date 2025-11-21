import pytest
import logging
import sys
import os
import tempfile
from unittest.mock import patch, MagicMock
from atlassian.logger import (
    get_console_handler,
    get_file_handler,
    get_logger,
    FORMATTER,
    LOG_FILE,
)


class TestLogger:
    def test_get_console_handler(self):
        handler = get_console_handler()
        assert isinstance(handler, logging.StreamHandler)
        assert handler.stream == sys.stdout
        assert handler.formatter == FORMATTER

    def test_get_file_handler(self):
        # Create the logs directory if it doesn't exist
        log_dir = os.path.dirname(LOG_FILE)
        os.makedirs(log_dir, exist_ok=True)

        handler = get_file_handler()
        assert isinstance(handler, logging.handlers.RotatingFileHandler)
        assert handler.backupCount == 1
        assert handler.formatter == FORMATTER

        # Clean up
        handler.close()

    def test_get_logger(self):
        logger = get_logger("test_logger")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_logger"
        assert logger.level == logging.DEBUG
        assert logger.propagate is False
        assert len(logger.handlers) > 0
