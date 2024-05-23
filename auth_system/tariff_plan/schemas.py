from datetime import datetime

from pydantic import BaseModel


class TariffPlanSchema(BaseModel):
    title: str
    description: str
    price: float
    doctor_amount: int | None = None
    duration: int
    created_at: datetime | None = None
    updated_at: datetime | None = None


class TariffPlanSchemaList(BaseModel):
    title: str
    description: str
    price: float
    doctor_amount: int | None = None
    duration: int
    used_time: int | None = None
    refund_time: int | None = None
    active: bool | None = None
    can_upgrade: bool | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None



class CreateTariffPlan(BaseModel):
    title: str
    description: str
    price: float
    doctor_amount: int | None = None
    duration: int


class ParticularUpdateTariffPlan(BaseModel):
    title: str | None = None
    description: str | None = None
    price: float | None = None
    doctor_amount: int | None = None
    duration: int | None = None


class UserTariffPlan(BaseModel):
    tariff_id: int
    time_left: int | None = None
    updated_at: datetime | None = None
    tariff_info: TariffPlanSchema | None


class CreateUserTariffPlan(BaseModel):
    tariff_id: int | None
    payment_intent_id: str | None = None


class ParticularUpdateUserTariffPlan(BaseModel):
    tariff_id: int | None = None
    expired_at: datetime | None = None
    customer: str | None = None
    payment_intent_id: str | None = None

class AllTariffWithActive(BaseModel):
    current_tariff: TariffPlanSchema | None = None
    other_tariff: list[TariffPlanSchemaList] | None = None
