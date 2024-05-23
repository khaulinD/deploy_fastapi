from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from db.models.tariff_plan_info import TariffPlanStore
from tariff_plan.schemas import TariffPlanSchema, CreateTariffPlan, ParticularUpdateTariffPlan

router = APIRouter(
    prefix="/tariff_plan",
    tags=["Tariff Plan"],
)


@router.post(
    "",
    response_model=TariffPlanSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_tariff_plan(
    tariff_income: CreateTariffPlan,
):
    tariff = tariff_income.model_dump()
    return await TariffPlanStore.create(data=tariff)


@router.get("/{plan_id}", response_model=TariffPlanSchema)
async def get_plan_by_id(
    plan_id: int
):
    return await TariffPlanStore.get_plan_by_id(plan_id=plan_id)


@router.get("")
async def get_all_plan():
    return await TariffPlanStore.get_all_plans_divided()


@router.patch("/{plan_id}")
async def update_plan_partial(
    plan_id: int,
    plan_update: ParticularUpdateTariffPlan,
):
    return await TariffPlanStore.update_plan(
        plan_id=plan_id,
        data=plan_update)


@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plan(
    plan_id: int,
):
    await TariffPlanStore.delete_plan(plan_id=plan_id)
