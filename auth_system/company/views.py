from fastapi import APIRouter, Depends, BackgroundTasks, Response
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
import random
from auth import utils as auth_utils
from company.schemas import CreateCompany, CompanySchema, CompanyDoctorsSchema, CompanyUpdatePartial
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
async def update_product_partial(
    company_id: int,
    company_update: CompanyUpdatePartial,
):
    return await CompanyStore.update_company(
        company_id=company_id,
        data=company_update)


