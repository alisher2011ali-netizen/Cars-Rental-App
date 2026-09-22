import enum
import os
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    DECIMAL,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    create_engine,
    func,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    sessionmaker,
)

data_path = os.getenv("FLET_APP_STORAGE_DATA")
if not data_path:
    data_path = os.getcwd()
db_path = os.path.join(data_path, "main.db")

engine = create_engine(f"sqlite:///{db_path}", echo=False)
session_factory = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


class ImageCategory(str, enum.Enum):
    AVATAR = "avatar"
    PASSPORT = "passport"
    SUB_PASSPORT = "sub_passport"
    DRIVE_LICENSE = "drive_license"
    CAR_PHOTO = "car_photo"


class Image(Base):
    __tablename__ = "images"

    id: Mapped[int] = mapped_column(primary_key=True)
    path: Mapped[str] = mapped_column(String(300))
    object_id: Mapped[int] = mapped_column(Integer)
    object_type: Mapped[str] = mapped_column(String(50))  # "car" or "tenant"
    category: Mapped[str] = mapped_column(String(50), nullable=False)


class Car(Base):
    __tablename__ = "cars"

    id: Mapped[int] = mapped_column(primary_key=True)
    brand: Mapped[str] = mapped_column(String(50))
    model: Mapped[str] = mapped_column(String(50))
    year: Mapped[int] = mapped_column(Integer)
    plate_number: Mapped[str] = mapped_column(String(20), unique=True)
    status: Mapped[str] = mapped_column(
        String(20), default="available"
    )  # available/rented/maintenance
    notes: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, onupdate=func.now(), nullable=True
    )

    rentals: Mapped[list["Rental"]] = relationship(back_populates="car")
    images: Mapped[list["Image"]] = relationship(
        "Image",
        primaryjoin="and_(Car.id==Image.object_id, Image.object_type=='car')",
        foreign_keys=[Image.object_id],
        viewonly=True,
    )


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150))

    phone_number: Mapped[str] = mapped_column(String(20))
    debt_sum: Mapped[Decimal] = mapped_column(
        DECIMAL, default=Decimal(0)
    )  # Total amount owed by tenant in rubles
    next_payment_due: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )  # Next payment due date

    avatar: Mapped["Image"] = relationship(
        "Image",
        primaryjoin=f"and_(Tenant.id==Image.object_id, Image.object_type=='tenant', Image.category=='{ImageCategory.AVATAR}')",
        foreign_keys=[Image.object_id],
        uselist=False,  # Возвращает один объект Image, а не list
        viewonly=True,
    )
    passport: Mapped["Image"] = relationship(
        "Image",
        primaryjoin=f"and_(Tenant.id==Image.object_id, Image.object_type=='tenant', Image.category=='{ImageCategory.PASSPORT}')",
        foreign_keys=[Image.object_id],
        uselist=False,
        viewonly=True,
    )
    sub_passport: Mapped["Image"] = relationship(
        "Image",
        primaryjoin=f"and_(Tenant.id==Image.object_id, Image.object_type=='tenant', Image.category=='{ImageCategory.SUB_PASSPORT}')",
        foreign_keys=[Image.object_id],
        uselist=False,
        viewonly=True,
    )
    drive_license: Mapped["Image"] = relationship(
        "Image",
        primaryjoin=f"and_(Tenant.id==Image.object_id, Image.object_type=='tenant', Image.category=='{ImageCategory.DRIVE_LICENSE}')",
        foreign_keys=[Image.object_id],
        uselist=False,
        viewonly=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, onupdate=func.now(), nullable=True
    )

    rentals: Mapped[list["Rental"]] = relationship(back_populates="tenant")


class Rental(Base):
    __tablename__ = "rentals"

    id: Mapped[int] = mapped_column(primary_key=True)
    car_id: Mapped[int] = mapped_column(ForeignKey("cars.id"))
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"))

    start_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    end_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    weekly_price: Mapped[Decimal] = mapped_column(DECIMAL)
    total_cost: Mapped[Decimal] = mapped_column(
        DECIMAL, default=Decimal(0)
    )  # weekly_price * number_of_weeks
    status: Mapped[str] = mapped_column(
        String(20), default="active"
    )  # active/completed/cancelled
    notes: Mapped[str | None] = mapped_column(String(500))

    car: Mapped["Car"] = relationship(back_populates="rentals")
    tenant: Mapped["Tenant"] = relationship(back_populates="rentals")
    payments: Mapped[list["Payment"]] = relationship(back_populates="rental")


class PaymentType(str, enum.Enum):
    income = "income"
    expense = "expense"


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    rental_id: Mapped[int | None] = mapped_column(
        ForeignKey("rentals.id"), nullable=True
    )

    amount: Mapped[Decimal] = mapped_column(DECIMAL)
    type: Mapped[PaymentType] = mapped_column(Enum(PaymentType))
    date: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    comment: Mapped[str | None] = mapped_column(String(200), nullable=True)

    is_parsed: Mapped[bool] = mapped_column(Boolean, default=False)
    operation_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    value_account_currency: Mapped[Decimal | None] = mapped_column(
        DECIMAL, nullable=True
    )
    remainder_account_currency: Mapped[Decimal | None] = mapped_column(
        DECIMAL, nullable=True
    )
    processing_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    authorisation_code: Mapped[int | None] = mapped_column(
        Integer, unique=True, nullable=True
    )
    description: Mapped[str | None] = mapped_column(String(200), nullable=True)

    rental: Mapped["Rental"] = relationship(back_populates="payments")


def init_db():
    Base.metadata.create_all(engine)
