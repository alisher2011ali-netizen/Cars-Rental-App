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
    # Fallback to the current working directory if no dedicated storage directory is set
    data_path = os.getcwd()
db_path = os.path.join(data_path, "main.db")

engine = create_engine(f"sqlite:///{db_path}", echo=False)
session_factory = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    """Serve as the base class for declarative SQLAlchemy model definitions."""


class ImageCategory(str, enum.Enum):
    """Categorize the purpose and document type of an uploaded image."""

    avatar = "avatar"
    passport = "passport"
    sub_passport = "sub_passport"
    drive_license = "drive_license"
    car_photo = "car_photo"


class ImageObjectType(str, enum.Enum):
    """Represent target domain entities that can be associated with an image."""

    car = "car"
    tenant = "tenant"


class CarStatus(str, enum.Enum):
    """Represent the operational availability status of a vehicle."""

    available = "available"
    rented = "rented"
    maintance = "maintance"
    other = "other"


class RentalStatus(str, enum.Enum):
    """Represent the lifecycle state of a vehicle rental contract."""

    active = "active"
    completed = "completed"
    cancelled = "cancelled"


class PaymentType(str, enum.Enum):
    """Classify the cash flow direction of a financial transaction."""

    income = "income"
    expense = "expense"


class Image(Base):
    """Store filesystem references and polymorphic associations for images.

    Attributes:
        id (int): Primary key.
        path (str): Relative or absolute storage path to the image file.
        object_id (int): Identifier of the linked domain entity.
        object_type (ImageObjectType): Discriminator indicating the linked entity type.
        category (ImageCategory): Functional category of the image.
    """

    __tablename__ = "images"

    id: Mapped[int] = mapped_column(primary_key=True)
    path: Mapped[str] = mapped_column(String(300))
    object_id: Mapped[int] = mapped_column(Integer)
    object_type: Mapped[ImageObjectType] = mapped_column(Enum(ImageObjectType))
    category: Mapped[ImageCategory] = mapped_column(Enum(ImageCategory), nullable=False)


class Car(Base):
    """Represent a vehicle asset available for lease.

    Attributes:
        id (int): Primary key.
        brand (str): Vehicle make.
        model (str): Vehicle model.
        year (int): Manufacture year.
        plate_number (str): Unique license plate number.
        region_code (str): Vehicle registration region code.
        status (CarStatus): Operational status of the vehicle.
        notes (str | None): Optional administrative notes.
        created_at (datetime): Timestamp when the record was created.
        updated_at (datetime | None): Timestamp when the record was last modified.
        rentals (list[Rental]): Leases associated with this vehicle.
        images (list[Image]): Read-only polymorphic collection of vehicle photos.
    """

    __tablename__ = "cars"

    id: Mapped[int] = mapped_column(primary_key=True)
    brand: Mapped[str] = mapped_column(String(50))
    model: Mapped[str] = mapped_column(String(50))
    year: Mapped[int] = mapped_column(Integer)
    plate_number: Mapped[str] = mapped_column(String(15), unique=True)
    region_code: Mapped[str] = mapped_column(String(3))
    status: Mapped[CarStatus] = mapped_column(
        Enum(CarStatus), default=CarStatus.available
    )
    notes: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, onupdate=func.now(), nullable=True
    )

    rentals: Mapped[list["Rental"]] = relationship(back_populates="car")
    # Polymorphic join without an explicit foreign key constraint to keep the images table generic
    images: Mapped[list["Image"]] = relationship(
        "Image",
        primaryjoin="and_(Car.id==Image.object_id, Image.object_type=='car')",
        foreign_keys=[Image.object_id],
        viewonly=True,
    )


class Tenant(Base):
    """Represent an individual leasing a vehicle.

    Attributes:
        id (int): Primary key.
        name (str): Full legal name of the tenant.
        phone_number (str): Primary contact phone number.
        debt_sum (Decimal): Outstanding debt balance.
        next_payment_due (datetime | None): Scheduled due date for the next payment.
        avatar (Image): Read-only reference to the tenant's profile avatar.
        passport (Image): Read-only reference to the tenant's primary passport page.
        sub_passport (Image): Read-only reference to the secondary passport/registration page.
        drive_license (Image): Read-only reference to the driver's license image.
        created_at (datetime): Timestamp when the record was created.
        updated_at (datetime | None): Timestamp when the record was last modified.
        rentals (list[Rental]): Leases associated with the tenant.
    """

    __tablename__ = "tenants"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150))

    phone_number: Mapped[str] = mapped_column(String(20))
    debt_sum: Mapped[Decimal] = mapped_column(DECIMAL, default=Decimal(0))
    next_payment_due: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Use explicit string interpolation in primaryjoin to filter by category and enforce 1-to-1 semantics
    avatar: Mapped["Image"] = relationship(
        "Image",
        primaryjoin=f"and_(Tenant.id==Image.object_id, Image.object_type=='tenant', Image.category=='{ImageCategory.avatar}')",
        foreign_keys=[Image.object_id],
        uselist=False,
        viewonly=True,
    )
    passport: Mapped["Image"] = relationship(
        "Image",
        primaryjoin=f"and_(Tenant.id==Image.object_id, Image.object_type=='tenant', Image.category=='{ImageCategory.passport}')",
        foreign_keys=[Image.object_id],
        uselist=False,
        viewonly=True,
    )
    sub_passport: Mapped["Image"] = relationship(
        "Image",
        primaryjoin=f"and_(Tenant.id==Image.object_id, Image.object_type=='tenant', Image.category=='{ImageCategory.sub_passport}')",
        foreign_keys=[Image.object_id],
        uselist=False,
        viewonly=True,
    )
    drive_license: Mapped["Image"] = relationship(
        "Image",
        primaryjoin=f"and_(Tenant.id==Image.object_id, Image.object_type=='tenant', Image.category=='{ImageCategory.drive_license}')",
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
    """Represent an agreement leasing a vehicle to a tenant.

    Attributes:
        id (int): Primary key.
        car_id (int): Foreign key referencing the associated car.
        tenant_id (int): Foreign key referencing the leasing tenant.
        start_date (datetime): Rental period commencement timestamp.
        end_date (datetime | None): Rental period expiration timestamp.
        period (int): Lease duration in days.
        price_per_period (Decimal): Cost charged per specified rental period.
        total_cost (Decimal): Aggregate lease cost.
        status (RentalStatus): Current lifecycle state of the rental.
        notes (str | None): Optional contractual or condition notes.
        car (Car): Linked vehicle entity.
        tenant (Tenant): Linked tenant entity.
        payments (list[Payment]): Payments logged against this rental agreement.
    """

    __tablename__ = "rentals"

    id: Mapped[int] = mapped_column(primary_key=True)
    car_id: Mapped[int] = mapped_column(ForeignKey("cars.id"))
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"))

    start_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    end_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    period: Mapped[int] = mapped_column(Integer)
    price_per_period: Mapped[Decimal] = mapped_column(DECIMAL)
    total_cost: Mapped[Decimal] = mapped_column(
        DECIMAL,
        default=Decimal(0),
    )
    status: Mapped[RentalStatus] = mapped_column(
        Enum(RentalStatus), default=RentalStatus.active
    )
    notes: Mapped[str | None] = mapped_column(String(500))

    car: Mapped["Car"] = relationship(back_populates="rentals")
    tenant: Mapped["Tenant"] = relationship(back_populates="rentals")
    payments: Mapped[list["Payment"]] = relationship(back_populates="rental")


class Payment(Base):
    """Record financial transactions, including bank statement imports.

    Attributes:
        id (int): Primary key.
        rental_id (int | None): Foreign key referencing the rental, if applicable.
        amount (Decimal): Transaction amount.
        type (PaymentType): Transaction flow direction.
        date (datetime): Transaction recording timestamp.
        notes (str | None): Optional transaction memo.
        is_parsed (bool): Flag indicating if the record originated from an imported statement.
        operation_date (datetime | None): Execution timestamp provided by the financial provider.
        category (str | None): Banking category classification.
        value_account_currency (Decimal | None): Transaction magnitude in settlement currency.
        remainder_account_currency (Decimal | None): Running account balance post-transaction.
        processing_date (datetime | None): Timestamp when the transaction cleared.
        authorisation_code (int | None): Bank authorization transaction reference code.
        description (str | None): Raw statement description payload.
        rental (Rental): Linked rental contract if attributed.
    """

    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    rental_id: Mapped[int | None] = mapped_column(
        ForeignKey("rentals.id"), nullable=True
    )

    amount: Mapped[Decimal] = mapped_column(DECIMAL)
    type: Mapped[PaymentType] = mapped_column(Enum(PaymentType))
    date: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    notes: Mapped[str | None] = mapped_column(String(200), nullable=True)

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


def init_db() -> None:
    """Create all configured database tables within the target SQLite instance.

    Args:
        None

    Returns:
        None: Tables are created in-place via metadata DDL execution.
    """
    Base.metadata.create_all(engine)
