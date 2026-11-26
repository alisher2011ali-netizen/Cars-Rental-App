import asyncio
import logging
import uuid
from pathlib import Path

from core.config import config
from core.models import Image, Payment, PaymentType, session_factory
from parsing.parser import process_sber_pdf
from PIL import Image as PILImage
from PIL import ImageOps

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
        pass

    def _process_and_save(
        src_path: str, dst_path: str, max_size: int = 1600, quality: int = 82
    ) -> None:
        Path(dst_path).parent.mkdir(parents=True, exist_ok=True)

        with PILImage.open(src_path) as img:  # Image.open отлично принимает Path
            img = ImageOps.exif_transpose(img)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.thumbnail((max_size, max_size), PILImage.Resampling.LANCZOS)
            img.save(dst_path, format="JPEG", quality=quality, optimize=True)

    async def save_image(
        self, image_path: str, object_id: int, object_type: str, category: str
    ) -> str:
        """Настоящий неблокирующий асинхронный метод для Flet."""
        try:
            subdir = IMAGE_SUBDIRS.get(category, "other")

            unique = uuid.uuid4().hex[:8]
            file_name = f"{object_id}_{unique}.jpg"
            dst_path = str(Path(config.app_data_path) / "images" / subdir / file_name)

        except Exception:
            logger.exception(
                f"An error occurred while saving the image for {object_type} {object_id}."
            )
            return ""

        await asyncio.to_thread(self._process_and_save_sync, image_path, dst_path)
        with session_factory as db:
            new_image = Image(
                object_type=object_type,
                object_id=object_id,
                category=category,
                path=dst_path,
            )
            db.add(new_image)
            db.commit()
        return dst_path

    def save_statement(self, file_path: str) -> bool:
        """Parse an external bank PDF statement and persist all extracted payments."""

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
