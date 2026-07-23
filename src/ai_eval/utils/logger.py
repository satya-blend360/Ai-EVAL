import logging
import sys
from pathlib import Path

def setup_logger(name: str = "ai_eval", log_level: int = logging.INFO) -> logging.Logger:
    """Sets up a standardized logger for the framework."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(log_level)
    
    # Console handler
    c_handler = logging.StreamHandler(sys.stdout)
    c_handler.setLevel(log_level)
    
    # Formatter
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    c_handler.setFormatter(formatter)
    logger.addHandler(c_handler)
    
    return logger

# Shared default logger
logger = setup_logger()
