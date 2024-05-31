from datetime import timedelta
from typing import TYPE_CHECKING

import stripe

from core.config import settings
from auth import utils as auth_utils
from db.postgres import Base
from decorators.db_session import db_session
from decorators.as_dict import AsDictMixin
from sqlalchemy.orm import Mapped, relationship, mapped_column
from sqlalchemy import DateTime, func, select, desc
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from typing import TYPE_CHECKING
from tariff_plan.schemas import ParticularUpdateTariffPlan
from tariff_plan.utils import calculate_recurring_interval

if TYPE_CHECKING:
    from db.models.user_tariff import UserTariffPlan

stripe.api_key = settings.payments.private_key


class TariffPlan(Base, AsDictMixin):
    title: Mapped[str]
    description: Mapped[str]
    price: Mapped[float]
    doctor_amount: Mapped[int] = mapped_column(nullable=True)
    duration: Mapped[int]

    created_at = mapped_column(DateTime, default=func.now())
    updated_at = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    stripe_product_id: Mapped[str]
    stripe_price_id: Mapped[str]
    # stripe_price_year: Mapped[str]
    user_tariff = relationship("UserTariffPlan", back_populates="tariff_plan")


class TariffPlanStore:

    @staticmethod
    @db_session
    async def get_count(session) -> int:
        count_query = select(func.count()).select_from(TariffPlan)
        result = await session.execute(count_query)
        return result.scalar_one()

    @staticmethod
    @db_session
    async def create(session, data: dict):
        print(data)
        if data['duration'] == 12:
            print(data["price"])
            data["price"] = round((data["price"] * 0.9 * 12))
        plan = TariffPlan(**data)
        session.add(plan)
        try:
            # Create corresponding product and price in Stripe
            product = stripe.Product.create(
                name=plan.title,
                description=plan.description,
                metadata={"tariff_id": plan.id, "doctor_amount": plan.doctor_amount}
            )
            if plan.duration == 1:

                price = stripe.Price.create(
                    product=product.id,
                    unit_amount_decimal=int(plan.price * 100),
                    currency="usd",
                    recurring={"interval": calculate_recurring_interval(plan.duration)},
                )
            else:
                print(plan.price)
                price = stripe.Price.create(
                    product=product.id,
                    unit_amount_decimal=int(plan.price * 100),
                    currency="usd",
                    recurring={"interval": calculate_recurring_interval(plan.duration)},
                )

            # Store the Stripe product and price IDs in your database or associate them with the tariff plan
            plan.stripe_product_id = product.id
            plan.stripe_price_id = price.id
            # plan.stripe_price_year = price_year.id
            await session.commit()

            return plan
        except Exception as e:
            # If an error occurs during the Stripe operation, rollback the database transaction
            await session.rollback()
            raise e

    @staticmethod
    @db_session
    async def get_plan_by_id(session, plan_id: int):
        result = await session.execute(select(TariffPlan).where(TariffPlan.id == plan_id))
        tariff_plan = result.scalar()
        if not tariff_plan:
            raise HTTPException(status_code=404, detail="Tariff not found")
        tariff_plan.used_time = None
        return tariff_plan

    @staticmethod
    @db_session
    async def get_plan_without_id(session, plan_id: int):
        result = await session.execute(select(TariffPlan).where(TariffPlan.id != plan_id))
        tariff_plan = [row[0] for row in result.all()]
        if not tariff_plan:
            raise HTTPException(status_code=404, detail="Tariff not found")
        return tariff_plan

    @staticmethod
    @db_session
    async def get_all_plan(session):
        result = await session.execute(
            select(TariffPlan).order_by(
                desc(TariffPlan.updated_at))
        )
        if not result:
            raise HTTPException(status_code=404, detail="Company not found")

        docs = [row[0] for row in result.all()]
        return docs

    @staticmethod
    @db_session
    async def update_plan(session,
                          plan_id: int,
                          data: ParticularUpdateTariffPlan):
        try:
            plan = await session.get(TariffPlan, plan_id)
            if plan is None:
                raise HTTPException(status_code=404, detail="Doctor not found")

            for name, value in data.model_dump(exclude_unset=True).items():
                setattr(plan, name, value)

            await validate_and_sync_with_stripe(plan, data)

            await session.commit()
            return plan
        except IntegrityError as e:
            HTTPException(status_code=400, detail=str(e))

    @staticmethod
    @db_session
    async def delete_plan(session, plan_id: int):
        try:
            query = select(TariffPlan).filter(TariffPlan.id == plan_id)
            result = await session.execute(query)
            plan = result.scalar()
            if plan:
                stripe.Product.delete(plan.stripe_product_id)
                stripe.Price.delete(plan.stripe_price_id)
                await session.delete(plan)
                await session.commit()
            else:
                raise HTTPException(status_code=404, detail="Plan not found")
        except IntegrityError as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="error while deleting plan")

    @staticmethod
    @db_session
    async def get_all_plans_divided(session):
        result_month = await session.execute(
            select(TariffPlan).where(TariffPlan.duration == 1).order_by(
                desc(TariffPlan.price))
        )
        result_year = await session.execute(
            select(TariffPlan).where(TariffPlan.duration == 12).order_by(
                desc(TariffPlan.price))
        )
        if not result_month or not result_year:
            raise HTTPException(status_code=404, detail="Company not found")

        data = {"month": [row[0] for row in result_month.all()],
                "year": [row[0] for row in result_year.all()]}
        return data


async def validate_and_sync_with_stripe(plan, data):
    # Validate and synchronize updates with Stripe
    try:
        # Modify product details in Stripe
        stripe.Product.modify(
            plan.stripe_product_id,
            name=data.title,
            description=data.description
        )

        # If price is updated, modify price details in Stripe
        if data.price is not None:
            stripe.Price.modify(
                plan.stripe_price_id,
                unit_amount_decimal=int(data.price * 100)
            )
    except stripe.error.StripeError as e:
        # Rollback changes if Stripe operation fails
        raise HTTPException(status_code=400, detail=str(e))

