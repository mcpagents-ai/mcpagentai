import logging

# ANSI escape codes for colors
RESET = "\033[0m"
COLOR_CODES = {
    logging.DEBUG: "\033[0;36m",  # Cyan
    logging.INFO: "\033[0;32m",  # Green
    logging.WARNING: "\033[0;33m",  # Yellow
    logging.ERROR: "\033[0;31m",  # Red
    logging.CRITICAL: "\033[1;31m",  # Bold Red
}


class ColoredFormatter(logging.Formatter):
    """
    Custom logging formatter to add colors based on the log level.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_color = COLOR_CODES.get(record.levelno, RESET)
        formatted_message = super().format(record)
        return f"{log_color}{formatted_message}{RESET}"


def get_logger(name: str) -> logging.Logger:
    """
    Return a named logger with colored output.

    Args:
        name (str): The name of the logger.

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        # Create console handler
        handler = logging.StreamHandler()

        # Define log format with color support
        formatter = ColoredFormatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        handler.setFormatter(formatter)
        logger.addHandler(handler)

        # Set the default logging level (can be adjusted as needed)
        logger.setLevel(logging.DEBUG)

    return logger
