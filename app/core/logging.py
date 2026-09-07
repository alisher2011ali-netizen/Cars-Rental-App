import logging
from logging.handlers import RotatingFileHandler
import os


def setup_logging():
    """
    Sets up logging for the application.
    Creates a 'logs' directory in FLET_APP_STORAGE_DATA if it doesn't exist
    and configures a rotating file handler.
    Logs are written to 'logs/app.log' with a maximum size of 5 MB and up to 3 backup files.
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
