"""Logger"""

import logging
import sys
from logging.handlers import RotatingFileHandler

FORMATTER = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
LOG_FILE = "logs/atlassian-api-py.log"


def get_console_handler():
    """
    Output log to console

    :return: StreamHandler
    :rtype: StreamHandler
    """
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(FORMATTER)
    return console_handler


def get_file_handler():
    """Output log to file

    :return: RotatingFileHandler
    :rtype: RotatingFileHandler
    """
    file_handler = RotatingFileHandler(
        filename=LOG_FILE, backupCount=1, encoding="utf-8"
    )
    file_handler.setFormatter(FORMATTER)
    return file_handler


def get_logger(name):
    """
    Get a logger instance

       Example 'application' code
       logger.debug('debug message')
       logger.info('info message')
       logger.warning('warn message')
       logger.error('error message')
       logger.critical('critical message')

    :param name: The name of the logger
    :type name: str
    :return: A logger instance
    :rtype: Logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # comment out this code if needs to print log in console.
    # os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    logger.addHandler(get_console_handler())

    logger.propagate = False

    return logger
