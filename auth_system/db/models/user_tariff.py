from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from company.schemas import CompanyUpdatePartial
from db.postgres import Base
from sqlalchemy import Integer, ForeignKey, DateTime, func, select, desc, String, TIMESTAMP
from fastapi import HTTPException, status
from sqlalchemy.orm import relationship, mapped_column, joinedload
from sqlalchemy.exc import IntegrityError
from decorators.as_dict import AsDictMixin
from typing import TYPE_CHECKING
from auth.utils import deactivate_company_doctor
from decorators.db_session import db_session
from doctor.schemas import DoctorUpdatePartial
from tariff_plan.schemas import ParticularUpdateUserTariffPlan


if TYPE_CHECKING:
    from db.models.tariff_plan_info import TariffPlan, TariffPlanStore
    from db.models.company import Company
    from db.models.doctors.doctor import Doctor


class UserTariffPlan(Base, AsDictMixin):
    tariff_id = mapped_column(Integer, ForeignKey('tariffplans.id'), nullable=True)
    expired_at = mapped_column(DateTime, nullable=True)
    customer = mapped_column(String, nullable=True, unique=True)
    payment_intent_id = mapped_column(String, nullable=True)
    subscription_id = mapped_column(String, nullable=True)

    created_at = mapped_column(DateTime, default=func.now())
    updated_at = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    company = relationship("Company", back_populates="user_tariff")
    doctor = relationship("Doctor", back_populates="user_tariff")
    tariff_plan = relationship("TariffPlan", back_populates="user_tariff")
    # addtional_users = relationship("AddtionalUser", back_populates="user_tariff")




class UserTariffPlanStore:

    @staticmethod
    @db_session
    async def create(session, user_id: int, user_type: str, data: dict):
        from db.models.company import CompanyStore
        from db.models.doctors.doctor import DoctorStore
        from db.models.tariff_plan_info import TariffPlanStore
        tariff_data = await TariffPlanStore.get_plan_by_id(plan_id=data["tariff_id"])
        data["expired_at"] = datetime.now() + relativedelta(months=tariff_data.duration)
        plan = UserTariffPlan(**data)
        session.add(plan)
        await session.commit()
        if user_type == "company":
            await CompanyStore.update_company(company_id=user_id, data=CompanyUpdatePartial(user_tariff_id=plan.id))
        elif user_type == "user":
            await DoctorStore.update_doctor(doctor_id=user_id, data=DoctorUpdatePartial(user_tariff_id=plan.id, active=True))
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user type")

        return plan

    @staticmethod
    @db_session
    async def create_previous(session, data: dict):
        from db.models.company import CompanyStore
        from db.models.doctors.company_doctor import CompanyDoctorStore
        if "customer" in data:
            tariff = await session.execute(select(UserTariffPlan).where(UserTariffPlan.customer == data["customer"]))
            tariff = tariff.scalar()
            if tariff:
                tariff.subscription_id = data["subscription_id"]
                await session.commit()
                customer = await CompanyStore.get_company_by_stripe_id_with_doctors(stripe_id=data['customer'])
                if customer.doctors:
                    await deactivate_company_doctor(customer.doctors, True)
                return tariff

        plan = UserTariffPlan(**data)
        session.add(plan)
        await session.commit()
        return plan

    @staticmethod
    @db_session
    async def get_by_customer(session, customer: str):
        result = await session.execute(select(UserTariffPlan).where(UserTariffPlan.customer == customer))
        user_tariff = result.scalar()
        return user_tariff

    @staticmethod
    @db_session
    async def get_user_plan_by_id(session, plan_id: int):
        from db.models.tariff_plan_info import TariffPlanStore
        print(plan_id)
        result = await session.execute(select(UserTariffPlan).where(UserTariffPlan.id == plan_id))
        user_tariff = result.scalar()

        if user_tariff:
            tariff_plan = await TariffPlanStore.get_plan_by_id(plan_id=user_tariff.tariff_id)
            user_tariff.tariff_info = tariff_plan
            user_tariff.time_left = (user_tariff.expired_at - datetime.utcnow()).days
        # if not user_tariff:
        #     raise HTTPException(status_code=404, detail="Tariff not found")
        return user_tariff

    @staticmethod
    @db_session
    async def get_clean_plan_by_id(session, plan_id: int):
        from db.models.tariff_plan_info import TariffPlanStore
        result = await session.execute(select(UserTariffPlan).where(UserTariffPlan.id == plan_id))
        user_tariff = result.scalar()
        return user_tariff

    @staticmethod
    @db_session
    async def get_all_plan(session):
        from db.models.tariff_plan_info import TariffPlanStore
        result = await session.execute(
            select(UserTariffPlan).order_by(
                desc(UserTariffPlan.updated_at))
        )
        user_tariff = result.scalar()
        tariff_plan = await TariffPlanStore.get_plan_by_id(plan_id=user_tariff.id)
        user_tariff.tariff_info = tariff_plan
        if not result:
            raise HTTPException(status_code=404, detail="Company not found")

        docs = [row[0] for row in result.all()]
        return docs

    @staticmethod
    @db_session
    async def setup_payment(session, plan_id: int, data: dict):

        try:
            print(data)
            if "expired_at" in data:
                plan = await session.get(UserTariffPlan, plan_id)
                plan.expired_at = datetime.utcfromtimestamp(data["expired_at"])
                await session.commit()
                return plan

            if "payment_intent_id" in data:
                plan = await session.get(UserTariffPlan, plan_id)
                plan.payment_intent_id = data["payment_intent_id"]
                await session.commit()
                return plan

            if "user_id" and "tariff_id" and "user_type" in data:
                from db.models.company import CompanyStore
                from db.models.doctors.doctor import DoctorStore
                from db.models.tariff_plan_info import TariffPlanStore

                tariff_data = await TariffPlanStore.get_plan_by_id(plan_id=data["tariff_id"])
                # data["expired_at"] = datetime.now() + timedelta(days=tariff_data.duration)
                if data["user_type"] == "company":
                    await CompanyStore.update_company(company_id=data["user_id"],
                                                      data=CompanyUpdatePartial(user_tariff_id=plan_id))
                else:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user type")
            plan = await session.get(UserTariffPlan, plan_id)
            if plan is None:
                raise HTTPException(status_code=404, detail="Plan not found")

            plan.tariff_id = data["tariff_id"]
            # plan.expired_at = data["expired_at"]

            await session.commit()
            return plan

        except IntegrityError as e:
            print(str(e))
            raise HTTPException(status_code=400, detail=str(e))

    @staticmethod
    @db_session
    async def update_plan(session, plan_id: int, data: ParticularUpdateUserTariffPlan):

        try:
            plan = await session.get(UserTariffPlan, plan_id)
            if plan is None:
                raise HTTPException(status_code=404, detail="Doctor not found")

            for name, value in data:
                setattr(plan, name, value)

            await session.commit()
            return plan

        except IntegrityError as e:
            HTTPException(status_code=400, detail=str(e))

    @staticmethod
    @db_session
    async def delete_plan(session, plan_id: int):
        try:
            query = select(UserTariffPlan).filter(UserTariffPlan.id == plan_id)
            result = await session.execute(query)
            plan = result.scalar()
            if plan:
                await session.delete(plan)
                await session.commit()
            else:
                raise HTTPException(status_code=404, detail="Plan not found")
        except IntegrityError as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="error while deleting plan")

    @staticmethod
    @db_session
    async def delete_customer_plan(session, customer_id: int, plan_id: str):
        from db.models.company import CompanyStore
        await CompanyStore.update_company(company_id=customer_id, data=CompanyUpdatePartial(user_tariff_id=None))

        query = select(UserTariffPlan).filter(UserTariffPlan.id == plan_id)
        result = await session.execute(query)
        plan = result.scalar()
        if plan:
            await session.delete(plan)
            await session.commit()
        else:
            raise HTTPException(status_code=404, detail="Plan not found")

    @staticmethod
    @db_session
    async def get_all_tariff_with_current(session, user_tariff: int | None):
        from db.models.tariff_plan_info import TariffPlanStore
        user_plan = await UserTariffPlanStore.get_clean_plan_by_id(plan_id=user_tariff)
        if user_tariff is None:
            other_tariff = await TariffPlanStore.get_all_plan()
            current_plan = None
        else:
            current_plan = await TariffPlanStore.get_plan_by_id(plan_id=user_plan.tariff_id)
            current_plan.used_time = (datetime.now() - user_plan.updated_at).days + 1
            # current_plan.refund_time = (datetime.now() - user_plan.updated_at).days + 1
            # print(current_plan.used_time)
            other_tariff = await TariffPlanStore.get_all_plan()
            for tariff in other_tariff:
                tariff.can_upgrade = False

                print(tariff.can_upgrade)

        return {"current_plan": current_plan,
                "other_tariff": other_tariff}
