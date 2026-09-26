import logging
import os
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)

default_images_path = Path("data/images/")


class FileManager:
    """Handle low-level filesystem I/O operations including file retrieval, copying, and deletion."""

    def __init__(self) -> None:
        pass

    def save_file(self, file_data: bytes, file_path: str) -> str:
        """Write raw binary payloads to the specified filesystem target.

        Args:
            file_data (bytes): Raw binary content to persist.
            file_path (str): Relative or absolute destination target path.

        Returns:
            str: Destination path where the file was written.
        """
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "wb") as f:
            f.write(file_data)

        logger.info(f"Saved file to: {file_path}.")
        return file_path

    def copy_file(self, source_path: str, destination_path: str) -> str:
        """Copy a file from source to target location preserving metadata.

        Args:
            source_path (str): Origin file location.
            destination_path (str): Destination file location.

        Returns:
            str: Target path where the file was copied.
        """
        Path(destination_path).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, destination_path)

        logger.info(f"Copied file from: {source_path} to: {destination_path}.")
        return destination_path

    def get_file(self, file_path: str) -> bytes | None:
        """Read and retrieve file contents as raw bytes if available.

        Args:
            file_path (str): Filesystem path to the desired resource.

        Returns:
            bytes | None: Raw file binary content if the file exists, otherwise None.
        """
        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                logger.info(f"Loaded file: {file_path}.")
                return f.read()

        logger.warning(f"Failed to load file: {file_path} (File does not exist)")
        return None

    def delete_file(self, file_path: str) -> bool:
        """Remove a specified file from storage if present on disk.

        Args:
            file_path (str): Filesystem path of the file to remove.

        Returns:
            bool: Always returns True indicating operation completion.
        """
        if os.path.exists(file_path):
            os.remove(file_path)

        logger.info(f"Deleted file: {file_path}.")
        return True
