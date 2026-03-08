import logging
import sys
import uuid
from contextvars import ContextVar
from typing import Optional

# Context variable to store a unique request ID for the current context
request_context: ContextVar[Optional[str]] = ContextVar("request_id", default=None)

class CustomFormatter(logging.Formatter):
    # ANSI Escape Codes for colors
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    cyan = "\x1b[36;20m"
    green = "\x1b[32;20m"
    reset = "\x1b[0m"
    
    # Updated format string to include thread/process info if needed, or simply the request ID
    format_str = "%(asctime)s | %(levelname)-8s | [%(request_id)s] | %(name)s:%(funcName)s:%(lineno)d - %(message)s"

    FORMATS = {
        logging.DEBUG: grey + format_str + reset,
        logging.INFO: green + format_str + reset,
        logging.WARNING: yellow + format_str + reset,
        logging.ERROR: red + format_str + reset,
        logging.CRITICAL: bold_red + format_str + reset
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.formatter_cache = {
            level: logging.Formatter(fmt, datefmt="%Y-%m-%d %H:%M:%S")
            for level, fmt in self.FORMATS.items()
        }

    def format(self, record):
        # Inject request_id into the record for the formatter
        record.request_id = request_context.get() or "NO-ID"
        
        formatter = self.formatter_cache.get(record.levelno)
        if not formatter:
            formatter = self.formatter_cache[logging.INFO]
        return formatter.format(record)

def setup_logging():
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Remove existing handlers to avoid duplicates
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # Create console handler
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(CustomFormatter())
    
    # Add handler to root logger
    root_logger.addHandler(stdout_handler)

    # Adjust Uvicorn loggers to use our custom formatter and have the right log level
    for logger_name in ("uvicorn", "uvicorn.access", "uvicorn.error"):
        uv_logger = logging.getLogger(logger_name)
        uv_logger.handlers = [stdout_handler]
        uv_logger.propagate = False

    return root_logger

# Create a default logger for the app named 'apipure'
logger = logging.getLogger("apipure")

def set_request_id(request_id: str):
    """Utility to set the current request ID."""
    return request_context.set(request_id)
