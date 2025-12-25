"""
Centralized logging utility for PDF Compliance Scanner
"""
import logging
import logging.handlers
from pathlib import Path
import config


def setup_logger(name: str = __name__) -> logging.Logger:
    """
    Set up and configure a logger instance.
    
    Args:
        name: Logger name (typically __name__ from calling module)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Only configure if not already configured
    if logger.hasHandlers():
        return logger
    
    logger.setLevel(getattr(logging, config.LOG_LEVEL))
    
    # Create formatter
    formatter = logging.Formatter(config.LOG_FORMAT)
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        config.LOG_FILE,
        maxBytes=config.LOG_MAX_BYTES,
        backupCount=config.LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


def log_separator(logger: logging.Logger, message: str = ""):
    """
    Log a visual separator with optional message.
    
    Args:
        logger: Logger instance
        message: Optional message to include in separator
    """
    sep = "=" * 80
    if message:
        logger.info(sep)
        logger.info(f" {message}")
        logger.info(sep)
    else:
        logger.info(sep)


# Create default logger for module-level use
default_logger = setup_logger('pdf_scanner')
