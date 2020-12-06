import logging
import sys
import os
from logging.handlers import RotatingFileHandler

FORMATTER = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
LOG_FILE = 'logs/atlassian-api.log'


def get_console_handler():
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(FORMATTER)
    return console_handler


def get_file_handler():
    file_handler = RotatingFileHandler(filename=LOG_FILE, backupCount=1, encoding="utf-8")
    file_handler.setFormatter(FORMATTER)
    return file_handler


def get_logger(name):
    """
    Example 'application' code
    logger.debug('debug message')
    logger.info('info message')
    logger.warning('warn message')
    logger.error('error message')
    logger.critical('critical message')
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # comment out this code if needs to print log in console.
    # logger.addHandler(get_console_handler())
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    logger.addHandler(get_file_handler())

    logger.propagate = False

    return logger
