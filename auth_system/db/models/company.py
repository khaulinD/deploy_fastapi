from typing import TYPE_CHECKING
from sqlalchemy import Column
from fastapi import HTTPException
from sqlalchemy import DateTime, func, select, desc, Integer, ForeignKey
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Mapped, mapped_column, relationship, selectinload
from starlette import status
from auth import utils as auth_utils
from company.schemas import CompanyUpdatePartial
from core.mailer import send_verification_email
from db.postgres import Base
from decorators.as_dict import AsDictMixin
from decorators.db_session import db_session
from user_helper.utils import generate_token, get_user_by_email

# from db.models.tariff_plan import TariffPlan
if TYPE_CHECKING:
    from db.models.user_tariff import UserTariffPlan


class Company(Base, AsDictMixin):
    name: Mapped[str] = mapped_column()
    password: Mapped[bytes] = mapped_column(nullable=True)
    email: Mapped[str] = mapped_column(unique=True)
    active: Mapped[bool] = mapped_column(default=True)

    created_at = mapped_column(DateTime, default=func.now())
    updated_at = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    doctors = relationship("CompanyDoctor", back_populates="company")

    user_tariff_id = mapped_column(Integer, ForeignKey('usertariffplans.id'))
    user_tariff = relationship("UserTariffPlan", back_populates="company")
    has_refunded: Mapped[bool] = mapped_column(default=False)

    stripe_customer_id: Mapped[str] = mapped_column(nullable=True, default=None)
    stripe_coupon_id: Mapped[str] = mapped_column(nullable=True)

    is_verified: Mapped[bool] = mapped_column(default=False)


class CompanyStore:
    @staticmethod
    @db_session
    async def create(session, data: dict):
        try:
            company, companydoctor = await get_user_by_email(data['email'])

            if company or companydoctor:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Email already registered')
            else:

                if 'password' in data:
                    data["password"] = auth_utils.hash_password(data["password"])
                company = Company(**data)
                session.add(company)
                await session.commit()

                # token = await generate_token(company, "company")
                # await send_verification_email(data["email"], token)
                company.role = "company"
                return company
        except IntegrityError as e:
            if "unique constraint" in str(e):
                raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                    detail="Email already registered")
            else:
                # For any other IntegrityError, re-raise it
                raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    @db_session
    async def get_company_by_id(session, company_id: int):
        from db.models.user_tariff import UserTariffPlanStore
        result = await session.execute(select(Company).where(Company.id == company_id))
        company = result.scalar()
        if company is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
        result = await UserTariffPlanStore.get_user_plan_by_id(plan_id=company.user_tariff_id)

        # tariff_info = result.scalar()
        company.tariff_plan = result
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        return company

    @staticmethod
    @db_session
    async def get_company_clean_by_id(session, company_id: int):
        result = await session.execute(select(Company).where(Company.id == company_id))
        company = result.scalar()
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        return company

    @staticmethod
    @db_session
    async def get_company_by_email(session, email):
        result = await session.execute(select(Company).where(Company.email == email))
        if not result:
            raise HTTPException(status_code=404, detail="Company not found")

        company = result.scalar()
        return company

    @staticmethod
    @db_session
    async def get_all_company(session, **kwargs):
        result = await session.execute(
            select(Company).order_by(
                desc(Company.updated_at))
        )

        if not result:
            raise HTTPException(status_code=404, detail="Company not found")

        docs = [row[0] for row in result.all()]
        return docs

    @staticmethod
    @db_session
    async def get_company_with_doctors(session, company_id: int):
        from db.models.user_tariff import UserTariffPlanStore
        # Join the Company and Doctor tables
        query = (
            select(Company)
            .options(selectinload(Company.doctors))  # Eagerly load doctors relationship
            .where(Company.id == company_id)
        )

        company = await session.execute(query)
        company_with_doctors = company.scalar()
        if not company_with_doctors.user_tariff_id:
            return None
        result = await UserTariffPlanStore.get_user_plan_by_id(company_with_doctors.user_tariff_id)
        # tariff_info = result.scalar()
        company_with_doctors.tariff_plan = result
        if not company_with_doctors:
            raise HTTPException(status_code=404, detail="Company not found")

        return company_with_doctors

    @staticmethod
    @db_session
    async def update_company(session,
                             company_id: int,
                             data: CompanyUpdatePartial):
        try:
            company = await session.get(Company, company_id)
            if company is None:
                raise HTTPException(status_code=404, detail="Company not found")

            for name, value in data.model_dump(exclude_unset=True).items():
                if name == "password":
                    value = auth_utils.hash_password(value)
                setattr(company, name, value)

            await session.commit()
            return company
        except IntegrityError as e:
            if "unique constraint" in str(e):
                raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                    detail="Email already registered")
            else:
                raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    @db_session
    async def get_company_with_tariff_plan(session, company_id: int):
        result = await session.execute(select(Company).options(selectinload(Company.user_tariff)).where(Company.id == company_id))
        company = result.scalar()
        return company

    @staticmethod
    @db_session
    async def get_company_by_stripe_id(session, stripe_id: str):
        result = await session.execute(select(Company).where(Company.stripe_customer_id == stripe_id))
        if not result:
            raise HTTPException(status_code=404, detail="Company not found")

        company = result.scalar()
        return company

    @staticmethod
    @db_session
    async def get_company_by_stripe_id_with_doctors(session, stripe_id: str):
        result = await session.execute(
            select(Company)
            .options(selectinload(Company.doctors))  # Eagerly load doctors relationship
            .where(Company.stripe_customer_id == stripe_id)
        )
        if not result:
            raise HTTPException(status_code=404, detail="Company not found")

        company = result.scalar()
        return company
