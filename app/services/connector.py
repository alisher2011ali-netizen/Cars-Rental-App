import base64
import logging
import uuid

from core.models import Car, Image, Payment, PaymentType, session_factory
from parsing.parser import process_sber_pdf
from services.file_manager import FileManager
from sqlalchemy import select
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class Connector:
    def __init__(self):
        self.file_manager = FileManager()

    def get_last_added_cars(
        self, limit: int = 5, db: Session | None = None
    ) -> tuple[list[Car], dict[int, list[str]]]:
        if db is None:
            db = session_factory()

        last_added_cars = db.scalars(
            select(Car).order_by(Car.id.desc()).limit(limit)
        ).all()
        if not last_added_cars:
            return [], {}
        try:
            images = {}
            for car in last_added_cars:
                images[car.id] = []

                if not car.images:
                    continue

                for car_image in car.images:
                    with open(car_image.path, "rb") as f:
                        image_bytes = f.read()
                        images[car.id].append(
                            base64.b64encode(image_bytes).decode("utf-8")
                        )
        except Exception:
            logger.exception(
                "An error occurred while retrieving images for the last added cars."
            )
            images = {car.id: [] for car in last_added_cars}

        return last_added_cars, images

    async def save_image(
        self,
        *,
        image_path: str,
        object_id: int,
        object_type: str,
        category: str = "car_photo",
        db: Session | None = None,
    ) -> str:
        if db is None:
            db = session_factory()

        try:
            unique_number = uuid.uuid4().hex[:8]
            if object_type == "car":
                new_path = f"data/images/cars/{object_id}_{unique_number}.jpg"
            elif object_type == "tenant":
                match category:
                    case "avatar":
                        new_path = f"data/images/tenants/avatars/{object_id}_{unique_number}.jpg"
                    case "passport":
                        new_path = f"data/images/tenants/passports/{object_id}_{unique_number}.jpg"
                    case "sub_passport":
                        new_path = f"data/images/tenants/sub_passports/{object_id}_{unique_number}.jpg"
                    case "driver_license":
                        new_path = f"data/images/tenants/driver_licenses/{object_id}_{unique_number}.jpg"

            self.file_manager.copy_file(image_path, new_path)
            new_image = Image(
                object_type=object_type,
                object_id=object_id,
                category=category,
                path=new_path,
            )
            db.add(new_image)
            db.commit()
            return new_path
        except Exception:
            logger.exception(
                f"An error occurred while saving the image for {object_type} {object_id}."
            )
            return ""

    def save_statement(self, file_path: str, db: Session | None = None) -> bool:
        if db is None:
            db = session_factory()

        try:
            data = process_sber_pdf(file_path)
            for payment in data:
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
