import os

from pydantic import BaseModel


class Config(BaseModel):
    app_data_path = os.getenv("FLET_APP_STORAGE_DATA", os.getcwd())


config = Config()
