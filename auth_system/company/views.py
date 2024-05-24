from fastapi import APIRouter, Depends, BackgroundTasks, Response, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
import random
from auth import utils as auth_utils
from company.schemas import CreateCompany, CompanySchema, CompanyDoctorsSchema, CompanyUpdatePartial, \
    CompanyUpdateSetting
from core.mailer import send_email_with_credentials
from db.models.company import CompanyStore

router = APIRouter(
    prefix="/company",
    tags=["Company"],
)


@router.post(
    "",
    response_model=CompanySchema,
    # response_model=CompanyTokenSchema | DoctorTokenSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_company(
    company_income: CreateCompany,
    background_tasks: BackgroundTasks,
    response: Response,
):
    company = company_income.model_dump()
    company = await CompanyStore.create(data=company)

    if company:
        await auth_utils.send_verification_code(user=company, background_tasks=background_tasks)
        # res = await generate_tokens_and_set_cookies(company, "company", response)
        return company
    return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"detail": "Error while registering"})


@router.get("/{company_id}", response_model=CompanySchema)
async def get_company_by_id(
    company_id: int
):
    return await CompanyStore.get_company_by_id(company_id=company_id)


@router.get("", response_model=list[CompanySchema])
async def get_all_company():
    return await CompanyStore.get_all_company()


# @router.get("/doctor/{company_id}", response_model=CompanyDoctorsSchema)
# async def get_all_company_with_d(company_id: int):
#     return await CompanyStore.get_company_with_doctors(company_id=company_id)


@router.patch("/{company_id}")
async def update_company_partial(
    company_id: int,
    company_update: CompanyUpdateSetting,
    background_tasks: BackgroundTasks,
):
    if company_update.email or company_update.oldPassword:
        user = await CompanyStore.get_company_clean_by_id(company_id=company_id)
        if company_update.oldPassword and company_update.newPassword:
            if not auth_utils.validate_password(
                    password=company_update.oldPassword,
                    hashed_password=user.password,
            ):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect password")
        new_user = await CompanyStore.update_company(
            company_id=company_id,
            data=company_update)
        if new_user:
            background_tasks.add_task(send_email_with_credentials,
                                      email_to=user.email,
                                      username=user.name,
                                      login=company_update.email if company_update.email else user.email,
                                      password=company_update.newPassword if company_update.newPassword else "********")
        return new_user
    new_user = await CompanyStore.update_company(
        company_id=company_id,
        data=company_update)
    return new_user


