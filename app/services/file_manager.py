import logging
import os
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)

default_images_path = Path("data/images/")


class FileManager:
    def __init__(self):
        pass

    def save_file(self, file_data: bytes, file_path: str) -> str:
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "wb") as f:
            f.write(file_data)

        logger.info(f"Saved file to: {file_path}.")
        return str(file_path)

    def copy_file(self, source_path: str, destination_path: str) -> str:
        Path(destination_path).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, destination_path)

        logger.info(f"Copied file from: {source_path} to: {destination_path}.")
        return str(destination_path)

    def get_file(self, file_path: str):
        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                logger.info(f"Loaded file: {file_path}.")
                return f.read()

        logger.warning(f"Failed to load file: {file_path} (File does not exist)")
        return None

    def delete_file(self, file_path: str):
        if os.path.exists(file_path):
            os.remove(file_path)

        logger.info(f"Deleted file: {file_path}.")
        return True
