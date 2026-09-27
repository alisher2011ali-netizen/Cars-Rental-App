import logging
import uuid
from pathlib import Path

from core.config import config
from core.models import Image, Payment, PaymentType, session_factory
from parsing.parser import process_sber_pdf
from services.file_manager import FileManager
from sqlalchemy.orm import Session

IMAGE_SUBDIRS: dict[str, str] = {
    "car_photo": "cars",
    "avatar": "tenants/avatars",
    "passport": "tenants/passports",
    "sub_passport": "tenants/sub_passports",
    "driver_license": "tenants/driver_licenses",
}

logger = logging.getLogger(__name__)


class Connector:
    """Coordinate database persistence, file management, and external data parsing."""

    def __init__(self) -> None:
        """Initialize the connector with supporting utility services.

        Args:
            None

        Returns:
            None: Initializes service instances.
        """
        self.file_manager = FileManager()

    async def save_image(
        self,
        *,
        image_path: str,
        object_id: int,
        object_type: str,
        category: str = "car_photo",
        db: Session | None = None,
    ) -> str:
        """Store an uploaded image on disk and register its metadata in the database.

        Args:
            image_path (str): Filesystem path to the temporary source image.
            object_id (int): Primary key of the entity associated with the image.
            object_type (str): Domain entity discriminator ('car' or 'tenant').
            category (str): Sub-category classification for the image. Defaults to 'car_photo'.
            db (Session | None): Optional existing database session. Defaults to None.

        Returns:
            str: Destination storage path if successfully saved, or an empty string on failure.
        """
        if db is None:
            db = session_factory()

        try:
            subdir = IMAGE_SUBDIRS.get(category, f"{object_type}s/{category}")

            unique_suffix = uuid.uuid4().hex[:8]
            file_name = f"{object_id}_{unique_suffix}.jpg"
            dest_path = Path(config.app_data_path) / "images" / subdir / file_name

            dest_str = str(dest_path)
            self.file_manager.copy_file(image_path, dest_str)

            new_image = Image(
                object_type=object_type,
                object_id=object_id,
                category=category,
                path=dest_str,
            )
            db.add(new_image)
            db.commit()
            return dest_str

        except Exception:
            logger.exception(
                f"An error occurred while saving the image for {object_type} {object_id}."
            )
            return ""

    def save_statement(self, file_path: str, db: Session | None = None) -> bool:
        """Parse an external bank PDF statement and persist all extracted payments.

        Args:
            file_path (str): Filesystem path to the bank statement PDF file.
            db (Session | None): Optional existing database session. Defaults to None.

        Returns:
            bool: True if parsing and database insertion succeeded, False otherwise.
        """
        if db is None:
            db = session_factory()

        try:
            data = process_sber_pdf(file_path)
            for payment in data:
                # Infer transaction direction based on sign since raw statements combine both flows
                payment["type"] = (
                    PaymentType.income
                    if payment["value_account_currency"] >= 0
                    else PaymentType.expense
                )
                payment["amount"] = payment["value_account_currency"]

                new_payment = Payment(is_parsed=True, **payment)
                db.add(new_payment)
            db.commit()
            return True

        except Exception:
            logger.exception(
                f"An error when trying to parse statement. File: {file_path}"
            )
            return False
