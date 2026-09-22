import os
import shutil
from pathlib import Path

default_images_path = Path("data/images/")


class FileManager:
    def __init__(self):
        pass

    def save_file(self, file_data: bytes, file_path: str) -> str:
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "wb") as f:
            f.write(file_data)

        return str(file_path)

    def copy_file(self, source_path: str, destination_path: str) -> str:
        Path(destination_path).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, destination_path)
        return str(destination_path)

    def get_file(self, file_path: str):
        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                return f.read()
        return None

    def delete_file(self, file_path: str):
        if os.path.exists(file_path):
            os.remove(file_path)
        return True
