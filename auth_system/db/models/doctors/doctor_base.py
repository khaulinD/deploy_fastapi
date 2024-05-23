from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.hybrid import hybrid_property


class DoctorBase:
    firstName: Mapped[str] = mapped_column()
    lastName: Mapped[str] = mapped_column()
    position: Mapped[str]
    password: Mapped[bytes]
    email: Mapped[str] = mapped_column(unique=True)
    active: Mapped[bool] = mapped_column(default=True)

    created_at = mapped_column(DateTime, default=func.now())
    updated_at = mapped_column(DateTime, default=func.now(), onupdate=func.now())





