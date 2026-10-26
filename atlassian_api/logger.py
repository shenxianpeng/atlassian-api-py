"""Logging helpers for the Atlassian clients."""

import logging
import sys
from logging.handlers import RotatingFileHandler

FORMATTER = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
LOG_FILE = "logs/atlassian-api-py.log"


def get_console_handler():
    """Create a console log handler that writes to stdout.

    :return: Configured stream handler.
    :rtype: StreamHandler
    """
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(FORMATTER)
    return console_handler


def get_file_handler():
    """Create a rotating file log handler.

    The caller is responsible for ensuring that the ``logs`` directory exists
    before attaching this handler.

    :return: Configured rotating file handler.
    :rtype: RotatingFileHandler
    """
    file_handler = RotatingFileHandler(
        filename=LOG_FILE, backupCount=1, encoding="utf-8"
    )
    file_handler.setFormatter(FORMATTER)
    return file_handler


def get_logger(name):
    """Return a package logger that follows the application's logging setup.

    The library never prints on its own: it only attaches a
    :class:`logging.NullHandler`, and records propagate to the handlers the
    application configures. To see request logs, for example::

        logging.basicConfig(level=logging.DEBUG)

    or attach :func:`get_console_handler` to ``logging.getLogger("atlassian_api")``.

    :param name: Logger name, usually ``__name__``.
    :type name: str
    :return: Logger instance.
    :rtype: Logger
    """
    logger = logging.getLogger(name)
    if not any(isinstance(h, logging.NullHandler) for h in logger.handlers):
        logger.addHandler(logging.NullHandler())
    return logger
