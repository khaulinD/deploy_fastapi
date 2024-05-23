import datetime
import math
from fastapi import HTTPException, status
from sqlalchemy import DateTime, func, ForeignKey, select, desc, Integer, or_, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Mapped, mapped_column, relationship, selectinload

from auth import utils as auth_utils
from core.config import settings
from core.mailer import send_email_with_credentials, send_email_async
from db.models.company import Company
from db.models.doctors.doctor_base import DoctorBase
from typing import TYPE_CHECKING

from db.postgres import Base
from decorators.as_dict import AsDictMixin
from decorators.db_session import db_session
from doctor.schemas import DoctorUpdatePartial
from user_helper.utils import get_user_by_email

if TYPE_CHECKING:
    from db.models.notes.note_history import NoteHistory


class CompanyDoctor(DoctorBase, Base, AsDictMixin):

    company_id = mapped_column(Integer(), ForeignKey("companys.id"))
    company = relationship("Company", back_populates="doctors")
    last_online = mapped_column(DateTime, onupdate=func.now())

    user_notes = relationship("NoteHistory", back_populates="user")


class CompanyDoctorStore:

    @staticmethod
    @db_session
    async def create(session, data: dict):
        from db.models.user_tariff import UserTariffPlanStore
        try:
            company, companydoctor = await get_user_by_email(data['email'])

            if company or companydoctor:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Email already registered')
            else:
                company_id = data['company_id']

                # Retrieve the company by ID
                result = await session.execute(
                    select(Company)
                    .options(selectinload(Company.user_tariff))
                    .options(selectinload(Company.doctors))
                    .where(Company.id == company_id)
                )
                company = result.scalar()

                if not company:
                    raise HTTPException(status_code=404, detail="Company not found")
                # Ensure the company has a tariff plan associated with it
                if not company.user_tariff:
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company does not have a tariff plan")
                # Check if the current number of doctors is less than the allowed number specified by the tariff plan
                tariff_plan = await UserTariffPlanStore.get_user_plan_by_id(plan_id=company.user_tariff.id)
                if (not tariff_plan.tariff_info.doctor_amount or
                        len(company.doctors) < tariff_plan.tariff_info.doctor_amount):
                    doctor = CompanyDoctor(**data)
                    # Add and commit the new doctor to the database
                    session.add(doctor)
                    await session.commit()
                    doctor.role = "user"
                    return doctor

                    # raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Email send failed")
                else:
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Maximum number of doctors reached for this company")

        except IntegrityError as e:
            if "unique constraint" in str(e):
                raise HTTPException(status_code=409, detail="Email already registered")
            else:
                raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    @db_session
    async def get_doctor_by_id(session, doctor_id: int):
        result = await session.execute(select(CompanyDoctor).where(CompanyDoctor.id == doctor_id))
        doctor = result.scalar()
        if not doctor:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Doctor not found")
        return doctor

    @staticmethod
    @db_session
    async def update_online_doctor(session, doctor_id: int):

        stmt = (update(CompanyDoctor)
                .where(CompanyDoctor.id == doctor_id)
                .values(last_online=datetime.datetime.now()))
        # Execute the update query
        await session.execute(stmt)

        # Commit the transaction
        await session.commit()

    @staticmethod
    @db_session
    async def get_doctor_by_email(session, email):
        result = await session.execute(select(CompanyDoctor).where(CompanyDoctor.email == email))
        doctor = result.scalar()
        return doctor

    @staticmethod
    @db_session
    async def get_all_doctor(session, pagination: int, page: int):

        offset = pagination * (page - 1)

        result = await session.execute(
            select(CompanyDoctor).order_by(
                desc(CompanyDoctor.updated_at)
            ).offset(offset).limit(pagination)
        )
        docs = [row[0] for row in result.all()]
        return docs

    @staticmethod
    @db_session
    async def get_doctor_company(session, company_id: int):
        result = await session.execute(select(CompanyDoctor).where(CompanyDoctor.company_id == company_id))

        docs = [row[0] for row in result.all()]
        if not docs:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Company not found")
        return docs


    @staticmethod
    @db_session
    async def update_doctor(session,
                            doctor_id: int,
                            data: DoctorUpdatePartial):

        try:
            doctor = await session.get(CompanyDoctor, doctor_id)
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

    @staticmethod
    @db_session
    async def delete_doctor(session, doctor_id: int):
        try:
            query = select(CompanyDoctor).filter(CompanyDoctor.id == doctor_id)
            result = await session.execute(query)
            doctor = result.scalar()
            if doctor:
                await session.delete(doctor)
                await session.commit()
            else:
                raise HTTPException(status_code=404, detail="Doctor not found")
        except IntegrityError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="error while deleting doctor")

    @staticmethod
    @db_session
    async def search_company_with_doctors(session, page: int, company_id: int, search_info: str = None):
        try:
            from db.models.user_tariff import UserTariffPlanStore
            pagination = settings.pagination
            # Calculate offset
            offset = pagination * (page - 1)
            # Perform the query to fetch the company
            company_query = (
                select(Company)
                .options(selectinload(Company.doctors))  # Eagerly load doctors relationship
                .where(Company.id == company_id)
            )
            company_result = await session.execute(company_query)
            company = company_result.scalars().first()  # Get the first result
            if not company:
                raise HTTPException(status_code=404, detail="Company not found")

            # Fetch the total number of doctors for the company
            total_doctors_query = select(func.count()).where(CompanyDoctor.company_id == company_id)
            total_doctors_result = await session.execute(total_doctors_query)
            total_doctors = total_doctors_result.scalar()

            # Calculate the total number of pages
            total_pages = math.ceil(total_doctors / pagination)
            company.amount_of_pages = total_pages

            # Fetch the TariffPlan associated with the company
            # result = await session.execute(select().where(TariffPlan.id == company.tariff_plan_id))

            tariff_info = await UserTariffPlanStore.get_user_plan_by_id(plan_id=company.user_tariff_id)
            company.user_tariff = tariff_info

            if total_doctors != 0:
                # Perform the query to fetch doctors with pagination
                if search_info:
                    search_info = search_info.replace(" ", "")
                    doctors_query = (
                        select(CompanyDoctor)
                        .where(
                            CompanyDoctor.company_id == company_id,
                            or_(
                                func.replace(func.concat(CompanyDoctor.firstName, CompanyDoctor.lastName), ' ',
                                             '').ilike("%" + search_info + "%"),
                                func.replace(func.concat(CompanyDoctor.lastName, CompanyDoctor.firstName), ' ',
                                             '').ilike("%" + search_info + "%")
                            )
                        )
                        .order_by(desc(CompanyDoctor.updated_at))
                        .offset(offset)
                        .limit(pagination)
                    )
                    doctors_result = await session.execute(doctors_query)
                    doctors = doctors_result.scalars().all()
                    total_pages = math.ceil(len(doctors) / pagination)
                else:
                    doctors_query = (
                        select(CompanyDoctor)
                        .where(CompanyDoctor.company_id == company_id)
                        .order_by(desc(CompanyDoctor.updated_at))
                        .offset(offset)
                        .limit(pagination)
                    )
                    doctors_result = await session.execute(doctors_query)
                    doctors = doctors_result.scalars().all()
                company.doctors = doctors
            company.amount_of_pages = total_pages
            return company
        except Exception as e:
            raise HTTPException(status_code=403, detail=str(e))

    @staticmethod
    @db_session
    async def delete_all_doctors(session, company_id: int):
        try:
            query = await session.execute(select(CompanyDoctor).filter(CompanyDoctor.company_id == company_id))

            for doctor in query.all():
                await session.delete(doctor[0])
            await session.commit()
        except IntegrityError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="error while deleting doctor")
