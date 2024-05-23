from datetime import datetime
from typing import Annotated
from annotated_types import MinLen, MaxLen
from pydantic import BaseModel, EmailStr, ConfigDict, Field

from doctor.schemas import CompanyDoctorSchema
from tariff_plan.schemas import TariffPlanSchema, UserTariffPlan


class CreateCompany(BaseModel):
    name: str
    email: EmailStr
    password: str
    active: bool = True
    user_tariff_id: int | None = None


class CreateCompanyByGoogle(BaseModel):
    name: str
    email: EmailStr
    active: bool = False
    is_verified: bool = True


class CompanySchema(BaseModel):
    model_config = ConfigDict(strict=True)
    id: int | None = None
    name: str = Field(..., min_length=3, max_length=100)
    # password: bytes | None = None
    email: EmailStr | None = None
    active: bool
    user_tariff_id: int | None = None
    is_verified: bool | None = None
    role: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class CompanyDoctorsSchema(CompanySchema):

    doctors: list[CompanyDoctorSchema] = []


class CompanyDoctorsSchemaWithAmount(CompanySchema):
    amount_of_pages: int = 1
    user_tariff: UserTariffPlan | None = None
    doctors: list[CompanyDoctorSchema] = []


class CompanyUpdatePartial(BaseModel):
    name: str | None = Field(..., min_length=3, max_length=100)
    active: bool | None = None
    password: str | None = None
    email: EmailStr | None = None
    user_tariff_id: int | None = None
    is_verified: bool | None = None

    stripe_customer_id: str | None = None
    stripe_coupon_id: str | None = None

    has_refunded: bool | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None



class TokenSchema(BaseModel):
    access_token: str
    refresh_token: str
    company_id: int
    role: str | None
    user_info: CompanySchema
