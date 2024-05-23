from fastapi import HTTPException, status
from sqlalchemy import DateTime, func, ForeignKey, select, desc, Integer
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Mapped, mapped_column, relationship

from auth import utils as auth_utils
from core.mailer import send_verification_email
from db.models.doctors.doctor_base import DoctorBase

from db.postgres import Base
from decorators.as_dict import AsDictMixin
from decorators.db_session import db_session
from doctor.schemas import DoctorUpdatePartial
from user_helper.utils import generate_token, get_user_by_email
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from db.models.user_tariff import UserTariffPlan


class Doctor(DoctorBase, Base, AsDictMixin):
    firstName: Mapped[str] = mapped_column()
    lastName: Mapped[str] = mapped_column()
    position: Mapped[str] = mapped_column(nullable=True)
    is_verified: Mapped[bool] = mapped_column(default=False)
    password: Mapped[bytes] = mapped_column(nullable=True)
    active: Mapped[bool] = mapped_column(default=False)
    user_tariff_id = mapped_column(Integer, ForeignKey('usertariffplans.id'))
    user_tariff = relationship("UserTariffPlan", back_populates="doctor")
    stripe_customer_id: Mapped[str] = mapped_column(nullable=True, default=None)

class DoctorStore:

    @staticmethod
    @db_session
    async def create(session, data: dict):
        try:
            company, companydoctor = await get_user_by_email(data['email'])

            if company or companydoctor:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Email already registered')
            else:
                if "password" in data:
                    data["password"] = auth_utils.hash_password(data["password"])
                doctor = Doctor(**data)
                session.add(doctor)
                await session.commit()
                doctor.role = "user"
                return doctor
        except IntegrityError as e:
            if "unique constraint" in str(e):
                raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                    detail="Email already registered")
            else:
                # For any other IntegrityError, re-raise it
                raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    @db_session
    async def get_doctor_by_id(session, doctor_id: int):
        from db.models.user_tariff import UserTariffPlanStore
        result = await session.execute(select(Doctor).where(Doctor.id == doctor_id))
        doctor = result.scalar()
        # print(doctor.user_tariff_id)
        if not doctor.user_tariff_id:
            return None

        result = await UserTariffPlanStore.get_user_plan_by_id(doctor.user_tariff_id)
        # tariff_info = result.scalar()
        doctor.tariff_plan = result
        return doctor

    @staticmethod
    @db_session
    async def get_doctor_clean_by_id(session, doctor_id: int):
        result = await session.execute(select(Doctor).where(Doctor.id == doctor_id))
        doctor = result.scalar()
        if not doctor:
            raise HTTPException(status_code=404, detail="Doctor not found")
        return doctor

    @staticmethod
    @db_session
    async def get_doctor_by_email(session, email):
        result = await session.execute(select(Doctor).where(Doctor.email == email))
        doctor = result.scalar()
        return doctor

    # @staticmethod
    # @db_session
    # async def get_all_doctor(session, pagination: int, page: int):
    #     # Calculate the offset
    #     if pagination < 0 or page < 0:
    #         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
    #
    #     offset = pagination * (page - 1)
    #
    #     result = await session.execute(
    #         select(Doctor).order_by(
    #             desc(Doctor.updated_at)
    #         ).offset(offset).limit(pagination)
    #     )
    #
    #     docs = [row[0] for row in result.all()]
    #     return docs

    @staticmethod
    @db_session
    async def update_doctor(session,
                            doctor_id: int,
                            data: DoctorUpdatePartial):
        try:
            doctor = await session.get(Doctor, doctor_id)
            if doctor is None:
                raise HTTPException(status_code=404, detail="Doctor not found")

            for name, value in data.model_dump(exclude_unset=True).items():
                if name == "password":
                    value = auth_utils.hash_password(value)
                setattr(doctor, name, value)

            await session.commit()
            return doctor
        except IntegrityError as e:
            if "unique constraint" in str(e):
                raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                    detail="Email already registered")
            else:
                raise HTTPException(status_code=500, detail=str(e))
