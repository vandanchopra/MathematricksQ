import os
import logging

COLORS = {
    'DEBUG': '\033[94m',     # Blue
    'INFO': '\033[92m',      # Green
    'WARNING': '\033[93m',   # Yellow
    'ERROR': '\033[91m',     # Red
    'CRITICAL': '\033[95m',  # Magenta
    'RESET': '\033[0m'
}

class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors to log levels"""
    def format(self, record):
        orig_levelname = record.levelname
        record.levelname = f"{COLORS.get(record.levelname, '')}{record.levelname}{COLORS['RESET']}"
        result = super().format(record)
        record.levelname = orig_levelname
        return result

_loggers = {}

def get_logger(name: str = 'killbill') -> logging.Logger:
    """Get a named logger instance."""
    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(name)

    # Remove all handlers to prevent duplicate logs
    while logger.handlers:
        logger.handlers.pop()
    logger.setLevel(logging.DEBUG)

    formatter = ColoredFormatter('%(levelname)s: %(asctime)s - %(name)s - %(message)s - %(filename)s:%(lineno)d')
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    logger.propagate = False  # Prevent duplicate logs from propagation to root logger
    _loggers[name] = logger
    return logger

# Set root logger to use colored formatter
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
if not root_logger.handlers:
    root_handler = logging.StreamHandler()
    root_handler.setFormatter(ColoredFormatter('%(levelname)s: %(asctime)s - %(name)s - %(message)s - %(filename)s:%(lineno)d'))
    root_logger.addHandler(root_handler)
else:
    for handler in root_logger.handlers:
        handler.setFormatter(ColoredFormatter('%(levelname)s: %(asctime)s - %(name)s - %(message)s - %(filename)s:%(lineno)d'))