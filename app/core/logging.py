import logging
import os
from logging.handlers import RotatingFileHandler

from core.config import config


def setup_logging() -> None:
    logs_dir = os.path.join(config.app_data_path, "logs")
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
