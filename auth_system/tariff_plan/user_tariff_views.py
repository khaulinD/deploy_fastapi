from typing import Optional

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from db.models.company import CompanyStore
from db.models.user_tariff import UserTariffPlanStore
from tariff_plan.schemas import ParticularUpdateUserTariffPlan, UserTariffPlan, CreateUserTariffPlan, \
    AllTariffWithActive

router = APIRouter(
    prefix="/user_tariff",
    tags=["User Tariff Plan"],
)


@router.post(
    "",
    response_model=CreateUserTariffPlan,
    status_code=status.HTTP_201_CREATED,
)
async def create_tariff_plan(
    user_type: str,
    user_id: int,
    tariff_income: CreateUserTariffPlan,
):
    tariff = tariff_income.model_dump()
    return await UserTariffPlanStore.create(user_id=user_id, user_type=user_type, data=tariff)


@router.get("/{plan_id}", response_model=UserTariffPlan)
async def get_plan_by_id(
    plan_id: int
):
    return await UserTariffPlanStore.get_user_plan_by_id(plan_id=plan_id)


@router.get("", response_model=list[UserTariffPlan])
async def get_all_plan():
    return await UserTariffPlanStore.get_all_plan()


@router.patch("/{plan_id}")
async def update_plan_partial(
    plan_id: int,
    plan_update: ParticularUpdateUserTariffPlan,
):
    return await UserTariffPlanStore.update_plan(
        plan_id=plan_id,
        data=plan_update)


@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plan(
    plan_id: int,
):
    await UserTariffPlanStore.delete_plan(plan_id=plan_id)



@router.get("/list/plan")
async def get_all_tariff_with_current(
    request: Request,
):
    payload = request.state.payload
    user = await CompanyStore.get_company_by_id(company_id=payload["sub"])
    return await UserTariffPlanStore.get_all_tariff_with_current(user_tariff=user.user_tariff_id)
