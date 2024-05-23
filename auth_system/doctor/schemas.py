from datetime import datetime
from typing import Annotated
from annotated_types import MinLen, MaxLen
from pydantic import BaseModel, EmailStr, ConfigDict, Field


class CreateDoctorByCompany(BaseModel):
    firstName: str = Field(min_length=3)
    lastName: str = Field(min_length=3)
    email: EmailStr
    position: str
    # password: str
    active: bool = True
    company_id: int
    # last_login: datetime = datetime.now()


class CreateDoctor(BaseModel):
    firstName: str
    lastName: str
    position: str
    email: EmailStr
    password: str
    active: bool = False
    user_tariff_id: int | None = None


class CreateDoctorByGoogle(BaseModel):
    firstName: str
    lastName: str
    email: EmailStr
    active: bool = False
    is_verified: bool = True


class DoctorSchema(BaseModel):
    model_config = ConfigDict(strict=True)

    id: int | None = None
    firstName: str
    lastName: str
    position: str
    email: EmailStr | None = None
    active: bool = True


class CompanyDoctorSchema(BaseModel):
    model_config = ConfigDict(strict=True)

    id: int
    firstName: str
    lastName: str
    position: str
    email: EmailStr | None = None
    active: bool = True
    company_id: int | None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    last_online: datetime | None = None


class CompanyDoctorUpdatePartial(BaseModel):

    active: bool | None = None
    password: str | None = None
    email: EmailStr | None = None
    firstName: str = Field(min_length=3)
    lastName: str = Field(min_length=3)
    position: str | None = None
    # last_online: datetime | None = None
    # company_id: int | None = None


class DoctorUpdatePartial(BaseModel):

    active: bool | None = None
    password: str | None = None
    email: EmailStr | None = None
    firstName: str | None = None
    lastName: str | None = None
    position: str | None = None
    is_verified: bool | None = None
    user_tariff_id: int | None = None


class TokenSchema(BaseModel):
    access_token: str
    refresh_token: str
    doctor_id: int
    role: str | None
    user_info: CompanyDoctorSchema
