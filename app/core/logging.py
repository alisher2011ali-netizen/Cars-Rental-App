import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logging() -> None:
    """Configure rotating file logging for the application.

    Create a dedicated 'logs' directory within the resolved storage path and attach
    a rotating file handler with a 5 MB limit and up to 3 backup archives.

    Args:
        None

    Returns:
        None: Logging subsystem is configured in-place.
    """
    app_data_path = os.getenv("FLET_APP_STORAGE_DATA", os.getcwd())

    logs_dir = os.path.join(app_data_path, "logs")
    log_file = os.path.join(logs_dir, "app.log")

    os.makedirs(logs_dir, exist_ok=True)

    file_handler = RotatingFileHandler(
        filename=log_file,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )

    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.setLevel(logging.ERROR)
    logger.addHandler(file_handler)
