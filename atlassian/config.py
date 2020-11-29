import configparser
import os
import copy

CONFIG_FILE_NAME = "config.ini"
CONFIG_CONNECTION = "connection"
CONFIG_LOGGING = "logging"

# Connection Section
HOST = 'host'
USER = 'user'
PASSWORD = 'password'
TIMEOUT = 'timeout'

# Logging Section
LOG_LEVEL = 'level'
LOG_FORMAT = 'format'
LOG_FILE_MAXSIZE = 'max_size'
LOG_DIR = 'dir'
LOG_FILE_NAME = 'file_name'
LOG_DEBUG = 'debug'
LOG_DATA_MAXSIZE = 'log_data_max_size'


DEFAULT_CONFIG = {
    CONFIG_CONNECTION: {
        HOST: 'localhost',
        TIMEOUT: 300
    },
    CONFIG_LOGGING: {
        LOG_LEVEL: 'WARNING',
        LOG_FORMAT: 'standard',
        LOG_DIR: './logs',
        LOG_FILE_NAME: 'aapy.log',
        LOG_FILE_MAXSIZE: 1024 * 512,
        LOG_DATA_MAXSIZE: 1024
    }
}


def eval_config(config):
    import ast
    for k in config:
        v = config[k]
        try:
            v = ast.literal_eval(v)
            config[k] = v
        except:
            pass
    return config


default_cfg = configparser.ConfigParser()
default_cfg.read_dict(DEFAULT_CONFIG)
config_path = os.path.join(os.getcwd(), CONFIG_FILE_NAME)
default_cfg.read(config_path)

connection_config = eval_config(dict(default_cfg.items(CONFIG_CONNECTION)))
logging_config = eval_config(dict(default_cfg.items(CONFIG_LOGGING)))


class Config:
    """
    Test example
    config.connection
    config.logging
    print(config.connection)
    print(config.logging)
    """

    def __init__(self):
        pass

    @property
    def connection(self):
        return copy.deepcopy(connection_config)

    @property
    def logging(self):
        return copy.deepcopy(logging_config)


config = Config()

