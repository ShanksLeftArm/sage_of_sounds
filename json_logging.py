import logging
from configuration import config

json_format = "{'time':'%(asctime)s', 'name': '%(name)s', 'function': '%(funcName)s', 'level': '%(levelname)s', 'message': '%(message)s'}"

standard_python_format = '%(asctime)-15s %(levelname)-8s %(message)s'

DEFAULT_LOG_LEVEL = logging.INFO
LOG_LEVEL_MAPPING = {
    'info': logging.INFO,
    'critical': logging.CRITICAL,
    'fatal': logging.FATAL,
    'error': logging.ERROR,
    'warning': logging.WARNING,
    'warn': logging.WARN,
    'info': logging.INFO,
    'debug': logging.DEBUG
}

def mapLoggingLevel(level_name: str) -> int:
    if level_name.lower() in LOG_LEVEL_MAPPING:
        return LOG_LEVEL_MAPPING[level_name.lower()]
    return DEFAULT_LOG_LEVEL


def getLogger(name: str):
    LOG_LEVEL = mapLoggingLevel(config['LOG_LEVEL']) if 'LOG_LEVEL' in config else DEFAULT_LOG_LEVEL   

    file_handler=logging.FileHandler(config['log_file'] if 'log_file' in config else '_log.log')
    stream_handler=logging.StreamHandler()

    stream_formatter=logging.Formatter(json_format)
    file_formatter=logging.Formatter(json_format)

    file_handler.setFormatter(file_formatter)
    stream_handler.setFormatter(stream_formatter)
    logger = logging.getLogger(name=name)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    logger.setLevel(LOG_LEVEL)
    return logger